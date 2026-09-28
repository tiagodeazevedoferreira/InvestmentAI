variable "project_id" {
  description = "Existing Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Google Cloud region for Artifact Registry and Cloud Run."
  type        = string
  default     = "southamerica-east1"
}

variable "artifact_registry_repository" {
  description = "Artifact Registry Docker repository ID."
  type        = string
  default     = "investmentai"
}

variable "deploy_service_account_id" {
  description = "GitHub Actions deployment service account ID."
  type        = string
  default     = "investmentai-deploy"
}

variable "runtime_service_account_id" {
  description = "Cloud Run runtime service account ID."
  type        = string
  default     = "investmentai-runtime"
}

variable "workload_identity_pool_id" {
  description = "Workload Identity Pool ID."
  type        = string
  default     = "github-actions"
}

variable "workload_identity_provider_id" {
  description = "Workload Identity Provider ID."
  type        = string
  default     = "investmentai"
}
