# Google Cloud production bootstrap

This Terraform module provisions the non-secret infrastructure boundary required by Task 049: required APIs, Artifact Registry, GitHub Actions deployment service account, Cloud Run runtime service account, minimum deployment IAM roles, Workload Identity Federation restricted to this repository and main, and Secret Manager secret containers.

It does not create the Google Cloud project, configure billing, create secret versions, deploy Cloud Run, configure DNS/TLS, enable trading, or create broker credentials.

## Usage

Run Terraform from an operator workstation with authorized Google credentials. The project must already exist and have billing enabled. Copy terraform.tfvars.example to terraform.tfvars, then run terraform init, terraform fmt -check, terraform validate, terraform plan and terraform apply.

Terraform creates empty Secret Manager containers only. Add secret versions separately. Never commit Firebase service-account JSON, webhook tokens, broker credentials or other secret values.

## GitHub production variables

Configure GCP_PROJECT_ID, GCP_REGION, ARTIFACT_REGISTRY_REPOSITORY, CLOUD_RUN_SERVICE, GCP_WIF_PROVIDER, GCP_DEPLOY_SERVICE_ACCOUNT and GCP_RUNTIME_SERVICE_ACCOUNT in the GitHub production environment. The Cloud Run service is created by Task 049.

The Workload Identity provider accepts only repository tiagodeazevedoferreira/InvestmentAI and refs/heads/main. The deployment service account has Artifact Registry writer, Cloud Run admin and runtime service-account impersonation.

The runtime service account receives Secret Manager accessor at project scope in this initial bootstrap. This can later be tightened to secret-level IAM. Task 049 grants the deployment service account service-level Cloud Run Invoker permission during deployment, after the Cloud Run service exists.