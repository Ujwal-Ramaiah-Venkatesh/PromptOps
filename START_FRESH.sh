#!/bin/bash

echo "=========================================="
echo "PromptOps - Fresh Start Script"
echo "=========================================="
echo ""

# Navigate to project root
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo "✓ Project root: $PROJECT_ROOT"
echo ""

# Step 1: Start Backend API
echo "Step 1/2: Starting Backend API on port 3800..."
cd "$PROJECT_ROOT/api_gateway"

# Start backend in background
nohup python -m uvicorn main:app --host 0.0.0.0 --port 3800 --reload > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!

echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  Logs: $PROJECT_ROOT/backend.log"

# Wait for backend to be ready
echo "  Waiting for backend to start..."
sleep 5

# Test backend
if curl -s http://localhost:3800/health > /dev/null; then
    echo "✓ Backend is healthy!"
else
    echo "✗ Backend failed to start. Check backend.log"
    exit 1
fi

echo ""

# Step 2: Start Frontend
echo "Step 2/2: Starting Frontend on port 3000..."
cd "$PROJECT_ROOT/frontend/dashboard"

# Start frontend in background
nohup npm run dev > "$PROJECT_ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo "  Logs: $PROJECT_ROOT/frontend.log"
echo ""

# Summary
echo "=========================================="
echo "✓ PromptOps is now running!"
echo "=========================================="
echo ""
echo "Backend API:  http://localhost:3800"
echo "  Health:     http://localhost:3800/health"
echo "  API Docs:   http://localhost:3800/docs"
echo ""
echo "Frontend:     http://localhost:3000"
echo ""
echo "Process IDs:"
echo "  Backend:    $BACKEND_PID"
echo "  Frontend:   $FRONTEND_PID"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend:    tail -f $PROJECT_ROOT/backend.log"
echo "  Frontend:   tail -f $PROJECT_ROOT/frontend.log"
echo ""
echo "=========================================="
