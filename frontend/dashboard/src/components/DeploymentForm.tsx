import React, { useState } from 'react';

interface DeploymentFormProps {
  onSubmit: (deploymentDetails: { command: string; repoUrl: string }) => void;
  onCancel: () => void;
}

export const DeploymentForm: React.FC<DeploymentFormProps> = ({ onSubmit, onCancel }) => {
  const [command, setCommand] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [errors, setErrors] = useState<{ command?: string; repoUrl?: string }>({});

  const validateGitHubUrl = (url: string): boolean => {
    const githubPattern = /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+\/?$/;
    return githubPattern.test(url.trim());
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: { command?: string; repoUrl?: string } = {};

    // Validate command
    if (!command.trim()) {
      newErrors.command = 'Please enter a deployment command';
    } else if (!command.toLowerCase().includes('deploy')) {
      newErrors.command = 'Command must include "deploy"';
    }

    // Validate GitHub URL
    if (!repoUrl.trim()) {
      newErrors.repoUrl = 'Please enter a GitHub repository URL';
    } else if (!validateGitHubUrl(repoUrl)) {
      newErrors.repoUrl = 'Please enter a valid GitHub URL (e.g., https://github.com/username/repo)';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Clear errors and submit
    setErrors({});
    onSubmit({ command: command.trim(), repoUrl: repoUrl.trim() });
  };

  const exampleCommands = [
    'Deploy my frontend to AWS production',
    'Deploy backend service to staging',
    'Deploy mobile app to AWS S3',
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        maxWidth: '600px',
        width: '100%',
        padding: '32px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{
            fontSize: '28px',
            fontWeight: '700',
            color: '#1a202c',
            marginBottom: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <span style={{ fontSize: '32px' }}>🚀</span>
            New Deployment
          </h2>
          <p style={{ color: '#64748b', fontSize: '15px', margin: 0 }}>
            Enter deployment details to proceed with PM approval workflow
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Deployment Command */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '600',
              color: '#334155',
              marginBottom: '8px'
            }}>
              Deployment Command *
            </label>
            <input
              type="text"
              value={command}
              onChange={(e) => {
                setCommand(e.target.value);
                if (errors.command) setErrors({ ...errors, command: undefined });
              }}
              placeholder="e.g., Deploy my frontend to AWS production"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: errors.command ? '2px solid #ef4444' : '2px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '15px',
                outline: 'none',
                transition: 'border-color 0.2s',
                boxSizing: 'border-box'
              }}
              onFocus={(e) => {
                if (!errors.command) e.currentTarget.style.borderColor = '#3b82f6';
              }}
              onBlur={(e) => {
                if (!errors.command) e.currentTarget.style.borderColor = '#e2e8f0';
              }}
            />
            {errors.command && (
              <p style={{ color: '#ef4444', fontSize: '13px', marginTop: '6px', marginBottom: 0 }}>
                {errors.command}
              </p>
            )}

            {/* Example commands */}
            <div style={{ marginTop: '12px' }}>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '8px' }}>
                Example commands:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {exampleCommands.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setCommand(example)}
                    style={{
                      padding: '8px 12px',
                      background: '#f1f5f9',
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px',
                      fontSize: '13px',
                      color: '#475569',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#e0e7ff';
                      e.currentTarget.style.borderColor = '#818cf8';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#f1f5f9';
                      e.currentTarget.style.borderColor = '#e2e8f0';
                    }}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* GitHub Repository URL */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '600',
              color: '#334155',
              marginBottom: '8px'
            }}>
              GitHub Repository URL *
            </label>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => {
                setRepoUrl(e.target.value);
                if (errors.repoUrl) setErrors({ ...errors, repoUrl: undefined });
              }}
              placeholder="https://github.com/username/repository"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: errors.repoUrl ? '2px solid #ef4444' : '2px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '15px',
                outline: 'none',
                transition: 'border-color 0.2s',
                boxSizing: 'border-box'
              }}
              onFocus={(e) => {
                if (!errors.repoUrl) e.currentTarget.style.borderColor = '#3b82f6';
              }}
              onBlur={(e) => {
                if (!errors.repoUrl) e.currentTarget.style.borderColor = '#e2e8f0';
              }}
            />
            {errors.repoUrl && (
              <p style={{ color: '#ef4444', fontSize: '13px', marginTop: '6px', marginBottom: 0 }}>
                {errors.repoUrl}
              </p>
            )}
            <p style={{ fontSize: '13px', color: '#64748b', marginTop: '6px', marginBottom: 0 }}>
              Enter the full GitHub repository URL for the application you want to deploy
            </p>
          </div>

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            gap: '12px',
            justifyContent: 'flex-end'
          }}>
            <button
              type="button"
              onClick={onCancel}
              style={{
                padding: '12px 24px',
                background: '#f1f5f9',
                border: 'none',
                borderRadius: '8px',
                fontSize: '15px',
                fontWeight: '600',
                color: '#475569',
                cursor: 'pointer',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#e2e8f0'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#f1f5f9'}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                padding: '12px 24px',
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                border: 'none',
                borderRadius: '8px',
                fontSize: '15px',
                fontWeight: '600',
                color: 'white',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              Continue to Approval
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
