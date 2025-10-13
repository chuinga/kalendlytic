# Test AWS Meeting Scheduling Agent Deployment
# PowerShell script to test deployed backend

Write-Host "🧪 Testing AWS Meeting Scheduling Agent Deployment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Get API Gateway URL from CloudFormation
Write-Host "`n🔍 Getting API Gateway URL..." -ForegroundColor Yellow
try {
    $apiUrl = aws cloudformation describe-stacks --stack-name "meeting-scheduling-agent-dev-api" --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text
    if ($apiUrl -and $apiUrl -ne "None") {
        Write-Host "✅ API Gateway URL: $apiUrl" -ForegroundColor Green
        
        # Test health endpoint
        Write-Host "`n🏥 Testing health endpoint..." -ForegroundColor Yellow
        try {
            $healthResponse = Invoke-RestMethod -Uri "$apiUrl/health" -Method Get -TimeoutSec 30
            Write-Host "✅ Health check passed: $($healthResponse | ConvertTo-Json)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # Test Nova Pro endpoint
        Write-Host "`n🤖 Testing Nova Pro integration..." -ForegroundColor Yellow
        try {
            $novaResponse = Invoke-RestMethod -Uri "$apiUrl/nova/test" -Method Get -TimeoutSec 30
            Write-Host "✅ Nova Pro test passed: $($novaResponse | ConvertTo-Json)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Nova Pro test failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # Test meeting scheduling endpoint
        Write-Host "`n📅 Testing meeting scheduling..." -ForegroundColor Yellow
        $testMeeting = @{
            title = "Test Meeting"
            duration = 30
            attendees = @("test@example.com")
        } | ConvertTo-Json
        
        try {
            $scheduleResponse = Invoke-RestMethod -Uri "$apiUrl/agent/schedule" -Method Post -Body $testMeeting -ContentType "application/json" -TimeoutSec 30
            Write-Host "✅ Meeting scheduling test passed: $($scheduleResponse | ConvertTo-Json)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Meeting scheduling test failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
    } else {
        Write-Host "❌ Could not retrieve API Gateway URL" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to get API Gateway URL: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Cognito User Pool
Write-Host "`n👤 Testing Cognito User Pool..." -ForegroundColor Yellow
try {
    $userPoolId = aws cloudformation describe-stacks --stack-name "meeting-scheduling-agent-dev-core" --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text
    if ($userPoolId -and $userPoolId -ne "None") {
        Write-Host "✅ Cognito User Pool ID: $userPoolId" -ForegroundColor Green
        
        # Describe user pool
        $userPoolInfo = aws cognito-idp describe-user-pool --user-pool-id $userPoolId --output json | ConvertFrom-Json
        Write-Host "✅ User Pool Status: $($userPoolInfo.UserPool.Status)" -ForegroundColor Green
    } else {
        Write-Host "❌ Could not retrieve Cognito User Pool ID" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Cognito test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test CloudFront Distribution
Write-Host "`n🌐 Testing CloudFront Distribution..." -ForegroundColor Yellow
try {
    $cloudFrontUrl = aws cloudformation describe-stacks --stack-name "meeting-scheduling-agent-dev-web" --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text
    if ($cloudFrontUrl -and $cloudFrontUrl -ne "None") {
        Write-Host "✅ CloudFront URL: $cloudFrontUrl" -ForegroundColor Green
        
        # Test CloudFront endpoint
        try {
            $response = Invoke-WebRequest -Uri $cloudFrontUrl -Method Head -TimeoutSec 30
            Write-Host "✅ CloudFront is accessible (Status: $($response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ CloudFront test failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Could not retrieve CloudFront URL" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ CloudFront test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# List all deployed stacks
Write-Host "`n📋 Deployed CloudFormation Stacks:" -ForegroundColor Yellow
try {
    $stacks = aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[?contains(StackName, `meeting-scheduling-agent`)].{Name:StackName,Status:StackStatus,Created:CreationTime}' --output table
    Write-Host $stacks -ForegroundColor White
} catch {
    Write-Host "❌ Could not list stacks: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✨ Deployment testing completed!" -ForegroundColor Green