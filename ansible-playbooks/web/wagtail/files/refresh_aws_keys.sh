#!/bin/bash

LOG_FILE="/var/log/refresh_aws_keys.log"
echo "==== Script started at $(date) ====" >> $LOG_FILE

# Get IMDSv2 token
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# IAM role name
ROLE_NAME="wagtail-assume-role"

# Get temporary credentials JSON from instance metadata
CREDS=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME)

# Parse credentials using jq
ACCESS_KEY=$(echo "$CREDS" | jq -r '.AccessKeyId')
SECRET_KEY=$(echo "$CREDS" | jq -r '.SecretAccessKey')
SESSION_TOKEN=$(echo "$CREDS" | jq -r '.Token')

# Update Parameter Store (suppress output)
aws ssm put-parameter --name "/application/web/wagtail/AWS_ACCESS_KEY_ID" \
  --value "$ACCESS_KEY" --type SecureString --overwrite >/dev/null 2>&1

aws ssm put-parameter --name "/application/web/wagtail/AWS_SECRET_ACCESS_KEY" \
  --value "$SECRET_KEY" --type SecureString --overwrite >/dev/null 2>&1

aws ssm put-parameter --name "/application/web/wagtail/AWS_SESSION_TOKEN" \
  --value "$SESSION_TOKEN" --type SecureString --overwrite >/dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✅ Updated AWS credentials in Parameter Store at $(date)" | tee -a $LOG_FILE
else
  echo "❌ Failed to update AWS credentials at $(date)" | tee -a $LOG_FILE
fi

