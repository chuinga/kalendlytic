#!/bin/bash

# AWS Meeting Scheduling Agent - CDK Bootstrap Script
# This script handles CDK bootstrapping for different environments and regions

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="meeting-scheduling-agent"

# Default values
ENVIRONMENT="dev"
REGION="eu-west-1"
PROFILE=""
VERBOSE=false
FORCE=false

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

Bootstrap AWS CDK for Meeting Scheduling Agent

OPTIONS:
    -e, --environment ENV    Environment (dev, staging, prod) [default: dev]
    -r, --region REGION      AWS region [default: eu-west-1]
    -p, --profile PROFILE    AWS profile to use
    -f, --force             Force bootstrap even if already exists
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

EXAMPLES:
    $0 -e dev -r eu-west-1
    $0 -e prod -p production-profile
    $0 --force -e staging

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
        -f|--force)
            FORCE=true
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

# Check if CDK is already bootstrapped
check_bootstrap_status() {
    log_info "Checking CDK bootstrap status..."
    
    if aws cloudformation describe-stacks --stack-name "CDKToolkit" --region "$REGION" &> /dev/null; then
        log_info "CDK is already bootstrapped in region $REGION"
        
        if [[ "$FORCE" == "false" ]]; then
            log_warning "Use --force to re-bootstrap"
            return 1
        else
            log_info "Force flag set, will re-bootstrap"
        fi
    else
        log_info "CDK is not bootstrapped in region $REGION"
    fi
    
    return 0
}

# Bootstrap CDK
bootstrap_cdk() {
    log_info "Bootstrapping CDK for account $AWS_ACCOUNT_ID in region $REGION..."
    
    cd "$PROJECT_ROOT"
    
    # Create bootstrap command with environment-specific configuration
    local bootstrap_args=(
        "aws://$AWS_ACCOUNT_ID/$REGION"
        "--context" "meeting-scheduling-agent:environment=$ENVIRONMENT"
        "--context" "meeting-scheduling-agent:region=$REGION"
        "--tags" "Project=meeting-scheduling-agent"
        "--tags" "Environment=$ENVIRONMENT"
        "--tags" "ManagedBy=CDK"
        "--cloudformation-execution-policies" "arn:aws:iam::aws:policy/AdministratorAccess"
        "--bootstrap-bucket-name" "cdk-${PROJECT_NAME}-${ENVIRONMENT}-${AWS_ACCOUNT_ID}-${REGION}"
        "--bootstrap-kms-key-id" "alias/cdk-${PROJECT_NAME}-${ENVIRONMENT}-key"
        "--qualifier" "${ENVIRONMENT}${REGION:0:3}"
    )
    
    # Add force flag if specified
    if [[ "$FORCE" == "true" ]]; then
        bootstrap_args+=("--force")
    fi
    
    # Run bootstrap
    cdk bootstrap "${bootstrap_args[@]}"
    
    log_success "CDK bootstrap completed"
}

# Verify bootstrap
verify_bootstrap() {
    log_info "Verifying CDK bootstrap..."
    
    # Check if CDKToolkit stack exists and is in good state
    local stack_status=$(aws cloudformation describe-stacks \
        --stack-name "CDKToolkit" \
        --region "$REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [[ "$stack_status" == "CREATE_COMPLETE" || "$stack_status" == "UPDATE_COMPLETE" ]]; then
        log_success "CDK bootstrap verification passed (Status: $stack_status)"
        
        # Display bootstrap resources
        log_info "Bootstrap resources:"
        aws cloudformation describe-stacks \
            --stack-name "CDKToolkit" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey!=`null`].[OutputKey,OutputValue,Description]' \
            --output table 2>/dev/null || log_warning "No outputs found"
    else
        log_error "CDK bootstrap verification failed (Status: $stack_status)"
        return 1
    fi
}

# Display bootstrap information
display_bootstrap_info() {
    log_info "CDK Bootstrap Information:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $REGION"
    echo "  Account: $AWS_ACCOUNT_ID"
    echo "  Qualifier: ${ENVIRONMENT}${REGION:0:3}"
    echo "  Bootstrap Bucket: cdk-${PROJECT_NAME}-${ENVIRONMENT}-${AWS_ACCOUNT_ID}-${REGION}"
    echo "  KMS Key Alias: alias/cdk-${PROJECT_NAME}-${ENVIRONMENT}-key"
    echo ""
    log_info "You can now deploy stacks using:"
    echo "  ./deploy.sh -e $ENVIRONMENT -r $REGION"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Bootstrap failed with exit code $exit_code"
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution
main() {
    log_info "Starting CDK bootstrap for AWS Meeting Scheduling Agent"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
    
    check_prerequisites
    
    if check_bootstrap_status; then
        bootstrap_cdk
        verify_bootstrap
        display_bootstrap_info
        
        log_success "CDK bootstrap completed successfully!"
    else
        log_info "CDK is already bootstrapped and --force was not specified"
        display_bootstrap_info
    fi
}

# Run main function
main "$@"