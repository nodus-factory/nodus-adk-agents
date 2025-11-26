"""
Agent Pool Manager - Gestiona múltiples agents A2A en un sol procés.

Aquest servidor centralitzat:
- Carrega agents dinàmicament des de configuració JSON
- Exposa tots els agents en un sol port (8000)
- Comparteix recursos (connexions DB, cache, observabilitat)
- Permet hot reload d'agents individuals
- Proporciona discovery automàtic d'agents
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import importlib
import structlog
import json
from pathlib import Path

logger = structlog.get_logger()


class AgentPoolManager:
    """
    Gestor centralitzat d'agents A2A.
    
    Permet carregar, registrar i gestionar múltiples agents A2A
    en un sol procés Python, compartint recursos i infraestructura.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicialitza el pool manager.
        
        Args:
            config_path: Path al fitxer JSON de configuració d'agents
        """
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.app = FastAPI(
            title="Nodus Agent Pool Manager",
            description="Central A2A agent hosting platform",
            version="1.0.0"
        )
        self._setup_routes()
        self.config_path = config_path
        
        logger.info("Agent Pool Manager initialized")
    
    def register_agent(
        self,
        name: str,
        module_path: str,
        config: Optional[Dict[str, Any]] = None,
        mount_path: Optional[str] = None,
    ) -> bool:
        """
        Registra un agent al pool.
        
        Args:
            name: Nom de l'agent (e.g., "weather")
            module_path: Path del mòdul Python (e.g., "nodus_adk_agents.a2a_weather_agent")
            config: Configuració opcional de l'agent
            mount_path: Path on muntar l'agent (default: /{name})
            
        Returns:
            True si l'agent s'ha registrat correctament
        """
        try:
            # Import del mòdul de l'agent
            logger.info(
                "Loading agent module",
                agent=name,
                module=module_path,
            )
            module = importlib.import_module(module_path)
            
            # Obtenir la FastAPI app de l'agent
            if not hasattr(module, "app"):
                raise AttributeError(f"Module {module_path} doesn't have 'app' attribute")
            
            agent_app = getattr(module, "app")
            
            # Mount point per l'agent
            mount_path = mount_path or f"/{name}"
            
            # Muntar l'agent app sota el pool
            self.app.mount(mount_path, agent_app)
            
            # Registrar metadata de l'agent
            self.agents[name] = {
                "module": module_path,
                "app": agent_app,
                "mount_path": mount_path,
                "config": config or {},
                "a2a_endpoint": f"{mount_path}/a2a",
                "card_endpoint": f"{mount_path}/",
            }
            
            logger.info(
                "✅ Agent registered successfully",
                agent=name,
                mount_path=mount_path,
                a2a_endpoint=self.agents[name]["a2a_endpoint"],
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "❌ Failed to register agent",
                agent=name,
                module=module_path,
                error=str(e),
                exc_info=True,
            )
            return False
    
    def unregister_agent(self, name: str) -> bool:
        """
        Desregistra un agent del pool.
        
        Args:
            name: Nom de l'agent a desregistrar
            
        Returns:
            True si s'ha desregistrat correctament
        """
        if name not in self.agents:
            logger.warning("Agent not found in pool", agent=name)
            return False
        
        # Note: FastAPI doesn't support unmounting apps dynamically
        # This would require a restart to fully unload
        del self.agents[name]
        
        logger.info("Agent unregistered (restart needed for cleanup)", agent=name)
        return True
    
    def reload_agent(self, name: str) -> bool:
        """
        Recarrega un agent (unregister + register).
        
        Args:
            name: Nom de l'agent a recarregar
            
        Returns:
            True si s'ha recarregat correctament
        """
        if name not in self.agents:
            logger.warning("Agent not found in pool", agent=name)
            return False
        
        agent_info = self.agents[name]
        
        # Reload del mòdul
        try:
            module = importlib.reload(
                importlib.import_module(agent_info["module"])
            )
            
            # Re-registrar
            return self.register_agent(
                name=name,
                module_path=agent_info["module"],
                config=agent_info["config"],
                mount_path=agent_info["mount_path"],
            )
            
        except Exception as e:
            logger.error(
                "Failed to reload agent",
                agent=name,
                error=str(e),
            )
            return False
    
    def load_from_config(self, config_path: Optional[str] = None) -> int:
        """
        Carrega agents des d'un fitxer JSON de configuració.
        
        Args:
            config_path: Path al fitxer JSON (default: self.config_path)
            
        Returns:
            Nombre d'agents carregats
        """
        config_file = config_path or self.config_path
        
        if not config_file:
            logger.warning("No config path provided")
            return 0
        
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            
            agents_config = config.get("agents", [])
            loaded_count = 0
            
            for agent_def in agents_config:
                # Skip disabled agents
                if not agent_def.get("enabled", True):
                    logger.info(
                        "Skipping disabled agent",
                        agent=agent_def.get("name"),
                    )
                    continue
                
                # Register agent
                success = self.register_agent(
                    name=agent_def["name"],
                    module_path=agent_def["module_path"],
                    config=agent_def.get("config", {}),
                )
                
                if success:
                    loaded_count += 1
            
            logger.info(
                "✅ Agents loaded from config",
                config_file=config_file,
                total=len(agents_config),
                loaded=loaded_count,
            )
            
            return loaded_count
            
        except FileNotFoundError:
            logger.error("Config file not found", path=config_file)
            return 0
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in config file", path=config_file, error=str(e))
            return 0
        except Exception as e:
            logger.error("Failed to load config", path=config_file, error=str(e))
            return 0
    
    def _setup_routes(self):
        """Configura les rutes del pool manager."""
        
        @self.app.get("/")
        async def root():
            """
            Pool root - Llista tots els agents disponibles.
            
            Retorna informació sobre el pool i els agents registrats.
            """
            return {
                "name": "Nodus Agent Pool Manager",
                "version": "1.0.0",
                "agents_count": len(self.agents),
                "agents": [
                    {
                        "name": name,
                        "a2a_endpoint": info["a2a_endpoint"],
                        "card_endpoint": info["card_endpoint"],
                        "module": info["module"],
                    }
                    for name, info in self.agents.items()
                ],
            }
        
        @self.app.get("/health")
        async def health():
            """Health check del pool."""
            return {
                "status": "healthy",
                "agents_count": len(self.agents),
                "agents": list(self.agents.keys()),
            }
        
        @self.app.post("/reload")
        async def reload_config():
            """
            Hot reload de la configuració d'agents.
            
            Recarrega el fitxer de configuració i actualitza els agents.
            """
            if not self.config_path:
                raise HTTPException(
                    status_code=400,
                    detail="No config path configured for pool"
                )
            
            loaded_count = self.load_from_config()
            
            return {
                "status": "reloaded",
                "agents_loaded": loaded_count,
                "agents": list(self.agents.keys()),
            }
        
        @self.app.post("/reload/{agent_name}")
        async def reload_single_agent(agent_name: str):
            """
            Recarrega un agent individual.
            
            Args:
                agent_name: Nom de l'agent a recarregar
            """
            success = self.reload_agent(agent_name)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent '{agent_name}' not found or failed to reload"
                )
            
            return {
                "status": "reloaded",
                "agent": agent_name,
            }
        
        @self.app.get("/agents")
        async def list_agents():
            """Llista detallada de tots els agents."""
            return {
                "agents": [
                    {
                        "name": name,
                        "module": info["module"],
                        "endpoints": {
                            "a2a": info["a2a_endpoint"],
                            "card": info["card_endpoint"],
                        },
                        "config": info["config"],
                    }
                    for name, info in self.agents.items()
                ]
            }


def create_pool_from_config(config_path: str) -> AgentPoolManager:
    """
    Helper per crear i carregar un pool des de configuració.
    
    Args:
        config_path: Path al fitxer JSON de configuració
        
    Returns:
        AgentPoolManager configurat i carregat
    """
    pool = AgentPoolManager(config_path=config_path)
    pool.load_from_config()
    return pool


# Entry point per executar el pool
if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Default config path
    config_path = "config/agent_pool.json"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    logger.info(
        "🚀 Starting Agent Pool Manager",
        config=config_path,
    )
    
    # Create and load pool
    pool = create_pool_from_config(config_path)
    
    # Start server
    logger.info("✅ Agent Pool Manager ready", port=8000)
    uvicorn.run(pool.app, host="0.0.0.0", port=8000, log_level="info")

