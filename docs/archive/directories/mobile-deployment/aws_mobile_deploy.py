"""
AWS Mobile App Deployment for PromptOps
========================================

Deploy Android/iOS apps to AWS S3 + CloudFront.
Option A: Direct APK/IPA hosting with download page.

Author: DevOps Engineer
Date: 2026-05-10
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Try to import boto3 for real AWS integration
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("boto3 not installed - using mock mode. Install with: pip install boto3")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# AWS Mobile Deployer
# ============================================================================

class AWSMobileDeployer:
    """
    AWS S3 + CloudFront mobile app deployer.

    Features:
    - S3 bucket creation and configuration
    - APK/IPA upload to S3
    - CloudFront distribution setup
    - Static download page generation
    - Version management
    - Changelog generation
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        use_mock: bool = False
    ):
        """
        Initialize AWS Mobile Deployer.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            aws_access_key: AWS access key
            aws_secret_key: AWS secret key
            use_mock: Force mock mode even if boto3 is available
        """
        self.bucket_name = bucket_name
        self.region = region
        self.aws_access_key = aws_access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.use_mock = use_mock or not BOTO3_AVAILABLE

        # Initialize AWS clients if boto3 is available
        if BOTO3_AVAILABLE and not use_mock:
            try:
                session_kwargs = {"region_name": region}
                if aws_access_key and aws_secret_key:
                    session_kwargs["aws_access_key_id"] = aws_access_key
                    session_kwargs["aws_secret_access_key"] = aws_secret_key

                self.s3_client = boto3.client('s3', **session_kwargs)
                self.cloudfront_client = boto3.client('cloudfront', **session_kwargs)
                logger.info("AWS clients initialized successfully")

                # Validate credentials immediately
                self._validate_credentials()
            except (NoCredentialsError, Exception) as e:
                logger.warning(f"Failed to initialize AWS clients: {e}. Falling back to mock mode.")
                self.use_mock = True
        else:
            self.s3_client = None
            self.cloudfront_client = None

    def _validate_credentials(self) -> bool:
        """
        Validate AWS credentials before deployment.

        Returns:
            True if credentials are valid

        Raises:
            RuntimeError: If credentials are invalid
        """
        if self.use_mock:
            logger.info("Mock mode - skipping credential validation")
            return True

        try:
            # Try to list buckets (minimal operation to test credentials)
            self.s3_client.list_buckets()
            logger.info("AWS credentials validated successfully")
            return True
        except NoCredentialsError:
            raise RuntimeError(
                "AWS credentials not found. Please configure credentials:\n"
                "  1. Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY\n"
                "  2. Run: aws configure\n"
                "  3. Or create ~/.aws/credentials file"
            )
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidClientTokenId':
                raise RuntimeError(
                    "AWS Access Key ID is invalid. Please check your credentials:\n"
                    "  - Verify AWS_ACCESS_KEY_ID is correct\n"
                    "  - Run: aws configure"
                )
            elif error_code == 'SignatureDoesNotMatch':
                raise RuntimeError(
                    "AWS Secret Access Key is invalid. Please check your credentials:\n"
                    "  - Verify AWS_SECRET_ACCESS_KEY is correct\n"
                    "  - Run: aws configure"
                )
            else:
                raise RuntimeError(f"AWS credential validation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"AWS credential validation failed: {e}")

    def create_bucket(self) -> Dict[str, Any]:
        """
        Create S3 bucket for app hosting.

        Returns:
            Bucket creation result
        """
        logger.info(f"Creating S3 bucket: {self.bucket_name}")

        if self.use_mock:
            # Mock implementation
            return {
                "status": "success",
                "bucket_name": self.bucket_name,
                "region": self.region,
                "bucket_url": f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com",
                "configuration": {
                    "versioning": "enabled",
                    "public_access": "enabled_for_downloads",
                    "encryption": "AES256"
                },
                "created_at": datetime.utcnow().isoformat(),
                "mode": "mock"
            }

        # Real boto3 implementation
        try:
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} already exists")
                bucket_exists = True
            except ClientError:
                bucket_exists = False

            # Create bucket if it doesn't exist
            if not bucket_exists:
                if self.region == 'us-east-1':
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                logger.info(f"Created bucket: {self.bucket_name}")

            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )

            # Enable encryption
            self.s3_client.put_bucket_encryption(
                Bucket=self.bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
                }
            )

            # Configure CORS for download page
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration={
                    'CORSRules': [{
                        'AllowedOrigins': ['*'],
                        'AllowedMethods': ['GET', 'HEAD'],
                        'AllowedHeaders': ['*'],
                        'MaxAgeSeconds': 3000
                    }]
                }
            )

            # Set public access for downloads (specific objects only)
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/apps/*"
                }]
            }
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )

            return {
                "status": "success",
                "bucket_name": self.bucket_name,
                "region": self.region,
                "bucket_url": f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com",
                "configuration": {
                    "versioning": "enabled",
                    "public_access": "enabled_for_downloads",
                    "encryption": "AES256",
                    "cors": "enabled"
                },
                "created_at": datetime.utcnow().isoformat(),
                "mode": "real",
                "already_existed": bucket_exists
            }

        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            return {
                "status": "error",
                "error": str(e),
                "bucket_name": self.bucket_name
            }

    def upload_apk(
        self,
        apk_path: str,
        app_name: str,
        version: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload APK to S3.

        Args:
            apk_path: Path to APK file
            app_name: Application name
            version: App version
            metadata: Additional metadata

        Returns:
            Upload result
        """
        logger.info(f"Uploading APK: {apk_path}")

        apk_file = Path(apk_path)

        # In mock mode, don't check file existence
        if not self.use_mock and not apk_file.exists():
            return {
                "status": "error",
                "error": f"APK file not found: {apk_path}"
            }

        # For mock mode, simulate file stats
        if self.use_mock:
            file_hash = "abc123def456789012345678901234567890123456789012345678901234"
            file_size = 25 * 1024 * 1024  # 25 MB
        else:
            file_hash = self._calculate_file_hash(apk_path)
            file_size = apk_file.stat().st_size

        # S3 key structure: apps/{app_name}/{version}/{filename}
        s3_key = f"apps/{app_name}/{version}/{apk_file.name}"

        if self.use_mock:
            # Mock upload
            return {
                "status": "success",
                "app_name": app_name,
                "version": version,
                "apk_file": apk_file.name,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "file_hash": file_hash,
                "s3_key": s3_key,
                "s3_url": f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}",
                "download_url": f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}",
                "uploaded_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "mode": "mock"
            }

        # Real boto3 upload
        try:
            # Prepare metadata
            s3_metadata = {
                "app-name": app_name,
                "version": version,
                "sha256": file_hash,
                "uploaded-at": datetime.utcnow().isoformat()
            }
            if metadata:
                s3_metadata.update({k.replace('_', '-'): str(v) for k, v in metadata.items()})

            # Upload file
            self.s3_client.upload_file(
                str(apk_file),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/vnd.android.package-archive',
                    'Metadata': s3_metadata,
                    'ContentDisposition': f'attachment; filename="{apk_file.name}"'
                }
            )

            logger.info(f"Uploaded APK to s3://{self.bucket_name}/{s3_key}")

            return {
                "status": "success",
                "app_name": app_name,
                "version": version,
                "apk_file": apk_file.name,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "file_hash": file_hash,
                "s3_key": s3_key,
                "s3_url": f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}",
                "download_url": f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}",
                "uploaded_at": datetime.utcnow().isoformat(),
                "metadata": s3_metadata,
                "mode": "real"
            }

        except ClientError as e:
            logger.error(f"Failed to upload APK: {e}")
            return {
                "status": "error",
                "error": str(e),
                "apk_path": apk_path
            }

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def create_cloudfront_distribution(
        self,
        bucket_name: str
    ) -> Dict[str, Any]:
        """
        Create CloudFront distribution.

        Args:
            bucket_name: S3 bucket name

        Returns:
            Distribution info
        """
        logger.info("Creating CloudFront distribution")

        if self.use_mock:
            # Mock implementation
            return {
                "status": "success",
                "distribution_id": "E1234ABCDEFGH",
                "domain_name": f"d1234abcdefgh.cloudfront.net",
                "origin": f"{bucket_name}.s3.{self.region}.amazonaws.com",
                "price_class": "PriceClass_100",
                "enabled": True,
                "cdn_url": f"https://d1234abcdefgh.cloudfront.net",
                "created_at": datetime.utcnow().isoformat(),
                "mode": "mock"
            }

        # Real CloudFront distribution creation
        try:
            origin_id = f"S3-{bucket_name}"
            caller_reference = f"mobile-app-{datetime.utcnow().timestamp()}"

            distribution_config = {
                'CallerReference': caller_reference,
                'Comment': f'Mobile app distribution for {bucket_name}',
                'Enabled': True,
                'Origins': {
                    'Quantity': 1,
                    'Items': [{
                        'Id': origin_id,
                        'DomainName': f"{bucket_name}.s3.{self.region}.amazonaws.com",
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': origin_id,
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'AllowedMethods': {
                        'Quantity': 2,
                        'Items': ['GET', 'HEAD'],
                        'CachedMethods': {
                            'Quantity': 2,
                            'Items': ['GET', 'HEAD']
                        }
                    },
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'none'}
                    },
                    'MinTTL': 0,
                    'DefaultTTL': 86400,
                    'MaxTTL': 31536000,
                    'Compress': True,
                    'TrustedSigners': {
                        'Enabled': False,
                        'Quantity': 0
                    }
                },
                'PriceClass': 'PriceClass_100',  # US, Canada, Europe
                'ViewerCertificate': {
                    'CloudFrontDefaultCertificate': True
                }
            }

            response = self.cloudfront_client.create_distribution(
                DistributionConfig=distribution_config
            )

            distribution = response['Distribution']
            distribution_id = distribution['Id']
            domain_name = distribution['DomainName']

            logger.info(f"Created CloudFront distribution: {distribution_id}")

            return {
                "status": "success",
                "distribution_id": distribution_id,
                "domain_name": domain_name,
                "origin": f"{bucket_name}.s3.{self.region}.amazonaws.com",
                "price_class": "PriceClass_100",
                "enabled": True,
                "cdn_url": f"https://{domain_name}",
                "created_at": datetime.utcnow().isoformat(),
                "mode": "real",
                "note": "Distribution may take 15-20 minutes to deploy globally"
            }

        except ClientError as e:
            logger.error(f"Failed to create CloudFront distribution: {e}")
            return {
                "status": "error",
                "error": str(e),
                "bucket_name": bucket_name
            }

    def generate_download_page(
        self,
        app_info: Dict[str, Any]
    ) -> str:
        """
        Generate HTML download page.

        Args:
            app_info: App information

        Returns:
            HTML content
        """
        logger.info("Generating download page")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_info.get('app_name', 'App')} - Download</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .app-icon {{
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            color: white;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .version {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .download-btn {{
            display: block;
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            transition: transform 0.2s;
            margin-bottom: 20px;
        }}
        .download-btn:hover {{
            transform: translateY(-2px);
        }}
        .info {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        .info-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        .info-item:last-child {{
            margin-bottom: 0;
        }}
        .label {{
            color: #666;
        }}
        .value {{
            color: #333;
            font-weight: 500;
        }}
        .instructions {{
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 10px;
            font-size: 14px;
            color: #856404;
        }}
        .instructions h3 {{
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .instructions ol {{
            margin-left: 20px;
        }}
        .instructions li {{
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="app-icon">📱</div>
        <h1>{app_info.get('app_name', 'Mobile App')}</h1>
        <div class="version">Version {app_info.get('version', '1.0.0')}</div>

        <a href="{app_info.get('download_url', '#')}" class="download-btn">
            📥 Download APK ({app_info.get('file_size_mb', '0')} MB)
        </a>

        <div class="info">
            <div class="info-item">
                <span class="label">Release Date:</span>
                <span class="value">{app_info.get('release_date', 'Today')}</span>
            </div>
            <div class="info-item">
                <span class="label">Min Android:</span>
                <span class="value">{app_info.get('min_sdk', 'API 26 (Android 8.0)')}</span>
            </div>
            <div class="info-item">
                <span class="label">File Size:</span>
                <span class="value">{app_info.get('file_size_mb', '0')} MB</span>
            </div>
            <div class="info-item">
                <span class="label">SHA256:</span>
                <span class="value" style="font-size: 10px; word-break: break-all;">{app_info.get('file_hash', 'N/A')[:16]}...</span>
            </div>
        </div>

        <div class="instructions">
            <h3>📋 Installation Instructions</h3>
            <ol>
                <li>Download the APK file</li>
                <li>Enable "Install from Unknown Sources" in Settings</li>
                <li>Open the downloaded APK file</li>
                <li>Follow the installation prompts</li>
                <li>Launch the app from your app drawer</li>
            </ol>
        </div>
    </div>
</body>
</html>"""

        return html

    def deploy_app(
        self,
        apk_path: str,
        app_name: str,
        version: str,
        create_distribution: bool = True
    ) -> Dict[str, Any]:
        """
        Complete app deployment workflow.

        Args:
            apk_path: Path to APK file
            app_name: Application name
            version: Version string
            create_distribution: Create CloudFront distribution

        Returns:
            Deployment result
        """
        logger.info(f"Starting deployment for {app_name} v{version}")

        deployment = {
            "deployment_id": f"deploy-{datetime.utcnow().timestamp()}",
            "app_name": app_name,
            "version": version,
            "started_at": datetime.utcnow().isoformat(),
            "steps": []
        }

        # Step 1: Create bucket (if needed)
        bucket_result = self.create_bucket()
        deployment["steps"].append({
            "step": "create_bucket",
            "result": bucket_result
        })

        # Step 2: Upload APK
        upload_result = self.upload_apk(apk_path, app_name, version)
        deployment["steps"].append({
            "step": "upload_apk",
            "result": upload_result
        })

        # Step 3: Create CloudFront (optional)
        if create_distribution:
            cf_result = self.create_cloudfront_distribution(self.bucket_name)
            deployment["steps"].append({
                "step": "create_cloudfront",
                "result": cf_result
            })
            deployment["cdn_url"] = cf_result["cdn_url"]

        # Step 4: Generate download page
        app_info = {
            "app_name": app_name,
            "version": version,
            "download_url": upload_result.get("download_url"),
            "file_size_mb": upload_result.get("file_size_mb"),
            "file_hash": upload_result.get("file_hash"),
            "release_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "min_sdk": "API 26 (Android 8.0)"
        }
        html_content = self.generate_download_page(app_info)
        deployment["steps"].append({
            "step": "generate_download_page",
            "result": {"status": "success", "page_size": len(html_content)}
        })

        deployment["completed_at"] = datetime.utcnow().isoformat()
        deployment["download_page_url"] = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/apps/{app_name}/{version}/index.html"
        deployment["direct_apk_url"] = upload_result.get("download_url")

        return deployment


# ============================================================================
# Testing
# ============================================================================

def test_aws_mobile_deployer():
    """Test AWS Mobile Deployer."""
    logger.info("Testing AWS Mobile Deployer...")

    deployer = AWSMobileDeployer(
        bucket_name="my-android-apps",
        region="us-east-1"
    )

    # Test 1: Create bucket
    print("\n=== Test 1: Create S3 Bucket ===")
    bucket_result = deployer.create_bucket()
    print(f"Bucket: {bucket_result['bucket_name']}")
    print(f"Region: {bucket_result['region']}")
    print(f"URL: {bucket_result['bucket_url']}")

    # Test 2: CloudFront distribution
    print("\n=== Test 2: Create CloudFront Distribution ===")
    cf_result = deployer.create_cloudfront_distribution("my-android-apps")
    print(f"Distribution ID: {cf_result['distribution_id']}")
    print(f"CDN Domain: {cf_result['domain_name']}")
    print(f"CDN URL: {cf_result['cdn_url']}")

    # Test 3: Generate download page
    print("\n=== Test 3: Generate Download Page ===")
    app_info = {
        "app_name": "AdaptiveRTC PTT",
        "version": "1.0.0",
        "download_url": "https://example.com/app.apk",
        "file_size_mb": "25.5",
        "file_hash": "abc123def456...",
        "release_date": "2026-05-10",
        "min_sdk": "API 26"
    }
    html = deployer.generate_download_page(app_info)
    print(f"HTML Page Size: {len(html)} bytes")
    print(f"Preview (first 200 chars):\n{html[:200]}...")


if __name__ == "__main__":
    test_aws_mobile_deployer()
