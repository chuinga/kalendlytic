#!/bin/bash

# AWS Meeting Scheduling Agent - Deployment Validation Script
# This script validates the deployment and performs health checks

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="meeting-scheduling-agent"

# Source shared configuration
source "$SCRIPT_DIR/config.sh"

# Default values
ENVIRONMENT="dev"
REGION="eu-west-1"
PROFILE=""
VERBOSE=false
DETAILED=false

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

Validate AWS Meeting Scheduling Agent deployment

OPTIONS:
    -e, --environment ENV   Environment to validate (dev, staging, prod) [default: dev]
    -r, --region REGION     AWS region [default: eu-west-1]
    -p, --profile PROFILE   AWS profile to use
    -d, --detailed         Perform detailed validation checks
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

EXAMPLES:
    $0 -e dev
    $0 -e prod -p production-profile --detailed
    $0 --verbose -e staging

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
        -d|--detailed)
            DETAILED=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
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
if ! validate_environment "$ENVIRONMENT"; then
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

# Validate stack status
validate_stack_status() {
    local stack_name="$1"
    local status=$(get_stack_status "$stack_name" "$REGION")
    
    case "$status" in
        CREATE_COMPLETE|UPDATE_COMPLETE)
            log_success "Stack $stack_name is healthy (Status: $status)"
            return 0
            ;;
        CREATE_IN_PROGRESS|UPDATE_IN_PROGRESS)
            log_warning "Stack $stack_name is updating (Status: $status)"
            return 1
            ;;
        CREATE_FAILED|UPDATE_FAILED|ROLLBACK_COMPLETE|ROLLBACK_FAILED)
            log_error "Stack $stack_name is in failed state (Status: $status)"
            return 1
            ;;
        NOT_FOUND)
            log_error "Stack $stack_name not found"
            return 1
            ;;
        *)
            log_warning "Stack $stack_name has unknown status: $status"
            return 1
            ;;
    esac
}

# Validate API Gateway endpoints
validate_api_endpoints() {
    log_info "Validating API Gateway endpoints..."
    
    local api_stack="${PROJECT_NAME}-${ENVIRONMENT}-api"
    
    # Get API Gateway URL from stack outputs
    local api_url=$(aws cloudformation describe-stacks \
        --stack-name "$api_stack" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$api_url" ]]; then
        log_info "API Gateway URL: $api_url"
        
        # Test health endpoint
        if command -v curl &> /dev/null; then
            local health_response=$(curl -s -o /dev/null -w "%{http_code}" "${api_url}/health" || echo "000")
            
            if [[ "$health_response" == "200" ]]; then
                log_success "API health endpoint is responding"
            else
                log_warning "API health endpoint returned status: $health_response"
            fi
        else
            log_info "curl not available, skipping endpoint test"
        fi
    else
        log_warning "API Gateway URL not found in stack outputs"
    fi
}

# Validate DynamoDB tables
validate_dynamodb_tables() {
    log_info "Validating DynamoDB tables..."
    
    local core_stack="${PROJECT_NAME}-${ENVIRONMENT}-core"
    
    # Get table names from stack outputs
    local tables=$(aws cloudformation describe-stacks \
        --stack-name "$core_stack" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?contains(OutputKey, `Table`)].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$tables" ]]; then
        for table in $tables; do
            local table_status=$(aws dynamodb describe-table \
                --table-name "$table" \
                --region "$REGION" \
                --query 'Table.TableStatus' \
                --output text 2>/dev/null || echo "NOT_FOUND")
            
            if [[ "$table_status" == "ACTIVE" ]]; then
                log_success "DynamoDB table $table is active"
            else
                log_error "DynamoDB table $table status: $table_status"
            fi
        done
    else
        log_warning "No DynamoDB tables found in stack outputs"
    fi
}

# Validate Lambda functions
validate_lambda_functions() {
    log_info "Validating Lambda functions..."
    
    local api_stack="${PROJECT_NAME}-${ENVIRONMENT}-api"
    
    # Get Lambda function names from stack resources
    local functions=$(aws cloudformation list-stack-resources \
        --stack-name "$api_stack" \
        --region "$REGION" \
        --query 'StackResourceSummaries[?ResourceType==`AWS::Lambda::Function`].PhysicalResourceId' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$functions" ]]; then
        for function in $functions; do
            local function_state=$(aws lambda get-function \
                --function-name "$function" \
                --region "$REGION" \
                --query 'Configuration.State' \
                --output text 2>/dev/null || echo "NOT_FOUND")
            
            if [[ "$function_state" == "Active" ]]; then
                log_success "Lambda function $function is active"
            else
                log_error "Lambda function $function state: $function_state"
            fi
        done
    else
        log_warning "No Lambda functions found in stack resources"
    fi
}

# Validate CloudFront distribution
validate_cloudfront() {
    log_info "Validating CloudFront distribution..."
    
    local web_stack="${PROJECT_NAME}-${ENVIRONMENT}-web"
    
    # Get CloudFront distribution ID from stack outputs
    local distribution_id=$(aws cloudformation describe-stacks \
        --stack-name "$web_stack" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$distribution_id" ]]; then
        local distribution_status=$(aws cloudfront get-distribution \
            --id "$distribution_id" \
            --query 'Distribution.Status' \
            --output text 2>/dev/null || echo "NOT_FOUND")
        
        if [[ "$distribution_status" == "Deployed" ]]; then
            log_success "CloudFront distribution is deployed"
        else
            log_warning "CloudFront distribution status: $distribution_status"
        fi
    else
        log_warning "CloudFront distribution ID not found in stack outputs"
    fi
}

# Validate monitoring setup
validate_monitoring() {
    log_info "Validating monitoring setup..."
    
    local monitoring_stack="${PROJECT_NAME}-${ENVIRONMENT}-monitoring"
    
    # Check if monitoring stack exists
    local monitoring_status=$(get_stack_status "$monitoring_stack" "$REGION")
    
    if [[ "$monitoring_status" == "CREATE_COMPLETE" || "$monitoring_status" == "UPDATE_COMPLETE" ]]; then
        log_success "Monitoring stack is deployed"
        
        # Check CloudWatch dashboard
        local dashboard_name="${PROJECT_NAME}-${ENVIRONMENT}-dashboard"
        if aws cloudwatch get-dashboard --dashboard-name "$dashboard_name" --region "$REGION" &> /dev/null; then
            log_success "CloudWatch dashboard is available"
        else
            log_info "CloudWatch dashboard not found (may be optional)"
        fi
    else
        log_warning "Monitoring stack status: $monitoring_status"
    fi
}

# Perform detailed validation
detailed_validation() {
    log_info "Performing detailed validation checks..."
    
    # Check secrets
    log_info "Checking secrets configuration..."
    local secret_prefix="/${PROJECT_NAME}/${ENVIRONMENT}"
    local secret_count=$(aws ssm get-parameters-by-path \
        --path "$secret_prefix" \
        --region "$REGION" \
        --query 'length(Parameters)' \
        --output text 2>/dev/null || echo "0")
    
    if [[ "$secret_count" -gt 0 ]]; then
        log_success "Found $secret_count secrets in Parameter Store"
    else
        log_warning "No secrets found in Parameter Store"
    fi
    
    # Check IAM roles
    log_info "Checking IAM roles..."
    local role_count=$(aws iam list-roles \
        --query "length(Roles[?contains(RoleName, '${PROJECT_NAME}-${ENVIRONMENT}')])" \
        --output text 2>/dev/null || echo "0")
    
    if [[ "$role_count" -gt 0 ]]; then
        log_success "Found $role_count IAM roles for the project"
    else
        log_warning "No project-specific IAM roles found"
    fi
    
    # Check S3 buckets
    log_info "Checking S3 buckets..."
    local bucket_count=$(aws s3api list-buckets \
        --query "length(Buckets[?contains(Name, '${PROJECT_NAME}-${ENVIRONMENT}')])" \
        --output text 2>/dev/null || echo "0")
    
    if [[ "$bucket_count" -gt 0 ]]; then
        log_success "Found $bucket_count S3 buckets for the project"
    else
        log_warning "No project-specific S3 buckets found"
    fi
}

# Generate validation report
generate_report() {
    log_info "Generating validation report..."
    
    local report_file="validation_report_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "AWS Meeting Scheduling Agent - Deployment Validation Report"
        echo "=========================================================="
        echo "Environment: $ENVIRONMENT"
        echo "Region: $REGION"
        echo "Validation Time: $(date)"
        echo "AWS Account: $(get_aws_account_id)"
        echo ""
        
        echo "Stack Status Summary:"
        echo "--------------------"
        local stacks=($(get_all_stack_names "$ENVIRONMENT"))
        for stack in "${stacks[@]}"; do
            local status=$(get_stack_status "$stack" "$REGION")
            echo "  $stack: $status"
        done
        
        echo ""
        echo "Validation completed at $(date)"
    } > "$report_file"
    
    log_success "Validation report saved to: $report_file"
}

# Main validation function
main() {
    log_info "Starting deployment validation for AWS Meeting Scheduling Agent"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
    
    # Check prerequisites
    if ! check_deployment_prerequisites "$ENVIRONMENT" "$REGION"; then
        log_error "Prerequisites check failed"
        exit 1
    fi
    
    local validation_passed=true
    
    # Validate all stacks
    log_info "Validating stack deployments..."
    local stacks=($(get_all_stack_names "$ENVIRONMENT"))
    
    for stack in "${stacks[@]}"; do
        if ! validate_stack_status "$stack"; then
            validation_passed=false
        fi
    done
    
    # Validate individual components
    validate_api_endpoints || validation_passed=false
    validate_dynamodb_tables || validation_passed=false
    validate_lambda_functions || validation_passed=false
    validate_cloudfront || validation_passed=false
    validate_monitoring || validation_passed=false
    
    # Perform detailed validation if requested
    if [[ "$DETAILED" == "true" ]]; then
        detailed_validation
    fi
    
    # Generate report
    generate_report
    
    # Final result
    if [[ "$validation_passed" == "true" ]]; then
        log_success "Deployment validation completed successfully!"
        log_info "All components are healthy and operational"
        exit 0
    else
        log_error "Deployment validation found issues"
        log_info "Check the validation report for details"
        exit 1
    fi
}

# Run main function
main "$@"