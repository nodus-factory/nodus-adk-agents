#!/bin/bash

# 🚀 Start All A2A Agents with Langfuse Observability
# This script starts all 5 A2A agents in the background with proper observability configuration

set -e

# Export Langfuse configuration (accessible from host machine)
export LANGFUSE_HOST="http://localhost:3000"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:3000/api/public/ingestion"
export LANGFUSE_PUBLIC_KEY="pk-lf-a401fb0c-6ee3-4636-afd4-803b9dfe4aaf"
export LANGFUSE_SECRET_KEY="sk-lf-ccb62e83-9148-49f8-8858-ff3c963bb7a8"
export ENVIRONMENT="development"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting A2A Agents with Langfuse Observability${NC}"
echo -e "${BLUE}=================================================${NC}\n"

# Function to start an agent
start_agent() {
    local agent_name=$1
    local port=$2
    local module=$3
    
    echo -e "${GREEN}✓ Starting ${agent_name} on port ${port}...${NC}"
    
    # Kill existing process if running
    lsof -ti :${port} | xargs kill -9 2>/dev/null || true
    
    # Start agent in background
    python -m ${module} > logs/${agent_name}.log 2>&1 &
    
    echo "  PID: $!"
    sleep 0.5
}

# Create logs directory
mkdir -p logs

# Start all agents
start_agent "weather_agent" 8001 "nodus_adk_agents.a2a_weather_agent"
start_agent "currency_agent" 8002 "nodus_adk_agents.a2a_currency_agent"
start_agent "calculator_agent" 8003 "nodus_adk_agents.a2a_calculator_agent"
start_agent "email_agent" 8004 "nodus_adk_agents.a2a_email_agent"
start_agent "hitl_math_agent" 8005 "nodus_adk_agents.a2a_hitl_math_agent"

echo -e "\n${GREEN}✅ All A2A agents started successfully!${NC}"
echo -e "${BLUE}=================================================${NC}\n"

echo "📊 Agent endpoints:"
echo "  • Weather:    http://localhost:8001"
echo "  • Currency:   http://localhost:8002"
echo "  • Calculator: http://localhost:8003"
echo "  • Email:      http://localhost:8004"
echo "  • HITL Math:  http://localhost:8005"

echo -e "\n📝 Logs available in: logs/"
echo -e "🔍 Langfuse UI: http://localhost:3000\n"

echo "💡 To stop all agents:"
echo "   kill \$(lsof -ti :8001,:8002,:8003,:8004,:8005)"

