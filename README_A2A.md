# Weather Agent A2A - Guia d'Ús

## 🌤️ Weather Agent amb A2A Protocol

Aquest és un agent de meteorologia que implementa el **A2A (Agent-to-Agent) Protocol** per comunicar-se amb altres agents via HTTPS.

### Característiques:

- ✅ **Dades reals** via Open-Meteo API (gratuït, sense API key)
- ✅ **A2A Protocol** (JSON-RPC 2.0 over HTTP)
- ✅ **Agent Card** per descobriment de capacitats
- ✅ **Ciutats espanyoles**: Barcelona, Madrid, València, Sevilla, Bilbao

---

## 🚀 Com Executar

### 1. Instal·lar dependències

```bash
cd nodus-adk-agents
pip install httpx fastapi uvicorn
```

### 2. Iniciar el Weather Agent (servidor separat)

```bash
python -m nodus_adk_agents.a2a_weather_agent
```

El servidor arrancarà a `http://localhost:8001`

### 3. Provar l'Agent directament

#### Descobrir capacitats (Agent Card):
```bash
curl http://localhost:8001/
```

#### Consultar el temps a Barcelona:
```bash
curl -X POST http://localhost:8001/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_forecast",
    "params": {"city": "barcelona", "days": 1},
    "id": 1
  }'
```

#### Pronòstic de 3 dies a Madrid:
```bash
curl -X POST http://localhost:8001/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_forecast",
    "params": {"city": "madrid", "days": 3},
    "id": 2
  }'
```

---

## 🔗 Integració amb Root Agent

### Usar A2AClient des del Root Agent:

```python
from nodus_adk_agents.a2a_client import A2AClient

# Crear client A2A
weather_client = A2AClient("http://localhost:8001/a2a")

# Descobrir capacitats
card = await weather_client.discover()
print(f"Agent: {card['name']}")
print(f"Capabilities: {card['capabilities']}")

# Consultar el temps
forecast = await weather_client.call(
    method="get_forecast",
    params={"city": "barcelona", "days": 1}
)

print(f"Temps a Barcelona: {forecast}")
```

---

## 📊 Exemple de Resposta

```json
{
  "jsonrpc": "2.0",
  "result": {
    "city": "barcelona",
    "forecasts": [
      {
        "date": "2025-11-21",
        "temp_max": 18.2,
        "temp_min": 12.5,
        "condition": "parcialment ennuvolat",
        "precipitation_prob": 10,
        "wind_speed": 15.3
      }
    ],
    "source": "Open-Meteo API",
    "timestamp": "2025-11-21T19:45:00"
  },
  "id": 1
}
```

---

## 🛠️ Desenvolupament

### Afegir més ciutats:

Edita `CITY_COORDS` a `a2a_weather_agent.py`:

```python
CITY_COORDS = {
    "barcelona": {"lat": 41.3879, "lon": 2.1699},
    "nova_ciutat": {"lat": XX.XXXX, "lon": Y.YYYY},
}
```

### Logs:

El servidor usa `structlog` per logging detallat:
- Info: Peticions A2A rebudes
- Error: Fallades d'API o errors de procés

---

## 📚 Referències

- **Open-Meteo API**: https://open-meteo.com/
- **A2A Protocol**: https://a2a-protocol.org/
- **JSON-RPC 2.0**: https://www.jsonrpc.org/specification

---

## 🧪 Tests

Provar amb diferents ciutats:

```bash
# Barcelona
curl -X POST http://localhost:8001/a2a -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_forecast","params":{"city":"barcelona"},"id":1}'

# Madrid 3 dies
curl -X POST http://localhost:8001/a2a -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_forecast","params":{"city":"madrid","days":3},"id":2}'

# Ciutat no existent (error)
curl -X POST http://localhost:8001/a2a -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_forecast","params":{"city":"paris"},"id":3}'
```


