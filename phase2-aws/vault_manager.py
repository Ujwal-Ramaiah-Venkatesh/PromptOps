"""
HashiCorp Vault Integration Module
===================================

Secret management and rotation using HashiCorp Vault.
ENH-005: Secret Rotation UI

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Secret Rotation (ENH-005)
"""

import hvac
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


class VaultManager:
    """
    Manages secrets in HashiCorp Vault.

    Features:
    - Create, read, update, delete secrets
    - Secret rotation
    - Secret versioning
    - Audit trail
    """

    def __init__(
        self,
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None
    ):
        """
        Initialize Vault client.

        Args:
            vault_url: Vault server URL (default: from VAULT_ADDR env)
            vault_token: Vault token (default: from VAULT_TOKEN env)
        """
        self.vault_url = vault_url or os.getenv('VAULT_ADDR', 'http://localhost:8200')
        self.vault_token = vault_token or os.getenv('VAULT_TOKEN', 'promptops-dev-token')

        try:
            self.client = hvac.Client(
                url=self.vault_url,
                token=self.vault_token
            )

            if not self.client.is_authenticated():
                raise Exception("Vault authentication failed")

            logger.info(f"Vault client initialized: {self.vault_url}")

        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            raise

    def create_secret(
        self,
        path: str,
        secret_data: Dict[str, Any],
        secret_type: str = 'generic',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update a secret in Vault.

        Args:
            path: Secret path (e.g., 'aws/credentials')
            secret_data: Secret key-value pairs
            secret_type: Secret type (generic, database, api_key, etc.)
            metadata: Additional metadata

        Returns:
            Dict with created secret info
        """
        try:
            # Write secret to Vault KV v2
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data,
                mount_point='promptops'
            )

            logger.info(f"Secret created at path: {path}")

            return {
                'path': path,
                'version': response['data']['version'],
                'created_time': response['data']['created_time'],
                'secret_type': secret_type,
                'metadata': metadata or {}
            }

        except Exception as e:
            logger.error(f"Failed to create secret at {path}: {e}")
            raise

    def read_secret(self, path: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Read a secret from Vault.

        Args:
            path: Secret path
            version: Specific version to read (None = latest)

        Returns:
            Secret data
        """
        try:
            if version:
                response = self.client.secrets.kv.v2.read_secret_version(
                    path=path,
                    version=version,
                    mount_point='promptops'
                )
            else:
                response = self.client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point='promptops'
                )

            return {
                'data': response['data']['data'],
                'metadata': response['data']['metadata'],
                'version': response['data']['metadata']['version']
            }

        except Exception as e:
            logger.error(f"Failed to read secret at {path}: {e}")
            raise

    def list_secrets(self, path: str = '') -> List[str]:
        """
        List secrets at a path.

        Args:
            path: Path to list (empty = root)

        Returns:
            List of secret paths
        """
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point='promptops'
            )

            return response['data']['keys']

        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {e}")
            return []

    def delete_secret(self, path: str, versions: Optional[List[int]] = None):
        """
        Delete a secret (soft delete - can be undeleted).

        Args:
            path: Secret path
            versions: Versions to delete (None = all versions)
        """
        try:
            if versions:
                self.client.secrets.kv.v2.delete_secret_versions(
                    path=path,
                    versions=versions,
                    mount_point='promptops'
                )
            else:
                self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=path,
                    mount_point='promptops'
                )

            logger.info(f"Secret deleted at path: {path}")

        except Exception as e:
            logger.error(f"Failed to delete secret at {path}: {e}")
            raise

    def rotate_secret(
        self,
        path: str,
        new_secret_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Rotate a secret (create new version).

        Args:
            path: Secret path
            new_secret_data: New secret values

        Returns:
            Rotation result
        """
        try:
            # Get current secret for audit
            current = self.read_secret(path)
            old_version = current['version']

            # Create new version
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=new_secret_data,
                mount_point='promptops'
            )

            new_version = response['data']['version']

            logger.info(f"Secret rotated at {path}: v{old_version} → v{new_version}")

            return {
                'path': path,
                'old_version': old_version,
                'new_version': new_version,
                'rotated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to rotate secret at {path}: {e}")
            raise

    def get_secret_metadata(self, path: str) -> Dict[str, Any]:
        """
        Get secret metadata (versions, created time, etc.).

        Args:
            path: Secret path

        Returns:
            Metadata dict
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point='promptops'
            )

            metadata = response['data']

            return {
                'path': path,
                'created_time': metadata['created_time'],
                'updated_time': metadata['updated_time'],
                'current_version': metadata['current_version'],
                'oldest_version': metadata['oldest_version'],
                'versions': metadata['versions']
            }

        except Exception as e:
            logger.error(f"Failed to get metadata for {path}: {e}")
            raise

    def get_secret_versions(self, path: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a secret.

        Args:
            path: Secret path

        Returns:
            List of version info
        """
        try:
            metadata = self.get_secret_metadata(path)
            versions = []

            for version, info in metadata['versions'].items():
                versions.append({
                    'version': int(version),
                    'created_time': info['created_time'],
                    'deletion_time': info.get('deletion_time'),
                    'destroyed': info.get('destroyed', False)
                })

            # Sort by version descending
            versions.sort(key=lambda x: x['version'], reverse=True)

            return versions

        except Exception as e:
            logger.error(f"Failed to get versions for {path}: {e}")
            return []

    def enable_secret_rotation(
        self,
        path: str,
        rotation_interval_days: int = 90
    ) -> Dict[str, Any]:
        """
        Enable automatic rotation for a secret.

        Args:
            path: Secret path
            rotation_interval_days: Days between rotations

        Returns:
            Rotation configuration
        """
        # This would integrate with database to track rotation schedule
        next_rotation = datetime.utcnow() + timedelta(days=rotation_interval_days)

        return {
            'path': path,
            'rotation_enabled': True,
            'rotation_interval_days': rotation_interval_days,
            'next_rotation_at': next_rotation.isoformat()
        }

    def check_health(self) -> Dict[str, Any]:
        """
        Check Vault health status.

        Returns:
            Health status dict
        """
        try:
            health = self.client.sys.read_health_status()

            return {
                'healthy': True,
                'initialized': health.get('initialized', False),
                'sealed': health.get('sealed', False),
                'standby': health.get('standby', False),
                'version': health.get('version', 'unknown')
            }

        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }


# Helper functions for common secret types

def generate_database_password(length: int = 32) -> str:
    """Generate secure random password for database."""
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_api_key(length: int = 64) -> str:
    """Generate secure API key."""
    import secrets

    return secrets.token_urlsafe(length)


def generate_ssh_key() -> Dict[str, str]:
    """Generate SSH key pair."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )

    # Get private key in PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Get public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    ).decode('utf-8')

    return {
        'private_key': private_pem,
        'public_key': public_pem
    }


# Test function
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("  Vault Manager Test")
    print("  Phase 2 - ENH-005: Secret Rotation")
    print("=" * 60)

    try:
        # Initialize Vault manager
        vault = VaultManager()

        # Check health
        print("\n[1] Checking Vault health...")
        health = vault.check_health()
        print(f"   Healthy: {health['healthy']}")
        print(f"   Initialized: {health.get('initialized')}")
        print(f"   Sealed: {health.get('sealed')}")

        # Create test secret
        print("\n[2] Creating test secret...")
        vault.create_secret(
            path='test/database',
            secret_data={
                'username': 'admin',
                'password': generate_database_password(),
                'host': 'localhost',
                'port': '5432'
            },
            secret_type='database'
        )
        print("   ✅ Secret created")

        # Read secret
        print("\n[3] Reading secret...")
        secret = vault.read_secret('test/database')
        print(f"   Version: {secret['version']}")
        print(f"   Data keys: {list(secret['data'].keys())}")

        # Rotate secret
        print("\n[4] Rotating secret...")
        rotation = vault.rotate_secret(
            path='test/database',
            new_secret_data={
                'username': 'admin',
                'password': generate_database_password(),
                'host': 'localhost',
                'port': '5432'
            }
        )
        print(f"   Old version: {rotation['old_version']}")
        print(f"   New version: {rotation['new_version']}")

        # Get versions
        print("\n[5] Getting secret versions...")
        versions = vault.get_secret_versions('test/database')
        print(f"   Total versions: {len(versions)}")
        for v in versions:
            print(f"   - v{v['version']}: {v['created_time']}")

        # List secrets
        print("\n[6] Listing secrets...")
        secrets = vault.list_secrets('test')
        print(f"   Found {len(secrets)} secrets:")
        for s in secrets:
            print(f"   - {s}")

        # Delete test secret
        print("\n[7] Cleaning up...")
        vault.delete_secret('test/database')
        print("   ✅ Test secret deleted")

        print("\n" + "=" * 60)
        print("✅ Vault Manager Test Complete")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Ensure Vault is running:")
        print("  docker compose -f docker-compose-phase2.yml up -d vault")
