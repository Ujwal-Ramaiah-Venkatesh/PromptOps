variable "app_name" {
  description = "Application name for tags and metadata"
  type        = string
}

variable "environment" {
  description = "Environment name (dev/staging/production)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region to deploy the static site"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name for the static website"
  type        = string
}

variable "index_document" {
  description = "Website index document"
  type        = string
  default     = "index.html"
}

variable "error_document" {
  description = "Website error document"
  type        = string
  default     = "index.html"
}

variable "enable_custom_domain" {
  description = "Enable custom domain + HTTPS via CloudFront and ACM"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Custom domain name (for example app.example.com)"
  type        = string
  default     = ""
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID for domain_name"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "Existing ACM certificate ARN in us-east-1. Leave empty to create and validate automatically."
  type        = string
  default     = ""
}
