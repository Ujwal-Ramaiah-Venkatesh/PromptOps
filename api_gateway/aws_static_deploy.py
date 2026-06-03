"""
PromptOps — AWS S3 Static Site Deployment
==========================================

Deploys a local static site to AWS S3 with public website hosting.
No CloudFront needed for a basic public URL — S3 website endpoint
gives a plain HTTP public URL immediately.

Steps executed:
  1. Validate source directory
  2. Resolve target AWS region
  3. Create S3 bucket (or reuse existing)
  4. Disable Block Public Access settings
  5. Enable S3 static website hosting
  6. Apply public-read bucket policy
  7. Upload all files with correct Content-Type headers
  8. Return public website URL
"""

import boto3
import json
import mimetypes
import os
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError


# ── Content-type map for PWA files ─────────────────────────────────────────────
MIME_OVERRIDES = {
    ".html":    "text/html; charset=utf-8",
    ".js":      "application/javascript; charset=utf-8",
    ".json":    "application/json",
    ".css":     "text/css; charset=utf-8",
    ".png":     "image/png",
    ".jpg":     "image/jpeg",
    ".jpeg":    "image/jpeg",
    ".webp":    "image/webp",
    ".ico":     "image/x-icon",
    ".svg":     "image/svg+xml",
    ".txt":     "text/plain; charset=utf-8",
    ".pdf":     "application/pdf",
    ".webmanifest": "application/manifest+json",
}

# Files that should be served with no-cache so updates are instant
NO_CACHE_FILES = {"index.html", "sw.js", "manifest.json"}


def _get_content_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return MIME_OVERRIDES.get(ext, mimetypes.guess_type(filename)[0] or "application/octet-stream")


def _cache_control(filename: str) -> str:
    """Service worker and entry point must never be cached by the browser."""
    if filename in NO_CACHE_FILES:
        return "no-cache, no-store, must-revalidate"
    return "public, max-age=86400"  # 1-day cache for assets


def deploy_to_s3(
    source_path: str,
    bucket_name: str,
    region: str = "us-east-1",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_session_token: str | None = None,
) -> dict:
    """
    Deploy a local static directory to S3 static website hosting.

    Returns a deployment result dict with the public URL and all steps.
    """
    steps = []
    source = Path(source_path)

    def _is_deployable_file(path: Path) -> bool:
        """Exclude hidden and VCS files from public website uploads."""
        rel_parts = path.relative_to(source).parts
        blocked_dirs = {".git", ".github", ".vscode", "__pycache__", ".idea"}
        for part in rel_parts:
            if part in blocked_dirs:
                return False
            if part.startswith("."):
                return False
        return True

    # ── Step 1: Validate source ────────────────────────────────────────────────
    if not source.is_dir():
        raise ValueError(f"Source directory not found: {source_path}")
    files = [f for f in source.rglob("*") if f.is_file() and _is_deployable_file(f)]
    steps.append({
        "step": "T-01",
        "title": "Validate source directory",
        "detail": f"{len(files)} files found in {source_path}",
        "status": "done",
    })

    # ── Step 2: Init boto3 clients ─────────────────────────────────────────────
    try:
        session_kwargs = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key
            if aws_session_token:
                session_kwargs["aws_session_token"] = aws_session_token

        session = boto3.session.Session(**session_kwargs)
        s3 = session.client("s3")

        # Quick credential check
        session.client("sts").get_caller_identity()
    except NoCredentialsError:
        raise PermissionError(
            "AWS credentials not found. Run `aws configure` in your terminal first."
        )
    steps.append({
        "step": "T-02",
        "title": "AWS credentials verified",
        "detail": f"Region: {region}",
        "status": "done",
    })

    # ── Step 3: Create bucket (or confirm it exists) ───────────────────────────
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        bucket_action = "created"
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            bucket_action = "already exists (reusing)"
        else:
            raise RuntimeError(f"Failed to create bucket: {e}") from e

    steps.append({
        "step": "T-03",
        "title": "S3 bucket ready",
        "detail": f"s3://{bucket_name} — {bucket_action}",
        "status": "done",
    })

    # ── Step 4: Disable Block Public Access ────────────────────────────────────
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls":       False,
            "IgnorePublicAcls":      False,
            "BlockPublicPolicy":     False,
            "RestrictPublicBuckets": False,
        },
    )
    steps.append({
        "step": "T-04",
        "title": "Block Public Access disabled",
        "detail": "All four Block Public Access settings set to False",
        "status": "done",
    })

    # ── Step 5: Enable static website hosting ─────────────────────────────────
    s3.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "index.html"},
        },
    )
    steps.append({
        "step": "T-05",
        "title": "Static website hosting enabled",
        "detail": "IndexDocument=index.html, ErrorDocument=index.html",
        "status": "done",
    })

    # ── Step 6: Apply public-read bucket policy ────────────────────────────────
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid":       "PublicReadGetObject",
                "Effect":    "Allow",
                "Principal": "*",
                "Action":    "s3:GetObject",
                "Resource":  f"arn:aws:s3:::{bucket_name}/*",
            }
        ],
    }
    s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
    steps.append({
        "step": "T-06",
        "title": "Public-read bucket policy applied",
        "detail": f"s3:GetObject allowed for Principal=* on {bucket_name}/*",
        "status": "done",
    })

    # ── Step 7: Upload all files ───────────────────────────────────────────────
    uploaded = []
    for file_path in files:
        key = file_path.relative_to(source).as_posix()   # forward slashes for S3
        content_type = _get_content_type(file_path.name)
        cache_control = _cache_control(file_path.name)

        s3.upload_file(
            Filename=str(file_path),
            Bucket=bucket_name,
            Key=key,
            ExtraArgs={
                "ContentType":  content_type,
                "CacheControl": cache_control,
            },
        )
        uploaded.append({"key": key, "content_type": content_type, "cache_control": cache_control})

    steps.append({
        "step": "T-07",
        "title": f"Files uploaded to S3 ({len(uploaded)} files)",
        "detail": uploaded,
        "status": "done",
    })

    # ── Step 8: Build public website URL ──────────────────────────────────────
    if region == "us-east-1":
        website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
    else:
        website_url = f"http://{bucket_name}.s3-website.{region}.amazonaws.com"

    steps.append({
        "step": "T-08",
        "title": "Deployment complete — public URL ready",
        "detail": website_url,
        "status": "done",
    })

    return {
        "app_name":    "jewelry-vault",
        "bucket":      bucket_name,
        "region":      region,
        "website_url": website_url,
        "s3_uri":      f"s3://{bucket_name}",
        "files_uploaded": len(uploaded),
        "files":       uploaded,
        "status":      "deployed",
        "steps":       steps,
    }
