"""
PromptOps Mobile Deployment UI Server
======================================

Simple UI server for manual mobile app deployment.

Author: DevOps Engineer
Date: 2026-05-11
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_gateway'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

from deploy_android_app import AndroidDeploymentOrchestrator
from aws_mobile_deploy import AWSMobileDeployer
from android_builder import AndroidBuilder

# Import new utilities
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
    from utils.output_handler import PlatformOutput
    from utils.port_finder import PortFinder
    output = PlatformOutput()
    PORT_FINDER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import utilities: {e}")
    output = None
    PortFinder = None
    PORT_FINDER_AVAILABLE = False

app = FastAPI(title="PromptOps Mobile Deployment", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import mobile deployment routes
try:
    from cicd_routes import router as cicd_router
    # Only include mobile deployment endpoints
    app.include_router(cicd_router, prefix="")
except Exception as e:
    print(f"Warning: Could not import cicd_routes: {e}")
    print("Creating basic mobile routes...")

    from fastapi import APIRouter
    from pydantic import BaseModel, Field
    from typing import Optional

    router = APIRouter(prefix="/api/v1/cicd", tags=["mobile"])

    class MobileDeploymentRequest(BaseModel):
        repo_url: str
        branch: str = "main"
        app_name: str
        deployment_option: str = "A"
        aws_bucket: Optional[str] = None
        aws_region: str = "us-east-1"

    @router.post("/mobile/deploy")
    async def deploy_mobile_app(request: MobileDeploymentRequest):
        """Deploy mobile app from Git repository"""
        orchestrator = AndroidDeploymentOrchestrator()

        aws_config = {
            "bucket_name": request.aws_bucket,
            "region": request.aws_region
        } if request.aws_bucket else None

        result = orchestrator.deploy_from_git(
            repo_url=request.repo_url,
            branch=request.branch,
            app_name=request.app_name,
            deployment_option=request.deployment_option,
            aws_config=aws_config
        )

        orchestrator.cleanup()
        return result

    @router.get("/health")
    async def health():
        return {"status": "healthy", "service": "mobile_deployment"}

    app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Mobile deployment UI"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptOps Mobile Deployment</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        .deploy-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .deploy-btn:hover {
            transform: translateY(-2px);
        }
        .deploy-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            display: none;
        }
        .status.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .status.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .status.info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 8px;
            display: none;
        }
        .result h3 {
            margin-bottom: 15px;
            color: #333;
        }
        .result-item {
            margin-bottom: 10px;
            font-size: 14px;
        }
        .result-label {
            font-weight: 600;
            color: #666;
        }
        .result-value {
            color: #333;
            word-break: break-all;
        }
        .download-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        .download-link:hover {
            text-decoration: underline;
        }
        .info-box {
            background: #fff3cd;
            border: 1px solid #ffeeba;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 30px;
            font-size: 14px;
            color: #856404;
        }
        .info-box strong {
            display: block;
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 PromptOps Mobile Deployment</h1>
        <div class="subtitle">Deploy Android apps to AWS S3 + CloudFront</div>

        <div class="info-box">
            <strong>✅ Auto-Java Version Selection Enabled:</strong>
            PromptOps will automatically use Java 17 if available on your system,
            even though Java 26 is your default. No manual switching required!
        </div>

        <form id="deployForm">
            <div class="form-group">
                <label for="repoUrl">Git Repository URL *</label>
                <input
                    type="text"
                    id="repoUrl"
                    name="repoUrl"
                    placeholder="https://github.com/username/repo"
                    value="https://github.com/kirankumarhs29/netSenseAI"
                    required
                >
            </div>

            <div class="form-group">
                <label for="branch">Branch</label>
                <input
                    type="text"
                    id="branch"
                    name="branch"
                    value="main"
                    required
                >
            </div>

            <div class="form-group">
                <label for="appName">Application Name *</label>
                <input
                    type="text"
                    id="appName"
                    name="appName"
                    placeholder="My Android App"
                    value="netSenseAI"
                    required
                >
            </div>

            <div class="form-group">
                <label for="deploymentOption">Deployment Option</label>
                <select id="deploymentOption" name="deploymentOption">
                    <option value="A" selected>Option A - AWS S3 + CloudFront</option>
                    <option value="B" disabled>Option B - Firebase (Coming Soon)</option>
                    <option value="C" disabled>Option C - Play Store (Coming Soon)</option>
                </select>
            </div>

            <div class="form-group">
                <label for="awsBucket">AWS S3 Bucket Name *</label>
                <input
                    type="text"
                    id="awsBucket"
                    name="awsBucket"
                    placeholder="my-android-apps-2026"
                    value="netsense-ai-2026"
                    required
                >
            </div>

            <div class="form-group">
                <label for="awsRegion">AWS Region</label>
                <select id="awsRegion" name="awsRegion">
                    <option value="us-east-1" selected>us-east-1 (US East - N. Virginia)</option>
                    <option value="us-west-2">us-west-2 (US West - Oregon)</option>
                    <option value="eu-west-1">eu-west-1 (Europe - Ireland)</option>
                    <option value="ap-south-1">ap-south-1 (Asia Pacific - Mumbai)</option>
                </select>
            </div>

            <button type="submit" class="deploy-btn" id="deployBtn">
                🚀 Deploy Application
            </button>
        </form>

        <div id="status" class="status"></div>
        <div id="result" class="result"></div>
    </div>

    <script>
        const form = document.getElementById('deployForm');
        const deployBtn = document.getElementById('deployBtn');
        const statusDiv = document.getElementById('status');
        const resultDiv = document.getElementById('result');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Get form data
            const formData = {
                repo_url: document.getElementById('repoUrl').value,
                branch: document.getElementById('branch').value,
                app_name: document.getElementById('appName').value,
                deployment_option: document.getElementById('deploymentOption').value,
                aws_bucket: document.getElementById('awsBucket').value,
                aws_region: document.getElementById('awsRegion').value
            };

            // Show status
            statusDiv.className = 'status info';
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '⏳ Starting deployment... This may take 5-15 minutes.';
            resultDiv.style.display = 'none';

            // Disable button
            deployBtn.disabled = true;
            deployBtn.textContent = '⏳ Deploying...';

            try {
                const response = await fetch('/api/v1/cicd/mobile/deploy', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (result.status === 'success') {
                    // Success
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = '✅ Deployment Successful!';

                    // Show results
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `
                        <h3>📊 Deployment Results</h3>
                        <div class="result-item">
                            <span class="result-label">Deployment ID:</span>
                            <span class="result-value">${result.deployment_id}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">App Name:</span>
                            <span class="result-value">${result.app_name}</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">Status:</span>
                            <span class="result-value">${result.status}</span>
                        </div>
                        ${result.download_url ? `
                        <div class="result-item">
                            <span class="result-label">Download Page:</span><br>
                            <a href="${result.download_url}" target="_blank" class="download-link">
                                ${result.download_url}
                            </a>
                        </div>
                        ` : ''}
                        ${result.direct_apk_url ? `
                        <div class="result-item">
                            <span class="result-label">Direct APK URL:</span><br>
                            <a href="${result.direct_apk_url}" target="_blank" class="download-link">
                                ${result.direct_apk_url}
                            </a>
                        </div>
                        ` : ''}
                        <div class="result-item">
                            <span class="result-label">Stages:</span>
                            <pre style="background: white; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px;">
${JSON.stringify(result.stages, null, 2)}</pre>
                        </div>
                    `;
                } else {
                    // Failed
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = `❌ Deployment Failed: ${result.error || 'Unknown error'}`;

                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `
                        <h3>❌ Error Details</h3>
                        <div class="result-item">
                            <span class="result-label">Error:</span>
                            <span class="result-value">${result.error}</span>
                        </div>
                        ${result.stages ? `
                        <div class="result-item">
                            <span class="result-label">Stages:</span>
                            <pre style="background: white; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px;">
${JSON.stringify(result.stages, null, 2)}</pre>
                        </div>
                        ` : ''}
                    `;
                }
            } catch (error) {
                statusDiv.className = 'status error';
                statusDiv.innerHTML = `❌ Request failed: ${error.message}`;
            } finally {
                // Re-enable button
                deployBtn.disabled = false;
                deployBtn.textContent = '🚀 Deploy Application';
            }
        });
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    import io
    import socket

    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Find available port (simple version)
    def is_port_available(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return True
        except OSError:
            return False

    port = 8000
    if not is_port_available(8000):
        print("[WARN] Port 8000 is busy, trying 8001...")
        port = 8001
        if not is_port_available(8001):
            print("[WARN] Port 8001 is also busy, trying 8002...")
            port = 8003

    print("\n" + "="*70)
    print("  PromptOps Mobile Deployment UI")
    print("="*70)
    print(f"\n[OK] Starting server on port {port}...")
    print(f"[OK] Open: http://localhost:{port}")
    print(f"[OK] API Docs: http://localhost:{port}/docs")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
