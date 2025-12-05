#!/bin/bash

# Configuration
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Resetting Database...${NC}"

# 1. Drop Tables
echo "Dropping all tables..."
export DB_HOST=localhost DB_NAME=postgres DB_USER=postgres DB_PASS=postgres FLASK_SECRET=dev_secret REDIS_URL=redis://127.0.0.1:6379/0
python3 reset_db.py

# 2. Re-initialize
echo -e "${GREEN}Re-initializing Database...${NC}"
python3 init_db.py

echo -e "${GREEN}Database reset complete!${NC}"
