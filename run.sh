#!/bin/bash

echo "Starting Docker containers (Qdrant & Redis)..."
docker compose up -d

echo "Starting Backend (FastAPI)..."
# Activate the virtual environment and start the backend in the background
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend (Next.js)..."
# Navigate to the frontend directory and start the frontend in the background
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================================"
echo "All services started successfully!"
echo "Backend is running at: http://localhost:8000"
echo "Frontend is running at: http://localhost:3005"
echo "Press Ctrl+C to stop all services."
echo "========================================================"
echo ""

# Trap Ctrl+C (SIGINT) and SIGTERM to kill background processes gracefully
trap "echo ''; echo 'Stopping all services...'; kill $BACKEND_PID $FRONTEND_PID; cd ..; docker compose stop; exit" SIGINT SIGTERM

# Wait for background processes so the script doesn't exit immediately
wait $BACKEND_PID $FRONTEND_PID
