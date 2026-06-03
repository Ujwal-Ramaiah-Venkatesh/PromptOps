output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.site.id
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.site.arn
}

output "website_endpoint" {
  description = "S3 static website endpoint"
  value       = aws_s3_bucket_website_configuration.site.website_endpoint
}

output "website_url" {
  description = "Public S3 website URL"
  value       = "http://${aws_s3_bucket_website_configuration.site.website_endpoint}"
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name (when custom domain is enabled)"
  value       = length(aws_cloudfront_distribution.site) > 0 ? aws_cloudfront_distribution.site[0].domain_name : null
}

output "custom_domain_url" {
  description = "Custom domain HTTPS URL (when enabled)"
  value       = var.enable_custom_domain && var.domain_name != "" ? "https://${var.domain_name}" : null
}
