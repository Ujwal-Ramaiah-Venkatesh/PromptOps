# Quick WebSocket Testing Guide

## 🚀 Start Everything

### 1. Backend
```bash
cd api_gateway
python start_with_mock_db.py
```
WebSocket runs at: `ws://localhost:8000/ws?token=<JWT>`

### 2. Frontend
```bash
cd frontend/dashboard
npm run dev
```

## 🧪 Test Real-Time Features

### Test Deployment Progress
```bash
curl -X POST http://localhost:8000/api/v1/websocket/test/deployment-progress \
  -H "Content-Type: application/json" \
  -d '{"deployment_id": "deploy-123", "status": "running", "progress": 75}'
```

### Test Drift Alert
```bash
curl -X POST http://localhost:8000/api/v1/websocket/test/drift-alert \
  -H "Content-Type: application/json" \
  -d '{"resource_type": "ecs_service", "severity": "high", "auto_fixable": true}'
```

## ✅ What to Verify

1. **Connection**: Green "Live" indicator appears
2. **Progress Bar**: Updates to 75% instantly
3. **Drift Toast**: Red toast notification appears (top-right)
4. **Auto-Reconnect**: Restart backend, frontend reconnects automatically
5. **Logs**: Stream in real-time in log viewer
6. **Metrics**: Update live in dashboard

## 📁 Where to Look

- **Example Page**: `frontend/dashboard/src/examples/RealTimeIntegrationExample.tsx`
- **Components**: `frontend/dashboard/src/components/`
- **Hooks**: `frontend/dashboard/src/hooks/useWebSocket.ts`
- **Client**: `frontend/dashboard/src/websocket/WSClient.ts`

## 🎯 Success = All Real-Time Updates Working!
