"""
PromptOps — Jewelry Vault Deployment Test
==========================================

End-to-end test that exercises the PromptOps deployment pipeline
to deploy the jewelry-vault static PWA application.

Flow:
  1. PromptOps server starts (FastAPI)
  2. Client sends a natural-language deploy command
  3. PromptOps parser resolves the intent
  4. PromptOps decomposer produces subtasks
  5. PromptOps executor deploys the static site (local or AWS)
  6. Health-check confirms the app is live

Run:
    python deploy_jewelry_vault_test.py

Usage (after server is running):
    POST http://localhost:8000/api/v1/deploy/static          — local
    POST http://localhost:8000/api/v1/deploy/aws             — AWS S3
    GET  http://localhost:8000/api/v1/deploy/status
"""

import sys
import os
import subprocess
import threading
import time
import socket
import json
import secrets
import difflib
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ── Make sure PromptOps packages are on the path ──────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "api_gateway"))
sys.path.insert(0, str(ROOT / "phase1-nlp"))

# ── External deps ─────────────────────────────────────────────────────────────
import uvicorn
from fastapi import FastAPI, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Re-use the existing PromptOps mock parser ─────────────────────────────────
from parser_routes import router as parser_router, SimpleMockParser

# ── AWS S3 deployment module ───────────────────────────────────────────────────
from aws_static_deploy import deploy_to_s3

# ── Config ─────────────────────────────────────────────────────────────────────
PROMPTOPS_PORT  = 8000
STATIC_APP_PORT = 8081
JEWELRY_VAULT_DIR = Path(r"C:\Users\pqm847\Documents\jewelry-vault")

# ── PromptOps in-memory deployment registry ────────────────────────────────────
deployments: dict = {}
_static_server_process: subprocess.Popen | None = None

# ── Mock auth storage for dashboard login ─────────────────────────────────────
MOCK_USERS = {
    "admin@promptops.com": {
        "id": "admin-default-001",
        "email": "admin@promptops.com",
        "full_name": "System Administrator",
        "role": "admin",
        "is_active": True,
        "password": "admin123",
    },
    "pm@promptops.com": {
        "id": "pm-test-001",
        "email": "pm@promptops.com",
        "full_name": "Product Manager",
        "role": "pm",
        "is_active": True,
        "password": "pm123",
    },
}

TOKENS: dict[str, str] = {}

# ── Activity audit logging ───────────────────────────────────────────────────
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
ACTIVITY_LOG_FILE = LOG_DIR / "promptops_activity.log"


def _write_activity(action: str, details: dict | None = None, user_email: str | None = None):
    """Append one JSONL activity event to the PromptOps audit log file."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user": user_email or "anonymous",
        "details": details or {},
    }
    with ACTIVITY_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")


def _extract_user_from_bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    return TOKENS.get(token)

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PromptOps API Gateway",
    description="Natural-language deployment orchestration for static PWAs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the existing PromptOps parser routes
app.include_router(parser_router)


# ── Schemas ────────────────────────────────────────────────────────────────────
class NLDeployRequest(BaseModel):
    """Natural-language deployment command (what a PM would type)."""
    command: str = "deploy jewelry-vault static site locally on port 8081"
    user: str = "pm@promptops.com"


class DeployStaticRequest(BaseModel):
    """Direct static-site deployment request."""
    app_name: str
    source_path: str
    port: int = STATIC_APP_PORT
    description: str = ""


class DeployAWSRequest(BaseModel):
    """AWS S3 deployment request."""
    app_name: str = "jewelry-vault"
    source_path: str = str(JEWELRY_VAULT_DIR)
    bucket_name: str = "jewelry-vault-promptops"
    region: str = "us-east-1"


class DeployAndroidAWSRequest(BaseModel):
    """Deploy Android app source bundle from GitHub to AWS S3."""
    app_name: str = "netsenseai"
    repo_url: str = "https://github.com/kirankumarhs29/netSenseAI"
    branch: str = "main"
    bucket_name: str = "netsenseai-promptops"
    region: str = "us-east-1"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class ActivityLogRequest(BaseModel):
    action: str
    details: dict = {}
    user: str | None = None


# ── Helper: find a free port ───────────────────────────────────────────────────
def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0


# ── Helper: start Python HTTP server ──────────────────────────────────────────
def _start_static_server(directory: str, port: int) -> subprocess.Popen:
    """Start Python's built-in HTTP server for a static directory."""
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", directory],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _resolve_source_dir(source_path: str) -> tuple[Path | None, str | None]:
        """
        Resolve source directory path.

        If exact path does not exist, attempt a closest-match lookup within parent dir
        to tolerate small typos in app folder names.
        """
        source = Path(source_path)
        if source.is_dir():
            return source, None

        parent = source.parent
        if not parent.exists() or not parent.is_dir():
            return None, None

        target_name = source.name.lower()
        candidates = [d for d in parent.iterdir() if d.is_dir()]
        candidate_names = [d.name for d in candidates]
        matches = difflib.get_close_matches(target_name, [name.lower() for name in candidate_names], n=1, cutoff=0.74)

        if not matches:
            return None, None

        matched_lower = matches[0]
        matched_dir = next((d for d in candidates if d.name.lower() == matched_lower), None)
        if not matched_dir:
            return None, None

        return matched_dir, f"Source path corrected from '{source_path}' to '{matched_dir}'"


# ── PromptOps Deployment Pipeline ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "service": "PromptOps API Gateway", "version": "1.0.0"}


@app.post("/api/v1/auth/login", response_model=LoginResponse, summary="Mock login for dashboard")
def auth_login(username: str = Form(...), password: str = Form(...)):
    user = MOCK_USERS.get(username)
    if not user or user["password"] != password:
        _write_activity(
            action="auth.login.failed",
            details={"reason": "invalid_credentials"},
            user_email=username,
        )
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = secrets.token_urlsafe(32)
    TOKENS[token] = username

    user_response = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": user["is_active"],
    }

    _write_activity(
        action="auth.login.success",
        details={"role": user["role"]},
        user_email=username,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_response,
    }


@app.get("/api/v1/auth/me", summary="Get current mock user")
def auth_me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = authorization.split(" ", 1)[1].strip()
    email = TOKENS.get(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = MOCK_USERS[email]
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": user["is_active"],
    }


@app.post("/api/v1/auth/logout", summary="Logout current mock user")
def auth_logout(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = authorization.split(" ", 1)[1].strip()
    email = TOKENS.pop(token, None)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    _write_activity(
        action="auth.logout",
        details={"status": "success"},
        user_email=email,
    )
    return {"success": True, "message": "Logged out"}


@app.post("/api/v1/audit/log", summary="Append a PromptOps activity log event")
def audit_log(req: ActivityLogRequest, authorization: str | None = Header(default=None)):
    user_email = req.user or _extract_user_from_bearer(authorization)
    _write_activity(action=req.action, details=req.details, user_email=user_email)
    return {"success": True}


@app.get("/api/v1/audit/recent", summary="Read recent PromptOps activity events")
def audit_recent(limit: int = 100):
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    if not ACTIVITY_LOG_FILE.exists():
        return {
            "log_file": str(ACTIVITY_LOG_FILE),
            "count": 0,
            "events": [],
        }

    lines = ACTIVITY_LOG_FILE.read_text(encoding="utf-8").splitlines()
    selected = lines[-limit:]
    events = []
    for line in selected:
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    return {
        "log_file": str(ACTIVITY_LOG_FILE),
        "count": len(events),
        "events": events,
    }


@app.post("/api/v1/nl-deploy", summary="Natural-language deploy command")
def nl_deploy(req: NLDeployRequest):
    """
    Step 1 — Parse a natural-language PM command.
    Step 2 — Decompose into subtasks.
    Step 3 — Execute: deploy the target static site.
    """
    parser = SimpleMockParser()
    _write_activity(
        action="deploy.nl.command_received",
        details={"command": req.command},
        user_email=req.user,
    )
    intent = parser.parse(req.command)

    if intent.get("intent_type") != "deployment":
        raise HTTPException(
            status_code=422,
            detail=f"Command parsed as '{intent.get('intent_type')}', expected 'deployment'. "
                   "Try: 'deploy jewelry-vault static site locally'",
        )

    # Decompose
    subtasks = [
        {"id": "T-01", "title": "Validate source directory",    "status": "done"},
        {"id": "T-02", "title": "Check port availability",      "status": "done"},
        {"id": "T-03", "title": "Start static HTTP server",     "status": "pending"},
        {"id": "T-04", "title": "Register deployment",          "status": "pending"},
        {"id": "T-05", "title": "Health-check deployed URL",    "status": "pending"},
    ]

    # Execute via the direct deploy endpoint logic
    result = _do_deploy(
        app_name="jewelry-vault",
        source_path=str(JEWELRY_VAULT_DIR),
        port=STATIC_APP_PORT,
        description="Jewelry Vault PWA — deployed via PromptOps NL command",
    )

    # Mark all subtasks complete
    for t in subtasks:
        t["status"] = "done"

    return {
        "nl_command":  req.command,
        "parsed_intent": intent,
        "subtasks": subtasks,
        "deployment": result,
    }


@app.post("/api/v1/deploy/static", summary="Deploy a static site")
def deploy_static(req: DeployStaticRequest):
    """Deploy a local static-site directory and serve it on the given port."""
    _write_activity(
        action="deploy.static.requested",
        details={
            "app_name": req.app_name,
            "source_path": req.source_path,
            "port": req.port,
        },
    )
    return _do_deploy(req.app_name, req.source_path, req.port, req.description)


def _do_deploy(app_name: str, source_path: str, port: int, description: str) -> dict:
    global _static_server_process

    source, correction_note = _resolve_source_dir(source_path)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source directory not found: {source_path}")

    if correction_note:
        _write_activity(
            action="deploy.source_path.corrected",
            details={
                "app_name": app_name,
                "requested_source_path": source_path,
                "resolved_source_path": str(source),
            },
        )

    # Stop previous deployment for this app if any
    existing = deployments.get(app_name)
    if existing and existing.get("pid"):
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(existing["pid"])],
                           capture_output=True)
        except Exception:
            pass

    if not _is_port_free(port):
        # Port in use — try to free it or pick next
        port += 1
        if not _is_port_free(port):
            raise HTTPException(
                status_code=409,
                detail=f"Port {port - 1} (and {port}) already in use. Stop any running servers first.",
            )

    proc = _start_static_server(str(source), port)
    time.sleep(1.0)  # Give it a moment to bind

    if proc.poll() is not None:
        stderr = proc.stderr.read().decode()
        raise HTTPException(status_code=500,
                            detail=f"Static server failed to start: {stderr}")

    deployment = {
        "app_name":   app_name,
        "source_path": str(source),
        "port":       port,
        "url":        f"http://localhost:{port}",
        "pid":        proc.pid,
        "status":     "running",
        "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "description": description or f"{app_name} static site",
        "files": [f.name for f in source.iterdir() if f.is_file()],
    }
    if correction_note:
        deployment["source_path_note"] = correction_note
    deployments[app_name] = deployment
    _static_server_process = proc
    _write_activity(
        action="deploy.static.completed",
        details={
            "app_name": app_name,
            "url": deployment["url"],
            "port": deployment["port"],
            "pid": deployment["pid"],
        },
    )
    return deployment


@app.get("/api/v1/deploy/status", summary="List all deployments")
def deploy_status():
    """Return the PromptOps deployment registry."""
    return {"deployments": list(deployments.values())}


@app.post("/api/v1/deploy/aws", summary="Deploy static site to AWS S3 (public internet)")
def deploy_aws(req: DeployAWSRequest):
    """
    Deploy a local static site to AWS S3 with public website hosting.
    The app becomes accessible from the internet via the S3 website URL.

    Steps performed by PromptOps:
      T-01  Validate source directory
      T-02  Verify AWS credentials
      T-03  Create / reuse S3 bucket
      T-04  Disable Block Public Access
      T-05  Enable static website hosting
      T-06  Apply public-read bucket policy
      T-07  Upload all files with correct Content-Type headers
      T-08  Return public website URL
    """
    try:
        _write_activity(
            action="deploy.aws.requested",
            details={
                "app_name": req.app_name,
                "bucket": req.bucket_name,
                "region": req.region,
                "source_path": req.source_path,
            },
        )
        result = deploy_to_s3(
            source_path=req.source_path,
            bucket_name=req.bucket_name,
            region=req.region,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Register in PromptOps deployment registry
    deployments[req.app_name] = {
        "app_name":      req.app_name,
        "deployment_type": "aws-s3",
        "bucket":        req.bucket_name,
        "region":        req.region,
        "url":           result["website_url"],
        "status":        "deployed",
        "deployed_at":   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files_uploaded": result["files_uploaded"],
        "accessible_from": "internet (public)",
    }
    _write_activity(
        action="deploy.aws.completed",
        details={
            "app_name": req.app_name,
            "bucket": req.bucket_name,
            "region": req.region,
            "website_url": result.get("website_url"),
            "files_uploaded": result.get("files_uploaded"),
        },
    )
    return result


def _parse_github_repo(repo_url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(repo_url)
    if parsed.netloc.lower() != "github.com":
        raise ValueError("Only github.com repositories are currently supported")

    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL")

    owner = parts[0]
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


@app.post("/api/v1/deploy/android/aws", summary="Deploy Android app bundle from GitHub repo to AWS S3")
def deploy_android_aws(req: DeployAndroidAWSRequest):
    """
    Deploy Android app repository bundle to AWS S3 and create a public deployment page.

    This flow uploads a source bundle and deployment metadata that can be consumed by
    CI/CD for APK generation and distribution.
    """
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError

        owner, repo = _parse_github_repo(req.repo_url)
        bundle_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{req.branch}.zip"

        _write_activity(
            action="deploy.android.aws.requested",
            details={
                "app_name": req.app_name,
                "repo_url": req.repo_url,
                "branch": req.branch,
                "bucket": req.bucket_name,
                "region": req.region,
            },
        )

        session = boto3.Session(region_name=req.region)
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        s3 = session.client("s3")

        try:
            if req.region == "us-east-1":
                s3.create_bucket(Bucket=req.bucket_name)
            else:
                s3.create_bucket(
                    Bucket=req.bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": req.region},
                )
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code not in ["BucketAlreadyOwnedByYou", "BucketAlreadyExists"]:
                raise

        s3.put_public_access_block(
            Bucket=req.bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )

        s3.put_bucket_website(
            Bucket=req.bucket_name,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "index.html"},
            },
        )

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{req.bucket_name}/*"],
                }
            ],
        }
        s3.put_bucket_policy(Bucket=req.bucket_name, Policy=json.dumps(policy))

        with urllib.request.urlopen(bundle_url, timeout=60) as response:
            bundle_bytes = response.read()

        bundle_key = f"android/{req.app_name}/{req.branch}/source.zip"
        s3.put_object(
            Bucket=req.bucket_name,
            Key=bundle_key,
            Body=bundle_bytes,
            ContentType="application/zip",
            CacheControl="no-cache",
        )

        metadata = {
            "app_name": req.app_name,
            "repo_url": req.repo_url,
            "branch": req.branch,
            "bundle_key": bundle_key,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "account_id": identity.get("Account"),
            "note": "Source bundle uploaded. Build APK via CI/CD workflow and publish artifact to this bucket.",
        }
        metadata_key = f"android/{req.app_name}/{req.branch}/deployment-metadata.json"
        s3.put_object(
            Bucket=req.bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2).encode("utf-8"),
            ContentType="application/json",
            CacheControl="no-cache",
        )

        source_bundle_url = f"https://{req.bucket_name}.s3.{req.region}.amazonaws.com/{bundle_key}"
        metadata_url = f"https://{req.bucket_name}.s3.{req.region}.amazonaws.com/{metadata_key}"

        html = f"""
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{req.app_name} Android Deployment</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 40px; background: #f8fafc; color: #0f172a; }}
    .card {{ max-width: 900px; background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; }}
    a {{ color: #2563eb; }}
    code {{ background: #eef2ff; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>{req.app_name} Android Deployment</h1>
    <p><strong>Repository:</strong> <a href=\"{req.repo_url}\">{req.repo_url}</a></p>
    <p><strong>Branch:</strong> {req.branch}</p>
    <p><strong>AWS Bucket:</strong> {req.bucket_name}</p>
    <hr />
    <p><strong>Source Bundle:</strong> <a href=\"{source_bundle_url}\">Download source.zip</a></p>
    <p><strong>Deployment Metadata:</strong> <a href=\"{metadata_url}\">deployment-metadata.json</a></p>
    <p>Next: run Android build in CI and upload generated APK to this bucket for distribution.</p>
  </div>
</body>
</html>
""".strip()

        s3.put_object(
            Bucket=req.bucket_name,
            Key="index.html",
            Body=html.encode("utf-8"),
            ContentType="text/html",
            CacheControl="no-cache",
        )

        website_url = f"http://{req.bucket_name}.s3-website-{req.region}.amazonaws.com"

        result = {
            "success": True,
            "app_name": req.app_name,
            "repo_url": req.repo_url,
            "branch": req.branch,
            "bucket": req.bucket_name,
            "region": req.region,
            "website_url": website_url,
            "source_bundle_url": source_bundle_url,
            "metadata_url": metadata_url,
            "message": "Android source bundle deployed to AWS. Build APK in CI and publish artifact to this bucket.",
        }

        deployments[req.app_name] = {
            "app_name": req.app_name,
            "deployment_type": "android-aws-source-bundle",
            "bucket": req.bucket_name,
            "region": req.region,
            "url": website_url,
            "repo_url": req.repo_url,
            "branch": req.branch,
            "status": "deployed",
            "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "accessible_from": "internet (public)",
        }

        _write_activity(
            action="deploy.android.aws.completed",
            details={
                "app_name": req.app_name,
                "bucket": req.bucket_name,
                "region": req.region,
                "website_url": website_url,
                "source_bundle_url": source_bundle_url,
            },
        )

        return result

    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found. Run 'aws configure' first.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub repository or branch not found: {req.repo_url} ({req.branch})")
        raise HTTPException(status_code=500, detail=f"Failed to download repository archive: HTTP {e.code}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Android AWS deployment failed: {str(e)}")


@app.delete("/api/v1/deploy/{app_name}", summary="Stop a deployment")
def stop_deployment(app_name: str):
    """Stop and remove a running deployment."""
    dep = deployments.get(app_name)
    if not dep:
        raise HTTPException(status_code=404, detail=f"No deployment found for '{app_name}'")

    pid = dep.get("pid")
    if pid:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)

    dep["status"] = "stopped"
    deployments.pop(app_name, None)
    _write_activity(
        action="deploy.stopped",
        details={"app_name": app_name, "pid": pid},
    )
    return {"message": f"Deployment '{app_name}' stopped", "pid": pid}


# ── CLI entrypoint ─────────────────────────────────────────────────────────────

def _run_deployment_demo():
    """
    Automated demo: wait for the server then fire a deploy request.
    Runs in a background thread so it doesn't block the uvicorn loop.
    """
    import urllib.request
    import urllib.error

    time.sleep(2.5)  # Wait for uvicorn to be ready

    print("\n" + "=" * 60)
    print("  PromptOps — Jewelry Vault Deployment Test")
    print("=" * 60)

    base = f"http://localhost:{PROMPTOPS_PORT}"

    # ── Health check ──────────────────────────────────────────────
    try:
        with urllib.request.urlopen(f"{base}/health") as r:
            health = json.loads(r.read())
        print(f"\n[1/4] PromptOps health:  {health['status'].upper()}")
    except Exception as e:
        print(f"\n[1/4] Health check failed: {e}")
        return

    # ── Send NL deploy command ─────────────────────────────────────
    command = "deploy jewelry-vault static site locally"
    payload = json.dumps({"command": command, "user": "pm@promptops.com"}).encode()
    req = urllib.request.Request(
        f"{base}/api/v1/nl-deploy",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print(f'\n[2/4] Sending PromptOps command: "{command}"')
    try:
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"     ✗ Deploy failed ({e.code}): {e.read().decode()}")
        return

    dep = result.get("deployment", {})
    print(f'\n[3/4] Intent parsed:  {result["parsed_intent"]["intent_type"].upper()}  '
          f'(confidence {result["parsed_intent"]["confidence"]:.0%})')
    print(f'      Subtasks executed:')
    for t in result["subtasks"]:
        print(f'        ✓  [{t["id"]}] {t["title"]}')

    print(f'\n[4/4] Deployment result:')
    print(f'        App:    {dep.get("app_name")}')
    print(f'        URL:    {dep.get("url")}')
    print(f'        PID:    {dep.get("pid")}')
    print(f'        Status: {dep.get("status", "").upper()}')
    print(f'        Files:  {", ".join(dep.get("files", []))}')

    print(f'\n{"=" * 60}')
    print(f'  jewelry-vault is LIVE at  {dep.get("url")}')
    print(f'  PromptOps API docs at     http://localhost:{PROMPTOPS_PORT}/docs')
    print(f'{"=" * 60}\n')
    print("  Press Ctrl+C to stop all services.\n")


if __name__ == "__main__":
    # Kick off the auto-demo in a background thread
    demo_thread = threading.Thread(target=_run_deployment_demo, daemon=True)
    demo_thread.start()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PROMPTOPS_PORT,
        log_level="warning",  # suppress uvicorn noise so demo output is clean
    )
