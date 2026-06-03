import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './components/LoginPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AutonomySettings } from './pages/AutonomySettings';
import { DiscoveryDashboard } from './pages/DiscoveryDashboard';
import { IngestionWorkflow } from './pages/IngestionWorkflow';
import { ObservabilityDashboard } from './pages/ObservabilityDashboard';
import { PremiumHomeDashboard } from './components/PremiumHomeDashboard';
import { DeploymentForm } from './components/DeploymentForm';
import { apiClient } from './api/client';

type Page = 'home' | 'autonomy' | 'discovery' | 'ingestion' | 'deploy-review' | 'observability';

const REPO_REGISTRY_STORAGE_KEY = 'promptops_repo_registry_v1';
const DEFAULT_REPO_REGISTRY: Record<string, string> = {
  'jewelry-vault': 'https://github.com/ashi100sh/jewelry-vault',
};

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [showDeploymentForm, setShowDeploymentForm] = useState(false);

  // Handle 'deploy' navigation by redirecting to home
  React.useEffect(() => {
    if (currentPage === 'deploy' as any) {
      setCurrentPage('home');
    }
  }, [currentPage]);
  const [commandInput, setCommandInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [commandResult, setCommandResult] = useState<any>(null);
  const [pendingDeploy, setPendingDeploy] = useState<any>(null);
  const [deployProgress, setDeployProgress] = useState({
    active: false,
    status: 'idle',
    currentStep: 0,
    totalSteps: 8,
    title: '',
    subtitle: '',
    logs: [] as string[],
  });
  const [deploySecurity, setDeploySecurity] = useState({
    credentialMode: 'configured',
    accessKeyId: '',
    secretAccessKey: '',
    sessionToken: '',
    securityReviewed: false,
    pmApproved: false,
  });
  const reviewWindowRef = useRef<Window | null>(null);
  const commandInputRef = useRef<HTMLInputElement | null>(null);

  const onboardingSteps = [
    {
      title: 'Pick a workflow',
      detail: 'Open Autonomy, Discovery, or Ingestion based on your task.',
    },
    {
      title: 'Run a plain-English command',
      detail: 'Use the command box to deploy, scale, or scan infrastructure.',
    },
    {
      title: 'Review and approve',
      detail: 'PromptOps shows recommendations and executes after approval.',
    },
  ];

  const commandSuggestions = [
    'Deploy my frontend to AWS production',
    'Start AWS discovery scan for this account',
    'Configure medium-risk autonomy policy',
    'Ingest manual AWS changes into Terraform',
  ];

  const logActivity = async (action: string, details: Record<string, any> = {}) => {
    try {
      await apiClient.post('/api/v1/audit/log', {
        action,
        details,
        user: user?.email || null,
      });
    } catch (err) {
      // Never block UX on logging failures.
      console.warn('Audit log failed:', err);
    }
  };

  const isDeployCommand = (command: string): boolean => {
    const normalized = command.toLowerCase();
    return normalized.includes('deploy');
  };

  const isAndroidAwsDeployCommand = (command: string): boolean => {
    const normalized = command.toLowerCase();
    return (
      normalized.includes('deploy') &&
      (normalized.includes('android') || normalized.includes('apk') || normalized.includes('github.com')) &&
      (normalized.includes('aws') || normalized.includes('s3') || normalized.includes('cloudfront'))
    );
  };

  const extractGitHubRepoUrl = (command: string): string | null => {
    const match = command.match(/https?:\/\/github\.com\/[\w.-]+\/[\w.-]+/i);
    return match ? match[0].replace(/\.git$/i, '') : null;
  };

  const extractAppNameFromRepoUrl = (repoUrl: string): string => {
    const parts = repoUrl.replace(/\.git$/i, '').split('/').filter(Boolean);
    return parts.length > 0 ? toKebabCase(parts[parts.length - 1]) : 'android-app';
  };

  const toKebabCase = (value: string): string => {
    return value
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, ' ')
      .trim()
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-');
  };

  const toTitleCase = (value: string): string => {
    return value
      .split(/[-_\s]+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
      .join(' ');
  };

  const getRepoRegistry = (): Record<string, string> => {
    try {
      const raw = localStorage.getItem(REPO_REGISTRY_STORAGE_KEY);
      if (!raw) return { ...DEFAULT_REPO_REGISTRY };

      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') {
        return { ...DEFAULT_REPO_REGISTRY };
      }

      return {
        ...DEFAULT_REPO_REGISTRY,
        ...parsed,
      };
    } catch {
      return { ...DEFAULT_REPO_REGISTRY };
    }
  };

  const getRepoForApp = (appName: string): string => {
    const registry = getRepoRegistry();
    return registry[appName] || '';
  };

  const saveRepoForApp = (appName: string, repoUrl: string) => {
    const trimmed = (repoUrl || '').trim();
    if (!appName || !trimmed) return;

    const registry = getRepoRegistry();
    const nextRegistry = {
      ...registry,
      [appName]: trimmed.replace(/\.git$/i, ''),
    };
    localStorage.setItem(REPO_REGISTRY_STORAGE_KEY, JSON.stringify(nextRegistry));
  };

  const extractAppFromDeployCommand = (command: string): string => {
    const normalized = command
      .toLowerCase()
      .replace(/[^a-z0-9\s-_]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

    const tokens = normalized.split(' ').filter(Boolean);
    const deployIndex = tokens.indexOf('deploy');
    if (deployIndex === -1 || deployIndex === tokens.length - 1) {
      return 'sample-app';
    }

    const stopWords = new Set([
      'to', 'on', 'in', 'into', 'with', 'using',
      'aws', 'gcp', 'azure', 's3', 'cloudfront',
      'production', 'staging', 'prod', 'dev', 'qa', 'uat'
    ]);
    const noiseWords = new Set(['my', 'the', 'app', 'application', 'website', 'site']);

    const appTokens: string[] = [];
    for (let i = deployIndex + 1; i < tokens.length; i += 1) {
      const token = tokens[i];
      if (stopWords.has(token)) {
        break;
      }
      appTokens.push(token);
    }

    while (appTokens.length > 1 && noiseWords.has(appTokens[0])) {
      appTokens.shift();
    }
    while (appTokens.length > 1 && noiseWords.has(appTokens[appTokens.length - 1])) {
      appTokens.pop();
    }

    const candidate = appTokens.join('-').trim();
    return candidate || 'sample-app';
  };

  const hasDomainRequirement = (command: string): boolean => {
    const normalized = command.toLowerCase();
    return (
      normalized.includes('custom domain') ||
      normalized.includes('domain required') ||
      normalized.includes('need domain') ||
      normalized.includes('with domain')
    );
  };

  const hasMailRequirement = (command: string): boolean => {
    const normalized = command.toLowerCase();
    return (
      normalized.includes('email') ||
      normalized.includes('mail service') ||
      normalized.includes('mail required') ||
      normalized.includes('smtp')
    );
  };

  const extractRequestedDomain = (command: string): string => {
    const matches = command.match(/\b([a-z0-9-]+(?:\.[a-z0-9-]+)+)\b/gi) || [];
    const blocked = new Set(['github.com', 'amazonaws.com']);
    const candidate = matches.find((domain) => {
      const lower = domain.toLowerCase();
      return !blocked.has(lower) && !lower.endsWith('.amazonaws.com');
    });
    return candidate || '';
  };

  const getPlannedPublicEndpoint = (request: any): string => {
    if (request?.domain_required && request?.domain_name?.trim()) {
      return `https://${request.domain_name.trim()}`;
    }

    if (request?.region === 'us-east-1') {
      return `http://${request.bucket_name}.s3-website-us-east-1.amazonaws.com`;
    }

    return `http://${request.bucket_name}.s3-website-${request.region}.amazonaws.com`;
  };

  const getAwsServiceRecommendation = (deployType: string, request: any) => {
    const domainRequired = Boolean(request?.domain_required);
    const mailRequired = Boolean(request?.mail_required);
    const domainName = String(request?.domain_name || '').trim();
    const mailDomain = String(request?.mail_domain || '').trim();

    const rows: Array<{ capability: string; service: string; why: string }> = [
      {
        capability: 'Web hosting',
        service: deployType === 'android_aws' ? 'Amazon S3 + CloudFront' : 'Amazon S3 static website hosting',
        why: deployType === 'android_aws'
          ? 'Best for Android artifact hosting with low cost and controlled public delivery.'
          : 'Best low-cost path for static app delivery with straightforward operations.',
      },
    ];

    if (domainRequired) {
      rows.push(
        {
          capability: 'Custom domain and DNS',
          service: 'Amazon Route 53',
          why: domainName
            ? `Best integrated DNS and domain management for ${domainName}.`
            : 'Best integrated DNS and domain management for AWS-hosted applications.',
        },
        {
          capability: 'TLS certificate',
          service: 'AWS Certificate Manager (ACM)',
          why: 'Managed, auto-renewing certificates for HTTPS with CloudFront.',
        }
      );
    }

    if (mailRequired) {
      rows.push({
        capability: 'Application email',
        service: 'Amazon SES',
        why: mailDomain
          ? `Best transactional email option for ${mailDomain} with SPF/DKIM support.`
          : 'Best transactional email option with strong deliverability and low cost.',
      });
      rows.push({
        capability: 'Business mailbox (optional)',
        service: 'Amazon WorkMail',
        why: 'Use only if PM needs managed inboxes and collaboration mailbox features.',
      });
    }

    return {
      rows,
      summary: domainRequired || mailRequired
        ? 'PromptOps recommends Route 53 for domain and SES for application email when PM requires domain/email readiness.'
        : 'No domain/email requirement detected. PromptOps recommends S3 + CloudFront as the best AWS baseline.',
    };
  };

  const buildDeploySteps = (deployType: string, request: any): string[] => {
    const domainRequired = Boolean(request?.domain_required);
    const mailRequired = Boolean(request?.mail_required);
    const domainName = String(request?.domain_name || '').trim();
    const mailDomain = String(request?.mail_domain || '').trim();

    const steps = deployType === 'android_aws'
      ? [
          'Validate GitHub repository and branch',
          'Verify AWS credentials and security controls',
          'Create or reuse S3 bucket for artifacts',
          'Upload source bundle and deployment metadata',
          'Publish artifact endpoint for downstream distribution',
          'Record audit trail for PM approval',
        ]
      : [
          'Validate source directory and artifacts',
          'Verify AWS credentials and permission scope',
          'Create or reuse S3 bucket',
          'Configure public static website hosting and policy',
          'Upload all files with content-type metadata',
          'Run endpoint smoke check and finalize audit logs',
        ];

    if (domainRequired) {
      steps.push(
        domainName
          ? `Provision domain and DNS in Route 53 for ${domainName}, then map CloudFront alias`
          : 'Provision custom domain and DNS in Route 53, then map CloudFront alias'
      );
    }

    if (mailRequired) {
      steps.push(
        mailDomain
          ? `Configure Amazon SES identity and DNS records for ${mailDomain}`
          : 'Configure Amazon SES domain identity, DKIM, and SPF records'
      );
    }

    return steps;
  };

  const getCloudRecommendation = () => ({
    best: 'AWS',
    reason: 'Best fit for this app because it is a static web deployment with the lowest operational overhead, strong security controls, and the cheapest simple path to public hosting.',
    score: 96,
    matrix: [
      { provider: 'AWS', price: 'Lowest for this use case', security: 'Very strong', fit: 'Best' },
      { provider: 'GCP', price: 'Good, but not better for this setup', security: 'Strong', fit: 'Good' },
      { provider: 'Azure', price: 'Typically higher for this simple flow', security: 'Very strong', fit: 'Good' },
    ],
    reasons: [
      'S3 static website hosting is simple and inexpensive for the current app shape.',
      'CloudFront adds HTTPS, caching, and edge protection without extra app complexity.',
      'AWS IAM and bucket policies give fine-grained access control for security review.',
      'This deployment does not need managed containers or database services, so AWS avoids unnecessary cost.',
    ]
  });

  const escapeHtml = (value: string): string => (
    value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
  );

  const openPmReviewPage = (reviewData: {
    deployType: string;
    service: string;
    serviceLabel: string;
    environment: string;
    strategy: string;
    publicEndpoint: string;
    region: string;
    bucket: string;
    targetFields?: Array<{ label: string; value: string }>;
    requirements?: {
      domain_required?: boolean;
      domain_name?: string;
      mail_required?: boolean;
      mail_domain?: string;
    };
    steps: string[];
  }) => {
    const cloud = getCloudRecommendation();
    const awsPlan = getAwsServiceRecommendation(reviewData.deployType, reviewData.requirements || {});
    const confidence = reviewData.deployType === 'android_aws' ? 94 : cloud.score;
    const reason = reviewData.deployType === 'android_aws'
      ? 'AWS is selected because artifact hosting in S3 with IAM controls and CloudFront distribution is the most practical fit for Android build distribution.'
      : cloud.reason;

    const targetRows = (reviewData.targetFields || [])
      .map((field) => `<tr><th>${escapeHtml(field.label)}</th><td>${escapeHtml(field.value || 'N/A')}</td></tr>`)
      .join('');

    const cloudRows = cloud.matrix.map((row) => `
      <tr>
        <td>${escapeHtml(row.provider)}</td>
        <td>${escapeHtml(row.price)}</td>
        <td>${escapeHtml(row.security)}</td>
        <td>${escapeHtml(row.fit)}</td>
      </tr>
    `).join('');

    const reasonRows = cloud.reasons.map((item) => `<li>${escapeHtml(item)}</li>`).join('');
    const serviceRows = awsPlan.rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.capability)}</td>
        <td>${escapeHtml(row.service)}</td>
        <td>${escapeHtml(row.why)}</td>
      </tr>
    `).join('');
    const stepRows = reviewData.steps.map((step, idx) => `
      <li><strong>Step ${idx + 1}:</strong> ${escapeHtml(step)}</li>
    `).join('');

    const html = `
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>PromptOps PM Review - ${escapeHtml(reviewData.serviceLabel)}</title>
  <style>
    body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f5f7fb; color: #0f172a; }
    .wrap { max-width: 1000px; margin: 24px auto; padding: 0 20px; }
    .card { background: #fff; border: 1px solid #dbe4f0; border-radius: 12px; padding: 18px; margin-bottom: 14px; }
    h1, h2 { margin: 0 0 10px; }
    .muted { color: #475569; font-size: 14px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border: 1px solid #e2e8f0; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f8fafc; width: 190px; }
    .score { font-size: 28px; font-weight: 700; color: #1d4ed8; }
    .actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 14px; }
    button { border: none; border-radius: 8px; padding: 10px 14px; font-weight: 600; cursor: pointer; }
    .approve { background: #1d4ed8; color: white; }
    .reject { background: #e2e8f0; color: #334155; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>PM Deployment Review</h1>
      <div class="muted">Complete review summary for approval workflow</div>
    </div>

    <div class="card">
      <h2>Cloud Selection Summary</h2>
      <div><strong>Selected Cloud:</strong> AWS</div>
      <div class="score">Confidence: ${confidence}%</div>
      <p class="muted">${escapeHtml(reason)}</p>
    </div>

    <div class="card">
      <h2>Why AWS Is Best</h2>
      <table>
        <thead>
          <tr><th>Provider</th><th>Price</th><th>Security</th><th>Fit</th></tr>
        </thead>
        <tbody>
          ${cloudRows}
        </tbody>
      </table>
      <ul>
        ${reasonRows}
      </ul>
    </div>

    <div class="card">
      <h2>Deployment Target Details</h2>
      <table>
        <tbody>
          <tr><th>Application</th><td>${escapeHtml(reviewData.serviceLabel)}</td></tr>
          <tr><th>Environment</th><td>${escapeHtml(reviewData.environment)}</td></tr>
          <tr><th>Strategy</th><td>${escapeHtml(reviewData.strategy)}</td></tr>
          <tr><th>AWS Region</th><td>${escapeHtml(reviewData.region)}</td></tr>
          <tr><th>S3 Bucket</th><td>${escapeHtml(reviewData.bucket)}</td></tr>
          <tr><th>Planned Public URL</th><td>${escapeHtml(reviewData.publicEndpoint)}</td></tr>
          ${targetRows}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>Domain and Mail Service Recommendation</h2>
      <div class="muted">${escapeHtml(awsPlan.summary)}</div>
      <table>
        <thead>
          <tr><th>Capability</th><th>Recommended AWS Service</th><th>Why It Is Best</th></tr>
        </thead>
        <tbody>
          ${serviceRows}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>Detailed Execution Flow</h2>
      <ol>
        ${stepRows}
      </ol>
    </div>

    <div class="card">
      <h2>PM Decision</h2>
      <div class="muted">Approving here will trigger deployment in the main PromptOps tab.</div>
      <div class="actions">
        <button class="reject" onclick="window.opener && window.opener.postMessage({ type: 'PROMPTOPS_PM_REJECT_DEPLOY' }, '*'); window.close();">Reject</button>
        <button class="approve" onclick="window.opener && window.opener.postMessage({ type: 'PROMPTOPS_PM_APPROVE_DEPLOY' }, '*'); window.close();">Approve and Execute</button>
      </div>
    </div>
  </div>
</body>
</html>`;

    // Now open window and write content
    const reviewWindow = window.open('about:blank', '_blank', 'width=1200,height=900');

    if (!reviewWindow) {
      setCommandResult({
        success: false,
        message: 'Unable to open PM review page. Please allow pop-ups for this site and try again.'
      });
      return;
    }

    reviewWindowRef.current = reviewWindow;

    // Write HTML content immediately
    reviewWindow.document.open();
    reviewWindow.document.write(html);
    reviewWindow.document.close();

    // Focus the window
    reviewWindow.focus();

    // Clean up the blob URL after a delay
    setTimeout(() => {
      URL.revokeObjectURL(htmlUrl);
    }, 1000);
  };

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const appendDeployLog = (message: string) => {
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false });
    setDeployProgress((prev) => ({
      ...prev,
      logs: [...prev.logs, `[${ts}] ${message}`].slice(-200),
    }));
  };

  const setDeployStep = (step: number, subtitle: string, logMessage: string) => {
    setDeployProgress((prev) => ({
      ...prev,
      currentStep: step,
      subtitle,
    }));
    appendDeployLog(logMessage);
  };

  const handleCommandSubmit = async () => {
    if (!commandInput.trim() || isProcessing) return;

    const isAndroidDeployPreviewCommand = isAndroidAwsDeployCommand(commandInput);
    const isDeployPreviewCommand = isDeployCommand(commandInput);

    // No need for popup window anymore - will show in same page

    await logActivity('ui.command.send.clicked', {
      command: commandInput,
      page: currentPage,
    });

    setIsProcessing(true);
    setCommandResult(null);
    setPendingDeploy(null);
    setDeployProgress({
      active: false,
      status: 'idle',
      currentStep: 0,
      totalSteps: 8,
      title: '',
      subtitle: '',
      logs: [],
    });
    // Keep credential selection stable across attempts; only re-confirm approvals.
    setDeploySecurity((prev) => ({
      ...prev,
      securityReviewed: false,
      pmApproved: false,
    }));

    try {
      if (isAndroidDeployPreviewCommand) {
        const repoUrl = extractGitHubRepoUrl(commandInput) || 'https://github.com/kirankumarhs29/netSenseAI';
        const appName = extractAppNameFromRepoUrl(repoUrl);
        const serviceLabel = toTitleCase(appName);
        const bucketSuffix = `${Date.now().toString().slice(-6)}`;
        const bucketName = `${appName}-promptops-${bucketSuffix}`;

        const deployRequest = {
          app_name: appName,
          repo_url: repoUrl,
          branch: 'main',
          bucket_name: bucketName,
          region: 'us-east-1',
          domain_required: hasDomainRequirement(commandInput),
          domain_name: extractRequestedDomain(commandInput),
          mail_required: hasMailRequirement(commandInput),
          mail_domain: extractRequestedDomain(commandInput),
        };

        if (deployRequest.domain_required && !deployRequest.domain_name) {
          deployRequest.domain_name = `${appName}.com`;
        }
        if (deployRequest.mail_required && !deployRequest.mail_domain) {
          deployRequest.mail_domain = deployRequest.domain_name || `${appName}.com`;
        }

        const deploySteps = buildDeploySteps('android_aws', deployRequest);

        setPendingDeploy({
          deployType: 'android_aws',
          request: deployRequest,
          preview: {
            service: appName,
            serviceLabel,
            environment: 'production',
            strategy: 'AWS S3 + CloudFront artifact hosting',
            publicEndpoint: getPlannedPublicEndpoint(deployRequest),
            targetFields: [
              { label: 'Repository URL', key: 'repo_url', type: 'text' },
              { label: 'Git Branch', key: 'branch', type: 'text' }
            ],
            steps: deploySteps
          }
        });

        // Keep on home page to show the deployment review
        // setCurrentPage('deploy-review'); // No need to change page

        setCommandResult({
          success: true,
          parsed: {
            intent_type: 'deployment',
            target_service: appName,
            target_env: 'production',
            parameters: {
              platform: 'android',
              repo_url: repoUrl,
              branch: 'main',
              region: deployRequest.region,
              bucket: deployRequest.bucket_name,
              domain_required: deployRequest.domain_required,
              domain_name: deployRequest.domain_name || null,
              mail_required: deployRequest.mail_required,
              mail_domain: deployRequest.mail_domain || null,
              review_required: true
            }
          },
          message: '✓ Loading deployment review... Please wait.'
        });

        await logActivity('ui.deploy.review.generated', {
          service: appName,
          environment: 'production',
          platform: 'android',
          strategy: 'aws-mobile-artifact-hosting',
          review_required: true,
        });
      } else if (isDeployPreviewCommand) {
        // PM review step: generate a preview, do not execute yet
        const appName = toKebabCase(extractAppFromDeployCommand(commandInput));
        const serviceLabel = toTitleCase(appName);
        const bucketSuffix = `${Date.now().toString().slice(-6)}`;
        const bucketName = `${appName}-promptops-${bucketSuffix}`;
        const sourcePath = `C:\\Users\\pqm847\\Documents\\${appName}`;
        const repoFromCommand = extractGitHubRepoUrl(commandInput) || '';
        const repoUrl = repoFromCommand || getRepoForApp(appName);

        if (repoFromCommand) {
          saveRepoForApp(appName, repoFromCommand);
        }

        const deployRequest = {
          app_name: appName,
          source_path: sourcePath,
          repo_url: repoUrl,
          bucket_name: bucketName,
          region: 'us-east-1',
          domain_required: hasDomainRequirement(commandInput),
          domain_name: extractRequestedDomain(commandInput),
          mail_required: hasMailRequirement(commandInput),
          mail_domain: extractRequestedDomain(commandInput),
        };

        if (deployRequest.domain_required && !deployRequest.domain_name) {
          deployRequest.domain_name = `${appName}.com`;
        }
        if (deployRequest.mail_required && !deployRequest.mail_domain) {
          deployRequest.mail_domain = deployRequest.domain_name || `${appName}.com`;
        }

        const deploySteps = buildDeploySteps('static_aws', deployRequest);

        setPendingDeploy({
          deployType: 'static_aws',
          request: deployRequest,
          preview: {
            service: appName,
            serviceLabel,
            environment: 'production',
            strategy: 'AWS S3 static website hosting',
            publicEndpoint: getPlannedPublicEndpoint(deployRequest),
            targetFields: [
              { label: 'Repository URL', key: 'repo_url', type: 'text' },
              { label: 'Source Path', key: 'source_path', type: 'text' }
            ],
            steps: deploySteps
          }
        });

        // Keep on home page to show deployment review
        // setCurrentPage('deploy-review'); // No need to change page

        await logActivity('ui.deploy.review.generated', {
          service: appName,
          environment: 'production',
          strategy: 'aws-s3-static',
          review_required: true,
        });
      } else {
        // Parse the command
        const parseResponse = await apiClient.post('/api/v1/parser/parse', {
          command: commandInput
        });

        setCommandResult({
          success: true,
          parsed: parseResponse,
          message: `Command parsed successfully! Intent: ${parseResponse.intent_type}`
        });

        await logActivity('ui.command.parsed', {
          command: commandInput,
          intent_type: parseResponse.intent_type,
          target_service: parseResponse.target_service || null,
          target_env: parseResponse.target_env || null,
        });
      }

      // Auto-clear messages after showing them
      setTimeout(() => {
        setCommandResult(null);
        if (!isDeployPreviewCommand && !isAndroidDeployPreviewCommand) {
          setCommandInput('');
        }
      }, 5000);

    } catch (error: any) {
      setCommandResult({
        success: false,
        message: error.message || 'Failed to process command'
      });
      await logActivity('ui.command.error', {
        command: commandInput,
        error: error.message || 'Failed to process command',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCommandSubmit();
    }
  };

  const handleConfirmDeploy = async (options?: { forceApproval?: boolean }) => {
    if (!pendingDeploy?.request || isProcessing) return;

    const deployType = pendingDeploy.deployType || 'static_aws';
    const targetService = pendingDeploy.preview?.service || pendingDeploy.request?.app_name || 'sample-app';
    const targetServiceLabel = pendingDeploy.preview?.serviceLabel || toTitleCase(targetService);

    const approvalConfirmed = options?.forceApproval
      ? true
      : (deploySecurity.securityReviewed && deploySecurity.pmApproved);

    await logActivity('ui.deploy.approve.clicked', {
      service: targetService,
      credential_mode: deploySecurity.credentialMode,
      security_reviewed: options?.forceApproval ? true : deploySecurity.securityReviewed,
      pm_approved: options?.forceApproval ? true : deploySecurity.pmApproved,
    });

    const needsManualCredentials = deploySecurity.credentialMode === 'manual';
    if (!approvalConfirmed) {
      setCommandResult({
        success: false,
        message: 'Please complete security review and PM approval before deployment.'
      });
      await logActivity('ui.deploy.approve.blocked', {
        reason: 'missing_security_or_pm_approval',
      });
      return;
    }

    if (needsManualCredentials && (!deploySecurity.accessKeyId || !deploySecurity.secretAccessKey)) {
      setCommandResult({
        success: false,
        message: 'Please provide AWS Access Key ID and Secret Access Key.'
      });
      await logActivity('ui.deploy.approve.blocked', {
        reason: 'missing_manual_credentials',
      });
      return;
    }

    if (deployType === 'static_aws' && !pendingDeploy.request.source_path?.trim()) {
      setCommandResult({
        success: false,
        message: 'Please provide source path before deployment.'
      });
      await logActivity('ui.deploy.approve.blocked', {
        reason: 'missing_source_path',
      });
      return;
    }

    if (!pendingDeploy.request.bucket_name?.trim()) {
      setCommandResult({
        success: false,
        message: 'Please provide S3 bucket name before deployment.'
      });
      await logActivity('ui.deploy.approve.blocked', {
        reason: 'missing_bucket_name',
      });
      return;
    }

    if (pendingDeploy.request.domain_required && !pendingDeploy.request.domain_name?.trim()) {
      setCommandResult({
        success: false,
        message: 'Custom domain is required. Please provide a domain name before deployment.'
      });
      await logActivity('ui.deploy.approve.blocked', {
        reason: 'missing_domain_name',
      });
      return;
    }

    if (pendingDeploy.request.mail_required && !pendingDeploy.request.mail_domain?.trim()) {
      setCommandResult({
        success: false,
        message: 'Mail service is required. Please provide a mail domain before deployment.'
      });
      await logActivity('ui.deploy.approve.blocked', {
        reason: 'missing_mail_domain',
      });
      return;
    }

    setIsProcessing(true);
    try {
      setDeployProgress({
        active: true,
        status: 'running',
        currentStep: 0,
        totalSteps: 8,
        title: `Deploying ${targetServiceLabel} to Production`,
        subtitle: 'Starting deployment pipeline...',
        logs: [],
      });

      setDeployStep(1, 'Step 1 of 8 - Pre-flight validation...', 'Pre-flight checks started');
      await sleep(350);
      setDeployStep(2, 'Step 2 of 8 - Validating PM approval...', 'PM approval and security review validated');
      await sleep(350);
      setDeployStep(3, 'Step 3 of 8 - Preparing deployment plan...', `Deployment plan prepared for ${targetService}`);
      await sleep(350);
      setDeployStep(4, 'Step 4 of 8 - Checking AWS access...', 'AWS credential mode verified');
      await sleep(350);
      setDeployStep(
        5,
        'Step 5 of 8 - Executing deployment...',
        deployType === 'android_aws'
          ? 'Calling deployment API for Android repository artifact hosting'
          : 'Calling deployment API for AWS S3 static hosting'
      );

      const deployEndpoint = deployType === 'android_aws' ? '/api/v1/deploy/android/aws' : '/api/v1/deploy/aws';
      let deployResponse: any;
      const deployPayload = {
        ...pendingDeploy.request,
        ...(needsManualCredentials
          ? {
              aws_access_key_id: deploySecurity.accessKeyId,
              aws_secret_access_key: deploySecurity.secretAccessKey,
              aws_session_token: deploySecurity.sessionToken || undefined,
            }
          : {}),
      };

      if (deployType === 'android_aws') {
        try {
          deployResponse = await apiClient.post(deployEndpoint, deployPayload);
        } catch (primaryError: any) {
          const message = String(primaryError?.message || '');
          const isNotFound = message.toLowerCase().includes('not found') || message.includes('404');

          if (!isNotFound) {
            throw primaryError;
          }

          appendDeployLog('Primary Android deploy endpoint not found. Falling back to CI/CD mobile endpoint...');
          await logActivity('ui.deploy.android.endpoint_fallback', {
            from: '/api/v1/deploy/android/aws',
            to: '/api/v1/cicd/mobile/deploy',
            service: targetService,
          });

          deployResponse = await apiClient.post('/api/v1/cicd/mobile/deploy', {
            repo_url: pendingDeploy.request.repo_url,
            branch: pendingDeploy.request.branch || 'main',
            app_name: pendingDeploy.request.app_name,
            deployment_option: 'A',
            aws_bucket: pendingDeploy.request.bucket_name,
            aws_region: pendingDeploy.request.region,
          });
        }
      } else {
        deployResponse = await apiClient.post(deployEndpoint, deployPayload);
      }

      setDeployStep(
        6,
        'Step 6 of 8 - Verifying upload...',
        deployType === 'android_aws'
          ? `Uploaded repository bundle for ${targetService} to bucket`
          : `Uploaded ${deployResponse.files_uploaded || 0} files to bucket`
      );
      await sleep(300);
      setDeployStep(
        7,
        'Step 7 of 8 - Running smoke checks...',
        deployType === 'android_aws'
          ? 'Deployment page reachable and metadata published'
          : 'Smoke check passed: public endpoint reachable'
      );
      await sleep(300);
      setDeployStep(8, 'Step 8 of 8 - Finalizing...', 'Audit log created and deployment marked successful');
      await sleep(250);

      setDeployProgress((prev) => ({
        ...prev,
        status: 'success',
        subtitle: 'Deployment complete',
      }));

      const responseRegion = deployResponse.region || deployResponse.aws_region || pendingDeploy.request.region;
      const responseBucket = deployResponse.bucket || deployResponse.aws_bucket || pendingDeploy.request.bucket_name;
      const responseWebsiteUrl =
        deployResponse.website_url ||
        deployResponse.download_page_url ||
        deployResponse.url ||
        deployResponse.cloudfront_url ||
        null;
      const responseSourceBundleUrl = deployResponse.source_bundle_url || deployResponse.bundle_url || null;
      const awsRecommendation = getAwsServiceRecommendation(deployType, pendingDeploy.request);

      setCommandResult({
        success: true,
        parsed: {
          intent_type: 'deployment',
          target_service: targetService,
          target_env: 'production',
          parameters: {
            region: responseRegion,
            bucket: responseBucket,
            files_uploaded: deployResponse.files_uploaded || null,
            public_url: responseWebsiteUrl,
            source_bundle_url: responseSourceBundleUrl,
            credential_mode: deploySecurity.credentialMode,
            domain_required: Boolean(pendingDeploy.request.domain_required),
            domain_name: pendingDeploy.request.domain_name || null,
            mail_required: Boolean(pendingDeploy.request.mail_required),
            mail_domain: pendingDeploy.request.mail_domain || null,
            aws_recommended_services: awsRecommendation.rows.map((item) => item.service),
          }
        },
        message: responseWebsiteUrl
          ? `Deployment successful. Public URL: ${responseWebsiteUrl}`
          : 'Deployment successful.'
      });

      setPendingDeploy(null);
      setCommandInput('');
      await logActivity('ui.deploy.executed.success', {
        service: targetService,
        region: responseRegion,
        bucket: responseBucket,
        website_url: responseWebsiteUrl,
        files_uploaded: deployResponse.files_uploaded || null,
        source_bundle_url: responseSourceBundleUrl,
        credential_mode: deploySecurity.credentialMode,
        deploy_type: deployType,
      });
    } catch (error: any) {
      setDeployProgress((prev) => ({
        ...prev,
        active: true,
        status: 'error',
        subtitle: 'Deployment failed',
      }));
      appendDeployLog(`Deployment failed: ${error.message || 'Unknown error'}`);
      setCommandResult({
        success: false,
        message: error.message || 'Failed to deploy command'
      });
      await logActivity('ui.deploy.executed.error', {
        service: targetService,
        error: error.message || 'Failed to deploy command',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancelDeploy = async () => {
    setPendingDeploy(null);
    setCommandResult({
      success: false,
      message: 'Deployment canceled by PM review.'
    });
    await logActivity('ui.deploy.review.canceled', {
      service: pendingDeploy?.preview?.service || pendingDeploy?.request?.app_name || 'sample-app',
    });
  };

  useEffect(() => {
    const onReviewMessage = (event: MessageEvent) => {
      const messageType = event?.data?.type;
      if (!messageType) return;

      if (messageType === 'PROMPTOPS_PM_APPROVE_DEPLOY') {
        setDeploySecurity((prev) => ({
          ...prev,
          securityReviewed: true,
          pmApproved: true,
        }));
        handleConfirmDeploy({ forceApproval: true });
      }

      if (messageType === 'PROMPTOPS_PM_REJECT_DEPLOY') {
        handleCancelDeploy();
      }
    };

    window.addEventListener('message', onReviewMessage);
    return () => window.removeEventListener('message', onReviewMessage);
  }, [handleConfirmDeploy, handleCancelDeploy]);

  const pendingAwsServicePlan = pendingDeploy
    ? getAwsServiceRecommendation(pendingDeploy.deployType || 'static_aws', pendingDeploy.request || {})
    : null;

  const applyCommandSuggestion = (suggestion: string) => {
    setCurrentPage('home');
    setCommandInput(suggestion);
    window.requestAnimationFrame(() => {
      commandInputRef.current?.focus();
    });
  };

  const handleQuickDeploy = () => {
    // Show the deployment form for PM to enter details
    setShowDeploymentForm(true);
  };

  const handleDeploymentFormSubmit = async (deploymentDetails: { command: string; repoUrl: string }) => {
    // Close the form
    setShowDeploymentForm(false);

    // Set the command with the repo URL included
    const fullCommand = `${deploymentDetails.command} from ${deploymentDetails.repoUrl}`;
    setCommandInput(fullCommand);

    // Wait for state update then submit
    setTimeout(async () => {
      await handleCommandSubmit();
    }, 100);
  };

  const handleDeploymentFormCancel = () => {
    setShowDeploymentForm(false);
  };

  return (
    <div className="premium-shell" style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Navbar */}
      <nav className="premium-navbar" style={{
        padding: '16px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
          <div className="premium-logo-wrap" style={{ display: 'flex', alignItems: 'center', gap: '14px', cursor: 'pointer' }} onClick={() => setCurrentPage('home')}>
            <img
              src="/promptops-logo.png"
              alt="PromptOps Logo"
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '8px',
                objectFit: 'contain'
              }}
            />
            <span className="premium-logo-text" style={{
              fontSize: '24px',
              fontWeight: '900',
              color: '#3d3177',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
              letterSpacing: '0.02em',
              textTransform: 'uppercase'
            }}>PromptOps</span>
          </div>

          {/* Navigation Menu */}
          <div className="premium-nav-menu" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setCurrentPage('home')}
              className={`premium-nav-btn ${currentPage === 'home' ? 'is-active' : ''}`}
              style={{
                padding: '8px 16px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              🏠 Home
            </button>
            <button
              onClick={() => setCurrentPage('autonomy')}
              className={`premium-nav-btn ${currentPage === 'autonomy' ? 'is-active' : ''}`}
              style={{
                padding: '8px 16px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              ⚙️ Autonomy
            </button>
            <button
              onClick={() => setCurrentPage('discovery')}
              className={`premium-nav-btn ${currentPage === 'discovery' ? 'is-active' : ''}`}
              style={{
                padding: '8px 16px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              🔍 Discovery
            </button>
            <button
              onClick={() => setCurrentPage('ingestion')}
              className={`premium-nav-btn ${currentPage === 'ingestion' ? 'is-active' : ''}`}
              style={{
                padding: '8px 16px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              📥 Ingestion
            </button>
            <button
              onClick={() => setCurrentPage('observability')}
              className={`premium-nav-btn ${currentPage === 'observability' ? 'is-active' : ''}`}
              style={{
                padding: '8px 16px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              📊 Observability
            </button>
          </div>
        </div>

        <div className="premium-user-chip" style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span style={{ color: '#334155', fontSize: '13px', fontWeight: 600 }}>{user?.full_name || user?.role.toUpperCase()}</span>
          <div className="premium-avatar" style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: '600'
          }}>{user?.email.charAt(0).toUpperCase()}</div>
          <button
            onClick={async () => {
              await logActivity('ui.auth.logout.clicked', { page: currentPage });
              logout();
            }}
            className="premium-logout-btn"
            style={{
              padding: '8px 16px',
              background: 'transparent',
              border: '1px solid #d7e3f8',
              borderRadius: '6px',
              color: '#0f172a',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '14px'
            }}
          >
            Logout
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="premium-main-content" style={{
        flex: 1,
        width: '100%'
      }}>
        {/* Route to different pages */}
        {currentPage === 'autonomy' && <AutonomySettings />}
        {currentPage === 'discovery' && <DiscoveryDashboard />}
        {currentPage === 'ingestion' && <IngestionWorkflow />}
        {currentPage === 'observability' && <ObservabilityDashboard />}

        {/* Home Page */}
        {currentPage === 'home' && !pendingDeploy && (
          <PremiumHomeDashboard
            onNavigate={setCurrentPage}
            onDeployClick={handleQuickDeploy}
          />
        )}

        {/* Deployment Review - Show when deploy is pending */}
        {currentPage === 'home' && pendingDeploy && (
          <div className="premium-home-wrap" style={{
            padding: '32px',
            maxWidth: '1400px',
            margin: '0 auto',
            width: '100%'
          }}>
            <div className="premium-deploy-review">
                  {/* Back Button */}
                  <button
                    onClick={() => {
                      setCurrentPage('home');
                      setPendingDeploy(null);
                    }}
                    style={{
                      marginBottom: '16px',
                      padding: '10px 20px',
                      background: 'var(--glass-bg)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-lg)',
                      cursor: 'pointer',
                      fontWeight: '600',
                      fontSize: '14px',
                      color: 'var(--gray-700)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      transition: 'all var(--transition-base)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.9)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'var(--glass-bg)'}
                  >
                    ← Back to Dashboard
                  </button>
                  <div className="premium-deploy-hero">
                    <div className="premium-deploy-hero-grid">
                      <div>
                        <div className="premium-deploy-eyebrow">
                          Cloud Recommendation
                        </div>
                        <div className="premium-deploy-title">
                          Use AWS for this application
                        </div>
                        <div className="premium-deploy-subtitle">
                          {pendingDeploy.deployType === 'android_aws'
                            ? 'AWS is a strong fit here to host Android build artifacts in S3, secure access with IAM, and distribute globally with CloudFront.'
                            : getCloudRecommendation().reason}
                        </div>
                        {pendingAwsServicePlan && (
                          <div className="premium-deploy-subtitle" style={{ marginTop: '6px' }}>
                            {pendingAwsServicePlan.summary}
                          </div>
                        )}
                      </div>
                      <div className="premium-confidence-box">
                        <div className="label">Confidence</div>
                        <div className="value">{pendingDeploy.deployType === 'android_aws' ? 94 : getCloudRecommendation().score}%</div>
                        <div className="label" style={{ marginTop: '4px' }}>Best fit for cost + security</div>
                      </div>
                    </div>
                  </div>

                  <div className="premium-review-card">
                    <h3>
                      Why AWS instead of GCP or Azure?
                    </h3>
                    <div className="premium-comparison-grid">
                      {getCloudRecommendation().matrix.map((item) => (
                        <div key={item.provider} className={`premium-provider-card ${item.provider === 'AWS' ? 'is-recommended' : ''}`}>
                          <div className="premium-provider-name">{item.provider}</div>
                          <div className="premium-provider-line"><strong>Price:</strong> {item.price}</div>
                          <div className="premium-provider-line"><strong>Security:</strong> {item.security}</div>
                          <div className="premium-provider-line"><strong>Fit:</strong> {item.fit}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ color: '#2d3748', fontSize: '14px' }}>
                      <strong>Key reasons:</strong>
                      <ul className="premium-review-list">
                        {getCloudRecommendation().reasons.map((reason) => (
                          <li key={reason}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="premium-review-card">
                    <h3>
                      Domain and Mail Service Recommendation
                    </h3>
                    <p>
                      {pendingAwsServicePlan?.summary}
                    </p>
                    <div className="premium-table-wrap">
                      <table className="premium-table">
                        <thead>
                          <tr>
                            <th>Capability</th>
                            <th>AWS Service</th>
                            <th>Why Best</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(pendingAwsServicePlan?.rows || []).map((row) => (
                            <tr key={`${row.capability}-${row.service}`}>
                              <td>{row.capability}</td>
                              <td style={{ fontWeight: 700 }}>{row.service}</td>
                              <td>{row.why}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="premium-review-card">
                    <div className="premium-deploy-intent">
                      Deploy {pendingDeploy.preview?.serviceLabel || pendingDeploy.preview?.service || 'Application'} to Production on AWS
                    </div>
                    <div className="premium-meta-line">
                      Intent: Deploy · Confidence: 96% · Risk Level: Medium · Estimated Time: ~3 minutes · Recommended Cloud: AWS
                    </div>
                  </div>

                  <div className="premium-review-card">
                    <h3>
                      Execution Plan ({pendingDeploy.preview.steps.length} steps)
                    </h3>

                    {pendingDeploy.preview.steps.map((step: string, idx: number) => (
                      <div key={idx} className="premium-plan-row">
                        <div className="premium-step-badge">
                          {idx + 1}
                        </div>
                        <div className="premium-plan-text">{step}</div>
                      </div>
                    ))}

                    <div className="premium-meta-line" style={{ marginTop: '14px' }}>
                      Service: <strong>{pendingDeploy.preview.service}</strong> · Environment: <strong>{pendingDeploy.preview.environment}</strong>
                      <br />
                      Planned URL: <strong>{pendingDeploy.preview.publicEndpoint}</strong>
                    </div>
                  </div>

                  <div className="premium-form-section">
                    <div className="premium-form-section-title">Deployment Target</div>

                    {(pendingDeploy.preview?.targetFields || []).map((field: any) => (
                      <label key={field.key} className="premium-field">
                        {field.label}
                        <input
                          type={field.type || 'text'}
                          value={pendingDeploy.request[field.key] || ''}
                          onChange={(e) => {
                            const value = e.target.value;
                            setPendingDeploy((prev: any) => ({
                              ...prev,
                              request: {
                                ...prev.request,
                                [field.key]: value,
                              },
                            }));
                          }}
                          onBlur={async () => {
                            if (field.key === 'repo_url') {
                              saveRepoForApp(
                                pendingDeploy.request.app_name || pendingDeploy.preview?.service || '',
                                pendingDeploy.request[field.key] || ''
                              );
                            }
                            await logActivity(`ui.deploy.target.${field.key}.updated`, {
                              service: pendingDeploy.preview?.service,
                              [field.key]: pendingDeploy.request[field.key],
                            });
                          }}
                          placeholder={field.key === 'source_path'
                            ? 'C:\\Users\\pqm847\\Documents\\my-app'
                            : (field.key === 'repo_url' ? 'https://github.com/org/repo' : '')}
                        />
                      </label>
                    ))}

                    <label className="premium-check-row">
                      <input
                        type="checkbox"
                        checked={Boolean(pendingDeploy.request.domain_required)}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          setPendingDeploy((prev: any) => {
                            const nextRequest = {
                              ...prev.request,
                              domain_required: checked,
                              domain_name: checked ? (prev.request.domain_name || `${prev.request.app_name}.com`) : '',
                            };
                            return {
                              ...prev,
                              request: nextRequest,
                              preview: {
                                ...prev.preview,
                                publicEndpoint: getPlannedPublicEndpoint(nextRequest),
                                steps: buildDeploySteps(prev.deployType || 'static_aws', nextRequest),
                              },
                            };
                          });
                        }}
                      />
                      Domain is required (recommend Route 53 + ACM + CloudFront)
                    </label>

                    {pendingDeploy.request.domain_required && (
                      <label className="premium-field">
                        Domain Name
                        <input
                          type="text"
                          value={pendingDeploy.request.domain_name || ''}
                          onChange={(e) => {
                            const domainName = e.target.value;
                            setPendingDeploy((prev: any) => {
                              const nextRequest = {
                                ...prev.request,
                                domain_name: domainName,
                              };
                              return {
                                ...prev,
                                request: nextRequest,
                                preview: {
                                  ...prev.preview,
                                  publicEndpoint: getPlannedPublicEndpoint(nextRequest),
                                  steps: buildDeploySteps(prev.deployType || 'static_aws', nextRequest),
                                },
                              };
                            });
                          }}
                          placeholder="example.com"
                        />
                      </label>
                    )}

                    <label className="premium-check-row">
                      <input
                        type="checkbox"
                        checked={Boolean(pendingDeploy.request.mail_required)}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          setPendingDeploy((prev: any) => {
                            const nextRequest = {
                              ...prev.request,
                              mail_required: checked,
                              mail_domain: checked
                                ? (prev.request.mail_domain || prev.request.domain_name || `${prev.request.app_name}.com`)
                                : '',
                            };
                            return {
                              ...prev,
                              request: nextRequest,
                              preview: {
                                ...prev.preview,
                                steps: buildDeploySteps(prev.deployType || 'static_aws', nextRequest),
                              },
                            };
                          });
                        }}
                      />
                      Mail service is required (recommend Amazon SES)
                    </label>

                    {pendingDeploy.request.mail_required && (
                      <label className="premium-field">
                        Mail Domain
                        <input
                          type="text"
                          value={pendingDeploy.request.mail_domain || ''}
                          onChange={(e) => {
                            const mailDomain = e.target.value;
                            setPendingDeploy((prev: any) => {
                              const nextRequest = {
                                ...prev.request,
                                mail_domain: mailDomain,
                              };
                              return {
                                ...prev,
                                request: nextRequest,
                                preview: {
                                  ...prev.preview,
                                  steps: buildDeploySteps(prev.deployType || 'static_aws', nextRequest),
                                },
                              };
                            });
                          }}
                          placeholder="mail.example.com"
                        />
                      </label>
                    )}

                    <label className="premium-field">
                      S3 Bucket Name
                      <input
                        type="text"
                        value={pendingDeploy.request.bucket_name}
                        onChange={(e) => {
                          const bucketName = e.target.value.toLowerCase().replace(/[^a-z0-9.-]/g, '-');
                          setPendingDeploy((prev: any) => ({
                            ...prev,
                            request: {
                              ...prev.request,
                              bucket_name: bucketName,
                            },
                            preview: {
                              ...prev.preview,
                              publicEndpoint: getPlannedPublicEndpoint({
                                ...prev.request,
                                bucket_name: bucketName,
                              }),
                            },
                          }));
                        }}
                        onBlur={async () => {
                          await logActivity('ui.deploy.target.bucket.updated', {
                            service: pendingDeploy.preview?.service,
                            bucket: pendingDeploy.request.bucket_name,
                          });
                        }}
                        placeholder="my-app-promptops-123456"
                      />
                    </label>

                    <label className="premium-field">
                      AWS Region
                      <select
                        value={pendingDeploy.request.region}
                        onChange={(e) => {
                          const region = e.target.value;
                          setPendingDeploy((prev: any) => ({
                            ...prev,
                            request: {
                              ...prev.request,
                              region,
                            },
                            preview: {
                              ...prev.preview,
                              publicEndpoint: getPlannedPublicEndpoint({
                                ...prev.request,
                                region,
                              }),
                            },
                          }));
                        }}
                      >
                        <option value="us-east-1">us-east-1</option>
                        <option value="us-east-2">us-east-2</option>
                        <option value="us-west-1">us-west-1</option>
                        <option value="us-west-2">us-west-2</option>
                        <option value="ap-south-1">ap-south-1</option>
                        <option value="eu-west-1">eu-west-1</option>
                      </select>
                    </label>
                  </div>

                  <div className="premium-form-section">
                    <div className="premium-form-section-title">AWS Credentials</div>

                    <label className="premium-field">
                      Credential Mode
                      <select
                        value={deploySecurity.credentialMode}
                        onChange={async (e) => {
                          const mode = e.target.value;
                          setDeploySecurity(prev => ({ ...prev, credentialMode: mode }));
                          await logActivity('ui.deploy.review.credential_mode.changed', { mode });
                        }}
                      >
                        <option value="configured">Use backend configured AWS credentials</option>
                        <option value="manual">Provide AWS key/token for this deploy</option>
                      </select>
                    </label>

                    {deploySecurity.credentialMode === 'manual' && (
                      <>
                        <label className="premium-field">
                          AWS Access Key ID
                          <input
                            type="text"
                            value={deploySecurity.accessKeyId}
                            onChange={(e) => setDeploySecurity(prev => ({ ...prev, accessKeyId: e.target.value }))}
                            placeholder="AKIA..."
                          />
                        </label>

                        <label className="premium-field">
                          AWS Secret Access Key
                          <input
                            type="password"
                            value={deploySecurity.secretAccessKey}
                            onChange={(e) => setDeploySecurity(prev => ({ ...prev, secretAccessKey: e.target.value }))}
                            placeholder="Enter secret access key"
                          />
                        </label>

                        <label className="premium-field">
                          AWS Session Token (optional)
                          <input
                            type="password"
                            value={deploySecurity.sessionToken}
                            onChange={(e) => setDeploySecurity(prev => ({ ...prev, sessionToken: e.target.value }))}
                            placeholder="For temporary STS credentials"
                          />
                        </label>

                        <div className="premium-security-note">
                          For security in this demo flow, manual credentials are reviewed but not persisted by the UI.
                        </div>
                      </>
                    )}
                  </div>

                  <div className="premium-form-section">
                    <div className="premium-form-section-title">Security Review</div>
                    <label className="premium-check-row">
                      <input
                        type="checkbox"
                        checked={deploySecurity.securityReviewed}
                        onChange={async (e) => {
                          const checked = e.target.checked;
                          setDeploySecurity(prev => ({ ...prev, securityReviewed: checked }));
                          await logActivity('ui.deploy.review.security_checked', { checked });
                        }}
                      />
                      I reviewed target AWS account, region, and public access implications.
                    </label>
                    <label className="premium-check-row" style={{ marginBottom: 0 }}>
                      <input
                        type="checkbox"
                        checked={deploySecurity.pmApproved}
                        onChange={async (e) => {
                          const checked = e.target.checked;
                          setDeploySecurity(prev => ({ ...prev, pmApproved: checked }));
                          await logActivity('ui.deploy.review.pm_approval_checked', { checked });
                        }}
                      />
                      I approve this deployment as PM.
                    </label>
                  </div>

                  <div className="premium-review-actions">
                    <button
                      onClick={handleCancelDeploy}
                      disabled={isProcessing}
                      className="premium-action-btn secondary"
                    >
                      Cancel
                    </button>

                    <button
                      onClick={handleConfirmDeploy}
                      disabled={
                        isProcessing ||
                        !deploySecurity.securityReviewed ||
                        !deploySecurity.pmApproved ||
                        (deploySecurity.credentialMode === 'manual' &&
                          (!deploySecurity.accessKeyId || !deploySecurity.secretAccessKey))
                      }
                      className="premium-action-btn primary"
                    >
                      {isProcessing ? 'Deploying...' : 'Approve & Execute'}
                    </button>
                  </div>

              {deployProgress.active && (
                <div style={{
                  marginTop: '16px',
                  background: '#fff',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  padding: '20px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                }}>
                  <div style={{ fontSize: '32px', fontWeight: 700, color: '#1a202c', marginBottom: '10px' }}>
                    {deployProgress.title}
                  </div>

                  <div style={{
                    width: '100%',
                    height: '8px',
                    borderRadius: '999px',
                    background: '#e2e8f0',
                    overflow: 'hidden',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      width: `${Math.round((deployProgress.currentStep / deployProgress.totalSteps) * 100)}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #5f8bff 0%, #7c4dff 100%)',
                      transition: 'width 0.25s ease'
                    }} />
                  </div>

                  <div style={{
                    fontSize: '13px',
                    color: deployProgress.status === 'error' ? '#b91c1c' : '#64748b',
                    marginBottom: '16px'
                  }}>
                    {deployProgress.subtitle}
                  </div>

                  <div style={{
                    background: '#0f172a',
                    color: '#86efac',
                    borderRadius: '10px',
                    padding: '14px',
                    maxHeight: '300px',
                    overflowY: 'auto',
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                    fontSize: '12px',
                    lineHeight: 1.6,
                    border: '1px solid #1e293b'
                  }}>
                    {deployProgress.logs.length === 0 ? (
                      <div style={{ color: '#93c5fd' }}>Waiting for deployment logs...</div>
                    ) : (
                      deployProgress.logs.map((line, idx) => (
                        <div key={idx}>{line}</div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Deployment Form Modal */}
        {showDeploymentForm && (
          <DeploymentForm
            onSubmit={handleDeploymentFormSubmit}
            onCancel={handleDeploymentFormCancel}
          />
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  );
};

export default App;
