"""
PromptOps Mobile Deployment - Usage Examples
==============================================

Quick start examples for deploying Android apps.

Author: DevOps Engineer
Date: 2026-05-11
"""

from deploy_android_app import AndroidDeploymentOrchestrator
from aws_mobile_deploy import AWSMobileDeployer
from android_builder import AndroidBuilder


def example1_deploy_from_github():
    """
    Example 1: Deploy Android app from GitHub repository.

    This is the most common use case - clone a repo and deploy.
    """
    print("\n" + "="*70)
    print("Example 1: Deploy from GitHub")
    print("="*70)

    orchestrator = AndroidDeploymentOrchestrator()

    result = orchestrator.deploy_from_git(
        repo_url="https://github.com/kirankumarhs29/AdaptiveRTC_PTT",
        branch="main",
        app_name="AdaptiveRTC PTT",
        deployment_option="A",
        aws_config={
            "bucket_name": "adaptive-rtc-apps",
            "region": "us-east-1"
        }
    )

    orchestrator.cleanup()

    print(f"\nDeployment Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Download URL: {result.get('download_url')}")
        print(f"Direct APK: {result.get('direct_apk_url')}")
    else:
        print(f"Error: {result.get('error')}")

    return result


def example2_upload_prebuilt_apk():
    """
    Example 2: Upload a pre-built APK file.

    Use this when you already have an APK file built locally.
    """
    print("\n" + "="*70)
    print("Example 2: Upload Pre-built APK")
    print("="*70)

    deployer = AWSMobileDeployer(
        bucket_name="my-android-apps",
        region="us-east-1",
        use_mock=True  # Set to False for real AWS deployment
    )

    # In real usage, replace with actual APK path
    apk_path = "/path/to/your/app-debug.apk"

    result = deployer.deploy_app(
        apk_path=apk_path,
        app_name="My Android App",
        version="1.0.0",
        create_distribution=True
    )

    print(f"\nDeployment Status: {result['steps'][-1]['result']['status']}")
    print(f"Download URL: {result.get('download_page_url')}")
    print(f"CDN URL: {result.get('cdn_url')}")

    return result


def example3_build_apk_only():
    """
    Example 3: Build APK from local Android project.

    Use this to just build an APK without deploying.
    """
    print("\n" + "="*70)
    print("Example 3: Build APK Only")
    print("="*70)

    # In real usage, replace with your Android project path
    project_path = "/path/to/your/android/project"

    try:
        builder = AndroidBuilder(project_path)

        # Build debug APK
        result = builder.build_debug_apk(module="app")

        if result['status'] == 'success':
            print(f"\nBuild successful!")
            print(f"APK Path: {result['apk_path']}")
            print(f"Size: {result.get('apk_size_mb')} MB")
            print(f"Duration: {result['duration_seconds']} seconds")
        else:
            print(f"\nBuild failed: {result.get('error')}")

        return result

    except FileNotFoundError as e:
        print(f"\nProject not found: {e}")
        return {"status": "error", "error": str(e)}


def example4_get_version_info():
    """
    Example 4: Extract version info from Android project.

    Use this to check the app version before deployment.
    """
    print("\n" + "="*70)
    print("Example 4: Get Version Info")
    print("="*70)

    # In real usage, replace with your Android project path
    project_path = "/path/to/your/android/project"

    try:
        builder = AndroidBuilder(project_path)
        version_info = builder.get_version_info(module="app")

        if version_info['status'] == 'success':
            print(f"\nVersion Code: {version_info['version_code']}")
            print(f"Version Name: {version_info['version_name']}")
            print(f"Gradle File: {version_info['gradle_file']}")
        else:
            print(f"\nFailed to get version: {version_info.get('error')}")

        return version_info

    except FileNotFoundError as e:
        print(f"\nProject not found: {e}")
        return {"status": "error", "error": str(e)}


def example5_create_aws_infrastructure():
    """
    Example 5: Create AWS infrastructure (bucket + CDN).

    Use this to set up AWS resources before deploying apps.
    """
    print("\n" + "="*70)
    print("Example 5: Create AWS Infrastructure")
    print("="*70)

    deployer = AWSMobileDeployer(
        bucket_name="my-mobile-apps",
        region="us-east-1",
        use_mock=True  # Set to False for real AWS
    )

    # Step 1: Create S3 bucket
    print("\nCreating S3 bucket...")
    bucket_result = deployer.create_bucket()
    print(f"Bucket Status: {bucket_result['status']}")
    print(f"Bucket URL: {bucket_result.get('bucket_url')}")

    # Step 2: Create CloudFront distribution
    print("\nCreating CloudFront distribution...")
    cf_result = deployer.create_cloudfront_distribution("my-mobile-apps")
    print(f"CloudFront Status: {cf_result['status']}")
    print(f"CDN URL: {cf_result.get('cdn_url')}")
    print(f"Distribution ID: {cf_result.get('distribution_id')}")

    return {
        "bucket": bucket_result,
        "cloudfront": cf_result
    }


def example6_deploy_with_custom_config():
    """
    Example 6: Deploy with custom AWS configuration.

    Use this for advanced configurations.
    """
    print("\n" + "="*70)
    print("Example 6: Custom Configuration Deployment")
    print("="*70)

    # Custom AWS config
    aws_config = {
        "bucket_name": "custom-app-bucket",
        "region": "eu-west-1",  # Europe
        # In real usage, add credentials:
        # "aws_access_key": "YOUR_ACCESS_KEY",
        # "aws_secret_key": "YOUR_SECRET_KEY"
    }

    orchestrator = AndroidDeploymentOrchestrator(
        work_dir="/tmp/my-builds"  # Custom work directory
    )

    result = orchestrator.deploy_from_git(
        repo_url="https://github.com/kirankumarhs29/netSenseAI",
        branch="main",
        app_name="netSenseAI",
        deployment_option="A",
        aws_config=aws_config
    )

    orchestrator.cleanup()

    print(f"\nDeployment Status: {result['status']}")
    print(f"Deployment ID: {result.get('deployment_id')}")

    return result


def example7_mock_mode_testing():
    """
    Example 7: Test deployment in mock mode (no AWS required).

    Use this for testing without AWS credentials.
    """
    print("\n" + "="*70)
    print("Example 7: Mock Mode Testing")
    print("="*70)

    deployer = AWSMobileDeployer(
        bucket_name="test-bucket",
        region="us-east-1",
        use_mock=True  # Force mock mode
    )

    # Test bucket creation
    bucket = deployer.create_bucket()
    print(f"\nMock Bucket Created: {bucket['bucket_name']}")
    print(f"Mode: {bucket.get('mode', 'unknown')}")

    # Test APK upload (with mock file)
    upload = deployer.upload_apk(
        apk_path="mock-app.apk",  # Won't actually check if exists in mock
        app_name="Test App",
        version="1.0.0"
    )
    print(f"\nMock Upload Status: {upload.get('status')}")
    print(f"S3 URL: {upload.get('s3_url')}")

    # Test CloudFront
    cdn = deployer.create_cloudfront_distribution("test-bucket")
    print(f"\nMock CDN Created: {cdn['distribution_id']}")
    print(f"CDN Domain: {cdn['domain_name']}")

    return {
        "bucket": bucket,
        "upload": upload,
        "cdn": cdn
    }


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("PromptOps Mobile Deployment - Usage Examples")
    print("="*70)

    examples = [
        # ("Example 1: Deploy from GitHub", example1_deploy_from_github),
        ("Example 2: Upload Pre-built APK", example2_upload_prebuilt_apk),
        # ("Example 3: Build APK Only", example3_build_apk_only),
        # ("Example 4: Get Version Info", example4_get_version_info),
        ("Example 5: Create AWS Infrastructure", example5_create_aws_infrastructure),
        # ("Example 6: Custom Configuration", example6_deploy_with_custom_config),
        ("Example 7: Mock Mode Testing", example7_mock_mode_testing),
    ]

    print("\nRunning examples in mock mode...")
    print("(Uncomment examples 1, 3, 4, 6 to test with real Android projects)")

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n{name} failed: {e}")

    print("\n" + "="*70)
    print("Examples complete!")
    print("="*70)


if __name__ == "__main__":
    main()
