import React, { useState } from 'react';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './components/LoginPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AutonomySettings } from './pages/AutonomySettings';
import { DiscoveryDashboard } from './pages/DiscoveryDashboard';
import { IngestionWorkflow } from './pages/IngestionWorkflow';
import { apiClient } from './api/client';

type Page = 'home' | 'autonomy' | 'discovery' | 'ingestion';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [commandInput, setCommandInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [commandResult, setCommandResult] = useState<any>(null);

  const handleCommandSubmit = async () => {
    if (!commandInput.trim() || isProcessing) return;

    setIsProcessing(true);
    setCommandResult(null);

    try {
      // Parse the command
      const parseResponse = await apiClient.post('/api/v1/parser/parse', {
        command: commandInput
      });

      setCommandResult({
        success: true,
        parsed: parseResponse,
        message: `Command parsed successfully! Intent: ${parseResponse.intent_type}`
      });

      // Show success message
      setTimeout(() => {
        setCommandResult(null);
        setCommandInput('');
      }, 5000);

    } catch (error: any) {
      setCommandResult({
        success: false,
        message: error.message || 'Failed to process command'
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

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Navbar */}
      <nav style={{
        background: 'white',
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => setCurrentPage('home')}>
            <div style={{
              width: '40px',
              height: '40px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
              fontWeight: 'bold',
              color: 'white'
            }}>P</div>
            <span style={{ fontSize: '20px', fontWeight: '700', color: '#1a202c' }}>PromptOps</span>
          </div>

          {/* Navigation Menu */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setCurrentPage('home')}
              style={{
                padding: '8px 16px',
                background: currentPage === 'home' ? '#eef2ff' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: currentPage === 'home' ? '#667eea' : '#718096',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              🏠 Home
            </button>
            <button
              onClick={() => setCurrentPage('autonomy')}
              style={{
                padding: '8px 16px',
                background: currentPage === 'autonomy' ? '#eef2ff' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: currentPage === 'autonomy' ? '#667eea' : '#718096',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              ⚙️ Autonomy
            </button>
            <button
              onClick={() => setCurrentPage('discovery')}
              style={{
                padding: '8px 16px',
                background: currentPage === 'discovery' ? '#eef2ff' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: currentPage === 'discovery' ? '#667eea' : '#718096',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              🔍 Discovery
            </button>
            <button
              onClick={() => setCurrentPage('ingestion')}
              style={{
                padding: '8px 16px',
                background: currentPage === 'ingestion' ? '#eef2ff' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: currentPage === 'ingestion' ? '#667eea' : '#718096',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              📥 Ingestion
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ color: '#718096', fontSize: '14px' }}>{user?.full_name || user?.role.toUpperCase()}</span>
          <div style={{
            width: '40px',
            height: '40px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: '600'
          }}>{user?.email.charAt(0).toUpperCase()}</div>
          <button
            onClick={logout}
            style={{
              padding: '8px 16px',
              background: 'transparent',
              border: '2px solid #e2e8f0',
              borderRadius: '6px',
              color: '#4a5568',
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
      <div style={{
        flex: 1,
        width: '100%'
      }}>
        {/* Route to different pages */}
        {currentPage === 'autonomy' && <AutonomySettings />}
        {currentPage === 'discovery' && <DiscoveryDashboard />}
        {currentPage === 'ingestion' && <IngestionWorkflow />}

        {/* Home Page */}
        {currentPage === 'home' && (
          <div style={{
            padding: '32px',
            maxWidth: '1400px',
            margin: '0 auto',
            width: '100%'
          }}>
            {/* Welcome Card */}
            <div style={{
              background: 'white',
              padding: '32px',
              borderRadius: '12px',
              marginBottom: '32px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
            }}>
              <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1a202c', marginBottom: '8px' }}>
                Welcome to PromptOps! 👋
              </h2>
              <p style={{ color: '#718096', fontSize: '14px' }}>
                Your AI-powered DevOps platform is ready. Type commands in natural language.
              </p>
            </div>

            {/* Command Input Card */}
            <div style={{
              background: 'white',
              padding: '32px',
              borderRadius: '12px',
              marginBottom: '32px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c', marginBottom: '16px' }}>
                What would you like to do?
              </h3>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Deploy Flipkar application on AWS..."
                  disabled={isProcessing}
                  style={{
                    width: '100%',
                    padding: '16px 60px 16px 16px',
                    border: '2px solid #e2e8f0',
                    borderRadius: '8px',
                    fontSize: '16px',
                    outline: 'none',
                    opacity: isProcessing ? 0.6 : 1
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#667eea'}
                  onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
                />
                <button
                  onClick={handleCommandSubmit}
                  disabled={!commandInput.trim() || isProcessing}
                  style={{
                    position: 'absolute',
                    right: '8px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: isProcessing || !commandInput.trim() ? '#cbd5e0' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                    padding: '10px 20px',
                    borderRadius: '6px',
                    cursor: isProcessing || !commandInput.trim() ? 'not-allowed' : 'pointer',
                    fontWeight: '600'
                  }}
                >
                  {isProcessing ? 'Processing...' : 'Send'}
                </button>
              </div>

              {/* Command Result */}
              {commandResult && (
                <div style={{
                  marginTop: '16px',
                  padding: '16px',
                  borderRadius: '8px',
                  background: commandResult.success ? '#f0fdf4' : '#fef2f2',
                  border: `2px solid ${commandResult.success ? '#86efac' : '#fca5a5'}`
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '8px'
                  }}>
                    <span style={{ fontSize: '20px' }}>{commandResult.success ? '✅' : '❌'}</span>
                    <strong style={{ color: commandResult.success ? '#166534' : '#991b1b' }}>
                      {commandResult.success ? 'Success!' : 'Error'}
                    </strong>
                  </div>
                  <p style={{ color: commandResult.success ? '#166534' : '#991b1b', margin: 0 }}>
                    {commandResult.message}
                  </p>
                  {commandResult.parsed && (
                    <div style={{ marginTop: '12px', fontSize: '14px', color: '#166534' }}>
                      <div><strong>Service:</strong> {commandResult.parsed.target_service || 'N/A'}</div>
                      <div><strong>Environment:</strong> {commandResult.parsed.target_env || 'N/A'}</div>
                      {commandResult.parsed.parameters && Object.keys(commandResult.parsed.parameters).length > 0 && (
                        <div><strong>Parameters:</strong> {JSON.stringify(commandResult.parsed.parameters)}</div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Quick Actions */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '16px',
                marginTop: '16px'
              }}>
                {[
                  { text: '🚀 Deploy frontend v2.0 to staging', page: 'home' as Page },
                  { text: '📈 Scale backend to 10 instances', page: 'home' as Page },
                  { text: '⚙️ Configure autonomy settings', page: 'autonomy' as Page },
                  { text: '🔍 Start AWS discovery scan', page: 'discovery' as Page }
                ].map((action, i) => (
                  <button
                    key={i}
                    onClick={() => setCurrentPage(action.page)}
                    style={{
                      padding: '12px 16px',
                      background: '#f7fafc',
                      border: '2px solid #e2e8f0',
                      borderRadius: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      color: '#4a5568',
                      fontSize: '14px'
                    }}
                  >
                    {action.text}
                  </button>
                ))}
              </div>
            </div>

            {/* Stats Grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '24px',
              marginBottom: '32px'
            }}>
              {[
                { icon: '🚀', label: 'Deployments Today', value: '12', color: '#667eea' },
                { icon: '✓', label: 'Success Rate', value: '98.2%', color: '#34a853' },
                { icon: '⏱', label: 'Avg Response', value: '2.1s', color: '#f9ab00' },
                { icon: '💰', label: 'Monthly Cost', value: '$4,230', color: '#ea4335' }
              ].map((stat, i) => (
                <div key={i} style={{
                  background: 'white',
                  padding: '24px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '24px',
                    marginBottom: '16px',
                    background: `${stat.color}20`,
                    color: stat.color
                  }}>{stat.icon}</div>
                  <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>{stat.label}</div>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#1a202c' }}>{stat.value}</div>
                </div>
              ))}
            </div>

            {/* Enhancement Cards */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '24px',
              marginBottom: '32px'
            }}>
              <div
                onClick={() => setCurrentPage('autonomy')}
                style={{
                  background: 'white',
                  padding: '24px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  cursor: 'pointer',
                  border: '2px solid transparent',
                  transition: 'border 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = '#667eea'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
              >
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>⚙️</div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c', marginBottom: '8px' }}>
                  Autonomy Settings
                </h3>
                <p style={{ fontSize: '14px', color: '#718096', marginBottom: '12px' }}>
                  Configure risk-based auto-execution tiers to reduce approval fatigue by 80%
                </p>
                <div style={{ fontSize: '12px', color: '#667eea', fontWeight: '600' }}>
                  ENHANCEMENT-001 →
                </div>
              </div>

              <div
                onClick={() => setCurrentPage('discovery')}
                style={{
                  background: 'white',
                  padding: '24px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  cursor: 'pointer',
                  border: '2px solid transparent',
                  transition: 'border 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = '#667eea'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
              >
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔍</div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c', marginBottom: '8px' }}>
                  Discovery & Onboarding
                </h3>
                <p style={{ fontSize: '14px', color: '#718096', marginBottom: '12px' }}>
                  Scan AWS accounts, infer context, and onboard infrastructure in 2 hours vs 3 weeks
                </p>
                <div style={{ fontSize: '12px', color: '#667eea', fontWeight: '600' }}>
                  ENHANCEMENT-003 →
                </div>
              </div>

              <div
                onClick={() => setCurrentPage('ingestion')}
                style={{
                  background: 'white',
                  padding: '24px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  cursor: 'pointer',
                  border: '2px solid transparent',
                  transition: 'border 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = '#667eea'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
              >
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>📥</div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c', marginBottom: '8px' }}>
                  Infrastructure Ingestion
                </h3>
                <p style={{ fontSize: '14px', color: '#718096', marginBottom: '12px' }}>
                  Import manual AWS Console changes into Terraform to maintain single source of truth
                </p>
                <div style={{ fontSize: '12px', color: '#667eea', fontWeight: '600' }}>
                  ENHANCEMENT-002 →
                </div>
              </div>
            </div>

            {/* System Status */}
            <div style={{
              background: 'white',
              padding: '32px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c', marginBottom: '24px' }}>
                System Status
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {[
                  { service: 'API Gateway', status: 'Running', port: '8000' },
                  { service: 'React Dashboard', status: 'Running', port: '5173' },
                  { service: 'Autonomy API', status: 'Connected', port: '-' },
                  { service: 'Discovery API', status: 'Connected', port: '-' },
                  { service: 'Ingestion API', status: 'Connected', port: '-' }
                ].map((item, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '16px',
                    background: '#f7fafc',
                    borderRadius: '8px'
                  }}>
                    <div>
                      <div style={{ fontWeight: '600', color: '#1a202c' }}>{item.service}</div>
                      <div style={{ fontSize: '13px', color: '#718096' }}>Port: {item.port}</div>
                    </div>
                    <div style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '600',
                      background: 'rgba(52, 168, 83, 0.1)',
                      color: '#34a853'
                    }}>
                      ✓ {item.status}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
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
