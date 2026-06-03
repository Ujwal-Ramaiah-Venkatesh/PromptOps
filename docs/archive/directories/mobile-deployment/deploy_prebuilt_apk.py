"""
Deploy Pre-built APK - Quick Solution
======================================

Upload and deploy a pre-built APK file directly to AWS.
No build required, works with any Java version.

Usage:
    python deploy_prebuilt_apk.py --apk-path <path> --app-name <name>

Author: DevOps Engineer
Date: 2026-05-11
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aws_mobile_deploy import AWSMobileDeployer

# Try to import output handler
try:
    from utils.output_handler import PlatformOutput
    output = PlatformOutput()
except ImportError:
    # Fallback to regular print
    class FallbackOutput:
        def print(self, *args, **kwargs):
            print(*args, **kwargs)
        def print_success(self, msg):
            print(f"[OK] {msg}")
        def print_error(self, msg):
            print(f"[ERROR] {msg}")
        def print_separator(self, **kwargs):
            print("=" * 70)
        def print_header(self, title, **kwargs):
            self.print_separator()
            print(f"  {title}")
            self.print_separator()
    output = FallbackOutput()


def main():
    parser = argparse.ArgumentParser(
        description="Deploy pre-built Android APK to AWS"
    )

    parser.add_argument(
        "--apk-path",
        required=True,
        help="Path to pre-built APK file"
    )

    parser.add_argument(
        "--app-name",
        required=True,
        help="Application name"
    )

    parser.add_argument(
        "--version",
        default="1.0.0",
        help="App version (default: 1.0.0)"
    )

    parser.add_argument(
        "--aws-bucket",
        required=True,
        help="AWS S3 bucket name"
    )

    parser.add_argument(
        "--aws-region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    # Validate APK file
    apk_path = Path(args.apk_path)
    if not apk_path.exists():
        output.print_error(f"APK file not found: {args.apk_path}")
        output.print("\nPlease provide a valid path to your APK file.")
        sys.exit(1)

    if not apk_path.suffix.lower() == '.apk':
        output.print_error(f"File is not an APK: {args.apk_path}")
        output.print("Expected: .apk extension")
        sys.exit(1)

    output.print()
    output.print_header("PromptOps Pre-built APK Deployment")
    output.print(f"\nAPK File:     {apk_path.name}")
    output.print(f"App Name:     {args.app_name}")
    output.print(f"Version:      {args.version}")
    output.print(f"AWS Bucket:   {args.aws_bucket}")
    output.print(f"AWS Region:   {args.aws_region}")
    output.print()
    output.print_separator()
    output.print()

    # Create deployer
    deployer = AWSMobileDeployer(
        bucket_name=args.aws_bucket,
        region=args.aws_region
    )

    output.print("[1/4] Creating AWS S3 bucket...")
    bucket_result = deployer.create_bucket()
    output.print(f"      Status: {bucket_result['status']}")

    output.print("\n[2/4] Uploading APK to S3...")
    upload_result = deployer.upload_apk(
        apk_path=str(apk_path),
        app_name=args.app_name,
        version=args.version
    )
    if upload_result['status'] != 'success':
        output.print_error(f"{upload_result.get('error')}")
        sys.exit(1)
    output.print(f"      Size: {upload_result['file_size_mb']} MB")
    output.print(f"      SHA256: {upload_result['file_hash'][:16]}...")

    output.print("\n[3/4] Creating CloudFront CDN...")
    cdn_result = deployer.create_cloudfront_distribution(args.aws_bucket)
    output.print(f"      Status: {cdn_result['status']}")
    output.print(f"      CDN URL: {cdn_result.get('cdn_url')}")

    output.print("\n[4/4] Generating download page...")
    app_info = {
        "app_name": args.app_name,
        "version": args.version,
        "download_url": upload_result.get("download_url"),
        "file_size_mb": upload_result.get("file_size_mb"),
        "file_hash": upload_result.get("file_hash"),
        "release_date": upload_result.get("uploaded_at", "").split("T")[0],
        "min_sdk": "API 26 (Android 8.0)"
    }
    html_content = deployer.generate_download_page(app_info)
    output.print(f"      Page size: {len(html_content)} bytes")

    output.print()
    output.print_separator()
    output.print("  Deployment Complete!")
    output.print_separator()
    output.print_success(f"Successfully deployed {args.app_name}!")
    output.print(f"\nDownload Page: {upload_result.get('s3_url', '').replace(apk_path.name, 'index.html')}")
    output.print(f"Direct APK URL: {upload_result.get('download_url')}")
    output.print(f"CDN URL: {cdn_result.get('cdn_url')}")
    output.print("\nShare the download page URL with your testers!")
    output.print_separator()
    output.print()


if __name__ == "__main__":
    main()
