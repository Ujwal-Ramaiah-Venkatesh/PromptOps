/**
 * Real-Time Integration Example
 * ==============================
 *
 * Complete example showing how to integrate all WebSocket
 * real-time components in a React application.
 *
 * This demonstrates:
 * - WebSocket connection setup
 * - Live log viewer
 * - Deployment progress tracking
 * - Drift alert notifications
 * - Real-time metrics dashboard
 *
 * @author PromptOps Team - Q3 2026
 * @date July 8, 2026
 */

import React, { useState } from 'react';
import LiveLogViewer from '../components/LiveLogViewer';
import DeploymentProgressBar from '../components/DeploymentProgressBar';
import DriftAlertToast from '../components/DriftAlertToast';
import RealTimeMetricsDashboard from '../components/RealTimeMetricsDashboard';

/**
 * Example Page Component
 *
 * This shows a complete real-time monitoring dashboard
 * with all WebSocket features integrated.
 */
export const RealTimeMonitoringPage: React.FC = () => {
  const [currentDeploymentId, setCurrentDeploymentId] = useState<string>('deploy-123');

  const handleDeploymentComplete = (status: string) => {
    console.log(`Deployment completed with status: ${status}`);
    // Could trigger notification, update UI, etc.
  };

  const handleFixDrift = (alert: any) => {
    console.log('Auto-fixing drift:', alert);
    // Call API to auto-fix the drift
    // Example: api.post('/api/v1/drift/fix', { alert_id: alert.id })
  };

  const handleViewDriftDetails = (alert: any) => {
    console.log('Viewing drift details:', alert);
    // Navigate to drift details page
    // Example: navigate(`/drift/${alert.id}`)
  };

  return (
    <div style={{ padding: '24px', backgroundColor: '#f9fafb', minHeight: '100vh' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#1f2937', margin: 0 }}>
          Real-Time Monitoring Dashboard
        </h1>
        <p style={{ fontSize: '16px', color: '#6b7280', marginTop: '8px' }}>
          Live infrastructure monitoring with WebSocket updates
        </p>
      </div>

      {/* Drift Alert Toasts (floating notifications) */}
      <DriftAlertToast
        onFixDrift={handleFixDrift}
        onViewDetails={handleViewDriftDetails}
        autoHideDelay={0} // 0 = manual dismiss only
      />

      {/* Main Content Grid */}
      <div style={{ display: 'grid', gap: '24px' }}>
        {/* Deployment Progress Section */}
        <section>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
            Active Deployment
          </h2>
          <DeploymentProgressBar
            deploymentId={currentDeploymentId}
            onComplete={handleDeploymentComplete}
          />
        </section>

        {/* Two Column Layout */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(600px, 1fr))',
          gap: '24px',
        }}>
          {/* Live Logs Section */}
          <section>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
              Deployment Logs
            </h2>
            <div style={{ height: '400px', backgroundColor: 'white', borderRadius: '8px', overflow: 'hidden' }}>
              <LiveLogViewer
                deploymentId={currentDeploymentId}
                maxLogs={500}
                autoScroll={true}
              />
            </div>
          </section>

          {/* Metrics Section */}
          <section>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
              Infrastructure Metrics
            </h2>
            <RealTimeMetricsDashboard />
          </section>
        </div>
      </div>
    </div>
  );
};

/**
 * Example: Integration in App.tsx
 * ================================
 *
 * To use the WebSocket components in your app:
 *
 * ```tsx
 * import React from 'react';
 * import { BrowserRouter, Routes, Route } from 'react-router-dom';
 * import { RealTimeMonitoringPage } from './examples/RealTimeIntegrationExample';
 *
 * function App() {
 *   return (
 *     <BrowserRouter>
 *       <Routes>
 *         <Route path="/monitoring" element={<RealTimeMonitoringPage />} />
 *         {/* Other routes... *\/}
 *       </Routes>
 *     </BrowserRouter>
 *   );
 * }
 *
 * export default App;
 * ```
 */

/**
 * Example: Individual Component Usage
 * ====================================
 */

// 1. Live Log Viewer - Standalone
export const LogViewerExample: React.FC = () => {
  return (
    <div style={{ height: '500px' }}>
      <LiveLogViewer
        deploymentId="deploy-123"
        maxLogs={1000}
        autoScroll={true}
      />
    </div>
  );
};

// 2. Deployment Progress - Standalone
export const ProgressExample: React.FC = () => {
  return (
    <DeploymentProgressBar
      deploymentId="deploy-123"
      onComplete={(status) => {
        console.log('Deployment finished:', status);
      }}
    />
  );
};

// 3. Drift Alerts - Standalone
export const DriftAlertsExample: React.FC = () => {
  return (
    <DriftAlertToast
      onFixDrift={(alert) => {
        console.log('Fix drift:', alert);
      }}
      onViewDetails={(alert) => {
        console.log('View details:', alert);
      }}
      autoHideDelay={10000} // Auto-hide after 10 seconds
    />
  );
};

// 4. Metrics Dashboard - Standalone
export const MetricsExample: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <RealTimeMetricsDashboard />
    </div>
  );
};

/**
 * Example: Custom Hook Usage
 * ===========================
 *
 * You can also use the hooks directly for custom components:
 */

import {
  useDeploymentProgress,
  useDeploymentLogs,
  useDriftAlerts,
  useRealTimeMetrics,
} from '../hooks/useWebSocket';

export const CustomComponent: React.FC = () => {
  // Get deployment progress
  const { progress, isConnected: progressConnected } = useDeploymentProgress('deploy-123');

  // Get live logs
  const { logs, clearLogs, isConnected: logsConnected } = useDeploymentLogs('deploy-123');

  // Get drift alerts
  const { alerts, clearAlert, clearAll } = useDriftAlerts();

  // Get real-time metrics
  const { metrics, lastUpdate } = useRealTimeMetrics();

  return (
    <div>
      <h3>Custom Real-Time Component</h3>

      {/* Show progress percentage */}
      {progress && (
        <div>
          Deployment Progress: {progress.progress}% - {progress.current_step}
        </div>
      )}

      {/* Show latest log */}
      {logs.length > 0 && (
        <div>
          Latest Log: {logs[logs.length - 1].message}
        </div>
      )}

      {/* Show drift alert count */}
      <div>Active Drift Alerts: {alerts.length}</div>

      {/* Show CPU usage */}
      {metrics && (
        <div>CPU Usage: {metrics.cpu_usage}%</div>
      )}
    </div>
  );
};

/**
 * Testing the WebSocket Connection
 * =================================
 *
 * To test your WebSocket integration:
 *
 * 1. Start the backend server:
 *    ```bash
 *    python api_gateway/start_with_mock_db.py
 *    ```
 *
 * 2. Use the test endpoints to emit events:
 *    ```bash
 *    # Test deployment progress
 *    curl -X POST http://localhost:8000/api/v1/websocket/test/deployment-progress \
 *      -H "Content-Type: application/json" \
 *      -d '{"deployment_id": "deploy-123", "progress": 50}'
 *
 *    # Test drift alert
 *    curl -X POST http://localhost:8000/api/v1/websocket/test/drift-alert \
 *      -H "Content-Type: application/json" \
 *      -d '{"resource_type": "ecs_service", "severity": "high"}'
 *    ```
 *
 * 3. Watch your frontend components update in real-time!
 */

export default RealTimeMonitoringPage;
