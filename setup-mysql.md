# Setting up MySQL Database
1. Create an EBS data volume \
Use GitHub Action __EBS Preparation__ and supply the required parameters \
The volume ID will be written to SSM - Parameter Store under ```/infrastructure/databases/[DB type]-[project name]-[function]/volume_id```
2. Create database instance \
Use GitHub Action __MySQL Base AMI__ and supply the required parameters \
The instance is named 
