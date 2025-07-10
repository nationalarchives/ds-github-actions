# ds-github-actions
Common GitHub Actions
### Discovery Deployment
Discovery entails two steps for deployment. First compiling the source code, creating the zip files and copying them to the S3 bucket for later deployment.
The next step is to deploy the file(s) with AWS CodeDeploy to the running instances.

The process is started from the Discovery repository.

### Theme Deployment
Deploying themes for WordPress websites by creating zip files and copying them to the shared S3 deployment bucket and start CodeDeploy service.  

To start a theme deployment you must head to the repo of the theme you would like to deploy and run the theme deployment job for the service you want to deploy to.

When running a job, you must select the environment and optionally the release. If a release isn't specified, it will use the latest default branch.

### Actions used
The actions should be kept up-to-date with the latest versions. Ensure you visit the repositories regulary and when updating run the pipelines.
#### blog, media and website
1) actions/checkout@v4
2) aws-actions/configure-aws-credentials@v1-node16
#### discovery
1) actions/checkout@v4
2) aws-actions/configure-aws-credentials@v2
3) microsoft/setup-msbuild@v1.1
4) actions/setup-python@v5
#### nginx
1) actions/checkout@v4
2) actions/setup-python@v5
3) aws-actions/configure-aws-credentials@v1-node16

### commands
CHANGE REPLICATION SOURCE TO SOURCE_HOST = "host", SOURCE_PORT = port, SOURCE_USER = "user", SOURCE_PASSWORD = "password", SOURCE_AUTO_POSITION = 1;
START REPLICA;
