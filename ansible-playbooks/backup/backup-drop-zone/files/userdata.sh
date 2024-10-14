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

echo "$(date '+%Y-%m-%d %T') - install git" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo dnf install git -y

echo "$(date '+%Y-%m-%d %T') - install python 3.11" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo dnf install python3.11 -y
echo "$(date '+%Y-%m-%d %T') - install pip" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo dnf install python3.11-pip -y

echo "$(date '+%Y-%m-%d %T') - install python libs" | sudo tee -a  /var/log/ami-install.log > /dev/null
python3.11 -m pip install requests
python3.11 -m pip install boto3
echo "$(date '+%Y-%m-%d %T') - install python libs for systemd" | sudo tee -a  /var/log/ami-install.log > /dev/null
sudo -H python3.11 -m pip3 install requests
sudo -H python3.11 -m pip3 install boto3

#sudo unzip /temp/secure-backups.zip /usr/local/share/applications/secure-backup
#sudo cp secure-backups.service /etc/systemd/system/
#sudo systemctl enable secure-backups.service
#sudo systemctl start secure-backups.service

cat << EOF > /var/finish-init.txt
[status]
finished = true
EOF
