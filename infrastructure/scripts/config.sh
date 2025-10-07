#!/bin/bash

# AWS Meeting Scheduling Agent - Deployment Configuration
# This file contains shared configuration and utility functions for deployment scripts

# Project configuration
export PROJECT_NAME="meeting-scheduling-agent"
export PROJECT_VERSION="1.0.0"

# Default AWS configuration
export DEFAULT_REGION="us-east-1"
export DEFAULT_ENVIRONMENT="dev"

# Stack naming patterns
get_stack_name() {
    local environment="$1"
    local stack_type="$2"
    echo "${PROJECT_NAME}-${environment}-${stack_type}"
}

# Get all stack names for an environment
get_all_stack_names() {
    local environment="$1"
    echo "$(get_stack_name "$environment" "core")"
    echo "$(get_stack_name "$environment" "api")"
    echo "$(get_stack_name "$environment" "web")"
    echo "$(get_stack_name "$environment" "monitoring")"
}

# Environment validation
validate_environment() {
    local environment="$1"
    case "$environment" in
        dev|staging|prod)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# AWS region validation
validate_region() {
    local region="$1"
    # Basic AWS region pattern validation
    if [[ "$region" =~ ^[a-z]{2}-[a-z]+-[0-9]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Check if AWS CLI is configured
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        return 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        return 1
    fi
    
    return 0
}

# Get AWS account ID
get_aws_account_id() {
    aws sts get-caller-identity --query Account --output text 2>/dev/null
}

# Get current AWS region
get_current_region() {
    aws configure get region 2>/dev/null || echo "$DEFAULT_REGION"
}

# Check if CDK is bootstrapped
is_cdk_bootstrapped() {
    local region="$1"
    aws cloudformation describe-stacks \
        --stack-name "CDKToolkit" \
        --region "$region" &> /dev/null
}

# Get stack status
get_stack_status() {
    local stack_name="$1"
    local region="$2"
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$region" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "NOT_FOUND"
}

# Wait for stack operation to complete
wait_for_stack() {
    local stack_name="$1"
    local region="$2"
    local operation="$3" # create, update, delete
    
    case "$operation" in
        create)
            aws cloudformation wait stack-create-complete \
                --stack-name "$stack_name" \
                --region "$region"
            ;;
        update)
            aws cloudformation wait stack-update-complete \
                --stack-name "$stack_name" \
                --region "$region"
            ;;
        delete)
            aws cloudformation wait stack-delete-complete \
                --stack-name "$stack_name" \
                --region "$region"
            ;;
    esac
}

# Generate deployment tags
get_deployment_tags() {
    local environment="$1"
    local additional_tags="$2"
    
    local base_tags="Project=$PROJECT_NAME,Environment=$environment,ManagedBy=CDK,Version=$PROJECT_VERSION"
    
    if [[ -n "$additional_tags" ]]; then
        echo "$base_tags,$additional_tags"
    else
        echo "$base_tags"
    fi
}

# Create backup directory
create_backup_dir() {
    local environment="$1"
    local backup_type="$2"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="backups/${timestamp}_${environment}_${backup_type}"
    
    mkdir -p "$backup_dir"
    echo "$backup_dir"
}

# Log deployment event
log_deployment_event() {
    local environment="$1"
    local event_type="$2"
    local message="$3"
    
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local log_file="logs/deployment_${environment}.log"
    
    mkdir -p "$(dirname "$log_file")"
    echo "[$timestamp] [$event_type] $message" >> "$log_file"
}

# Check deployment prerequisites
check_deployment_prerequisites() {
    local environment="$1"
    local region="$2"
    
    # Validate environment
    if ! validate_environment "$environment"; then
        echo "Invalid environment: $environment"
        return 1
    fi
    
    # Validate region
    if ! validate_region "$region"; then
        echo "Invalid AWS region: $region"
        return 1
    fi
    
    # Check AWS CLI
    if ! check_aws_cli; then
        echo "AWS CLI not configured or not working"
        return 1
    fi
    
    # Check CDK
    if ! command -v cdk &> /dev/null; then
        echo "AWS CDK not installed"
        return 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "Node.js not installed"
        return 1
    fi
    
    return 0
}

# Export functions for use in other scripts
export -f get_stack_name
export -f get_all_stack_names
export -f validate_environment
export -f validate_region
export -f check_aws_cli
export -f get_aws_account_id
export -f get_current_region
export -f is_cdk_bootstrapped
export -f get_stack_status
export -f wait_for_stack
export -f get_deployment_tags
export -f create_backup_dir
export -f log_deployment_event
export -f check_deployment_prerequisites