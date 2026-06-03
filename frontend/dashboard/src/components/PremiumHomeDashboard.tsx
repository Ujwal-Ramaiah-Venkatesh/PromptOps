import React from 'react';
import './PremiumHomeDashboard.css';

interface PremiumHomeDashboardProps {
  onNavigate: (page: string) => void;
  onDeployClick?: () => void;
}

export const PremiumHomeDashboard: React.FC<PremiumHomeDashboardProps> = ({ onNavigate, onDeployClick }) => {
  const quickActions = [
    {
      icon: '🚀',
      title: 'Deploy Application',
      description: 'Deploy your infrastructure or DevOps tasks',
      action: () => onDeployClick ? onDeployClick() : onNavigate('deploy')
    },
    {
      icon: '⚙️',
      title: 'Configure Autonomy',
      description: 'Set up infrastructure monitoring with alerts for my production environment',
      action: () => onNavigate('autonomy')
    },
    {
      icon: '🔍',
      title: 'Discover & Scan',
      description: 'Analyze and catalog existing cloud infrastructure',
      action: () => onNavigate('discovery')
    },
    {
      icon: '📥',
      title: 'Ingest Configuration',
      description: 'Import infrastructure changes from manual changes into Terraform',
      action: () => onNavigate('ingestion')
    }
  ];

  const recommendedCommands = [
    'Deploy my frontend to AWS production',
    'Start AWS discovery scan for this account',
    'Configure medium-risk autonomy policy',
    'Ingest manual AWS changes into Terraform'
  ];

  const stats = [
    { icon: '🚀', value: '12', label: 'Active Deployments', color: '#8b5cf6' },
    { icon: '📊', value: '98.2%', label: 'System Health', color: '#10b981' },
    { icon: '⚡', value: '23s', label: 'Avg Response Time', color: '#3b82f6' },
    { icon: '💰', value: '$4,230', label: 'Monthly Cost', color: '#f59e0b' }
  ];

  const systemStatus = [
    { name: 'API Gateway', status: 'running' },
    { name: 'Parser Service', status: 'running' },
    { name: 'Autonomy ML', status: 'running' },
    { name: 'Discovery ML', status: 'running' },
    { name: 'Ingestion API', status: 'running' }
  ];

  return (
    <div className="premium-home-dashboard">
      {/* Header Section */}
      <div className="phd-header">
        <div className="phd-header-content">
          <h1 className="phd-title">
            Manage Cloud Infrastructure
            <br />
            <span className="phd-subtitle-text">in Plain English</span>
          </h1>
          <p className="phd-description">
            Deploy, scale, and manage infrastructure using plain-English commands
          </p>
          <div className="phd-header-actions">
            <button className="phd-btn phd-btn-primary">
              Get Started
            </button>
            <button className="phd-btn phd-btn-secondary">
              View Documentation
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="phd-content-grid">

        {/* Left Column - Quick Actions */}
        <div className="phd-column phd-column-main">

          {/* Welcome Card */}
          <div className="phd-card phd-welcome-card">
            <div className="phd-welcome-icon-container">
              <div className="phd-devops-background">
                <div className="phd-devops-icon">☁️</div>
                <div className="phd-devops-icon">🔒</div>
                <div className="phd-devops-icon">⚙️</div>
                <div className="phd-devops-icon">🚀</div>
                <div className="phd-devops-icon">📊</div>
                <div className="phd-devops-icon">🔄</div>
              </div>
            </div>
            <h2 className="phd-welcome-title">Welcome to PromptOps!</h2>
            <p className="phd-welcome-text">
              Your AI-powered platform for cloud infrastructure management.
            </p>
          </div>

          {/* Quick Start Section */}
          <div className="phd-section">
            <h3 className="phd-section-title">Start Here</h3>
            <div className="phd-quick-actions">
              {quickActions.map((action, index) => (
                <div
                  key={index}
                  className="phd-action-card"
                  onClick={action.action}
                >
                  <div className="phd-action-icon">{action.icon}</div>
                  <div className="phd-action-content">
                    <h4 className="phd-action-title">{action.title}</h4>
                    <p className="phd-action-desc">{action.description}</p>
                  </div>
                  <div className="phd-action-arrow">→</div>
                </div>
              ))}
            </div>
          </div>

          {/* Stats Grid */}
          <div className="phd-section">
            <h3 className="phd-section-title">System Overview</h3>
            <div className="phd-stats-grid">
              {stats.map((stat, index) => (
                <div key={index} className="phd-stat-card">
                  <div className="phd-stat-icon" style={{ color: stat.color }}>
                    {stat.icon}
                  </div>
                  <div className="phd-stat-content">
                    <div className="phd-stat-value">{stat.value}</div>
                    <div className="phd-stat-label">{stat.label}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommended Commands */}
          <div className="phd-section">
            <h3 className="phd-section-title">Recommended Commands</h3>
            <div className="phd-commands-list">
              {recommendedCommands.map((command, index) => (
                <div key={index} className="phd-command-item">
                  <div className="phd-command-icon">💬</div>
                  <div className="phd-command-text">{command}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - System Status */}
        <div className="phd-column phd-column-sidebar">

          {/* Quick Actions Summary */}
          <div className="phd-card">
            <h3 className="phd-card-title">⚡ Quick Actions</h3>
            <div className="phd-quick-list">
              <button className="phd-quick-btn">
                <span className="phd-quick-icon">🚀</span>
                <span>New Deployment</span>
              </button>
              <button className="phd-quick-btn">
                <span className="phd-quick-icon">📊</span>
                <span>View Analytics</span>
              </button>
              <button className="phd-quick-btn">
                <span className="phd-quick-icon">⚙️</span>
                <span>Settings</span>
              </button>
            </div>
          </div>

          {/* System Status */}
          <div className="phd-card">
            <h3 className="phd-card-title">🔧 System Status</h3>
            <div className="phd-status-list">
              {systemStatus.map((service, index) => (
                <div key={index} className="phd-status-item">
                  <div className="phd-status-dot"></div>
                  <span className="phd-status-name">{service.name}</span>
                  <span className="phd-status-badge">Running</span>
                </div>
              ))}
            </div>
          </div>

          {/* Documentation Link */}
          <div className="phd-card phd-docs-card">
            <div className="phd-docs-icon">📚</div>
            <h4 className="phd-docs-title">Need Help?</h4>
            <p className="phd-docs-text">
              Check out our documentation for detailed guides and tutorials.
            </p>
            <button className="phd-docs-btn">
              View Docs →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
