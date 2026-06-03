# AWS Static Site Terraform

This Terraform config provisions the same type of deployment used in PromptOps UI for static website hosting:

- S3 bucket
- Static website configuration
- Public-read bucket policy
- Optional custom domain with HTTPS:
	- ACM certificate (us-east-1)
	- CloudFront distribution
	- Route53 alias records
- Outputs for website endpoint/URL

## Files

- main.tf
- variables.tf
- outputs.tf
- terraform.tfvars.example

## Usage

1. Copy variables file:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

2. Update `terraform.tfvars` with your unique `bucket_name`.

3. Initialize and apply:

```powershell
terraform init
terraform plan
terraform apply
```

4. Upload your built/static files to the bucket (example):

```powershell
aws s3 sync "C:\Users\pqm847\Documents\jewelry-vault" s3://<bucket-name> --delete
```

5. Get output URL:

```powershell
terraform output website_url
```

## Notes

- Bucket names must be globally unique.
- This configuration intentionally allows public website access for static hosting.

## Custom Domain + HTTPS

To enable custom domain and TLS:

1. Set these values in `terraform.tfvars`:

```hcl
enable_custom_domain = true
domain_name          = "app.example.com"
hosted_zone_id       = "<your-route53-hosted-zone-id>"
acm_certificate_arn  = ""
```

2. Run apply:

```powershell
terraform apply
```

3. If `acm_certificate_arn` is empty, Terraform creates and validates a certificate in `us-east-1` automatically.

4. Outputs to use:

```powershell
terraform output cloudfront_domain_name
terraform output custom_domain_url
```

If you already have a certificate in `us-east-1`, set `acm_certificate_arn` and Terraform will reuse it.
