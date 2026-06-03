"""
Java Version Manager for PromptOps
===================================

Automatically detect and use the correct Java version for Android builds.
Supports multiple Java installations and auto-switching.

Features:
- Detect all installed Java versions
- Auto-select compatible version for project
- Support for Java 8, 11, 17, 21, 26+
- Environment variable management
- Docker fallback option

Author: DevOps Engineer
Date: 2026-05-11
"""

import os
import re
import subprocess
import platform
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JavaVersionManager:
    """
    Manages multiple Java versions and auto-selects compatible one.
    """

    def __init__(self):
        self.system = platform.system()
        self.detected_versions = {}
        self.current_version = None
        self._detect_java_installations()

    def _detect_java_installations(self) -> Dict[int, str]:
        """
        Detect all Java installations on the system.

        Returns:
            Dict mapping Java major version to installation path
        """
        logger.info("Detecting Java installations...")

        search_paths = self._get_search_paths()

        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue

            try:
                for item in os.listdir(search_path):
                    item_path = os.path.join(search_path, item)
                    if not os.path.isdir(item_path):
                        continue

                    # Check for Java installation
                    java_exe = self._get_java_executable(item_path)
                    if java_exe and os.path.exists(java_exe):
                        version = self._get_java_version(java_exe)
                        if version:
                            self.detected_versions[version] = item_path
                            logger.info(f"Found Java {version} at: {item_path}")
            except Exception as e:
                logger.warning(f"Error scanning {search_path}: {e}")

        # Also check current JAVA_HOME
        java_home = os.getenv("JAVA_HOME")
        if java_home:
            java_exe = self._get_java_executable(java_home)
            if java_exe and os.path.exists(java_exe):
                version = self._get_java_version(java_exe)
                if version and version not in self.detected_versions:
                    self.detected_versions[version] = java_home
                    logger.info(f"Found Java {version} at JAVA_HOME: {java_home}")

        # Check system PATH
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_output = result.stderr or result.stdout
                version = self._parse_version_string(version_output)
                if version:
                    self.current_version = version
                    logger.info(f"Current system Java: {version}")
        except Exception:
            pass

        return self.detected_versions

    def _get_search_paths(self) -> List[str]:
        """Get OS-specific Java installation search paths."""
        if self.system == "Windows":
            return [
                "C:\\Program Files\\Java",
                "C:\\Program Files\\Eclipse Adoptium",
                "C:\\Program Files\\AdoptOpenJDK",
                "C:\\Program Files\\Temurin",
                "C:\\Program Files\\Amazon Corretto",
                "C:\\Program Files\\Zulu",
                "C:\\Program Files (x86)\\Java"
            ]
        elif self.system == "Darwin":  # macOS
            return [
                "/Library/Java/JavaVirtualMachines",
                "/System/Library/Java/JavaVirtualMachines",
                os.path.expanduser("~/Library/Java/JavaVirtualMachines")
            ]
        else:  # Linux
            return [
                "/usr/lib/jvm",
                "/usr/java",
                "/opt/java",
                os.path.expanduser("~/.sdkman/candidates/java")
            ]

    def _get_java_executable(self, java_home: str) -> Optional[str]:
        """Get path to java executable."""
        if self.system == "Windows":
            return os.path.join(java_home, "bin", "java.exe")
        else:
            return os.path.join(java_home, "bin", "java")

    def _get_java_version(self, java_exe: str) -> Optional[int]:
        """Get Java major version from executable."""
        try:
            result = subprocess.run(
                [java_exe, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_output = result.stderr or result.stdout
            return self._parse_version_string(version_output)
        except Exception:
            return None

    def _parse_version_string(self, version_string: str) -> Optional[int]:
        """
        Parse Java version string to major version number.

        Examples:
            "java version \"1.8.0_481\"" -> 8
            "openjdk version \"11.0.12\"" -> 11
            "java version \"17.0.5\"" -> 17
            "java version \"26\"" -> 26
        """
        # Pattern: version "X.Y.Z" or version "X"
        match = re.search(r'version\s+"?(\d+)(?:\.(\d+))?', version_string)
        if match:
            major = int(match.group(1))
            minor = match.group(2)

            # Java 1.x versions (1.8 = Java 8, 1.7 = Java 7)
            if major == 1 and minor:
                return int(minor)
            else:
                return major
        return None

    def get_compatible_java(
        self,
        kotlin_version: Optional[str] = None,
        gradle_version: Optional[str] = None,
        min_version: int = 8,
        max_version: int = 21
    ) -> Optional[Tuple[int, str]]:
        """
        Get compatible Java version for the project.

        Args:
            kotlin_version: Kotlin version (e.g., "1.9.10")
            gradle_version: Gradle version (e.g., "8.3.0")
            min_version: Minimum Java version required
            max_version: Maximum Java version supported

        Returns:
            Tuple of (java_version, java_home_path) or None
        """
        # Adjust max version based on Kotlin version
        if kotlin_version:
            if kotlin_version.startswith("1.9"):
                max_version = min(max_version, 21)
            elif kotlin_version.startswith("1.8"):
                max_version = min(max_version, 19)
            elif kotlin_version.startswith("1.7"):
                max_version = min(max_version, 18)

        # Adjust for Gradle version
        if gradle_version:
            gradle_major = int(gradle_version.split('.')[0])
            if gradle_major >= 8:
                min_version = max(min_version, 17)
            elif gradle_major >= 7:
                min_version = max(min_version, 11)

        logger.info(f"Looking for Java version between {min_version} and {max_version}")

        # Find compatible versions
        compatible = []
        for version, path in self.detected_versions.items():
            if min_version <= version <= max_version:
                compatible.append((version, path))

        if not compatible:
            logger.warning(f"No compatible Java found (need {min_version}-{max_version})")

            # Auto-install Java 17 if needed
            if min_version <= 17 <= max_version:
                logger.info("Attempting to auto-install Java 17...")
                try:
                    from auto_java_installer import AutoJavaInstaller
                    installer = AutoJavaInstaller()
                    result = installer.install_java_17()

                    if result["status"] == "success":
                        java_home = result["java_home"]
                        logger.info(f"Java 17 auto-installed at: {java_home}")

                        # Add to detected versions
                        self.detected_versions[17] = java_home

                        # Return the newly installed Java 17
                        return (17, java_home)
                    else:
                        logger.error(f"Auto-installation failed: {result.get('error')}")
                except Exception as e:
                    logger.error(f"Auto-installation error: {e}")

            return None

        # Sort by version (prefer newer within range)
        compatible.sort(reverse=True)

        selected_version, selected_path = compatible[0]
        logger.info(f"Selected Java {selected_version} at: {selected_path}")

        return (selected_version, selected_path)

    def set_java_version(self, java_version: int) -> bool:
        """
        Set JAVA_HOME to use specific Java version.

        Args:
            java_version: Java major version to use

        Returns:
            True if successful, False otherwise
        """
        if java_version not in self.detected_versions:
            logger.error(f"Java {java_version} not found on system")
            return False

        java_home = self.detected_versions[java_version]
        java_exe = self._get_java_executable(java_home)

        if not os.path.exists(java_exe):
            logger.error(f"Java executable not found: {java_exe}")
            return False

        # Set environment variables for current process
        os.environ["JAVA_HOME"] = java_home

        # Update PATH
        bin_path = os.path.join(java_home, "bin")
        if bin_path not in os.environ["PATH"]:
            if self.system == "Windows":
                os.environ["PATH"] = f"{bin_path};{os.environ['PATH']}"
            else:
                os.environ["PATH"] = f"{bin_path}:{os.environ['PATH']}"

        logger.info(f"Set JAVA_HOME to Java {java_version}: {java_home}")
        return True

    def get_docker_fallback(
        self,
        java_version: int = 17
    ) -> Dict[str, str]:
        """
        Get Docker configuration for building with specific Java version.

        Args:
            java_version: Java version to use in Docker

        Returns:
            Docker configuration dict
        """
        image_map = {
            8: "eclipse-temurin:8-jdk",
            11: "eclipse-temurin:11-jdk",
            17: "eclipse-temurin:17-jdk",
            21: "eclipse-temurin:21-jdk"
        }

        image = image_map.get(java_version, "eclipse-temurin:17-jdk")

        return {
            "image": image,
            "command": "./gradlew assembleDebug",
            "description": f"Build with Java {java_version} in Docker"
        }

    def generate_build_report(self) -> Dict:
        """Generate comprehensive Java environment report."""
        return {
            "system": self.system,
            "current_java_version": self.current_version,
            "detected_versions": {
                str(v): p for v, p in self.detected_versions.items()
            },
            "java_home": os.getenv("JAVA_HOME"),
            "path": os.getenv("PATH"),
            "recommendations": self._get_recommendations()
        }

    def _get_recommendations(self) -> List[str]:
        """Get recommendations for Java setup."""
        recommendations = []

        if not self.detected_versions:
            recommendations.append("No Java installations detected. Install Java 17 LTS.")

        if self.current_version and self.current_version > 21:
            recommendations.append(
                f"Java {self.current_version} may be too new for some projects. "
                f"Consider installing Java 17 LTS."
            )

        if 17 not in self.detected_versions:
            recommendations.append(
                "Java 17 LTS not found. This is the recommended version for "
                "Android development."
            )

        if len(self.detected_versions) > 3:
            recommendations.append(
                f"Multiple Java versions detected ({len(self.detected_versions)}). "
                f"Consider using SDKMAN or jEnv for easier management."
            )

        return recommendations


# ============================================================================
# Utility Functions
# ============================================================================

def auto_select_java_for_build(
    project_path: str,
    kotlin_version: Optional[str] = None
) -> Optional[Tuple[int, str]]:
    """
    Auto-select compatible Java version for Android build.

    Args:
        project_path: Path to Android project
        kotlin_version: Optional Kotlin version override

    Returns:
        Tuple of (java_version, java_home) or None
    """
    manager = JavaVersionManager()

    # Try to detect Kotlin version from project
    if not kotlin_version:
        build_gradle = Path(project_path) / "build.gradle.kts"
        if not build_gradle.exists():
            build_gradle = Path(project_path) / "build.gradle"

        if build_gradle.exists():
            with open(build_gradle, 'r') as f:
                content = f.read()
                match = re.search(r'kotlin.*version\s+"([^"]+)"', content)
                if match:
                    kotlin_version = match.group(1)

    return manager.get_compatible_java(kotlin_version=kotlin_version)


def print_java_report():
    """Print comprehensive Java environment report."""
    manager = JavaVersionManager()
    report = manager.generate_build_report()

    print("\n" + "="*70)
    print("  Java Environment Report")
    print("="*70)
    print(f"\nSystem: {report['system']}")
    print(f"Current Java: {report['current_java_version']}")
    print(f"JAVA_HOME: {report['java_home']}")
    print(f"\nDetected Java Installations:")

    if report['detected_versions']:
        for version, path in sorted(report['detected_versions'].items()):
            print(f"  - Java {version}: {path}")
    else:
        print("  (none)")

    print(f"\nRecommendations:")
    if report['recommendations']:
        for rec in report['recommendations']:
            print(f"  - {rec}")
    else:
        print("  - Java environment is properly configured")

    print("="*70 + "\n")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "report":
        print_java_report()
    else:
        manager = JavaVersionManager()

        print("\nAvailable Java versions:")
        for version, path in sorted(manager.detected_versions.items()):
            print(f"  Java {version}: {path}")

        # Example: Get compatible Java for Kotlin 1.9.10
        result = manager.get_compatible_java(kotlin_version="1.9.10")
        if result:
            version, path = result
            print(f"\nRecommended for Kotlin 1.9.10: Java {version}")
            print(f"Path: {path}")
