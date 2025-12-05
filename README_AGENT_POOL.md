# 🎯 Agent Pool Manager

Sistema centralitzat per gestionar múltiples agents A2A en un sol procés Python.

## 📊 Comparació: Abans vs Després

### ❌ Abans (Processos Individuals)

```
weather_agent    → Python process :8001 → ~100MB RAM
currency_agent   → Python process :8002 → ~100MB RAM
calculator_agent → Python process :8003 → ~100MB RAM
email_agent      → Python process :8004 → ~100MB RAM
hitl_math_agent  → Python process :8005 → ~100MB RAM

Total: 5 processos, 5 ports, ~500MB RAM
```

### ✅ Després (Agent Pool)

```
Agent Pool Manager → 1 Python process :8000 → ~100MB RAM
  ├─ /weather/a2a
  ├─ /currency/a2a
  ├─ /calculator/a2a
  ├─ /email/a2a
  └─ /hitl_math/a2a

Total: 1 procés, 1 port, ~100MB RAM
✅ 80% reducció de recursos!
```

---

## 🚀 Ús Ràpid

### Development (fora de Docker)

```bash
cd nodus-adk-agents

# Iniciar el pool
./start_agent_pool.sh

# O manualment:
python -m nodus_adk_agents.agent_pool_manager config/agent_pool.json
```

### Production (Docker)

```bash
cd nodus-adk-infra

# Build i start del pool
docker compose up agent-pool

# O reconstruir:
docker compose build agent-pool
docker compose up -d agent-pool
```

---

## 📝 Configuració

Edita `config/agent_pool.json`:

```json
{
  "agents": [
    {
      "name": "weather",
      "module_path": "nodus_adk_agents.a2a_weather_agent",
      "enabled": true,
      "config": {
        "cache_ttl": 300
      }
    },
    {
      "name": "nou_agent",
      "module_path": "nodus_adk_agents.a2a_nou_agent",
      "enabled": true
    }
  ]
}
```

**Camp obligatoris**:
- `name`: Identificador únic de l'agent
- `module_path`: Path del mòdul Python
- `enabled`: True/false per activar/desactivar

**Camps opcionals**:
- `config`: Configuració específica de l'agent

---

## 🔌 Endpoints

Una vegada el pool està running:

### Pool Manager

```bash
# Llista d'agents
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Info detallada d'agents
curl http://localhost:8000/agents
```

### Agents Individuals

```bash
# Weather Agent Card
curl http://localhost:8000/weather/

# Weather A2A call
curl -X POST http://localhost:8000/weather/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_forecast",
    "params": {"city": "barcelona"},
    "id": 1
  }'

# Currency Agent
curl http://localhost:8000/currency/

# Calculator Agent
curl http://localhost:8000/calculator/
```

---

## ♻️ Hot Reload

### Recarregar tots els agents

```bash
curl -X POST http://localhost:8000/reload
```

### Recarregar un agent individual

```bash
curl -X POST http://localhost:8000/reload/weather
```

---

## ➕ Afegir Nou Agent

### 1. Crear el mòdul de l'agent

```python
# src/nodus_adk_agents/a2a_nou_agent.py

from fastapi import FastAPI

app = FastAPI(title="Nou Agent A2A")

@app.get("/")
async def agent_card():
    return {
        "name": "nou_agent",
        "description": "Descripció del nou agent",
        "capabilities": ["method1", "method2"]
    }

@app.post("/a2a")
async def a2a_handler(request: dict):
    # Lògica A2A (JSON-RPC 2.0)
    method = request["method"]
    params = request["params"]
    
    if method == "method1":
        return {
            "jsonrpc": "2.0",
            "result": {"status": "ok"},
            "id": request["id"]
        }
    
    # ... més mètodes
```

### 2. Afegir al config JSON

```json
{
  "name": "nou_agent",
  "module_path": "nodus_adk_agents.a2a_nou_agent",
  "enabled": true
}
```

### 3. Reload

```bash
# Si el pool està running:
curl -X POST http://localhost:8000/reload

# O restart:
./start_agent_pool.sh
```

**🎉 Cap canvi al codi del Root Agent necessari!**

---

## 🐛 Troubleshooting

### L'agent no apareix al pool

**Comprova els logs**:
```bash
# Development
tail -f logs/agent_pool.log

# Docker
docker compose logs agent-pool
```

**Errors comuns**:
- `Module not found`: El `module_path` és incorrecte
- `No 'app' attribute`: L'agent no exposa una FastAPI app
- `enabled: false`: L'agent està deshabilitat al config

### Port 8000 ja en ús

```bash
# Matar el procés que usa el port
lsof -ti :8000 | xargs kill -9

# O canviar el port al script
uvicorn.run(pool.app, host="0.0.0.0", port=8001)
```

### Agent no respon

1. Verifica que està carregat:
   ```bash
   curl http://localhost:8000/agents | jq
   ```

2. Comprova el health:
   ```bash
   curl http://localhost:8000/health
   ```

3. Prova l'agent directament:
   ```bash
   curl http://localhost:8000/{agent_name}/
   ```

---

## 📊 Observabilitat

### Logs Estructurats

```bash
# Tots els logs
docker compose logs -f agent-pool

# Només errors
docker compose logs agent-pool | grep ERROR

# Agent específic
docker compose logs agent-pool | grep "agent=weather"
```

### Mètriques (futur)

- Request count per agent
- Latency per agent
- Error rate per agent
- Memory usage per agent

---

## 🚀 Escalabilitat

### Opció 1: Pool amb 50+ agents

```json
{
  "agents": [
    {"name": "agent1", "module_path": "...", "enabled": true},
    {"name": "agent2", "module_path": "...", "enabled": true},
    // ... 48 més
  ]
}
```

**1 procés Python pot gestionar 50-100 agents lleugers.**

### Opció 2: Múltiples pools

```yaml
# docker-compose.yml

agent-pool-core:  # Agents core
  ports: ["8000:8000"]
  
agent-pool-business:  # Agents business
  ports: ["8010:8000"]
  
agent-pool-heavy:  # Agents pesats
  ports: ["8020:8000"]
```

### Opció 3: Pool + Contenidors individuals

```yaml
agent-pool:  # 90% dels agents
  ports: ["8000:8000"]
  
payment-agent:  # Agent crític individual
  ports: ["8030:8000"]
```

---

## 🔐 Seguretat (futur)

### Autenticació entre agents

```json
{
  "name": "secure_agent",
  "module_path": "...",
  "auth": {
    "type": "bearer",
    "token_env": "SECURE_AGENT_TOKEN"
  }
}
```

### Rate Limiting

```json
{
  "name": "rate_limited_agent",
  "rate_limit": {
    "calls_per_minute": 60,
    "burst": 10
  }
}
```

---

## 📚 Referències

- [A2A Protocol](https://a2a-protocol.org/)
- [Agent Cards Spec](https://a2a-protocol.org/dev/specification/#agent-cards)
- [FastAPI Sub Applications](https://fastapi.tiangolo.com/advanced/sub-applications/)

---

## 💡 Roadmap

- [ ] Health checks individuals per agent
- [ ] Métriques Prometheus per agent
- [ ] Circuit breakers per agent
- [ ] Auto-discovery via service mesh
- [ ] A/B testing entre versions d'agents
- [ ] Agent versioning (v1, v2, etc.)
- [ ] Dynamic scaling (add/remove agents runtime)


