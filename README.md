# ds-github-actions
Common GitHub Actions
### Theme Deployment
Deploying themes for WordPress websites by creating zip files and copying them to the shared S3 deployment bucket and start CodeDeploy service.  

To start a theme deployment you must head to the repo of the theme you would like to deploy and run the theme deployment job for the service you want to deploy to.

When running a job, you must select the environment and optionally the release. If a release isn't specified, it will use the latest default branch.
