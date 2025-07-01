#!/bin/bash

# Configurations
SOURCE_DIR="/media"
TMP_DIR="/media/.backup-zips"
S3_BUCKET="s3://ds-dev-deployment-source/wagtail-content"
LOG_FILE="/var/log/media_backup.log"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
ZIP_NAME="media-backup-$TIMESTAMP.zip"
ZIP_PATH="$TMP_DIR/$ZIP_NAME"

# Setup
sudo mkdir -p "$TMP_DIR"
sudo mkdir -p /var/log

# Find updated files in the last 24h excluding wagtail-content.zip
UPDATED_FILES=$(find "$SOURCE_DIR" -type f -mtime -1 ! -name "wagtail-content.zip")

if [ -z "$UPDATED_FILES" ]; then
    echo "$(date): No updated files to backup." >> "$LOG_FILE"
    exit 0
fi

# Create zip
cd "$SOURCE_DIR"
echo "$UPDATED_FILES" | zip -@ "$ZIP_PATH"

# Upload to S3
sudo aws s3 cp "$ZIP_PATH" "$S3_BUCKET/$ZIP_NAME"

# Log the operation
sudo echo "$(date): Uploaded $ZIP_PATH to $S3_BUCKET/$ZIP_NAME" >> "$LOG_FILE"

# Clean up
sudo rm -f "$ZIP_PATH"
