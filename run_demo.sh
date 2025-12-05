#!/bin/bash

# Configuration
DB_CONTAINER_NAME="postgres_alpine"
DB_PASSWORD="postgres"
DB_PORT="5432"
AUTH_PORT="5002"
CHAT_PORT="5003"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LiveChat Demo Setup...${NC}"

# 0. Cleanup Ports
echo -e "${GREEN}[0/5] Cleaning up ports...${NC}"
lsof -ti:$AUTH_PORT | xargs kill -9 2>/dev/null
lsof -ti:$CHAT_PORT | xargs kill -9 2>/dev/null


# 1. Database Setup
echo -e "${GREEN}[1/5] Checking Database...${NC}"
if [ ! "$(docker ps -a -q -f name=$DB_CONTAINER_NAME)" ]; then
    echo "Creating PostgreSQL container..."
    docker run --name $DB_CONTAINER_NAME -e POSTGRES_PASSWORD=$DB_PASSWORD -d -p $DB_PORT:5432 postgres:alpine
elif [ "$(docker ps -aq -f status=exited -f name=$DB_CONTAINER_NAME)" ]; then
    echo "Starting existing PostgreSQL container..."
    docker start $DB_CONTAINER_NAME
else
    echo "PostgreSQL container is already running."
fi

# Wait for DB to be ready
echo "Waiting for database to be ready..."
sleep 3 # Give it a moment to start up

# 2. Initialize Database
echo -e "${GREEN}[2/5] Initializing Database...${NC}"
export DB_HOST=localhost DB_NAME=postgres DB_USER=postgres DB_PASS=postgres FLASK_SECRET=dev_secret
export AUTH_SERVICE_URL="http://127.0.0.1:$AUTH_PORT"
export CHAT_SERVICE_URL="http://127.0.0.1:$CHAT_PORT"
python3 init_db.py

# 3. Start Services
echo -e "${GREEN}[3/5] Starting Auth Service...${NC}"
echo -e "${GREEN}[3/5] Starting Auth Service...${NC}"
PORT=$AUTH_PORT python3 services/auth_service.py > auth_service.log 2>&1 &
AUTH_PID=$!
echo "Auth Service started (PID: $AUTH_PID)"

echo -e "${GREEN}[4/5] Starting Chat Service...${NC}"
echo -e "${GREEN}[4/5] Starting Chat Service...${NC}"
PORT=$CHAT_PORT python3 services/chat_service.py > chat_service.log 2>&1 &
CHAT_PID=$!
echo "Chat Service started (PID: $CHAT_PID)"

# 4. Open Browser
echo -e "${GREEN}[5/5] Opening Browser...${NC}"
sleep 2 # Wait for services to bind ports
open "http://127.0.0.1:$AUTH_PORT"

echo -e "${GREEN}Demo is running!${NC}"
echo "Press Ctrl+C to stop all services."

# Cleanup function
cleanup() {
    echo -e "\n${RED}Stopping services...${NC}"
    kill $AUTH_PID
    kill $CHAT_PID
    # Optional: Stop DB
    # docker stop $DB_CONTAINER_NAME
    echo "Services stopped."
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

# Keep script running
wait
