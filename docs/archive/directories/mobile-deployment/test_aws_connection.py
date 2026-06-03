"""
Test AWS Connection
===================

Quick script to verify AWS credentials are working.

Author: DevOps Engineer
Date: 2026-05-11
"""

import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError

    print("\n" + "="*70)
    print("  AWS Connection Test")
    print("="*70)

    # Try to create S3 client
    print("\n1. Testing boto3 installation... ", end="")
    print("[OK] boto3 installed")

    # Try to create clients
    print("2. Creating AWS clients... ", end="")
    try:
        s3_client = boto3.client('s3')
        print("[OK] S3 client created")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        exit(1)

    # Try to list buckets (tests credentials)
    print("3. Testing AWS credentials... ", end="")
    try:
        response = s3_client.list_buckets()
        print("[OK] Credentials valid")

        # Show existing buckets
        buckets = response.get('Buckets', [])
        print(f"\n4. Existing S3 buckets: {len(buckets)}")
        if buckets:
            for bucket in buckets[:5]:  # Show first 5
                print(f"   - {bucket['Name']}")
            if len(buckets) > 5:
                print(f"   ... and {len(buckets) - 5} more")
        else:
            print("   (No buckets yet - this is fine!)")

        print("\n" + "="*70)
        print("[OK] AWS CONNECTION SUCCESSFUL!")
        print("="*70)
        print("\nYou're ready to deploy Android apps!")
        print("\nNext step:")
        print("  python mobile-deployment/deploy_android_app.py \\")
        print("    --repo-url <your-github-url> \\")
        print("    --app-name \"Your App\" \\")
        print("    --option A \\")
        print("    --aws-bucket your-unique-bucket-name")
        print()

    except NoCredentialsError:
        print("[ERROR] No credentials found")
        print("\nPlease configure AWS credentials:")
        print("  1. Run: aws configure")
        print("  2. Or set environment variables:")
        print("     - AWS_ACCESS_KEY_ID")
        print("     - AWS_SECRET_ACCESS_KEY")
        print("     - AWS_DEFAULT_REGION")
        exit(1)

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidAccessKeyId':
            print("[ERROR] Invalid access key")
        elif error_code == 'SignatureDoesNotMatch':
            print("[ERROR] Invalid secret key")
        else:
            print(f"[ERROR] AWS error: {error_code}")
        print(f"\nDetails: {e}")
        exit(1)

except ImportError:
    print("\n[ERROR] boto3 not installed")
    print("\nPlease install boto3:")
    print("  pip install boto3")
    exit(1)

except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    exit(1)
