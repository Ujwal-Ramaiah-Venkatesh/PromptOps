import React from 'react';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './components/LoginPage';
import { ProtectedRoute } from './components/ProtectedRoute';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

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
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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
              placeholder="Deploy frontend v2.0 to staging..."
              style={{
                width: '100%',
                padding: '16px 60px 16px 16px',
                border: '2px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '16px',
                outline: 'none'
              }}
              onFocus={(e) => e.target.style.borderColor = '#667eea'}
              onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
            />
            <button style={{
              position: 'absolute',
              right: '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600'
            }}>Send</button>
          </div>

          {/* Quick Actions */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '16px',
            marginTop: '16px'
          }}>
            {[
              '🚀 Deploy frontend v2.0 to staging',
              '📈 Scale backend to 10 instances',
              '💰 Show AWS cost breakdown',
              '🔍 Check database performance'
            ].map((action, i) => (
              <button key={i} style={{
                padding: '12px 16px',
                background: '#f7fafc',
                border: '2px solid #e2e8f0',
                borderRadius: '8px',
                textAlign: 'left',
                cursor: 'pointer',
                color: '#4a5568',
                fontSize: '14px'
              }}>{action}</button>
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
              { service: 'React Dashboard', status: 'Running', port: '3001' },
              { service: 'Backend Integration', status: 'Connected', port: '-' }
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
