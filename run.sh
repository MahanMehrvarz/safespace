#!/bin/bash

# PractAI Startup Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting PractAI...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}⚠️  .env file not found!${NC}"
    echo -e "${YELLOW}Copying .env.example to .env...${NC}"
    cp .env.example .env
    echo -e "${RED}Please edit .env with your API keys before running!${NC}"
    exit 1
fi

# Start the server
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo -e "${YELLOW}Access the application at: http://localhost:8000${NC}"
echo ""
python api/main.py
