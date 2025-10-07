#!/bin/bash

# AWS Meeting Scheduling Agent - Rollback Script
# This script handles rollback and disaster recovery procedures

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="meeting-scheduling-agent"

# Default values
ENVIRONMENT="dev"
REGION="us-east-1"
PROFILE=""
VERBOSE=false
DRY_RUN=false
FORCE=false
ROLLBACK_TO_VERSION=""
BACKUP_BEFORE_ROLLBACK=true

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

Rollback AWS Meeting Scheduling Agent infrastructure

OPTIONS:
    -e, --environment ENV       Environment (dev, staging, prod) [default: dev]
    -r, --region REGION         AWS region [default: us-east-1]
    -p, --profile PROFILE       AWS profile to use
    -v, --version VERSION       Rollback to specific version/changeset
    -f, --force                 Force rollback without confirmation
    --no-backup                 Skip backup before rollback
    --verbose                   Enable verbose output
    --dry-run                   Show what would be rolled back
    -h, --help                  Show this help message

ROLLBACK STRATEGIES:
    1. Version rollback: Rollback to a specific CloudFormation changeset
    2. Complete destroy: Destroy all stacks (use with caution)
    3. Selective rollback: Rollback specific stacks only

EXAMPLES:
    $0 -e dev -r us-east-1
    $0 -e prod -v changeset-123 --force
    $0 --dry-run -e staging
    $0 --no-backup -e dev

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
        -v|--version)
            ROLLBACK_TO_VERSION="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --no-backup)
            BACKUP_BEFORE_ROLLBACK=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
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

# Get stack names
get_stack_names() {
    echo "${PROJECT_NAME}-${ENVIRONMENT}-core"
    echo "${PROJECT_NAME}-${ENVIRONMENT}-api"
    echo "${PROJECT_NAME}-${ENVIRONMENT}-web"
    echo "${PROJECT_NAME}-${ENVIRONMENT}-monitoring"
}

# Get stack status
get_stack_status() {
    local stack_name="$1"
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "NOT_FOUND"
}

# List available changesets for rollback
list_changesets() {
    local stack_name="$1"
    
    log_info "Available changesets for $stack_name:"
    
    aws cloudformation list-change-sets \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Summaries[?Status==`CREATE_COMPLETE`].[ChangeSetName,CreationTime,Description]' \
        --output table 2>/dev/null || log_warning "No changesets found for $stack_name"
}

# Create backup of current state
create_backup() {
    if [[ "$BACKUP_BEFORE_ROLLBACK" == "false" ]]; then
        log_info "Skipping backup as requested"
        return 0
    fi
    
    log_info "Creating backup of current state..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)_${ENVIRONMENT}_rollback"
    mkdir -p "$backup_dir"
    
    local stacks=($(get_stack_names))
    
    for stack in "${stacks[@]}"; do
        local stack_status=$(get_stack_status "$stack")
        
        if [[ "$stack_status" != "NOT_FOUND" ]]; then
            log_info "Backing up stack: $stack"
            
            # Export stack template
            aws cloudformation get-template \
                --stack-name "$stack" \
                --region "$REGION" \
                --query 'TemplateBody' \
                > "$backup_dir/${stack}_template.json" 2>/dev/null || true
            
            # Export stack parameters
            aws cloudformation describe-stacks \
                --stack-name "$stack" \
                --region "$REGION" \
                --query 'Stacks[0].Parameters' \
                > "$backup_dir/${stack}_parameters.json" 2>/dev/null || true
            
            # Export stack outputs
            aws cloudformation describe-stacks \
                --stack-name "$stack" \
                --region "$REGION" \
                --query 'Stacks[0].Outputs' \
                > "$backup_dir/${stack}_outputs.json" 2>/dev/null || true
            
            # Export stack tags
            aws cloudformation describe-stacks \
                --stack-name "$stack" \
                --region "$REGION" \
                --query 'Stacks[0].Tags' \
                > "$backup_dir/${stack}_tags.json" 2>/dev/null || true
        fi
    done
    
    # Create backup metadata
    cat > "$backup_dir/metadata.json" << EOF
{
    "environment": "$ENVIRONMENT",
    "region": "$REGION",
    "account_id": "$AWS_ACCOUNT_ID",
    "backup_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "rollback_reason": "Pre-rollback backup",
    "stacks": $(printf '%s\n' "${stacks[@]}" | jq -R . | jq -s .)
}
EOF
    
    log_success "Backup created at: $backup_dir"
    echo "$backup_dir"
}

# Rollback to specific changeset
rollback_to_changeset() {
    local stack_name="$1"
    local changeset_name="$2"
    
    log_info "Rolling back $stack_name to changeset: $changeset_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would rollback $stack_name to changeset $changeset_name"
        return 0
    fi
    
    # Execute changeset rollback
    aws cloudformation execute-change-set \
        --change-set-name "$changeset_name" \
        --stack-name "$stack_name" \
        --region "$REGION"
    
    # Wait for rollback to complete
    log_info "Waiting for rollback to complete..."
    aws cloudformation wait stack-update-complete \
        --stack-name "$stack_name" \
        --region "$REGION"
    
    log_success "Rollback completed for $stack_name"
}

# Destroy stack (complete rollback)
destroy_stack() {
    local stack_name="$1"
    
    log_warning "Destroying stack: $stack_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would destroy stack $stack_name"
        return 0
    fi
    
    cd "$PROJECT_ROOT"
    
    # Use CDK destroy for proper cleanup
    cdk destroy "$stack_name" \
        --context "meeting-scheduling-agent:environment=$ENVIRONMENT" \
        --context "meeting-scheduling-agent:region=$REGION" \
        --force
    
    log_success "Stack $stack_name destroyed"
}

# Rollback all stacks
rollback_all_stacks() {
    log_warning "Rolling back all stacks for environment: $ENVIRONMENT"
    
    # Get stacks in reverse order for proper dependency handling
    local stacks=($(get_stack_names | tac))
    
    # Create backup first
    local backup_dir=""
    if [[ "$BACKUP_BEFORE_ROLLBACK" == "true" ]]; then
        backup_dir=$(create_backup)
    fi
    
    # Confirm rollback unless forced
    if [[ "$FORCE" == "false" && "$DRY_RUN" == "false" ]]; then
        echo ""
        log_warning "This will rollback/destroy the following stacks:"
        printf '%s\n' "${stacks[@]}"
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "Rollback cancelled by user"
            exit 0
        fi
    fi
    
    # Rollback each stack
    for stack in "${stacks[@]}"; do
        local stack_status=$(get_stack_status "$stack")
        
        if [[ "$stack_status" == "NOT_FOUND" ]]; then
            log_info "Stack $stack does not exist, skipping"
            continue
        fi
        
        log_info "Processing stack: $stack (Status: $stack_status)"
        
        if [[ -n "$ROLLBACK_TO_VERSION" ]]; then
            # Try to rollback to specific changeset
            rollback_to_changeset "$stack" "$ROLLBACK_TO_VERSION"
        else
            # Destroy stack completely
            destroy_stack "$stack"
        fi
    done
    
    if [[ -n "$backup_dir" ]]; then
        log_info "Backup available at: $backup_dir"
    fi
}

# Show rollback options
show_rollback_options() {
    log_info "Rollback options for environment: $ENVIRONMENT"
    
    local stacks=($(get_stack_names))
    
    for stack in "${stacks[@]}"; do
        local stack_status=$(get_stack_status "$stack")
        
        if [[ "$stack_status" != "NOT_FOUND" ]]; then
            echo ""
            log_info "Stack: $stack (Status: $stack_status)"
            list_changesets "$stack"
        else
            log_info "Stack: $stack (Status: NOT_FOUND)"
        fi
    done
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."
    
    local stacks=($(get_stack_names))
    local all_healthy=true
    
    for stack in "${stacks[@]}"; do
        local stack_status=$(get_stack_status "$stack")
        
        if [[ "$stack_status" == "NOT_FOUND" ]]; then
            log_success "Stack $stack successfully removed"
        elif [[ "$stack_status" == "CREATE_COMPLETE" || "$stack_status" == "UPDATE_COMPLETE" ]]; then
            log_success "Stack $stack is healthy (Status: $stack_status)"
        else
            log_error "Stack $stack is in unexpected state (Status: $stack_status)"
            all_healthy=false
        fi
    done
    
    if [[ "$all_healthy" == "true" ]]; then
        log_success "Rollback verification passed"
    else
        log_error "Rollback verification failed"
        return 1
    fi
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Rollback failed with exit code $exit_code"
        log_info "Check the backup directory for recovery options"
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution
main() {
    log_info "Starting rollback for AWS Meeting Scheduling Agent"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
    
    check_prerequisites
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No actual changes will be made"
        show_rollback_options
        return 0
    fi
    
    if [[ -z "$ROLLBACK_TO_VERSION" ]]; then
        log_warning "No specific version specified, will perform complete rollback (destroy)"
        show_rollback_options
        echo ""
    fi
    
    rollback_all_stacks
    verify_rollback
    
    log_success "Rollback completed successfully!"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
}

# Run main function
main "$@"