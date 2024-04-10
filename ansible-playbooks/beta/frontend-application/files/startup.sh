#!/bin/bash

# set environment variables
source /etc/environment

sudo touch /var/log/server-startup.log

region="eu-west-2"
if [ -z ${TRAEFIK_IMAGE+x} ]; then export TRAEFIK_IMAGE="none"; fi
if [ -z ${FRONTEND_APP_IMAGE+x} ]; then export FRONTEND_APP_IMAGE="none"; fi

# get docker image tag from parameter store
echo "retrieve versions"
exp_traefik_image=$(aws ssm get-parameter --name /application/beta/docker-images --query Parameter.Value --region $region --output text | jq -r '.["traefik"]')
exp_app_image=$(aws ssm get-parameter --name /application/beta/docker-images --query Parameter.Value --region $region --output text | jq -r '.["frontend-application"]')

set_traefik_image=$(yq '.services.traefik.image' /var/docker/compose.traefik.yml)
set_app_image=$(yq '.services.blue-web.image' /var/docker/compose.yml)

# update traefik version if needed
if [[ "$TRAEFIK_IMAGE" != "$exp_traefik_image" ]] || [[ "$set_traefik_image" != "$exp_traefik_image" ]]; then
  sudo yq -i ".services.traefik.image = \"$exp_traefik_image\"" /var/docker/compose.traefik.yml
  export TRAEFIK_IMAGE="$exp_traefik_image"
  sudo sed -i "s|export TRAEFIK_IMAGE=.*|export TRAEFIK_IMAGE=\"$exp_traefik_image\"|g" /etc/environment
fi

# check if traefik is running...
TRAEFIK_ID=$(sudo docker ps --all --filter "name=traefik" --format "{{.ID}}")
if [ ! -z "$TRAEFIK_ID" ]; then
  sudo docker stop $TRAEFIK_ID
fi
sudo /usr/local/bin/traefik-run.sh

# update app version
if [[ "$FRONTEND_APP_IMAGE" = "$exp_app_image" ]] || [[ "$set_app_image" != "$exp_app_image" ]]; then
  sudo yq -i ".services.blue-web.image = \"$exp_app_image\"" /var/docker/compose.yml
  export FRONTEND_APP_IMAGE="$exp_app_image"
  sudo sed -i "s|export FRONTEND_APP_IMAGE=.*|export FRONTEND_APP_IMAGE=\"$exp_app_image\"|g" /etc/environment
fi

sudo /usr/local/bin/website-blue-green-deploy.sh
