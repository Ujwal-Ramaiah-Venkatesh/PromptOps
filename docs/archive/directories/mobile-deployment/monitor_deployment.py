"""
Real-time Deployment Monitor
============================

Shows deployment progress in real-time.

Author: PromptOps Team
Date: 2026-05-11
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def monitor_deployment():
    """Monitor deployment progress."""
    downloads_folder = Path.home() / "Downloads"
    apk_files = []
    last_check = None

    print("\n" + "="*70)
    print("  PromptOps Deployment Monitor")
    print("="*70)
    print("\nPress Ctrl+C to stop monitoring\n")
    print("="*70)

    try:
        while True:
            now = datetime.now().strftime("%H:%M:%S")

            # Find APK files
            current_apks = list(downloads_folder.glob("*.apk"))

            # Check for new APKs
            if len(current_apks) != len(apk_files):
                apk_files = current_apks
                print(f"\n[{now}] APK files in Downloads: {len(apk_files)}")
                for apk in apk_files:
                    size_mb = apk.stat().st_size / (1024 * 1024)
                    print(f"  - {apk.name} ({size_mb:.1f} MB)")

            # Status update
            if not last_check or (datetime.now() - last_check).seconds >= 10:
                print(f"\n[{now}] Status:")
                print(f"  Watching: {downloads_folder}")
                print(f"  APK count: {len(apk_files)}")
                print(f"  Auto-deploy watcher: ACTIVE")

                # Check watcher log
                log_file = Path("/tmp/auto_deploy.log")
                if log_file.exists():
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            if lines:
                                last_line = lines[-1].strip()
                                if last_line:
                                    print(f"  Last log: {last_line[:60]}...")
                    except:
                        pass

                last_check = datetime.now()

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n[MONITOR] Stopped by user")
        print("="*70 + "\n")

if __name__ == "__main__":
    monitor_deployment()
