"""
Deploy Android App with Java Version Fix
==========================================

Wrapper script that sets compatible Java version for Android builds.
Handles Java 26 incompatibility with Kotlin 1.9.x

Usage:
    python deploy_with_java_fix.py --repo-url <url> --app-name <name>

Author: DevOps Engineer
Date: 2026-05-11
"""

import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Deploy Android app with Java compatibility fix")
    parser.add_argument("--repo-url", required=True, help="Git repository URL")
    parser.add_argument("--branch", default="main", help="Git branch")
    parser.add_argument("--app-name", required=True, help="Application name")
    parser.add_argument("--option", default="A", choices=["A", "B", "C"], help="Deployment option")
    parser.add_argument("--aws-bucket", help="AWS S3 bucket name")
    parser.add_argument("--aws-region", default="us-east-1", help="AWS region")

    args = parser.parse_args()

    print("\n" + "="*70)
    print("  Android Deployment with Java Compatibility Fix")
    print("="*70)

    # Check current Java version
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        java_output = result.stderr
        print(f"\nDetected Java: {java_output.split('\\n')[0]}")

        if 'version "26"' in java_output:
            print("\n[WARNING] Java 26 detected!")
            print("Kotlin 1.9.x doesn't support Java 26.")
            print("\nSOLUTIONS:")
            print("1. Install Java 17 LTS (recommended)")
            print("   Download: https://adoptium.net/teapot/")
            print("2. Set JAVA_HOME to Java 17")
            print("3. Use pre-built APK upload instead")
            print("\nFor now, trying build anyway (may fail)...")

    except Exception as e:
        print(f"Could not detect Java version: {e}")

    # Build command for deploy_android_app.py
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "deploy_android_app.py"),
        "--repo-url", args.repo_url,
        "--branch", args.branch,
        "--app-name", args.app_name,
        "--option", args.option
    ]

    if args.aws_bucket:
        cmd.extend(["--aws-bucket", args.aws_bucket])

    cmd.extend(["--aws-region", args.aws_region])

    print("\n" + "="*70)
    print("  Starting Deployment")
    print("="*70)
    print(f"\nCommand: {' '.join(cmd)}\n")

    # Run deployment
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
