#!/bin/bash

# Ensure Docker is accessible
if ! docker info > /dev/null 2>&1; then
    echo "Docker not accessible. Trying to fix DOCKER_HOST..."
    export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
    
    if ! docker info > /dev/null 2>&1; then
        echo "Docker still not accessible. Restarting Colima..."
        colima stop
        colima start
        # Wait a bit for socket to be ready
        sleep 5
        export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
    fi
fi

# Kill any existing processes
echo "Stopping existing services..."
lsof -ti:5000 | xargs kill -9 2>/dev/null
lsof -ti:5002 | xargs kill -9 2>/dev/null
lsof -ti:5003 | xargs kill -9 2>/dev/null
lsof -ti:5004 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start Redis
echo "Starting Redis..."
docker run -d --name livechat-redis -p 6379:6379 redis:alpine 2>/dev/null || docker start livechat-redis

# Start Postgres (if not running)
echo "Starting Postgres..."
docker run -d --name livechat-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:alpine 2>/dev/null || docker start livechat-db

# Wait for DB
sleep 3

# Export Env Vars
export DB_HOST=127.0.0.1
export DB_NAME=postgres
export DB_USER=postgres
export DB_PASS=postgres
export FLASK_SECRET=dev_secret
export REDIS_URL="redis://127.0.0.1:6379/0"
export AUTH_SERVICE_URL="http://127.0.0.1:5002"
# Nginx will be the entry point for Chat
export CHAT_SERVICE_URL="http://127.0.0.1:8080" 

# Start Auth Service
echo "Starting Auth Service (Port 5002)..."
PORT=5002 python3 services/auth_service.py > auth_service.log 2>&1 &

# Start Chat Service Instance 1
echo "Starting Chat Service 1 (Port 5003)..."
PORT=5003 python3 services/chat_service.py > chat_service_1.log 2>&1 &

# Start Chat Service Instance 2
echo "Starting Chat Service 2 (Port 5004)..."
PORT=5004 python3 services/chat_service.py > chat_service_2.log 2>&1 &

# Start Nginx
echo "Starting Nginx (Port 8080)..."
# We mount the local nginx.conf to the container
docker run -d --name livechat-nginx \
    -p 8080:8080 \
    -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
    --add-host=host.docker.internal:host-gateway \
    nginx:alpine 2>/dev/null || docker start livechat-nginx

echo "Scalable Demo is running!"
echo "Access via: http://127.0.0.1:8080"
