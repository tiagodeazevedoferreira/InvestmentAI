terraform {
  required_version = ">= 1.8.0"
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region = var.region
}

locals {
  repository = "tiagodeazevedoferreira/InvestmentAI"
  api_services = toset(["artifactregistry.googleapis.com","run.googleapis.com","iam.googleapis.com","iamcredentials.googleapis.com","sts.googleapis.com","secretmanager.googleapis.com"])
}

resource "google_project_service" "required" {
  for_each = local.api_services
  project = var.project_id
  service = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "investmentai" {
  project = var.project_id
  location = var.region
  repository_id = var.artifact_registry_repository
  description = "InvestmentAI production container images"
  format = "DOCKER"
  depends_on = [google_project_service.required]
}

resource "google_service_account" "deploy" {
  project = var.project_id
  account_id = var.deploy_service_account_id
  display_name = "InvestmentAI GitHub deployment"
}

resource "google_service_account" "runtime" {
  project = var.project_id
  account_id = var.runtime_service_account_id
  display_name = "InvestmentAI Cloud Run runtime"
}

resource "google_project_iam_member" "deploy_artifact_writer" {
  project = var.project_id
  role = "roles/artifactregistry.writer"
  member = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_project_iam_member" "deploy_run_admin" {
  project = var.project_id
  role = "roles/run.admin"
  member = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_service_account_iam_member" "deploy_runtime_user" {
  service_account_id = google_service_account.runtime.name
  role = "roles/iam.serviceAccountUser"
  member = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_project_iam_member" "runtime_secret_accessor" {
  project = var.project_id
  role = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_iam_workload_identity_pool" "github" {
  project = var.project_id
  workload_identity_pool_id = var.workload_identity_pool_id
  display_name = "GitHub Actions"
  description = "OIDC federation for InvestmentAI GitHub Actions"
  depends_on = [google_project_service.required]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project = var.project_id
  workload_identity_pool_id = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = var.workload_identity_provider_id
  display_name = "InvestmentAI GitHub OIDC"
  attribute_mapping = {
    "google.subject" = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref" = "assertion.ref"
  }
  attribute_condition = "assertion.repository == 'tiagodeazevedoferreira/InvestmentAI' && assertion.ref == 'refs/heads/main'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_deploy" {
  service_account_id = google_service_account.deploy.name
  role = "roles/iam.workloadIdentityUser"
  member = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/tiagodeazevedoferreira/InvestmentAI"
}

resource "google_secret_manager_secret" "firebase_database_url" {
  project = var.project_id
  secret_id = "investmentai-firebase-database-url"
  replication {\n    auto {}\n  }
}

resource "google_secret_manager_secret" "firebase_service_account" {
  project = var.project_id
  secret_id = "investmentai-firebase-service-account"
  replication {\n    auto {}\n  }
}

resource "google_secret_manager_secret" "tradingview_webhook_secret" {
  project = var.project_id
  secret_id = "investmentai-tradingview-webhook-secret"
  replication {\n    auto {}\n  }
}

output "artifact_registry_repository" {\n  value = google_artifact_registry_repository.investmentai.name\n}
output "deploy_service_account" {\n  value = google_service_account.deploy.email\n}
output "runtime_service_account" {\n  value = google_service_account.runtime.email\n}
output "workload_identity_provider" {\n  value = google_iam_workload_identity_pool_provider.github.name\n}