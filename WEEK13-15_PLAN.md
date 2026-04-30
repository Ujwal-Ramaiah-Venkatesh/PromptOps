# Week 13-15: Security Fixes & Staging Deployment

**Timeline:** May 1 – May 19, 2026 (15 working days)  
**Status:** 🚀 READY TO START  
**Owner:** PromptOps Team  
**Prerequisites:** Week 11-12 Complete ✅

---

## Executive Summary

Address critical security issues identified in the security audit and deploy the production-ready system to staging environment. This phase focuses on authentication, authorization, secrets management, and production deployment.

**Current Status**: Week 11-12 Complete - System is **staging-ready** but requires security fixes before production.

---

## Critical Security Issues from Audit

From SECURITY_AUDIT.md:

**🔴 Critical (Blocking Production)**:
1. No authentication/authorization (A07)
2. CORS misconfigured - allows all origins (A05)
3. No access control - anyone can deploy (A01)

**🟡 High Priority**:
4. Secrets in plaintext .env files (A02)
5. No rate limiting (A05)
6. Security logging gaps (A09)

**Total Effort**: 60-80 hours

---

## Goals

1. **Security Fixes Phase 1** - Authentication & Authorization (Week 13)
2. **Security Fixes Phase 2** - Secrets & Infrastructure (Week 14)
3. **Staging Deployment** - Deploy and validate (Week 15)
4. **User Acceptance Testing** - PM team validation
5. **Production Readiness Review** - Final checklist

---

## Task Breakdown

### SECURITY-001: Authentication System ⏱️ Week 13, Day 1-3

**Goal:** Implement JWT-based authentication for all API endpoints.

**Current State**: No authentication - users self-identify via email in request body.

**Target State**: JWT tokens with secure login/logout flow.

**Implementation:**

#### 1. Install Dependencies
```bash
pip install python-jose[cryptography] passlib bcrypt python-multipart
```

#### 2. Create Auth Module (`api_gateway/auth/`)

**File: `auth/models.py`**
```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from database.models import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="pm")  # pm, engineer, lead, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
```

**File: `auth/jwt.py`**
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**File: `auth/dependencies.py`**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.db import get_db
from auth.jwt import decode_token
from auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

#### 3. Add Auth Endpoints to API Gateway

**Update `api_gateway/main.py`:**
```python
from fastapi.security import OAuth2PasswordRequestForm
from auth.jwt import create_access_token, get_password_hash, verify_password
from auth.models import User
from auth.dependencies import get_current_user, get_current_active_user

@app.post("/api/v1/auth/register")
async def register(
    email: str,
    password: str,
    full_name: str,
    db: Session = Depends(get_db)
):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role="pm"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User created successfully", "email": user.email}

@app.post("/api/v1/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@app.get("/api/v1/auth/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }
```

#### 4. Protect All Endpoints

**Update existing endpoints:**
```python
@app.post("/api/v1/parse-intent")
async def parse_intent(
    request: ParseIntentRequest,
    current_user: User = Depends(get_current_active_user)  # ADD THIS
):
    # Now we know who the user is from the token!
    # Use current_user.email instead of request.user
    pass

@app.post("/api/v1/execute")
async def execute_task(
    request: ExecuteRequest,
    current_user: User = Depends(get_current_active_user)  # ADD THIS
):
    # Verify user has permission for target environment
    if request.target_env == "production" and current_user.role not in ["lead", "admin"]:
        raise HTTPException(403, "Production access requires lead or admin role")
    pass
```

**Success Criteria:**
- ✅ User registration working
- ✅ Login returns JWT token
- ✅ All endpoints require authentication
- ✅ Token validation working
- ✅ 401 errors for invalid tokens

**Effort:** 16 hours

---

### SECURITY-002: Role-Based Access Control (RBAC) ⏱️ Week 13, Day 3-4

**Goal:** Implement environment-based permissions.

**Roles:**
- `viewer`: Read-only (audit, drift)
- `pm`: Deploy to staging, scale
- `engineer`: Deploy to staging/production (with approval)
- `lead`: All operations, user management
- `admin`: System administration

**Implementation:**

```python
# auth/permissions.py
from functools import wraps
from fastapi import HTTPException
from auth.models import User

def require_role(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires one of: {', '.join(allowed_roles)}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_environment_access(environment: str, user: User) -> bool:
    """Check if user can access environment"""
    if environment == "production":
        return user.role in ["engineer", "lead", "admin"]
    elif environment == "staging":
        return user.role in ["pm", "engineer", "lead", "admin"]
    return user.role in ["viewer", "pm", "engineer", "lead", "admin"]

# Usage
@app.post("/api/v1/execute")
async def execute_task(
    request: ExecuteRequest,
    current_user: User = Depends(get_current_active_user)
):
    # Check environment access
    if not require_environment_access(request.target_env, current_user):
        raise HTTPException(
            403,
            f"User role '{current_user.role}' cannot access '{request.target_env}' environment"
        )
    # ... rest of execution
```

**Success Criteria:**
- ✅ Role-based endpoint access
- ✅ Environment-based permissions
- ✅ Production requires elevated role
- ✅ 403 errors for unauthorized access

**Effort:** 12 hours

---

### SECURITY-003: Fix CORS Configuration ⏱️ Week 13, Day 4

**Goal:** Restrict CORS to specific domains.

**Current:** `allow_origins=["*"]` - allows all domains (insecure!)

**Update `api_gateway/main.py`:**
```python
import os

# Get allowed origins from environment
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # FIXED: Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods
    allow_headers=["Authorization", "Content-Type"],  # Specific headers
)
```

**`.env` files:**
```bash
# .env.development
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# .env.production
CORS_ORIGINS=https://dashboard.promptops.com,https://promptops.com
```

**Success Criteria:**
- ✅ CORS restricted to specific domains
- ✅ Development allows localhost
- ✅ Production allows only production domain
- ✅ Unauthorized origins rejected

**Effort:** 2 hours

---

### SECURITY-004: Rate Limiting ⏱️ Week 13, Day 5

**Goal:** Prevent abuse with rate limiting.

**Install:**
```bash
pip install slowapi
```

**Implementation:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/parse-intent")
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def parse_intent(
    request: Request,
    data: ParseIntentRequest,
    current_user: User = Depends(get_current_active_user)
):
    pass

@app.post("/api/v1/execute")
@limiter.limit("10/minute")  # More restrictive for expensive operations
async def execute_task(
    request: Request,
    data: ExecuteRequest,
    current_user: User = Depends(get_current_active_user)
):
    pass
```

**Success Criteria:**
- ✅ Rate limits per endpoint
- ✅ 429 error when exceeded
- ✅ Different limits for different endpoints
- ✅ Per-IP and per-user limits

**Effort:** 4 hours

---

### SECURITY-005: Secrets Management ⏱️ Week 14, Day 1-2

**Goal:** Move secrets to AWS Secrets Manager.

**Current:** Secrets in `.env` files (insecure!)

**Implementation:**

```python
# utils/secrets.py
import boto3
import json
from functools import lru_cache

@lru_cache()
def get_secret(secret_name: str) -> dict:
    """Get secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        raise

# Usage in main.py
from utils.secrets import get_secret

# Get database credentials
db_secret = get_secret('promptops/production/database')
DATABASE_URL = f"postgresql://{db_secret['username']}:{db_secret['password']}@{db_secret['host']}:{db_secret['port']}/{db_secret['database']}"

# Get API keys
api_keys = get_secret('promptops/production/api-keys')
ANTHROPIC_API_KEY = api_keys['anthropic']
JWT_SECRET_KEY = api_keys['jwt_secret']
```

**Store secrets in AWS:**
```bash
aws secretsmanager create-secret \
  --name promptops/production/database \
  --secret-string '{"username":"promptops","password":"SECURE_PASSWORD","host":"db.promptops.com","port":"5432","database":"promptops"}'

aws secretsmanager create-secret \
  --name promptops/production/api-keys \
  --secret-string '{"anthropic":"sk-ant-xxxxx","jwt_secret":"RANDOM_256_BIT_KEY"}'
```

**Success Criteria:**
- ✅ No secrets in code or .env files
- ✅ Secrets loaded from AWS Secrets Manager
- ✅ Automatic rotation configured
- ✅ Development uses local .env, production uses Secrets Manager

**Effort:** 8 hours

---

### SECURITY-006: Security Logging ⏱️ Week 14, Day 2-3

**Goal:** Log all security events.

**Implementation:**

```python
# utils/security_logger.py
import logging
from datetime import datetime

security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Log to file
handler = logging.FileHandler('logs/security.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(handler)

def log_login_attempt(email: str, success: bool, ip: str):
    security_logger.info(f"Login attempt: {email} from {ip} - {'SUCCESS' if success else 'FAILED'}")

def log_failed_approval(user: str, operation_id: str, attempted_phrase: str):
    security_logger.warning(f"Failed approval: {user} tried '{attempted_phrase}' for {operation_id}")

def log_production_deployment(user: str, service: str, version: str):
    security_logger.info(f"Production deployment: {user} deployed {service} {version}")

# Use in endpoints
@app.post("/api/v1/auth/login")
async def login(form_data: OAuth2PasswordRequestForm, request: Request):
    user = authenticate_user(form_data.username, form_data.password)
    log_login_attempt(
        form_data.username,
        success=user is not None,
        ip=request.client.host
    )
    # ... rest of login
```

**Success Criteria:**
- ✅ All login attempts logged
- ✅ Failed approvals logged
- ✅ Production deployments logged
- ✅ Security log separate from application log

**Effort:** 8 hours

---

### SECURITY-007: Frontend Authentication ⏱️ Week 14, Day 3-5

**Goal:** Add login UI to React dashboard.

**Components to Create:**

**1. Login Page (`src/pages/Login.tsx`):**
```typescript
import React, { useState } from 'react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: email,
          password: password
        })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        window.location.href = '/dashboard';
      } else {
        setError('Invalid email or password');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleLogin}>
        <h1>PromptOps Login</h1>
        {error && <div className="error">{error}</div>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Sign In</button>
      </form>
    </div>
  );
}
```

**2. Update API Client (`src/utils/api.ts`):**
```typescript
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

export const apiClient = {
  async parseIntent(command: string) {
    const response = await fetch(`${API_BASE_URL}/parse-intent`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ command })
    });
    
    if (response.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }
    
    return response.json();
  }
};
```

**Success Criteria:**
- ✅ Login page created
- ✅ JWT token stored in localStorage
- ✅ All API calls include Authorization header
- ✅ 401 errors redirect to login
- ✅ User info displayed in navbar

**Effort:** 8 hours

---

### DEPLOY-001: Staging Environment Setup ⏱️ Week 15, Day 1-2

**Goal:** Deploy to AWS staging environment.

**Infrastructure:**
- ECS Fargate (API Gateway + Context Collector)
- RDS PostgreSQL (db.t3.micro)
- S3 + CloudFront (Frontend)
- Application Load Balancer
- Route53 (staging.promptops.com)

**Deployment Steps:**

1. **Create RDS Instance:**
```bash
aws rds create-db-instance \
  --db-instance-identifier promptops-staging \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.5 \
  --master-username promptops \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 20 \
  --storage-encrypted \
  --tags Key=Environment,Value=staging
```

2. **Deploy via CI/CD:**
```bash
git push origin main
# GitHub Actions will automatically deploy to staging
```

3. **Run Database Migrations:**
```bash
psql -h staging-db-endpoint -U promptops -d promptops -f database/schema.sql
```

**Success Criteria:**
- ✅ Backend running on ECS
- ✅ Frontend on CloudFront
- ✅ Database initialized
- ✅ Health check passing
- ✅ Accessible at staging.promptops.com

**Effort:** 16 hours

---

### TEST-001: User Acceptance Testing ⏱️ Week 15, Day 3-5

**Goal:** PM team validates all workflows.

**Test Scenarios:**

1. **Authentication**
   - Register new user
   - Login/logout
   - Token expiration handling

2. **Staging Deployment**
   - Parse command
   - Review decomposition
   - Execute deployment
   - Verify in audit log

3. **Production Deployment**
   - Requires elevated role
   - Typed approval workflow
   - Execution monitoring

4. **Audit Trail**
   - Filter by user/environment
   - Export to CSV
   - Pagination

5. **Drift Detection**
   - View drift events
   - Acknowledge drift
   - Revert drift

**Success Criteria:**
- ✅ All 5 scenarios pass
- ✅ No critical bugs found
- ✅ Performance acceptable
- ✅ PM team approval

**Effort:** 24 hours (3 days with team)

---

## Timeline Summary

| Week | Days | Tasks | Effort |
|------|------|-------|--------|
| **Week 13** | 1-3 | Authentication (JWT, login, register) | 16h |
| | 3-4 | RBAC (roles, permissions) | 12h |
| | 4 | Fix CORS | 2h |
| | 5 | Rate limiting | 4h |
| **Week 14** | 1-2 | Secrets Management | 8h |
| | 2-3 | Security Logging | 8h |
| | 3-5 | Frontend Authentication UI | 8h |
| **Week 15** | 1-2 | Staging Deployment | 16h |
| | 3-5 | User Acceptance Testing | 24h |
| **Total** | **15 days** | **9 tasks** | **98 hours** |

---

## Success Metrics

### Security ✅
- ✅ All endpoints require authentication
- ✅ Role-based access control working
- ✅ CORS restricted to specific domains
- ✅ Rate limiting active
- ✅ Secrets in AWS Secrets Manager
- ✅ Security events logged

### Deployment ✅
- ✅ Staging environment operational
- ✅ CI/CD pipeline deploying automatically
- ✅ Zero-downtime deployments
- ✅ Health checks passing
- ✅ Monitoring configured

### Testing ✅
- ✅ All UAT scenarios passing
- ✅ No critical bugs
- ✅ Performance targets met
- ✅ PM team approval

---

## Production Readiness Checklist

After Week 13-15, review this checklist:

- [ ] Authentication implemented and tested
- [ ] Authorization working (RBAC)
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Secrets in Secrets Manager
- [ ] Security logging enabled
- [ ] Staging deployment successful
- [ ] UAT completed
- [ ] Load testing passed
- [ ] Security audit re-run
- [ ] Disaster recovery tested
- [ ] Documentation updated
- [ ] Runbooks reviewed
- [ ] On-call rotation planned

---

## Next Steps (Week 16+)

**Week 16: Production Deployment**
- Final security review
- Stakeholder approval
- Production infrastructure setup
- Gradual rollout (10% → 50% → 100%)
- Post-deployment monitoring

---

**Author**: PromptOps Team  
**Date**: 2026-04-30  
**Status**: Ready to Start  
**Prerequisites**: Week 11-12 Complete ✅
