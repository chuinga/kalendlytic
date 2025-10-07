# AWS Meeting Scheduling Agent - CDK Deployment Script (PowerShell)
# This script handles environment-specific deployments with proper error handling and rollback capabilities

param(
    [Parameter(HelpMessage="Environment to deploy (dev, staging, prod)")]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",
    
    [Parameter(HelpMessage="AWS region")]
    [string]$Region = "us-east-1",
    
    [Parameter(HelpMessage="AWS profile to use")]
    [string]$Profile = "",
    
    [Parameter(HelpMessage="Only run CDK bootstrap")]
    [switch]$BootstrapOnly,
    
    [Parameter(HelpMessage="Rollback to previous deployment")]
    [switch]$Rollback,
    
    [Parameter(HelpMessage="Force deployment without confirmation")]
    [switch]$Force,
    
    [Parameter(HelpMessage="Enable verbose output")]
    [switch]$Verbose,
    
    [Parameter(HelpMessage="Show what would be deployed without executing")]
    [switch]$DryRun,
    
    [Parameter(HelpMessage="Show help message")]
    [switch]$Help
)

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ProjectName = "meeting-scheduling-agent"

# Error handling
$ErrorActionPreference = "Stop"

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Usage function
function Show-Usage {
    @"
Usage: .\deploy.ps1 [OPTIONS]

Deploy AWS Meeting Scheduling Agent infrastructure using CDK

OPTIONS:
    -Environment ENV     Environment to deploy (dev, staging, prod) [default: dev]
    -Region REGION       AWS region [default: us-east-1]
    -Profile PROFILE     AWS profile to use
    -BootstrapOnly       Only run CDK bootstrap
    -Rollback           Rollback to previous deployment
    -Force              Force deployment without confirmation
    -Verbose            Enable verbose output
    -DryRun             Show what would be deployed without executing
    -Help               Show this help message

EXAMPLES:
    .\deploy.ps1 -Environment dev -Region us-east-1
    .\deploy.ps1 -Environment prod -Profile production-profile -Force
    .\deploy.ps1 -BootstrapOnly -Environment staging
    .\deploy.ps1 -Rollback -Environment dev

"@
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Set AWS profile if provided
if ($Profile) {
    $env:AWS_PROFILE = $Profile
    Write-Info "Using AWS profile: $Profile"
}

# Set verbose mode
if ($Verbose) {
    $VerbosePreference = "Continue"
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    try {
        $null = Get-Command aws -ErrorAction Stop
    }
    catch {
        Write-Error "AWS CLI is not installed. Please install it first."
        exit 1
    }
    
    # Check if CDK is installed
    try {
        $null = Get-Command cdk -ErrorAction Stop
    }
    catch {
        Write-Error "AWS CDK is not installed. Please install it first: npm install -g aws-cdk"
        exit 1
    }
    
    # Check if Node.js is installed
    try {
        $null = Get-Command node -ErrorAction Stop
    }
    catch {
        Write-Error "Node.js is not installed. Please install it first."
        exit 1
    }
    
    # Check AWS credentials
    try {
        $null = aws sts get-caller-identity 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "AWS credentials check failed"
        }
    }
    catch {
        Write-Error "AWS credentials not configured or invalid. Please run 'aws configure' or set AWS_PROFILE."
        exit 1
    }
    
    # Get AWS account ID
    $script:AwsAccountId = aws sts get-caller-identity --query Account --output text
    Write-Info "AWS Account ID: $AwsAccountId"
    Write-Info "AWS Region: $Region"
    
    Write-Success "Prerequisites check passed"
}

# Install dependencies
function Install-Dependencies {
    Write-Info "Installing dependencies..."
    Set-Location $ProjectRoot
    
    if (-not (Test-Path "node_modules")) {
        npm install
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install dependencies"
        }
    }
    else {
        Write-Info "Dependencies already installed"
    }
    
    Write-Success "Dependencies installed"
}

# Build the project
function Build-Project {
    Write-Info "Building project..."
    Set-Location $ProjectRoot
    
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to build project"
    }
    
    Write-Success "Project built successfully"
}

# Bootstrap CDK
function Initialize-CdkBootstrap {
    Write-Info "Bootstrapping CDK for account $AwsAccountId in region $Region..."
    
    Set-Location $ProjectRoot
    
    # Bootstrap with specific tags and configuration
    cdk bootstrap "aws://$AwsAccountId/$Region" `
        --context "meeting-scheduling-agent:environment=$Environment" `
        --context "meeting-scheduling-agent:region=$Region" `
        --tags "Project=meeting-scheduling-agent" `
        --tags "Environment=$Environment" `
        --cloudformation-execution-policies "arn:aws:iam::aws:policy/AdministratorAccess"
    
    if ($LASTEXITCODE -ne 0) {
        throw "CDK bootstrap failed"
    }
    
    Write-Success "CDK bootstrap completed"
}

# Get stack names
function Get-StackNames {
    return @(
        "$ProjectName-$Environment-core",
        "$ProjectName-$Environment-api",
        "$ProjectName-$Environment-web",
        "$ProjectName-$Environment-monitoring"
    )
}

# Deploy stacks
function Deploy-Stacks {
    Write-Info "Deploying stacks for environment: $Environment"
    
    Set-Location $ProjectRoot
    
    $cdkArgs = @(
        "--context", "meeting-scheduling-agent:environment=$Environment",
        "--context", "meeting-scheduling-agent:region=$Region",
        "--require-approval", "never"
    )
    
    if (-not $Force) {
        $cdkArgs[-1] = "any-change"
    }
    
    if ($DryRun) {
        Write-Info "Dry run mode - showing what would be deployed:"
        cdk diff --all @cdkArgs
        return
    }
    
    # Deploy stacks in order (dependencies are handled by CDK)
    Write-Info "Deploying all stacks..."
    cdk deploy --all @cdkArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "Stack deployment failed"
    }
    
    Write-Success "All stacks deployed successfully"
}

# Rollback deployment
function Invoke-Rollback {
    Write-Warning "Rolling back deployment for environment: $Environment"
    
    Set-Location $ProjectRoot
    
    # Get stack names in reverse order for rollback
    $stacks = Get-StackNames
    [array]::Reverse($stacks)
    
    foreach ($stack in $stacks) {
        Write-Info "Rolling back stack: $stack"
        
        # Check if stack exists
        try {
            $null = aws cloudformation describe-stacks --stack-name $stack --region $Region 2>$null
            if ($LASTEXITCODE -eq 0) {
                # Get the previous template from stack events or use destroy
                Write-Warning "Destroying stack: $stack (rollback strategy)"
                cdk destroy $stack `
                    --context "meeting-scheduling-agent:environment=$Environment" `
                    --context "meeting-scheduling-agent:region=$Region" `
                    --force
            }
        }
        catch {
            Write-Info "Stack $stack does not exist, skipping rollback"
        }
    }
    
    Write-Success "Rollback completed"
}

# Verify deployment
function Test-Deployment {
    Write-Info "Verifying deployment..."
    
    $stacks = Get-StackNames
    $allHealthy = $true
    
    foreach ($stack in $stacks) {
        Write-Info "Checking stack: $stack"
        
        try {
            $stackStatus = aws cloudformation describe-stacks `
                --stack-name $stack `
                --region $Region `
                --query 'Stacks[0].StackStatus' `
                --output text 2>$null
            
            if ($LASTEXITCODE -ne 0) {
                $stackStatus = "NOT_FOUND"
            }
        }
        catch {
            $stackStatus = "NOT_FOUND"
        }
        
        if ($stackStatus -eq "CREATE_COMPLETE" -or $stackStatus -eq "UPDATE_COMPLETE") {
            Write-Success "Stack $stack is healthy (Status: $stackStatus)"
        }
        else {
            Write-Error "Stack $stack is not healthy (Status: $stackStatus)"
            $allHealthy = $false
        }
    }
    
    if ($allHealthy) {
        Write-Success "All stacks are healthy"
        Show-Outputs
    }
    else {
        Write-Error "Some stacks are not healthy"
        throw "Deployment verification failed"
    }
}

# Display stack outputs
function Show-Outputs {
    Write-Info "Deployment outputs:"
    
    $stacks = Get-StackNames
    
    foreach ($stack in $stacks) {
        Write-Host ""
        Write-Info "Outputs for $stack:"
        
        try {
            aws cloudformation describe-stacks `
                --stack-name $stack `
                --region $Region `
                --query 'Stacks[0].Outputs[?OutputKey!=`null`].[OutputKey,OutputValue,Description]' `
                --output table 2>$null
            
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "No outputs found for $stack"
            }
        }
        catch {
            Write-Warning "No outputs found for $stack"
        }
    }
}

# Main execution
function Main {
    try {
        Write-Info "Starting deployment for AWS Meeting Scheduling Agent"
        Write-Info "Environment: $Environment"
        Write-Info "Region: $Region"
        
        Test-Prerequisites
        
        if ($Rollback) {
            Invoke-Rollback
            return
        }
        
        Install-Dependencies
        Build-Project
        
        # Always bootstrap if it's the first deployment or if explicitly requested
        if ($BootstrapOnly) {
            Initialize-CdkBootstrap
            Write-Success "Bootstrap completed. Run without -BootstrapOnly to deploy stacks."
            return
        }
        
        # Check if CDK is bootstrapped
        try {
            $null = aws cloudformation describe-stacks --stack-name "CDKToolkit" --region $Region 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Info "CDK not bootstrapped, bootstrapping now..."
                Initialize-CdkBootstrap
            }
        }
        catch {
            Write-Info "CDK not bootstrapped, bootstrapping now..."
            Initialize-CdkBootstrap
        }
        
        Deploy-Stacks
        Test-Deployment
        
        Write-Success "Deployment completed successfully!"
        Write-Info "Environment: $Environment"
        Write-Info "Region: $Region"
    }
    catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        
        if (-not $Rollback) {
            Write-Info "To rollback this deployment, run: .\deploy.ps1 -Rollback -Environment $Environment -Region $Region"
        }
        
        exit 1
    }
}

# Run main function
Main