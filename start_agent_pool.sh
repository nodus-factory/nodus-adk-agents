#!/bin/bash

# 🚀 Start Agent Pool Manager
# Centralitza tots els agents A2A en un sol procés

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
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Agent Pool Manager${NC}"
echo -e "${BLUE}================================${NC}\n"

# Check if config exists
CONFIG_FILE="config/agent_pool.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠️  Config file not found: $CONFIG_FILE${NC}"
    echo "Creating default config..."
    mkdir -p config
    cat > "$CONFIG_FILE" << 'EOF'
{
  "pool": {
    "name": "nodus-core-agents",
    "description": "Core A2A agents for Nodus OS",
    "version": "1.0.0"
  },
  "agents": [
    {
      "name": "weather",
      "module_path": "nodus_adk_agents.a2a_weather_agent",
      "enabled": true
    },
    {
      "name": "currency",
      "module_path": "nodus_adk_agents.a2a_currency_agent",
      "enabled": true
    },
    {
      "name": "calculator",
      "module_path": "nodus_adk_agents.a2a_calculator_agent",
      "enabled": true
    },
    {
      "name": "email",
      "module_path": "nodus_adk_agents.a2a_email_agent",
      "enabled": true
    },
    {
      "name": "hitl_math",
      "module_path": "nodus_adk_agents.a2a_hitl_math_agent",
      "enabled": true
    }
  ]
}
EOF
fi

# Kill existing process if running
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}✓ Starting Agent Pool Manager on port 8000...${NC}"
echo -e "${GREEN}✓ Config: $CONFIG_FILE${NC}"
echo ""

# Start pool manager
python -m nodus_adk_agents.agent_pool_manager "$CONFIG_FILE"

