#!/bin/bash

sudo touch /var/log/mysql-daily-backup.log

echo "$(date '+%Y-%m-%d %T') - get instance details" | sudo tee -a /var/log/mysql-daily-backup.log > /dev/null
TOKEN=$(curl --request PUT "http://169.254.169.254/latest/api/token" --header "X-aws-ec2-metadata-token-ttl-seconds: 3600")
account_id=$(curl -s http://169.254.169.254/latest/meta-data/identity-credentials/ec2/info --header "X-aws-ec2-metadata-token: $TOKEN" | jq -rc .AccountId)
instance_id=$(curl -s http://169.254.169.254/latest/meta-data/instance-id --header "X-aws-ec2-metadata-token: $TOKEN")
instance_name=$(curl -s http://169.254.169.254/latest/meta-data/tags/instance/Name --header "X-aws-ec2-metadata-token: $TOKEN")

if [[ -z "$instance_name" ]] || [[ $instance_name =~ "404 - Not Found" ]]; then
  instance_name=$instance_id
fi

suffix=$(date +"%Y-%m-%d_%H-%M-%S")
backup_name="ds_${account_id}_${instance_name}_${suffix}"
backup_dir=/backups
if [ ! -d $backup_dir ]; then sudo mkdir $backup_dir; fi

sql_file="${backup_dir}/${backup_name}.sql"
zip_file="${backup_dir}/${backup_name}.zip"

echo "$(date '+%Y-%m-%d %T') - read credentials" | sudo tee -a /var/log/mysql-daily-backup.log > /dev/null
secret_values=$(aws secretsmanager get-secret-value \
  --secret-id $SECRET_KEY \
  --region eu-west-2 \
  --output json)
bkup_username=$(echo $secret_values | jq -rc .SecretString | jq -rc .db_username)
bkup_password=$(echo $secret_values | jq -rc .SecretString | jq -rc .db_password)
db_host=$(echo $secret_values | jq -rc .SecretString | jq -rc .db_host)
db_name=$(echo $secret_values | jq -rc .SecretString | jq -rc .db_name)

echo "$(date '+%Y-%m-%d %T') - write database dump" | sudo tee -a /var/log/mysql-daily-backup.log > /dev/null
sudo mysqldump --host $db_host --user $bkup_username --password="$bkup_password" \
  --events --routines --triggers --lock-all-tables  \
  --databases $db_name \
  --result-file $sql_file
echo "$(date '+%Y-%m-%d %T') - create zip file" | sudo tee -a /var/log/mysql-daily-backup.log > /dev/null
sudo zip $zip_file $sql_file

echo "$(date '+%Y-%m-%d %T') - remove sql text file" | sudo tee -a /var/log/mysql-daily-backup.log > /dev/null
sudo rm $sql_file

echo "$(date '+%Y-%m-%d %T') - copy files to S3" | sudo tee -a /var/log/mysql-daily-backup.log > /dev/null
aws s3 cp $zip_file s3://$BACKUP_TARGET/databases/rds/blog/ --recursive --exclude "*" --include "$zip_file"
sudo rm $zip_file
