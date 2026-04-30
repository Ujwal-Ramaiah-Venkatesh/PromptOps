"""
AWS Lambda function for rotating PromptOps secrets

This function is called by AWS Secrets Manager to rotate database credentials
Week 13-15: SECURITY-005

Deploy this as a Lambda function with appropriate IAM permissions
"""

import boto3
import json
import logging
import os
import psycopg2

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for secret rotation

    Args:
        event: Event data from Secrets Manager
        context: Lambda context

    Steps:
        1. createSecret - Generate new credentials
        2. setSecret - Update database with new credentials
        3. testSecret - Verify new credentials work
        4. finishSecret - Mark rotation complete
    """
    service_client = boto3.client('secretsmanager')
    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    logger.info(f"Rotating secret {arn}, step: {step}")

    # Get current secret metadata
    metadata = service_client.describe_secret(SecretId=arn)
    if not metadata['RotationEnabled']:
        logger.error(f"Secret {arn} is not enabled for rotation")
        raise ValueError(f"Secret {arn} is not enabled for rotation")

    versions = metadata['VersionIdsToStages']
    if token not in versions:
        logger.error(f"Secret version {token} has no stage for rotation")
        raise ValueError(f"Secret version {token} has no stage for rotation")

    if "AWSCURRENT" in versions[token]:
        logger.info(f"Secret version {token} already set as AWSCURRENT")
        return

    elif "AWSPENDING" not in versions[token]:
        logger.error(f"Secret version {token} not set as AWSPENDING for rotation")
        raise ValueError(f"Secret version {token} not set as AWSPENDING for rotation")

    # Route to appropriate step function
    if step == "createSecret":
        create_secret(service_client, arn, token)

    elif step == "setSecret":
        set_secret(service_client, arn, token)

    elif step == "testSecret":
        test_secret(service_client, arn, token)

    elif step == "finishSecret":
        finish_secret(service_client, arn, token)

    else:
        raise ValueError(f"Invalid step parameter: {step}")


def create_secret(service_client, arn, token):
    """
    Generate new secret credentials

    Creates a new password and stores it as AWSPENDING version
    """
    logger.info("Creating new secret")

    # Get current secret
    current_dict = json.loads(
        service_client.get_secret_value(SecretId=arn, VersionStage="AWSCURRENT")['SecretString']
    )

    # Generate new password (exclude special chars that might cause issues)
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(32))

    # Create new secret with same structure but new password
    new_dict = current_dict.copy()
    new_dict['password'] = new_password

    # Put new secret
    service_client.put_secret_value(
        SecretId=arn,
        ClientRequestToken=token,
        SecretString=json.dumps(new_dict),
        VersionStages=['AWSPENDING']
    )

    logger.info(f"Created new secret version {token}")


def set_secret(service_client, arn, token):
    """
    Update database with new credentials

    Connects with current credentials and creates new user or updates password
    """
    logger.info("Setting new secret in database")

    # Get both current and pending secrets
    current_dict = json.loads(
        service_client.get_secret_value(SecretId=arn, VersionStage="AWSCURRENT")['SecretString']
    )
    pending_dict = json.loads(
        service_client.get_secret_value(SecretId=arn, VersionStage="AWSPENDING", VersionId=token)['SecretString']
    )

    # Connect with current (superuser) credentials
    conn = psycopg2.connect(
        host=current_dict['host'],
        port=int(current_dict['port']),
        database=current_dict['database'],
        user=current_dict['username'],
        password=current_dict['password']
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cursor:
            # Update password for existing user
            username = pending_dict['username']
            new_password = pending_dict['password']

            # SQL to update password (escaping handled by parameterization)
            cursor.execute(
                f"ALTER USER {username} WITH PASSWORD %s",
                (new_password,)
            )

            logger.info(f"Updated password for user {username}")

    finally:
        conn.close()


def test_secret(service_client, arn, token):
    """
    Verify new credentials work

    Attempts to connect with pending credentials
    """
    logger.info("Testing new secret")

    # Get pending secret
    pending_dict = json.loads(
        service_client.get_secret_value(SecretId=arn, VersionStage="AWSPENDING", VersionId=token)['SecretString']
    )

    # Try to connect with new credentials
    try:
        conn = psycopg2.connect(
            host=pending_dict['host'],
            port=int(pending_dict['port']),
            database=pending_dict['database'],
            user=pending_dict['username'],
            password=pending_dict['password']
        )
        conn.close()
        logger.info("Successfully connected with new credentials")

    except Exception as e:
        logger.error(f"Failed to connect with new credentials: {e}")
        raise


def finish_secret(service_client, arn, token):
    """
    Finalize rotation

    Moves AWSCURRENT label to new secret version
    """
    logger.info("Finishing secret rotation")

    # Get current version
    metadata = service_client.describe_secret(SecretId=arn)
    current_version = None
    for version, stages in metadata['VersionIdsToStages'].items():
        if "AWSCURRENT" in stages:
            current_version = version
            break

    # Move labels
    service_client.update_secret_version_stage(
        SecretId=arn,
        VersionStage="AWSCURRENT",
        MoveToVersionId=token,
        RemoveFromVersionId=current_version
    )

    logger.info(f"Rotation complete. New version {token} is now AWSCURRENT")
