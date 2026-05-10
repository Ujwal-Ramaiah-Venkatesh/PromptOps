"""
Terraform Generator for PromptOps
==================================

Generates Terraform modules for multi-cloud infrastructure.
Supports AWS, Azure, and GCP resources.

Author: DevOps Engineer - Phase 6 Week 60-61
Date: 2026-05-10
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class CloudProvider(Enum):
    """Cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ResourceType(Enum):
    """Infrastructure resource types."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    KUBERNETES = "kubernetes"


# ============================================================================
# Terraform Generator
# ============================================================================

class TerraformGenerator:
    """
    Terraform module generator.

    Features:
    - Multi-cloud resource generation
    - Module composition
    - Variable management
    - Output definitions
    - Backend configuration
    - Provider setup
    """

    def __init__(self):
        """Initialize Terraform Generator."""
        self.terraform_version = "~> 1.5"

    def generate_module(
        self,
        module_name: str,
        provider: str,
        resources: List[Dict[str, Any]],
        variables: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate Terraform module.

        Args:
            module_name: Module name
            provider: Cloud provider (aws, azure, gcp)
            resources: List of resources to create
            variables: Input variables
            outputs: Output values

        Returns:
            Terraform module files
        """
        logger.info(f"Generating Terraform module: {module_name}")

        module = {
            "module_name": module_name,
            "provider": provider,
            "files": {}
        }

        # Generate main.tf
        module["files"]["main.tf"] = self._generate_main_tf(resources, provider)

        # Generate variables.tf
        module["files"]["variables.tf"] = self._generate_variables_tf(variables or {})

        # Generate outputs.tf
        module["files"]["outputs.tf"] = self._generate_outputs_tf(outputs or {})

        # Generate versions.tf
        module["files"]["versions.tf"] = self._generate_versions_tf(provider)

        module["generated_at"] = datetime.utcnow().isoformat()

        return module

    def _generate_main_tf(self, resources: List[Dict[str, Any]], provider: str) -> str:
        """Generate main.tf content."""
        lines = []

        for resource in resources:
            resource_type = resource.get("type")
            resource_name = resource.get("name")
            config = resource.get("config", {})

            if provider == "aws":
                tf_resource = self._generate_aws_resource(resource_type, resource_name, config)
            elif provider == "azure":
                tf_resource = self._generate_azure_resource(resource_type, resource_name, config)
            elif provider == "gcp":
                tf_resource = self._generate_gcp_resource(resource_type, resource_name, config)
            else:
                continue

            lines.append(tf_resource)
            lines.append("")

        return "\n".join(lines)

    def _generate_aws_resource(self, resource_type: str, name: str, config: Dict[str, Any]) -> str:
        """Generate AWS resource block."""
        if resource_type == "ec2":
            return f"""resource "aws_instance" "{name}" {{
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {{
    Name        = "{name}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }}
}}"""
        elif resource_type == "s3":
            return f"""resource "aws_s3_bucket" "{name}" {{
  bucket = var.bucket_name

  tags = {{
    Name        = "{name}"
    Environment = var.environment
  }}
}}

resource "aws_s3_bucket_versioning" "{name}_versioning" {{
  bucket = aws_s3_bucket.{name}.id

  versioning_configuration {{
    status = "Enabled"
  }}
}}"""
        elif resource_type == "vpc":
            return f"""resource "aws_vpc" "{name}" {{
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name        = "{name}"
    Environment = var.environment
  }}
}}

resource "aws_subnet" "{name}_subnet" {{
  vpc_id            = aws_vpc.{name}.id
  cidr_block        = var.subnet_cidr
  availability_zone = var.availability_zone

  tags = {{
    Name = "{name}-subnet"
  }}
}}"""
        elif resource_type == "rds":
            return f"""resource "aws_db_instance" "{name}" {{
  identifier           = "{name}"
  engine              = "postgres"
  engine_version      = "15.3"
  instance_class      = var.db_instance_class
  allocated_storage   = var.db_storage_size
  storage_type        = "gp3"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  skip_final_snapshot = true

  tags = {{
    Name        = "{name}"
    Environment = var.environment
  }}
}}"""
        elif resource_type == "eks":
            return f"""resource "aws_eks_cluster" "{name}" {{
  name     = "{name}"
  role_arn = aws_iam_role.{name}_cluster_role.arn
  version  = var.kubernetes_version

  vpc_config {{
    subnet_ids = var.subnet_ids
  }}

  tags = {{
    Name        = "{name}"
    Environment = var.environment
  }}
}}

resource "aws_iam_role" "{name}_cluster_role" {{
  name = "{name}-cluster-role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "eks.amazonaws.com"
      }}
    }}]
  }})
}}

resource "aws_iam_role_policy_attachment" "{name}_cluster_policy" {{
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.{name}_cluster_role.name
}}"""

        return f'# Resource type {resource_type} not implemented'

    def _generate_azure_resource(self, resource_type: str, name: str, config: Dict[str, Any]) -> str:
        """Generate Azure resource block."""
        if resource_type == "vm":
            return f"""resource "azurerm_virtual_machine" "{name}" {{
  name                  = "{name}"
  location              = var.location
  resource_group_name   = var.resource_group_name
  network_interface_ids = [azurerm_network_interface.{name}_nic.id]
  vm_size              = var.vm_size

  storage_os_disk {{
    name              = "{name}-osdisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Premium_LRS"
  }}

  storage_image_reference {{
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }}

  os_profile {{
    computer_name  = "{name}"
    admin_username = var.admin_username
    admin_password = var.admin_password
  }}

  os_profile_linux_config {{
    disable_password_authentication = false
  }}

  tags = {{
    Environment = var.environment
  }}
}}"""
        elif resource_type == "storage":
            return f"""resource "azurerm_storage_account" "{name}" {{
  name                     = "{name}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {{
    Environment = var.environment
  }}
}}"""
        elif resource_type == "aks":
            return f"""resource "azurerm_kubernetes_cluster" "{name}" {{
  name                = "{name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = "{name}"

  default_node_pool {{
    name       = "default"
    node_count = var.node_count
    vm_size    = var.node_vm_size
  }}

  identity {{
    type = "SystemAssigned"
  }}

  tags = {{
    Environment = var.environment
  }}
}}"""

        return f'# Resource type {resource_type} not implemented'

    def _generate_gcp_resource(self, resource_type: str, name: str, config: Dict[str, Any]) -> str:
        """Generate GCP resource block."""
        if resource_type == "compute":
            return f"""resource "google_compute_instance" "{name}" {{
  name         = "{name}"
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {{
    initialize_params {{
      image = "debian-cloud/debian-11"
    }}
  }}

  network_interface {{
    network = "default"

    access_config {{
      // Ephemeral IP
    }}
  }}

  labels = {{
    environment = var.environment
  }}
}}"""
        elif resource_type == "storage":
            return f"""resource "google_storage_bucket" "{name}" {{
  name     = "{name}"
  location = var.region

  versioning {{
    enabled = true
  }}

  labels = {{
    environment = var.environment
  }}
}}"""
        elif resource_type == "gke":
            return f"""resource "google_container_cluster" "{name}" {{
  name     = "{name}"
  location = var.region

  initial_node_count = var.node_count

  node_config {{
    machine_type = var.machine_type

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }}
}}"""

        return f'# Resource type {resource_type} not implemented'

    def _generate_variables_tf(self, variables: Dict[str, Any]) -> str:
        """Generate variables.tf content."""
        lines = []

        # Default variables
        default_vars = {
            "environment": {"type": "string", "description": "Environment name"},
            "region": {"type": "string", "description": "Cloud region"},
            "tags": {"type": "map(string)", "description": "Resource tags", "default": {}}
        }

        all_vars = {**default_vars, **variables}

        for var_name, var_config in all_vars.items():
            var_block = f"""variable "{var_name}" {{
  description = "{var_config.get('description', '')}"
  type        = {var_config.get('type', 'string')}"""

            if 'default' in var_config:
                default_value = var_config['default']
                if isinstance(default_value, str):
                    var_block += f'\n  default     = "{default_value}"'
                else:
                    var_block += f'\n  default     = {json.dumps(default_value)}'

            var_block += "\n}"
            lines.append(var_block)
            lines.append("")

        return "\n".join(lines)

    def _generate_outputs_tf(self, outputs: Dict[str, Any]) -> str:
        """Generate outputs.tf content."""
        lines = []

        for output_name, output_config in outputs.items():
            output_block = f"""output "{output_name}" {{
  description = "{output_config.get('description', '')}"
  value       = {output_config.get('value', '')}"""

            if output_config.get('sensitive'):
                output_block += "\n  sensitive   = true"

            output_block += "\n}"
            lines.append(output_block)
            lines.append("")

        return "\n".join(lines)

    def _generate_versions_tf(self, provider: str) -> str:
        """Generate versions.tf content."""
        provider_versions = {
            "aws": "~> 5.0",
            "azure": "~> 3.0",
            "gcp": "~> 5.0"
        }

        provider_sources = {
            "aws": "hashicorp/aws",
            "azure": "hashicorp/azurerm",
            "gcp": "hashicorp/google"
        }

        return f"""terraform {{
  required_version = "{self.terraform_version}"

  required_providers {{
    {provider} = {{
      source  = "{provider_sources.get(provider, f'hashicorp/{provider}')}"
      version = "{provider_versions.get(provider, '~> 1.0')}"
    }}
  }}
}}"""

    def generate_backend_config(
        self,
        backend_type: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Generate backend configuration.

        Args:
            backend_type: Backend type (s3, azurerm, gcs, local)
            config: Backend configuration

        Returns:
            Backend configuration
        """
        logger.info(f"Generating {backend_type} backend configuration")

        if backend_type == "s3":
            return f"""terraform {{
  backend "s3" {{
    bucket         = "{config.get('bucket')}"
    key            = "{config.get('key', 'terraform.tfstate')}"
    region         = "{config.get('region', 'us-east-1')}"
    encrypt        = true
    dynamodb_table = "{config.get('dynamodb_table', 'terraform-locks')}"
  }}
}}"""
        elif backend_type == "azurerm":
            return f"""terraform {{
  backend "azurerm" {{
    resource_group_name  = "{config.get('resource_group_name')}"
    storage_account_name = "{config.get('storage_account_name')}"
    container_name       = "{config.get('container_name')}"
    key                  = "{config.get('key', 'terraform.tfstate')}"
  }}
}}"""
        elif backend_type == "gcs":
            return f"""terraform {{
  backend "gcs" {{
    bucket = "{config.get('bucket')}"
    prefix = "{config.get('prefix', 'terraform/state')}"
  }}
}}"""
        else:
            return """terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}"""

    def generate_provider_config(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate provider configuration.

        Args:
            provider: Cloud provider
            config: Provider configuration

        Returns:
            Provider configuration
        """
        config = config or {}

        if provider == "aws":
            return f"""provider "aws" {{
  region = var.region

  default_tags {{
    tags = {{
      ManagedBy = "Terraform"
      Project   = var.project_name
    }}
  }}
}}"""
        elif provider == "azure":
            return f"""provider "azurerm" {{
  features {{}}

  subscription_id = var.subscription_id
}}"""
        elif provider == "gcp":
            return f"""provider "google" {{
  project = var.project_id
  region  = var.region
}}"""

        return f'# Provider {provider} configuration not implemented'


# ============================================================================
# Testing
# ============================================================================

def test_terraform_generator():
    """Test Terraform Generator."""
    logger.info("Testing Terraform Generator...")

    generator = TerraformGenerator()

    # Test 1: Generate AWS module
    print("\n=== Test 1: AWS EC2 Module ===")
    aws_module = generator.generate_module(
        module_name="ec2-web-server",
        provider="aws",
        resources=[
            {"type": "ec2", "name": "web", "config": {}},
            {"type": "s3", "name": "data", "config": {}}
        ],
        variables={
            "ami_id": {"type": "string", "description": "AMI ID"},
            "instance_type": {"type": "string", "description": "Instance type", "default": "t3.micro"}
        },
        outputs={
            "instance_id": {"value": "aws_instance.web.id", "description": "EC2 instance ID"},
            "bucket_name": {"value": "aws_s3_bucket.data.bucket", "description": "S3 bucket name"}
        }
    )
    print(f"Module: {aws_module['module_name']}")
    print(f"Provider: {aws_module['provider']}")
    print(f"Files: {list(aws_module['files'].keys())}")
    print("\n--- main.tf (first 500 chars) ---")
    print(aws_module['files']['main.tf'][:500])

    # Test 2: Generate Azure module
    print("\n\n=== Test 2: Azure AKS Module ===")
    azure_module = generator.generate_module(
        module_name="aks-cluster",
        provider="azure",
        resources=[
            {"type": "aks", "name": "cluster", "config": {}}
        ]
    )
    print(f"Module: {azure_module['module_name']}")
    print(f"Provider: {azure_module['provider']}")

    # Test 3: Backend configuration
    print("\n\n=== Test 3: S3 Backend Configuration ===")
    backend = generator.generate_backend_config(
        backend_type="s3",
        config={
            "bucket": "my-terraform-state",
            "key": "prod/terraform.tfstate",
            "region": "us-east-1",
            "dynamodb_table": "terraform-locks"
        }
    )
    print(backend)


if __name__ == "__main__":
    test_terraform_generator()
