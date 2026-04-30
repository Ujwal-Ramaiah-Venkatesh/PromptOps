#!/bin/bash
#
# Setup AWS Secrets Manager for PromptOps
# Week 13-15: SECURITY-005
#
# Usage: ./setup_secrets.sh [staging|production]
#

set -e

ENVIRONMENT=${1:-staging}
AWS_REGION=${AWS_REGION:-us-east-1}

echo "=========================================="
echo "  PromptOps Secrets Setup"
echo "  Environment: $ENVIRONMENT"
echo "  Region: $AWS_REGION"
echo "=========================================="

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not installed"
    echo "Install: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

echo ""
echo "1. Creating Database Credentials Secret..."

# Generate secure password if not provided
DB_PASSWORD=${DB_PASSWORD:-$(openssl rand -base64 32)}

aws secretsmanager create-secret \
    --name "promptops/${ENVIRONMENT}/database" \
    --description "Database credentials for PromptOps ${ENVIRONMENT}" \
    --secret-string "{
        \"username\": \"promptops_${ENVIRONMENT}\",
        \"password\": \"${DB_PASSWORD}\",
        \"host\": \"promptops-${ENVIRONMENT}.cluster-xxxxx.${AWS_REGION}.rds.amazonaws.com\",
        \"port\": \"5432\",
        \"database\": \"promptops\"
    }" \
    --region $AWS_REGION \
    2>/dev/null && echo "✓ Database secret created" || echo "⚠ Database secret already exists"

echo ""
echo "2. Creating API Keys Secret..."

# Generate JWT secret
JWT_SECRET=${JWT_SECRET:-$(openssl rand -base64 64 | tr -d '\n')}

# Anthropic API key (must be provided)
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY not set"
    echo "Export it: export ANTHROPIC_API_KEY=sk-ant-xxxxx"
    ANTHROPIC_API_KEY="REPLACE_WITH_REAL_KEY"
fi

aws secretsmanager create-secret \
    --name "promptops/${ENVIRONMENT}/api-keys" \
    --description "API keys for PromptOps ${ENVIRONMENT}" \
    --secret-string "{
        \"jwt_secret\": \"${JWT_SECRET}\",
        \"anthropic\": \"${ANTHROPIC_API_KEY}\"
    }" \
    --region $AWS_REGION \
    2>/dev/null && echo "✓ API keys secret created" || echo "⚠ API keys secret already exists"

echo ""
echo "3. Configuring Secret Rotation (Database)..."

# Create rotation Lambda (placeholder - full implementation needed)
echo "⚠ Manual step: Create rotation Lambda function"
echo "  See: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html"

# Enable automatic rotation (30 days)
aws secretsmanager rotate-secret \
    --secret-id "promptops/${ENVIRONMENT}/database" \
    --rotation-rules "AutomaticallyAfterDays=30" \
    --region $AWS_REGION \
    2>/dev/null && echo "✓ Rotation configured" || echo "⚠ Rotation configuration failed (Lambda required)"

echo ""
echo "4. Setting up IAM Permissions..."

# Create IAM policy for secrets access
cat > /tmp/promptops-secrets-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:${AWS_REGION}:*:secret:promptops/${ENVIRONMENT}/*"
            ]
        }
    ]
}
EOF

aws iam create-policy \
    --policy-name "PromptOpsSecretsAccess-${ENVIRONMENT}" \
    --policy-document file:///tmp/promptops-secrets-policy.json \
    --description "Allow PromptOps ${ENVIRONMENT} to access secrets" \
    2>/dev/null && echo "✓ IAM policy created" || echo "⚠ IAM policy already exists"

rm /tmp/promptops-secrets-policy.json

echo ""
echo "5. Verifying Secrets..."

echo "Database secret:"
aws secretsmanager get-secret-value \
    --secret-id "promptops/${ENVIRONMENT}/database" \
    --region $AWS_REGION \
    --query 'SecretString' \
    --output text | jq '.'

echo ""
echo "API keys secret (redacted):"
aws secretsmanager get-secret-value \
    --secret-id "promptops/${ENVIRONMENT}/api-keys" \
    --region $AWS_REGION \
    --query 'SecretString' \
    --output text | jq '. | with_entries(select(.key) | .value = "***REDACTED***")'

echo ""
echo "=========================================="
echo "  Secrets Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Update RDS host in database secret (replace xxxxx)"
echo "  2. Set ANTHROPIC_API_KEY if not already set"
echo "  3. Attach IAM policy to ECS task role"
echo "  4. Set ENVIRONMENT=staging/production in ECS"
echo ""
echo "To update secrets:"
echo "  aws secretsmanager update-secret --secret-id promptops/${ENVIRONMENT}/database --secret-string '{...}'"
echo ""
