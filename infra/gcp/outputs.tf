output "gcp_project_id" { value = var.project_id }
output "region" { value = var.region }
output "artifact_registry_repository" { value = google_artifact_registry_repository.investmentai.repository_id }
output "github_workload_identity_provider" { value = google_iam_workload_identity_pool_provider.github.name }
output "deploy_service_account" { value = google_service_account.deploy.email }
output "runtime_service_account" { value = google_service_account.runtime.email }
