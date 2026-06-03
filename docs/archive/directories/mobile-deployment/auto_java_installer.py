"""
Automatic Java 17 Installer for PromptOps
=========================================

Automatically downloads and installs Java 17 when not found.
No user intervention required.

Author: PromptOps Team
Date: 2026-05-11
"""

import os
import sys
import logging
import urllib.request
import zipfile
import tarfile
import platform
from pathlib import Path
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoJavaInstaller:
    """
    Automatically downloads and installs Java 17 if not found.
    """

    def __init__(self):
        self.system = platform.system()
        self.machine = platform.machine()

        # PromptOps managed Java directory
        self.java_dir = Path.home() / ".promptops" / "java"
        self.java_dir.mkdir(parents=True, exist_ok=True)

        # Java 17 installation path
        self.java_17_dir = self.java_dir / "jdk-17"

    def get_download_url(self) -> Optional[str]:
        """
        Get download URL for Java 17 based on platform.

        Returns:
            Download URL or None
        """
        # Eclipse Adoptium (Temurin) Java 17 LTS
        base_url = "https://api.adoptium.net/v3/binary/latest/17/ga"

        if self.system == "Windows":
            if "AMD64" in self.machine or "x86_64" in self.machine:
                # Windows x64 zip (portable, no admin needed)
                return f"{base_url}/windows/x64/jdk/hotspot/normal/eclipse"
            else:
                logger.error(f"Unsupported Windows architecture: {self.machine}")
                return None

        elif self.system == "Linux":
            if "x86_64" in self.machine:
                return f"{base_url}/linux/x64/jdk/hotspot/normal/eclipse"
            elif "aarch64" in self.machine or "arm64" in self.machine:
                return f"{base_url}/linux/aarch64/jdk/hotspot/normal/eclipse"
            else:
                logger.error(f"Unsupported Linux architecture: {self.machine}")
                return None

        elif self.system == "Darwin":  # macOS
            if "arm64" in self.machine:
                return f"{base_url}/mac/aarch64/jdk/hotspot/normal/eclipse"
            else:
                return f"{base_url}/mac/x64/jdk/hotspot/normal/eclipse"

        logger.error(f"Unsupported operating system: {self.system}")
        return None

    def is_java_17_installed(self) -> bool:
        """
        Check if Java 17 is already installed by PromptOps.

        Returns:
            True if installed, False otherwise
        """
        java_exe = self.get_java_executable()
        return java_exe is not None and java_exe.exists()

    def get_java_executable(self) -> Optional[Path]:
        """
        Get path to Java 17 executable.

        Returns:
            Path to java executable or None
        """
        if self.system == "Windows":
            java_exe = self.java_17_dir / "bin" / "java.exe"
        else:
            java_exe = self.java_17_dir / "bin" / "java"

        if java_exe.exists():
            return java_exe

        return None

    def get_java_home(self) -> Optional[str]:
        """
        Get JAVA_HOME path for Java 17.

        Returns:
            JAVA_HOME path or None
        """
        if self.is_java_17_installed():
            return str(self.java_17_dir)
        return None

    def download_java_17(self) -> bool:
        """
        Download Java 17 portable package.

        Returns:
            True if successful, False otherwise
        """
        url = self.get_download_url()
        if not url:
            logger.error("Could not determine download URL")
            return False

        logger.info(f"Downloading Java 17 from Adoptium...")
        logger.info(f"URL: {url}")

        # Determine file extension
        if self.system == "Windows":
            download_file = self.java_dir / "jdk-17.zip"
        else:
            download_file = self.java_dir / "jdk-17.tar.gz"

        try:
            # Download with progress
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded / total_size) * 100)
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    print(f"\rDownloading: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

            urllib.request.urlretrieve(url, download_file, reporthook=report_progress)
            print()  # New line after progress

            logger.info(f"Downloaded to: {download_file}")
            logger.info(f"File size: {download_file.stat().st_size / (1024*1024):.1f} MB")

            return True

        except Exception as e:
            logger.error(f"Download failed: {e}")
            if download_file.exists():
                download_file.unlink()
            return False

    def extract_java_17(self) -> bool:
        """
        Extract downloaded Java 17 package.

        Returns:
            True if successful, False otherwise
        """
        if self.system == "Windows":
            archive_file = self.java_dir / "jdk-17.zip"
        else:
            archive_file = self.java_dir / "jdk-17.tar.gz"

        if not archive_file.exists():
            logger.error(f"Archive not found: {archive_file}")
            return False

        try:
            logger.info(f"Extracting Java 17...")

            # Remove old installation if exists
            if self.java_17_dir.exists():
                import shutil
                shutil.rmtree(self.java_17_dir)

            # Extract
            extract_dir = self.java_dir / "temp_extract"
            extract_dir.mkdir(exist_ok=True)

            if self.system == "Windows":
                with zipfile.ZipFile(archive_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                with tarfile.open(archive_file, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)

            # Find the actual JDK directory (usually jdk-17.x.x+y)
            extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                logger.error("No directory found in archive")
                return False

            jdk_dir = extracted_dirs[0]

            # Move to final location
            import shutil
            shutil.move(str(jdk_dir), str(self.java_17_dir))

            # Cleanup
            shutil.rmtree(extract_dir)
            archive_file.unlink()

            logger.info(f"Java 17 installed to: {self.java_17_dir}")

            # Set executable permissions on Unix
            if self.system != "Windows":
                bin_dir = self.java_17_dir / "bin"
                for exe_file in bin_dir.glob("*"):
                    if exe_file.is_file():
                        os.chmod(exe_file, 0o755)

            # Verify installation
            java_exe = self.get_java_executable()
            if java_exe and java_exe.exists():
                logger.info("Java 17 installation verified!")
                return True
            else:
                logger.error("Java executable not found after extraction")
                return False

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def install_java_17(self) -> Dict[str, any]:
        """
        Install Java 17 automatically.

        Returns:
            Installation result dict
        """
        # Check if already installed
        if self.is_java_17_installed():
            java_home = self.get_java_home()
            logger.info(f"Java 17 already installed at: {java_home}")
            return {
                "status": "success",
                "already_installed": True,
                "java_home": java_home,
                "java_executable": str(self.get_java_executable())
            }

        logger.info("Java 17 not found. Installing automatically...")
        logger.info(f"Installation directory: {self.java_17_dir}")

        # Download
        logger.info("[1/2] Downloading Java 17 (~180 MB)...")
        if not self.download_java_17():
            return {
                "status": "failed",
                "error": "Download failed",
                "suggestion": "Check internet connection or firewall settings"
            }

        # Extract
        logger.info("[2/2] Extracting Java 17...")
        if not self.extract_java_17():
            return {
                "status": "failed",
                "error": "Extraction failed",
                "suggestion": "Check disk space and permissions"
            }

        # Success
        java_home = self.get_java_home()
        java_exe = self.get_java_executable()

        logger.info("")
        logger.info("="*70)
        logger.info("  Java 17 Installation Complete!")
        logger.info("="*70)
        logger.info(f"JAVA_HOME: {java_home}")
        logger.info(f"Java Executable: {java_exe}")
        logger.info("="*70)

        return {
            "status": "success",
            "already_installed": False,
            "java_home": java_home,
            "java_executable": str(java_exe),
            "message": "Java 17 installed successfully"
        }


def install_java_17_if_needed() -> Optional[str]:
    """
    Convenience function to install Java 17 if needed.

    Returns:
        JAVA_HOME path or None if failed
    """
    installer = AutoJavaInstaller()
    result = installer.install_java_17()

    if result["status"] == "success":
        return result["java_home"]
    else:
        logger.error(f"Installation failed: {result.get('error')}")
        return None


# Example usage
if __name__ == "__main__":
    installer = AutoJavaInstaller()

    print("\n" + "="*70)
    print("  PromptOps - Automatic Java 17 Installer")
    print("="*70)
    print(f"\nSystem: {installer.system}")
    print(f"Architecture: {installer.machine}")
    print(f"Installation directory: {installer.java_17_dir}")
    print("\n" + "="*70 + "\n")

    result = installer.install_java_17()

    print("\n" + "="*70)
    if result["status"] == "success":
        print("  SUCCESS!")
        print("="*70)
        print(f"Java 17 installed at: {result['java_home']}")
        print(f"\nTo use this Java:")
        print(f"  export JAVA_HOME={result['java_home']}")
        print(f"  export PATH=$JAVA_HOME/bin:$PATH")
    else:
        print("  FAILED!")
        print("="*70)
        print(f"Error: {result.get('error')}")
        print(f"Suggestion: {result.get('suggestion', 'N/A')}")
    print("="*70 + "\n")
