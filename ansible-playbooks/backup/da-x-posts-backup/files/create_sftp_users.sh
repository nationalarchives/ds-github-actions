#!/bin/bash

cd /sftp-users
for filename in *.zip; do
  username=$(echo "${filename%.*}")

  sudo useradd -m -g sftp -s /sbin/nologin "$username"
  sudo passwd -l "$username"

  unzip "$filename"
  sudo cp "/home/$username/.ssh/$username.pub" "/home/$username/.ssh/authorized_keys"
  sudo chmod 0644 "/home/$username/.ssh/authorized_keys"

  sudo rm -R "$username"

  sudo mkdir "/sftp-data/$username"
  sudo chown root:root "/sftp-data/$username"
  sudo chmod 0755 "/sftp-data/$username"
  sudo mkdir "/sftp-data/$username/uploads"
  sudo chown $username:$username "/sftp-data/$username/uploads"
  sudo chmod 0760 "/sftp-data/$username/uploads"
done
