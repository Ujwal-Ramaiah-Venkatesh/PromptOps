"""
Auto-Deploy Watcher
===================

Watches Downloads folder for APK file and deploys automatically.
No manual deployment command needed!

Author: PromptOps Team
Date: 2026-05-11
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
import subprocess

# Configuration
WATCH_FOLDER = Path.home() / "Downloads"
APK_PATTERNS = ["*netSense*.apk", "*android*.apk", "*.apk"]
CHECK_INTERVAL = 5  # seconds
APP_NAME = "netSenseAI"
VERSION = "1.0.0"
AWS_BUCKET = "netsense-ai-2026"
AWS_REGION = "us-east-1"


class AutoDeployWatcher:
    """Watches for APK and deploys automatically."""

    def __init__(self):
        self.watch_folder = WATCH_FOLDER
        self.deployed_files = set()
        self.script_dir = Path(__file__).parent

    def find_new_apk(self):
        """Find newly downloaded APK files."""
        for pattern in APK_PATTERNS:
            for apk_file in self.watch_folder.glob(pattern):
                if apk_file.is_file() and str(apk_file) not in self.deployed_files:
                    # Check if file is completely downloaded (not being written)
                    try:
                        initial_size = apk_file.stat().st_size
                        time.sleep(1)
                        final_size = apk_file.stat().st_size

                        if initial_size == final_size and final_size > 1024 * 1024:  # > 1MB
                            return apk_file
                    except Exception:
                        continue
        return None

    def deploy_apk(self, apk_path):
        """Deploy APK to AWS."""
        print("\n" + "="*70)
        print(f"  NEW APK DETECTED!")
        print("="*70)
        print(f"File: {apk_path.name}")
        print(f"Size: {apk_path.stat().st_size / (1024*1024):.1f} MB")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        print("\n[AUTO-DEPLOY] Starting deployment...")
        print()

        # Build deployment command
        deploy_script = self.script_dir / "deploy_prebuilt_apk.py"

        cmd = [
            sys.executable,
            str(deploy_script),
            "--apk-path", str(apk_path),
            "--app-name", APP_NAME,
            "--version", VERSION,
            "--aws-bucket", AWS_BUCKET,
            "--aws-region", AWS_REGION
        ]

        try:
            # Run deployment
            result = subprocess.run(
                cmd,
                capture_output=False,  # Show output in real-time
                text=True
            )

            if result.returncode == 0:
                print("\n" + "="*70)
                print("  AUTO-DEPLOYMENT SUCCESSFUL!")
                print("="*70)
                print(f"\nAPK deployed: {apk_path.name}")
                print(f"App name: {APP_NAME}")
                print(f"Version: {VERSION}")
                print("\nCheck the output above for download URLs!")
                print("="*70 + "\n")

                # Mark as deployed
                self.deployed_files.add(str(apk_path))
                return True
            else:
                print("\n" + "="*70)
                print("  AUTO-DEPLOYMENT FAILED!")
                print("="*70)
                print(f"Exit code: {result.returncode}")
                print("\nYou can retry manually with:")
                print(f"python deploy_prebuilt_apk.py --apk-path \"{apk_path}\" --app-name {APP_NAME} --version {VERSION} --aws-bucket {AWS_BUCKET}")
                print("="*70 + "\n")
                return False

        except Exception as e:
            print(f"\n[ERROR] Deployment failed: {e}")
            return False

    def watch(self):
        """Watch for APK files and deploy automatically."""
        print("\n" + "="*70)
        print("  PromptOps Auto-Deploy Watcher")
        print("="*70)
        print(f"\nWatching: {self.watch_folder}")
        print(f"Patterns: {', '.join(APK_PATTERNS)}")
        print(f"Check interval: {CHECK_INTERVAL} seconds")
        print("\nWaiting for APK download...")
        print("(Press Ctrl+C to stop)")
        print("="*70 + "\n")

        try:
            while True:
                apk_file = self.find_new_apk()

                if apk_file:
                    self.deploy_apk(apk_file)
                    print("\n[WATCHER] Continuing to watch for more APK files...")
                    print()

                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n[WATCHER] Stopped by user")
            print("="*70)
            if self.deployed_files:
                print(f"\nTotal deployments: {len(self.deployed_files)}")
                for deployed in self.deployed_files:
                    print(f"  - {Path(deployed).name}")
            print("\n" + "="*70 + "\n")


def main():
    """Run the auto-deploy watcher."""
    watcher = AutoDeployWatcher()
    watcher.watch()


if __name__ == "__main__":
    main()
