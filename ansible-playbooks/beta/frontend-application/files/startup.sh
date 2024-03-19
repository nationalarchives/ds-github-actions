#!/bin/bash

# set environment variables
source /etc/environment

sudo touch /var/log/server-startup.log

region="eu-west-2"
if [ -z ${TRAEFIK_IMAGE+x} ]; then export TRAEFIK_IMAGE="none"; fi
if [ -z ${WEBSERVER_IMAGE+x} ]; then export WEBSERVER_IMAGE="none"; fi


# get docker image tag from parameter store
echo "retrieve versions"
exp_traefik_image=$(aws ssm get-parameter --name /application/private_beta/dw/docker/release --query Parameter.Value --region $region --output text | jq -r '.["traefik"]')
exp_webserver_image=$(aws ssm get-parameter --name /application/private_beta/dw/docker/release --query Parameter.Value --region $region --output text | jq -r '.["website"]')

# update compose.traefik.yml if needed
if [ "$TRAEFIK_IMAGE" = "$exp_traefik_image" ]; then
  sudo sed -i "s|image: traefik:.*|image: traefik:$exp_traefik_image|g" /var/docker/compose.traefik.yml
  update_traefik="yes"
  echo "traefik image updating to $exp_traefik_image"
else
  update_traefik="no"
fi

# check if traefik is running...
TRAEFIK_ID=$(sudo docker ps --all --filter "name=traefik" --format "{{.ID}}")
if [ -z "$TRAEFIK_ID" ]; then
  # traefik isn't running
  echo "starting up traefik - $exp_traefik_image"
  source /usr/local/bin/traefik-run.sh
  export TRAEFIK_IMAGE="$exp_traefik_image"
  echo "traefik image version set to $exp_traefik_image"
elif [ $update_traefik = "yes" ]; then
  echo "updating traefik to $exp_traefik_image ..."
  source /usr/local/bin/traefik-run.sh
  export TRAEFIK_IMAGE="$exp_traefik_image"
  echo "traefik image version set to $exp_traefik_image"
else
  echo "traefik is ok - tag:$exp_traefik_image"
fi

# update compose.yml if needed
if [ "$WEBSERVER_IMAGE" = "$exp_webserver_image" ]; then
  sudo sed -i "s|image: ghcr.io/nationalarchives/national-archives-website:.*|image: ghcr.io/nationalarchives/national-archives-website:$exp_webserver_image|g" /var/docker/compose.yml
  update_website="yes"
  echo "website needs updating to $exp_webserver_image"
else
  update_website="no"
fi

# check if website is running...
BLUE_ID=$(sudo docker ps --filter "name=blue-dw" --format "{{.ID}}")
GREEN_ID=$(sudo docker ps --filter "name=green-dw" --format "{{.ID}}")
if [ -z "$BLUE_ID" ] && [ -z "$GREEN_ID" ]; then
  # website isn't running
  echo "starting up website - $exp_webserver_image"
  source /usr/local/bin/website-blue-green-deploy.sh
  sudo sed -i "s|export WEBSERVER_IMAGE=.*|export WEBSERVER_IMAGE=$exp_webserver_image|g" /etc/environment
  echo "webserver image version set to $exp_webserver_image"
elif [ $update_website = "yes" ]; then
  echo "updating website to $exp_webserver_image ..."
  source /usr/local/bin/website-blue-green-deploy.sh
  sudo sed -i "s|export WEBSERVER_IMAGE=.*|export WEBSERVER_IMAGE=$exp_webserver_image|g" /etc/environment
  echo "webserver image version set to $exp_webserver_image"
else
  echo "website is ok - tag:$exp_webserver_image"
fi

sudo source /etc/environment
# run correct container if needed
