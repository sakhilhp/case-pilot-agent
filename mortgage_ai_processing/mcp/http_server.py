"""
HTTP transport layer for MCP server.
Provides HTTP/JSON-RPC interface for the mortgage processing MCP server.
"""

import json
import logging
from typing import Dict, Any, Optional
from aiohttp import web, web_request
from aiohttp.web_response import Response
import asyncio

from .mortgage_server import get_mcp_server


class MCPHTTPServer:
    """HTTP transport layer for MCP server."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.mcp_server = get_mcp_server()
        self.logger = logging.getLogger("mcp_http_server")
        
        # Setup routes
        self.app.router.add_post('/mcp', self.handle_mcp_request)
        self.app.router.add_get('/health', self.handle_health_check)
        self.app.router.add_get('/info', self.handle_server_info)
        self.app.router.add_options('/mcp', self.handle_cors_preflight)
        
        # Add CORS middleware
        self.app.middlewares.append(self.cors_middleware)
        
    @web.middleware
    async def cors_middleware(self, request: web_request.Request, handler):
        """Add CORS headers to all responses."""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
        
    async def handle_cors_preflight(self, request: web_request.Request) -> Response:
        """Handle CORS preflight requests."""
        return web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        )
        
    async def handle_health_check(self, request: web_request.Request) -> Response:
        """Handle health check requests."""
        health_data = {
            "status": "healthy",
            "server": "mortgage-processing-mcp-server",
            "version": "1.0.0",
            "agents": len(self.mcp_server.agents),
            "tools": len(self.mcp_server.tools)
        }
        return web.json_response(health_data)
        
    async def handle_server_info(self, request: web_request.Request) -> Response:
        """Handle server info requests."""
        # Create a simple MCP request for server info
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "server/info",
            "params": {},
            "id": "http-info-request"
        }
        
        response_json = await self.mcp_server.handle_request(json.dumps(mcp_request))
        response_data = json.loads(response_json)
        
        return web.json_response(response_data)
        
    async def handle_mcp_request(self, request: web_request.Request) -> Response:
        """Handle MCP JSON-RPC requests."""
        try:
            # Parse JSON request body
            request_data = await request.json()
            self.logger.info(f"Received MCP request: {request_data.get('method', 'unknown')}")
            
            # Validate JSON-RPC format
            if not self.validate_jsonrpc_request(request_data):
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request",
                        "data": "Request must be valid JSON-RPC 2.0"
                    },
                    "id": request_data.get("id")
                }
                return web.json_response(error_response, status=400)
            
            # Forward to MCP server
            response_json = await self.mcp_server.handle_request(json.dumps(request_data))
            response_data = json.loads(response_json)
            
            # Return appropriate HTTP status
            status = 200 if not response_data.get("error") else 400
            
            return web.json_response(response_data, status=status)
            
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": "Invalid JSON"
                },
                "id": None
            }
            return web.json_response(error_response, status=400)
            
        except Exception as e:
            self.logger.error(f"Error handling MCP request: {str(e)}")
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                },
                "id": request_data.get("id") if 'request_data' in locals() else None
            }
            return web.json_response(error_response, status=500)
            
    def validate_jsonrpc_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate JSON-RPC 2.0 request format."""
        if not isinstance(request_data, dict):
            return False
            
        # Check required fields
        if "jsonrpc" not in request_data or request_data["jsonrpc"] != "2.0":
            return False
            
        if "method" not in request_data or not isinstance(request_data["method"], str):
            return False
            
        return True
        
    async def start(self):
        """Start the HTTP server."""
        self.logger.info(f"Starting MCP HTTP server on {self.host}:{self.port}")
        self.logger.info(f"MCP Server: {self.mcp_server.server_name} v{self.mcp_server.version}")
        self.logger.info(f"Tools registered: {len(self.mcp_server.tools)}")
        self.logger.info(f"Agents registered: {len(self.mcp_server.agents)}")
        self.logger.info("Available endpoints:")
        self.logger.info(f"  POST http://{self.host}:{self.port}/mcp - MCP JSON-RPC requests")
        self.logger.info(f"  GET  http://{self.host}:{self.port}/health - Health check")
        self.logger.info(f"  GET  http://{self.host}:{self.port}/info - Server information")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print(f"🚀 MCP HTTP Server running on http://{self.host}:{self.port}")
        print(f"📋 Server Info: http://{self.host}:{self.port}/info")
        print(f"❤️  Health Check: http://{self.host}:{self.port}/health")
        print(f"🔧 MCP Endpoint: http://{self.host}:{self.port}/mcp")
        print()
        print("Ready to accept MCP requests via HTTP!")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down MCP HTTP server...")
            await runner.cleanup()


async def start_mcp_http_server(host: str = "localhost", port: int = 8000):
    """Start the MCP HTTP server."""
    server = MCPHTTPServer(host, port)
    await server.start()


if __name__ == "__main__":
    # For direct execution
    asyncio.run(start_mcp_http_server())