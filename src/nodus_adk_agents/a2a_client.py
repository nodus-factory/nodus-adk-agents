"""
A2A Client for Root Agent
Enables HTTP-based agent-to-agent communication following A2A Protocol
"""

from typing import Any, Dict, Optional

import httpx
import structlog

logger = structlog.get_logger()


class A2AClient:
    """
    Client for A2A (Agent-to-Agent) communication
    Implements JSON-RPC 2.0 over HTTP
    """
    
    def __init__(self, agent_endpoint: str, timeout: float = 30.0):
        """
        Initialize A2A client
        
        Args:
            agent_endpoint: Base URL of the A2A agent (e.g., http://localhost:8001/a2a)
            timeout: Request timeout in seconds
        """
        self.agent_endpoint = agent_endpoint
        self.timeout = timeout
        self._request_id = 0
    
    def _next_request_id(self) -> int:
        """Generate next request ID"""
        self._request_id += 1
        return self._request_id
    
    async def call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call an A2A agent method
        
        Args:
            method: Method name to call
            params: Method parameters (optional)
            
        Returns:
            Result from the agent
            
        Raises:
            Exception: If the request fails or agent returns an error
        """
        request_id = self._next_request_id()
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id,
        }
        
        logger.info(
            "A2A request",
            endpoint=self.agent_endpoint,
            method=method,
            request_id=request_id,
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.agent_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                
                logger.info(
                    "HTTP response received",
                    status=response.status_code,
                    content_type=response.headers.get("content-type"),
                    body_preview=response.text[:200] if response.text else "Empty"
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(
                    "JSON parsed",
                    result_type=type(result).__name__,
                    has_result="result" in result if result else False,
                    has_error="error" in result if result else False
                )
            
            # Check for JSON-RPC error (must be not null)
            if result and result.get("error") is not None:
                error = result["error"]
                error_msg = f"A2A Error {error.get('code')}: {error.get('message')}"
                logger.error("A2A error response", error=error)
                raise Exception(error_msg)
            
            logger.info(
                "A2A response received",
                endpoint=self.agent_endpoint,
                method=method,
                request_id=request_id,
            )
            
            if result is None:
                logger.error("A2A response is None!")
                return {}
            
            return result.get("result", {})
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "A2A HTTP error",
                status=e.response.status_code,
                endpoint=self.agent_endpoint,
            )
            raise Exception(f"A2A HTTP error {e.response.status_code}: {e}")
        
        except httpx.TimeoutException:
            logger.error("A2A request timeout", endpoint=self.agent_endpoint)
            raise Exception(f"A2A timeout to {self.agent_endpoint}")
        
        except Exception as e:
            logger.error("A2A request failed", error=str(e), endpoint=self.agent_endpoint)
            raise
    
    async def discover(self) -> Dict[str, Any]:
        """
        Discover agent capabilities via Agent Card
        
        Returns:
            Agent Card with capabilities
        """
        # Agent Card is at the root endpoint (not /a2a)
        base_url = self.agent_endpoint.replace("/a2a", "")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(base_url)
                response.raise_for_status()
                card = response.json()
            
            logger.info("Agent discovered", name=card.get("name"), endpoint=base_url)
            return card
        
        except Exception as e:
            logger.error("Agent discovery failed", error=str(e), endpoint=base_url)
            raise Exception(f"Failed to discover agent at {base_url}: {e}")

