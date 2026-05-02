# HashiCorp Vault Setup Guide

**Date:** 2026-04-30  
**Phase:** 2 - Secret Rotation (ENH-005)  
**Cost:** $0 (open-source, local Docker)

---

## 🎯 Overview

This guide sets up HashiCorp Vault for secret management and rotation in PromptOps Phase 2 (ENH-005).

**Benefits:**
- ✅ **FREE** - Open-source version
- ✅ Secure secret storage
- ✅ Automated secret rotation
- ✅ Audit logging
- ✅ Dynamic secrets

---

## 🚀 Quick Start with Docker

### **Option 1: Docker Compose (Recommended)**

```bash
# Start Vault with PostgreSQL
docker compose -f docker-compose-phase2.yml up -d vault

# Check status
docker compose -f docker-compose-phase2.yml ps vault

# View logs
docker compose -f docker-compose-phase2.yml logs -f vault
```

**Vault is now running at:** http://localhost:8200

**Dev Root Token:** `promptops-dev-token`

### **Option 2: Standalone Docker**

```bash
# Run Vault in dev mode
docker run -d \
  --name vault-dev \
  --cap-add=IPC_LOCK \
  -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=promptops-dev-token' \
  -e 'VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200' \
  vault:1.15

# Check status
docker logs vault-dev
```

---

## 🔧 Vault Configuration

### **1. Set Environment Variables**

```bash
# In .env file
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=promptops-dev-token
```

Or export directly:

```bash
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='promptops-dev-token'
```

### **2. Verify Vault is Running**

```bash
# Install Vault CLI (optional)
# Windows: choco install vault
# Mac: brew install vault
# Linux: wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip

# Check status
vault status

# Expected output:
# Key             Value
# ---             -----
# Seal Type       shamir
# Initialized     true
# Sealed          false
# ...
```

---

## 📦 Secret Paths Structure

PromptOps uses this secret organization:

```
promptops/
├── aws/
│   ├── access_key_id
│   ├── secret_access_key
│   └── session_token
├── database/
│   ├── postgres_password
│   ├── postgres_admin_password
│   └── connection_string
├── api_keys/
│   ├── github_token
│   ├── slack_webhook
│   └── pagerduty_key
└── certificates/
    ├── ssl_cert
    ├── ssl_key
    └── ca_bundle
```

---

## 🔑 Creating Secrets

### **Using Vault CLI:**

```bash
# AWS credentials
vault kv put promptops/aws \
  access_key_id="AKIA..." \
  secret_access_key="..." \
  region="us-east-1"

# Database password
vault kv put promptops/database \
  postgres_password="secure_password_here" \
  host="localhost" \
  port="5432"

# API keys
vault kv put promptops/api_keys \
  github_token="ghp_..." \
  slack_webhook="https://hooks.slack.com/..."

# SSL certificates
vault kv put promptops/certificates \
  ssl_cert=@/path/to/cert.pem \
  ssl_key=@/path/to/key.pem
```

### **Using HTTP API:**

```bash
# Create secret
curl -X POST \
  -H "X-Vault-Token: promptops-dev-token" \
  -d '{"data": {"username": "admin", "password": "secret123"}}' \
  http://localhost:8200/v1/promptops/data/test-secret

# Read secret
curl -H "X-Vault-Token: promptops-dev-token" \
  http://localhost:8200/v1/promptops/data/test-secret
```

### **Using Python (PromptOps):**

```python
import hvac

# Initialize Vault client
client = hvac.Client(
    url='http://localhost:8200',
    token='promptops-dev-token'
)

# Write secret
client.secrets.kv.v2.create_or_update_secret(
    path='aws',
    secret=dict(
        access_key_id='AKIA...',
        secret_access_key='...'
    )
)

# Read secret
secret = client.secrets.kv.v2.read_secret_version(path='aws')
print(secret['data']['data'])  # {'access_key_id': 'AKIA...', ...}
```

---

## 🔄 Secret Rotation Configuration

### **Rotation Policy Example:**

```bash
# Enable database secrets engine
vault secrets enable database

# Configure PostgreSQL connection
vault write database/config/postgresql \
  plugin_name=postgresql-database-plugin \
  allowed_roles="promptops-role" \
  connection_url="postgresql://{{username}}:{{password}}@localhost:5432/promptops?sslmode=disable" \
  username="vault" \
  password="vault-password"

# Create role for dynamic credentials
vault write database/roles/promptops-role \
  db_name=postgresql \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

# Generate dynamic credentials
vault read database/creds/promptops-role
```

---

## 🔐 Security Best Practices

### **1. Production Setup (Not Dev Mode)**

```bash
# Initialize Vault (production)
vault operator init

# Save unseal keys and root token securely!

# Unseal Vault (requires 3 of 5 keys by default)
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>

# Verify
vault status
```

### **2. Enable Audit Logging**

```bash
# File audit backend
vault audit enable file file_path=/vault/logs/audit.log

# Syslog audit backend
vault audit enable syslog

# View audit logs
docker exec vault-dev cat /vault/logs/audit.log | tail -20
```

### **3. Create Policy for PromptOps**

```bash
# Create policy file: promptops-policy.hcl
cat > promptops-policy.hcl <<EOF
# Read and list secrets
path "promptops/*" {
  capabilities = ["read", "list"]
}

# Allow secret rotation
path "promptops/rotate/*" {
  capabilities = ["create", "update"]
}

# Allow creating new secrets
path "promptops/data/*" {
  capabilities = ["create", "update", "read", "delete"]
}
EOF

# Apply policy
vault policy write promptops promptops-policy.hcl

# Create token with policy
vault token create -policy=promptops
```

### **4. Enable TLS (Production)**

```bash
# Generate certificates
openssl req -x509 -newkey rsa:4096 -keyout vault-key.pem -out vault-cert.pem -days 365 -nodes

# Configure Vault with TLS
vault server -config=vault-config.hcl

# vault-config.hcl:
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_cert_file = "/vault/config/vault-cert.pem"
  tls_key_file  = "/vault/config/vault-key.pem"
}
```

---

## 📊 Vault Management Commands

### **Secret Operations:**

```bash
# List secrets
vault kv list promptops/

# Read secret
vault kv get promptops/aws

# Delete secret
vault kv delete promptops/test-secret

# Undelete secret
vault kv undelete -versions=2 promptops/test-secret

# Destroy secret permanently
vault kv destroy -versions=2 promptops/test-secret

# View secret metadata
vault kv metadata get promptops/aws
```

### **Token Operations:**

```bash
# Create token
vault token create -ttl=1h

# Revoke token
vault token revoke <token>

# Renew token
vault token renew <token>

# Lookup token info
vault token lookup <token>
```

### **Seal/Unseal Operations:**

```bash
# Seal Vault (locks all access)
vault operator seal

# Unseal Vault
vault operator unseal <key>

# Check seal status
vault status
```

---

## 🧪 Testing Vault Integration

### **Python Test Script:**

```python
# test_vault.py
import hvac
import os

def test_vault_connection():
    """Test Vault connection."""
    client = hvac.Client(
        url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
        token=os.getenv('VAULT_TOKEN', 'promptops-dev-token')
    )

    # Check if authenticated
    assert client.is_authenticated(), "Vault authentication failed"
    print("✅ Vault connection successful")

    # Write test secret
    client.secrets.kv.v2.create_or_update_secret(
        path='test',
        secret={'password': 'test123', 'username': 'testuser'}
    )
    print("✅ Secret written successfully")

    # Read test secret
    secret = client.secrets.kv.v2.read_secret_version(path='test')
    assert secret['data']['data']['password'] == 'test123'
    print("✅ Secret read successfully")

    # Delete test secret
    client.secrets.kv.v2.delete_metadata_and_all_versions(path='test')
    print("✅ Secret deleted successfully")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_vault_connection()
```

**Run test:**

```bash
pip install hvac
python test_vault.py
```

---

## 🐛 Troubleshooting

### **Issue: "connection refused"**

```bash
# Check if Vault is running
docker ps | grep vault

# Check logs
docker logs vault-dev

# Restart Vault
docker restart vault-dev
```

### **Issue: "permission denied"**

```bash
# Check token
echo $VAULT_TOKEN

# Verify token is valid
vault token lookup

# Check policy
vault token capabilities promptops/aws
```

### **Issue: "sealed vault"**

```bash
# Check seal status
vault status

# Unseal (requires unseal keys)
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>
```

---

## ✅ Setup Checklist

- [ ] Vault Docker container running
- [ ] Environment variables set (VAULT_ADDR, VAULT_TOKEN)
- [ ] Vault CLI installed (optional)
- [ ] Test secret created and read successfully
- [ ] Audit logging enabled
- [ ] Policies configured
- [ ] Backup unseal keys (production only)

---

## 📚 Resources

- **Vault Docs:** https://www.vaultproject.io/docs
- **hvac (Python Client):** https://hvac.readthedocs.io/
- **Vault API:** https://www.vaultproject.io/api-docs
- **Docker Image:** https://hub.docker.com/_/vault

---

**Next Steps:**
1. ✅ Start Vault with Docker Compose
2. → Create secret paths for PromptOps
3. → Implement secret rotation in Phase 2
4. → Build Secret Rotation UI (ENH-005)

---

**Status:** 📝 Ready for implementation
