#!/bin/bash

# AWS Meeting Scheduling Agent - CDK Deployment Script
# This script handles environment-specific deployments with proper error handling and rollback capabilities

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="meeting-scheduling-agent"

# Default values
ENVIRONMENT="dev"
REGION="us-east-1"
PROFILE=""
BOOTSTRAP_ONLY=false
ROLLBACK=false
FORCE_DEPLOY=false
VERBOSE=false
DRY_RUN=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy AWS Meeting Scheduling Agent infrastructure using CDK

OPTIONS:
    -e, --environment ENV    Environment to deploy (dev, staging, prod) [default: dev]
    -r, --region REGION      AWS region [default: us-east-1]
    -p, --profile PROFILE    AWS profile to use
    -b, --bootstrap-only     Only run CDK bootstrap
    -R, --rollback          Rollback to previous deployment
    -f, --force             Force deployment without confirmation
    -v, --verbose           Enable verbose output
    -d, --dry-run           Show what would be deployed without executing
    -h, --help              Show this help message

EXAMPLES:
    $0 -e dev -r us-east-1
    $0 -e prod -p production-profile --force
    $0 --bootstrap-only -e staging
    $0 --rollback -e dev

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -b|--bootstrap-only)
            BOOTSTRAP_ONLY=true
            shift
            ;;
        -R|--rollback)
            ROLLBACK=true
            shift
            ;;
        -f|--force)
            FORCE_DEPLOY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
    exit 1
fi

# Set AWS profile if provided
if [[ -n "$PROFILE" ]]; then
    export AWS_PROFILE="$PROFILE"
    log_info "Using AWS profile: $PROFILE"
fi

# Set verbose mode
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if CDK is installed
    if ! command -v cdk &> /dev/null; then
        log_error "AWS CDK is not installed. Please install it first: npm install -g aws-cdk"
        exit 1
    fi
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid. Please run 'aws configure' or set AWS_PROFILE."
        exit 1
    fi
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_info "AWS Account ID: $AWS_ACCOUNT_ID"
    log_info "AWS Region: $REGION"
    
    log_success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "node_modules" ]]; then
        npm install
    else
        log_info "Dependencies already installed"
    fi
    
    log_success "Dependencies installed"
}

# Build the project
build_project() {
    log_info "Building project..."
    cd "$PROJECT_ROOT"
    
    npm run build
    
    log_success "Project built successfully"
}

# Bootstrap CDK
bootstrap_cdk() {
    log_info "Bootstrapping CDK for account $AWS_ACCOUNT_ID in region $REGION..."
    
    cd "$PROJECT_ROOT"
    
    # Bootstrap with specific tags and configuration
    cdk bootstrap aws://$AWS_ACCOUNT_ID/$REGION \
        --context "meeting-scheduling-agent:environment=$ENVIRONMENT" \
        --context "meeting-scheduling-agent:region=$REGION" \
        --tags "Project=meeting-scheduling-agent" \
        --tags "Environment=$ENVIRONMENT" \
        --cloudformation-execution-policies "arn:aws:iam::aws:policy/AdministratorAccess"
    
    log_success "CDK bootstrap completed"
}

# Get stack names
get_stack_names() {
    echo "${PROJECT_NAME}-${ENVIRONMENT}-core"
    echo "${PROJECT_NAME}-${ENVIRONMENT}-api"
    echo "${PROJECT_NAME}-${ENVIRONMENT}-web"
    echo "${PROJECT_NAME}-${ENVIRONMENT}-monitoring"
}

# Deploy stacks
deploy_stacks() {
    log_info "Deploying stacks for environment: $ENVIRONMENT"
    
    cd "$PROJECT_ROOT"
    
    local cdk_args=(
        "--context" "meeting-scheduling-agent:environment=$ENVIRONMENT"
        "--context" "meeting-scheduling-agent:region=$REGION"
        "--require-approval" "never"
    )
    
    if [[ "$FORCE_DEPLOY" == "false" ]]; then
        cdk_args+=("--require-approval" "any-change")
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run mode - showing what would be deployed:"
        cdk diff --all "${cdk_args[@]}"
        return 0
    fi
    
    # Deploy stacks in order (dependencies are handled by CDK)
    log_info "Deploying all stacks..."
    cdk deploy --all "${cdk_args[@]}"
    
    log_success "All stacks deployed successfully"
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment for environment: $ENVIRONMENT"
    
    cd "$PROJECT_ROOT"
    
    # Get stack names in reverse order for rollback
    local stacks=($(get_stack_names | tac))
    
    for stack in "${stacks[@]}"; do
        log_info "Rolling back stack: $stack"
        
        # Check if stack exists
        if aws cloudformation describe-stacks --stack-name "$stack" --region "$REGION" &> /dev/null; then
            # Get the previous template from stack events or use destroy
            log_warning "Destroying stack: $stack (rollback strategy)"
            cdk destroy "$stack" \
                --context "meeting-scheduling-agent:environment=$ENVIRONMENT" \
                --context "meeting-scheduling-agent:region=$REGION" \
                --force
        else
            log_info "Stack $stack does not exist, skipping rollback"
        fi
    done
    
    log_success "Rollback completed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    local stacks=($(get_stack_names))
    local all_healthy=true
    
    for stack in "${stacks[@]}"; do
        log_info "Checking stack: $stack"
        
        local stack_status=$(aws cloudformation describe-stacks \
            --stack-name "$stack" \
            --region "$REGION" \
            --query 'Stacks[0].StackStatus' \
            --output text 2>/dev/null || echo "NOT_FOUND")
        
        if [[ "$stack_status" == "CREATE_COMPLETE" || "$stack_status" == "UPDATE_COMPLETE" ]]; then
            log_success "Stack $stack is healthy (Status: $stack_status)"
        else
            log_error "Stack $stack is not healthy (Status: $stack_status)"
            all_healthy=false
        fi
    done
    
    if [[ "$all_healthy" == "true" ]]; then
        log_success "All stacks are healthy"
        
        # Get and display important outputs
        display_outputs
    else
        log_error "Some stacks are not healthy"
        return 1
    fi
}

# Display stack outputs
display_outputs() {
    log_info "Deployment outputs:"
    
    local stacks=($(get_stack_names))
    
    for stack in "${stacks[@]}"; do
        echo ""
        log_info "Outputs for $stack:"
        
        aws cloudformation describe-stacks \
            --stack-name "$stack" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey!=`null`].[OutputKey,OutputValue,Description]' \
            --output table 2>/dev/null || log_warning "No outputs found for $stack"
    done
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Deployment failed with exit code $exit_code"
        
        if [[ "$ROLLBACK" == "false" ]]; then
            log_info "To rollback this deployment, run: $0 --rollback -e $ENVIRONMENT -r $REGION"
        fi
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution
main() {
    log_info "Starting deployment for AWS Meeting Scheduling Agent"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
    
    check_prerequisites
    
    if [[ "$ROLLBACK" == "true" ]]; then
        rollback_deployment
        return 0
    fi
    
    install_dependencies
    build_project
    
    # Always bootstrap if it's the first deployment or if explicitly requested
    if [[ "$BOOTSTRAP_ONLY" == "true" ]]; then
        bootstrap_cdk
        log_success "Bootstrap completed. Run without --bootstrap-only to deploy stacks."
        return 0
    fi
    
    # Check if CDK is bootstrapped
    if ! aws cloudformation describe-stacks --stack-name "CDKToolkit" --region "$REGION" &> /dev/null; then
        log_info "CDK not bootstrapped, bootstrapping now..."
        bootstrap_cdk
    fi
    
    deploy_stacks
    verify_deployment
    
    log_success "Deployment completed successfully!"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
}

# Run main function
main "$@"