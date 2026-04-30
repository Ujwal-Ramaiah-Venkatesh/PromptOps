"""
Secrets Management for PromptOps

Handles loading secrets from AWS Secrets Manager (production)
or local .env files (development)

Week 13-15: SECURITY-005
"""

import os
import json
from functools import lru_cache
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Raised when a secret cannot be found"""
    pass


class SecretsManager:
    """
    Unified secrets manager that works in both development and production

    Development: Reads from .env files
    Production: Reads from AWS Secrets Manager
    """

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.use_aws = self.environment in ["staging", "production"]

        if self.use_aws:
            try:
                import boto3
                self.sm_client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))
                logger.info(f"Secrets Manager initialized for {self.environment} with AWS")
            except ImportError:
                logger.warning("boto3 not installed. Falling back to environment variables.")
                self.use_aws = False
        else:
            logger.info(f"Secrets Manager initialized for {self.environment} with local .env")

    def get_secret(self, secret_name: str, default: Optional[str] = ...) -> Optional[str]:
        """
        Get a secret value

        Args:
            secret_name: Name of the secret (e.g., 'JWT_SECRET_KEY')
            default: Default value if secret not found (use ... for no default)

        Returns:
            Secret value as string, or None if default=None and not found

        Raises:
            SecretNotFoundError: If secret not found and no default provided
        """
        if self.use_aws:
            return self._get_from_aws(secret_name, default)
        else:
            return self._get_from_env(secret_name, default)

    @lru_cache(maxsize=16)
    def get_secret_dict(self, secret_path: str) -> Dict[str, Any]:
        """
        Get a secret as a dictionary (for complex secrets)

        Args:
            secret_path: AWS Secrets Manager path (e.g., 'promptops/production/database')

        Returns:
            Dictionary with secret values

        Raises:
            SecretNotFoundError: If secret not found
        """
        if not self.use_aws:
            raise SecretNotFoundError(
                f"Dictionary secrets only available in AWS. "
                f"Use individual environment variables in {self.environment}."
            )

        try:
            response = self.sm_client.get_secret_value(SecretId=secret_path)
            secret_string = response['SecretString']
            return json.loads(secret_string)
        except self.sm_client.exceptions.ResourceNotFoundException:
            raise SecretNotFoundError(f"Secret not found: {secret_path}")
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_path}: {e}")
            raise SecretNotFoundError(f"Failed to retrieve secret: {secret_path}") from e

    def _get_from_aws(self, secret_name: str, default: Optional[str] = ...) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            # Try to get as simple string secret first
            response = self.sm_client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except self.sm_client.exceptions.ResourceNotFoundException:
            if default is not ...:
                logger.warning(f"Secret {secret_name} not found in AWS, using default")
                return default
            raise SecretNotFoundError(f"Secret not found in AWS: {secret_name}")
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name} from AWS: {e}")
            if default is not ...:
                return default
            raise SecretNotFoundError(f"Failed to retrieve secret: {secret_name}") from e

    def _get_from_env(self, secret_name: str, default: Optional[str] = ...) -> Optional[str]:
        """Get secret from environment variables"""
        value = os.getenv(secret_name)
        if value is None:
            # If default was provided (even if None), return it
            if default is not ...:
                return default
            raise SecretNotFoundError(f"Environment variable not found: {secret_name}")
        return value

    def get_database_url(self) -> str:
        """
        Get database connection URL

        Development: Uses DATABASE_URL from .env
        Production: Constructs from AWS Secrets Manager

        Returns:
            PostgreSQL connection URL
        """
        if self.use_aws:
            db_secret = self.get_secret_dict('promptops/production/database')
            username = db_secret['username']
            password = db_secret['password']
            host = db_secret['host']
            port = db_secret.get('port', 5432)
            database = db_secret['database']
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        else:
            return self.get_secret('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/promptops')

    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        if self.use_aws:
            api_keys = self.get_secret_dict('promptops/production/api-keys')
            return api_keys['jwt_secret']
        else:
            return self.get_secret('JWT_SECRET_KEY', 'dev-secret-key-change-in-production-1234567890')

    def get_anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic (Claude) API key"""
        if self.use_aws:
            api_keys = self.get_secret_dict('promptops/production/api-keys')
            return api_keys.get('anthropic')
        else:
            return self.get_secret('CLAUDE_API_KEY', None)

    def get_cors_origins(self) -> list[str]:
        """Get allowed CORS origins"""
        origins_str = self.get_secret(
            'CORS_ORIGINS',
            'http://localhost:3000,http://localhost:3001,http://localhost:3003,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3003,http://127.0.0.1:5173'
        )
        return origins_str.split(',')


# Global secrets manager instance
_secrets_manager = None

def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(secret_name: str, default: Optional[str] = None) -> str:
    """
    Convenience function to get a secret

    Args:
        secret_name: Name of the secret
        default: Default value if not found

    Returns:
        Secret value
    """
    return get_secrets_manager().get_secret(secret_name, default)
