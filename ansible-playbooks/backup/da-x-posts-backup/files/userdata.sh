#!/bin/bash

sudo touch /var/log/ami-install.log

echo "$(date '+%Y-%m-%d %T') - update system" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo dnf update

# create swap file
echo "$(date '+%Y-%m-%d %T') - create swap file" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo fallocate -l 4G /swapfile
sudo chmod 0600 /swapfile
sudo /sbin/mkswap /swapfile
sudo /sbin/swapon /swapfile

# Install Cloudwatch agent
echo "$(date '+%Y-%m-%d %T') - install CloudWatch agent" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo dnf install amazon-cloudwatch-agent -y
sudo aws s3 cp s3://tna-backup-tooling/cloudwatch/cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/bin/config.json
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json

echo "$(date '+%Y-%m-%d %T') - install collectd" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo dnf install collectd -y

echo "$(date '+%Y-%m-%d %T') - install inotify-tools" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo dnf install inotify-tools -y

echo "$(date '+%Y-%m-%d %T') - create backup target directory" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo mkdir /sftp-data
sudo chmod 0755 /sftp-data

echo "$(date '+%Y-%m-%d %T') - update sshd config file" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo tee -a /etc/ssh/sshd_config <<< "
Match Group sftp
    ChrootDirectory /sftp-data
    PermitTunnel no
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
    ForceCommand internal-sftp -d /%u/uploads
"

echo "$(date '+%Y-%m-%d %T') - create sftp user group" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo groupadd sftp

echo "$(date '+%Y-%m-%d %T') - create backup target directory" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo mkdir /sftp-users
sudo chmod 0700 /sftp-users

cat << EOF > /var/finish-init.txt
[status]
finished = true
EOF
