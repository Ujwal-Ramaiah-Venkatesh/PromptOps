#!/usr/bin/env python3
"""Simple APK monitor for auto-deployment."""
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

DOWNLOADS = Path.home() / "Downloads"
WATCHED_FILE = Path(os.path.expanduser("~/watched_apks.txt"))

def get_watched():
    """Get list of already-watched APKs."""
    if WATCHED_FILE.exists():
        content = WATCHED_FILE.read_text().strip()
        if content:
            return set(content.split('\n'))
    return set()

def mark_watched(apk_name):
    """Mark APK as watched."""
    with open(WATCHED_FILE, 'a') as f:
        f.write(f"{apk_name}\n")

def deploy_apk(apk_path):
    """Deploy APK to AWS."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*70}")
    print(f"  [{now}] DEPLOYING APK")
    print(f"{'='*70}")

    script_dir = Path(__file__).parent
    deploy_script = script_dir / "deploy_prebuilt_apk.py"

    cmd = [
        sys.executable,
        str(deploy_script),
        "--apk-path", str(apk_path),
        "--app-name", "netSenseAI",
        "--version", "1.0.0",
        "--aws-bucket", "netsense-ai-2026"
    ]

    result = subprocess.run(cmd, capture_output=False)

    print(f"\n{'='*70}")
    print(f"  [{now}] DEPLOYMENT COMPLETE")
    print(f"{'='*70}\n")

    return result.returncode == 0

def main():
    """Main monitoring loop."""
    WATCHED_FILE.touch(exist_ok=True)

    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*70}")
    print(f"  AUTO-DEPLOY MONITOR STARTED")
    print(f"{'='*70}")
    print(f"[{now}] Watching: {DOWNLOADS}")
    print(f"[{now}] Checking every 5 seconds...")
    print(f"[{now}] Press Ctrl+C to stop")
    print(f"{'='*70}\n")

    watched = get_watched()
    check_count = 0

    while True:
        try:
            check_count += 1
            apk_files = list(DOWNLOADS.glob("*.apk"))

            # Show periodic status
            if check_count % 12 == 0:  # Every 60 seconds
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] Status: Monitoring active, {len(apk_files)} APK(s) in Downloads")

            for apk in apk_files:
                apk_name = apk.name

                if apk_name not in watched:
                    now = datetime.now().strftime("%H:%M:%S")
                    size_mb = apk.stat().st_size / (1024 * 1024)

                    print(f"\n{'='*70}")
                    print(f"  [{now}] NEW APK DETECTED!")
                    print(f"{'='*70}")
                    print(f"File: {apk_name}")
                    print(f"Size: {size_mb:.1f} MB")
                    print(f"Path: {apk}")
                    print(f"{'='*70}\n")

                    # Mark as watched immediately
                    mark_watched(apk_name)
                    watched.add(apk_name)

                    # Deploy
                    deploy_apk(apk)

            time.sleep(5)

        except KeyboardInterrupt:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{now}] Monitor stopped by user\n")
            break
        except Exception as e:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
