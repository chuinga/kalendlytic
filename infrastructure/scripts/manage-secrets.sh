#!/bin/bash

# AWS Meeting Scheduling Agent - Secrets Management Script
# This script handles environment variables and secret management for different environments

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="meeting-scheduling-agent"

# Default values
ENVIRONMENT="dev"
REGION="us-east-1"
PROFILE=""
ACTION="list"
SECRET_NAME=""
SECRET_VALUE=""
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
Usage: $0 [OPTIONS] ACTION

Manage secrets and environment variables for AWS Meeting Scheduling Agent

ACTIONS:
    list                    List all secrets for environment
    get SECRET_NAME         Get specific secret value
    set SECRET_NAME VALUE   Set secret value
    delete SECRET_NAME      Delete secret
    rotate SECRET_NAME      Rotate secret (generate new value)
    export                  Export secrets to .env file
    import FILE             Import secrets from file

OPTIONS:
    -e, --environment ENV   Environment (dev, staging, prod) [default: dev]
    -r, --region REGION     AWS region [default: us-east-1]
    -p, --profile PROFILE   AWS profile to use
    -v, --verbose          Enable verbose output
    -d, --dry-run          Show what would be done
    -h, --help             Show this help message

EXAMPLES:
    $0 list -e dev
    $0 get BEDROCK_API_KEY -e prod
    $0 set BEDROCK_API_KEY "secret-value" -e dev
    $0 export -e staging
    $0 rotate JWT_SECRET -e prod

EOF
}# Parse
 command line arguments
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
        list|get|set|delete|rotate|export|import)
            ACTION="$1"
            shift
            
            # Handle action-specific arguments
            case $ACTION in
                get|delete|rotate)
                    if [[ $# -gt 0 && ! $1 =~ ^- ]]; then
                        SECRET_NAME="$1"
                        shift
                    fi
                    ;;
                set)
                    if [[ $# -gt 1 && ! $1 =~ ^- && ! $2 =~ ^- ]]; then
                        SECRET_NAME="$1"
                        SECRET_VALUE="$2"
                        shift 2
                    fi
                    ;;
                import)
                    if [[ $# -gt 0 && ! $1 =~ ^- ]]; then
                        IMPORT_FILE="$1"
                        shift
                    fi
                    ;;
            esac
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
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid."
        exit 1
    fi
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_info "AWS Account ID: $AWS_ACCOUNT_ID"
    log_info "AWS Region: $REGION"
    
    log_success "Prerequisites check passed"
}

# Get secret name prefix for environment
get_secret_prefix() {
    echo "/${PROJECT_NAME}/${ENVIRONMENT}"
}

# List all secrets
list_secrets() {
    log_info "Listing secrets for environment: $ENVIRONMENT"
    
    local prefix=$(get_secret_prefix)
    
    aws ssm get-parameters-by-path \
        --path "$prefix" \
        --recursive \
        --region "$REGION" \
        --query 'Parameters[*].[Name,Type,LastModifiedDate]' \
        --output table 2>/dev/null || {
        log_warning "No secrets found for environment $ENVIRONMENT"
        return 0
    }
}

# Get specific secret
get_secret() {
    local secret_name="$1"
    local full_name="$(get_secret_prefix)/${secret_name}"
    
    log_info "Getting secret: $secret_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would get secret $full_name"
        return 0
    fi
    
    local value=$(aws ssm get-parameter \
        --name "$full_name" \
        --with-decryption \
        --region "$REGION" \
        --query 'Parameter.Value' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$value" ]]; then
        echo "$value"
    else
        log_error "Secret $secret_name not found"
        return 1
    fi
}

# Set secret value
set_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local full_name="$(get_secret_prefix)/${secret_name}"
    
    log_info "Setting secret: $secret_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would set secret $full_name"
        return 0
    fi
    
    aws ssm put-parameter \
        --name "$full_name" \
        --value "$secret_value" \
        --type "SecureString" \
        --region "$REGION" \
        --overwrite \
        --tags "Key=Project,Value=$PROJECT_NAME" \
               "Key=Environment,Value=$ENVIRONMENT" \
               "Key=ManagedBy,Value=CDK" > /dev/null
    
    log_success "Secret $secret_name set successfully"
}

# Delete secret
delete_secret() {
    local secret_name="$1"
    local full_name="$(get_secret_prefix)/${secret_name}"
    
    log_warning "Deleting secret: $secret_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would delete secret $full_name"
        return 0
    fi
    
    aws ssm delete-parameter \
        --name "$full_name" \
        --region "$REGION" > /dev/null
    
    log_success "Secret $secret_name deleted successfully"
}

# Generate random secret value
generate_secret_value() {
    local length="${1:-32}"
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Rotate secret
rotate_secret() {
    local secret_name="$1"
    
    log_info "Rotating secret: $secret_name"
    
    # Generate new value based on secret type
    local new_value=""
    case "$secret_name" in
        *API_KEY*|*SECRET*|*TOKEN*)
            new_value=$(generate_secret_value 64)
            ;;
        *PASSWORD*)
            new_value=$(generate_secret_value 32)
            ;;
        JWT_SECRET)
            new_value=$(generate_secret_value 64)
            ;;
        *)
            new_value=$(generate_secret_value 32)
            ;;
    esac
    
    set_secret "$secret_name" "$new_value"
    log_success "Secret $secret_name rotated successfully"
}

# Export secrets to .env file
export_secrets() {
    log_info "Exporting secrets to .env file for environment: $ENVIRONMENT"
    
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    local prefix=$(get_secret_prefix)
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would export secrets to $env_file"
        return 0
    fi
    
    # Create backup of existing file
    if [[ -f "$env_file" ]]; then
        cp "$env_file" "$env_file.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Backed up existing $env_file"
    fi
    
    # Get all parameters and format as .env
    {
        echo "# Environment variables for $ENVIRONMENT"
        echo "# Generated on $(date)"
        echo "# DO NOT COMMIT THIS FILE TO VERSION CONTROL"
        echo ""
        echo "NODE_ENV=$ENVIRONMENT"
        echo "AWS_REGION=$REGION"
        echo ""
        
        aws ssm get-parameters-by-path \
            --path "$prefix" \
            --recursive \
            --with-decryption \
            --region "$REGION" \
            --query 'Parameters[*].[Name,Value]' \
            --output text 2>/dev/null | while read -r name value; do
            # Extract just the parameter name without the path
            local param_name=$(basename "$name")
            echo "${param_name}=${value}"
        done
    } > "$env_file"
    
    log_success "Secrets exported to $env_file"
    log_warning "Remember to add $env_file to .gitignore"
}

# Import secrets from file
import_secrets() {
    local import_file="${IMPORT_FILE:-}"
    
    if [[ -z "$import_file" ]]; then
        log_error "Import file not specified"
        return 1
    fi
    
    if [[ ! -f "$import_file" ]]; then
        log_error "Import file not found: $import_file"
        return 1
    fi
    
    log_info "Importing secrets from: $import_file"
    
    # Read and process each line
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        # Skip comments and empty lines
        if [[ "$key" =~ ^#.*$ ]] || [[ -z "$key" ]]; then
            continue
        fi
        
        # Skip environment variables that shouldn't be stored as secrets
        case "$key" in
            NODE_ENV|AWS_REGION|AWS_ACCOUNT_ID)
                continue
                ;;
        esac
        
        # Remove quotes from value if present
        value=$(echo "$value" | sed 's/^["'\'']//' | sed 's/["'\'']$//')
        
        if [[ -n "$value" ]]; then
            set_secret "$key" "$value"
        fi
    done < "$import_file"
    
    log_success "Secrets imported from $import_file"
}

# Initialize default secrets for environment
init_default_secrets() {
    log_info "Initializing default secrets for environment: $ENVIRONMENT"
    
    # Default secrets that should exist
    local default_secrets=(
        "JWT_SECRET"
        "BEDROCK_API_KEY"
        "CALENDAR_ENCRYPTION_KEY"
        "WEBHOOK_SECRET"
    )
    
    for secret in "${default_secrets[@]}"; do
        local full_name="$(get_secret_prefix)/${secret}"
        
        # Check if secret already exists
        if aws ssm get-parameter --name "$full_name" --region "$REGION" &> /dev/null; then
            log_info "Secret $secret already exists"
        else
            log_info "Creating default secret: $secret"
            local default_value=$(generate_secret_value)
            set_secret "$secret" "$default_value"
        fi
    done
}

# Main execution
main() {
    log_info "Managing secrets for AWS Meeting Scheduling Agent"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
    log_info "Action: $ACTION"
    
    check_prerequisites
    
    case "$ACTION" in
        list)
            list_secrets
            ;;
        get)
            if [[ -z "$SECRET_NAME" ]]; then
                log_error "Secret name required for get action"
                usage
                exit 1
            fi
            get_secret "$SECRET_NAME"
            ;;
        set)
            if [[ -z "$SECRET_NAME" || -z "$SECRET_VALUE" ]]; then
                log_error "Secret name and value required for set action"
                usage
                exit 1
            fi
            set_secret "$SECRET_NAME" "$SECRET_VALUE"
            ;;
        delete)
            if [[ -z "$SECRET_NAME" ]]; then
                log_error "Secret name required for delete action"
                usage
                exit 1
            fi
            delete_secret "$SECRET_NAME"
            ;;
        rotate)
            if [[ -z "$SECRET_NAME" ]]; then
                log_error "Secret name required for rotate action"
                usage
                exit 1
            fi
            rotate_secret "$SECRET_NAME"
            ;;
        export)
            export_secrets
            ;;
        import)
            import_secrets
            ;;
        init)
            init_default_secrets
            ;;
        *)
            log_error "Unknown action: $ACTION"
            usage
            exit 1
            ;;
    esac
    
    log_success "Secret management completed successfully!"
}

# Run main function
main "$@"