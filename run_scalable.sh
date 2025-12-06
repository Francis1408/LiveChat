#!/bin/bash

# Function to check if Docker is responsive
check_docker() {
    docker info > /dev/null 2>&1
    return $?
}

echo "Initializing Docker environment..."

# 1. Get Colima Socket
echo "Checking Colima status..."
COLIMA_STATUS_OUTPUT=$(colima status 2>&1)
echo "Starting/Restarting Colima..."
colima stop > /dev/null 2>&1
colima start

# Re-fetch socket
COLIMA_STATUS_OUTPUT=$(colima status 2>&1)
COLIMA_SOCKET=$(echo "$COLIMA_STATUS_OUTPUT" | grep "socket:" | sed -n 's/.*socket: \(unix:\/\/[^[:space:]"]*\).*/\1/p')

# 2. Configure Environment
if [ -n "$COLIMA_SOCKET" ]; then
    export DOCKER_HOST="$COLIMA_SOCKET"
    echo "Set DOCKER_HOST=$DOCKER_HOST"
fi

# 3. Check again, if still failing, restart Colima
if ! check_docker; then
    echo "Docker still not accessible with socket $COLIMA_SOCKET. Restarting Colima..."
    colima stop
    colima start
    
    # Re-fetch socket in case it changed
    COLIMA_STATUS_OUTPUT=$(colima status 2>&1)
    if echo "$COLIMA_STATUS_OUTPUT" | grep -q "socket:"; then
        COLIMA_SOCKET=$(echo "$COLIMA_STATUS_OUTPUT" | grep "socket:" | sed -n 's/.*socket: \(unix:\/\/[^[:space:]"]*\).*/\1/p')
        export DOCKER_HOST="$COLIMA_SOCKET"
        echo "New DOCKER_HOST=$DOCKER_HOST"
    fi
fi

# 4. Wait for Docker Readiness
echo "Verifying Docker connection..."
MAX_RETRIES=5 #30 was too long
COUNT=0
while ! check_docker; do
    sleep 1
    echo -n "."
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
         echo ""
         echo "Error: Docker did not become ready after $MAX_RETRIES seconds."
         echo "Last DOCKER_HOST: $DOCKER_HOST"
         exit 1
    fi
done
echo ""
echo "Docker is ready!"
docker version --format 'Server Version: {{.Server.Version}}'

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

# Wait for DB to be ready
echo "Waiting for Postgres to be ready..."
until docker exec livechat-db pg_isready -U postgres > /dev/null 2>&1; do
  echo -n "."
  sleep 1
done
echo ""
echo "Postgres is ready!"

# Initialize Database Schema
echo "Initializing Database Schema..."
# We need to run init_db.py. It connects to localhost:5432 which is now forwarded to the container.
# Ensure required env vars are set for the script (though it loads from .env, exports here override/ensure)
export DB_HOST=127.0.0.1
export DB_NAME=postgres
export DB_USER=postgres
export DB_PASS=postgres
./venv/bin/python3 init_db.py

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
PORT=5002 ./venv/bin/python3 services/auth_service.py > auth_service.log 2>&1 &

# Start Chat Service Instance 1
echo "Starting Chat Service 1 (Port 5003)..."
PORT=5003 ./venv/bin/python3 services/chat_service.py > chat_service_1.log 2>&1 &

# Start Chat Service Instance 2
echo "Starting Chat Service 2 (Port 5004)..."
PORT=5004 ./venv/bin/python3 services/chat_service.py > chat_service_2.log 2>&1 &

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
