"""
MCP (Model Context Protocol) server implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import json
import logging
from datetime import datetime

from ..tools.base import BaseTool, ToolResult, ToolMetadata
from ..agents.base import BaseAgent


@dataclass
class MCPRequest:
    """MCP protocol request structure."""
    method: str
    id: Optional[str] = None
    jsonrpc: str = "2.0"
    params: Optional[Dict[str, Any]] = None


@dataclass
class MCPResponse:
    """MCP protocol response structure."""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    jsonrpc: str = "2.0"


@dataclass
class MCPError:
    """MCP protocol error structure."""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class MCPServer(ABC):
    """
    Base MCP server implementation for mortgage processing system.
    
    Provides MCP protocol compliance and exposes tools and workflows
    as standardized interfaces.
    """
    
    def __init__(self, server_name: str, version: str = "1.0.0"):
        self.server_name = server_name
        self.version = version
        self.tools: Dict[str, BaseTool] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.request_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(f"mcp_server.{server_name}")
        
        # Register default MCP methods
        self._register_default_handlers()
        
    def _register_default_handlers(self) -> None:
        """Register default MCP protocol handlers."""
        self.request_handlers.update({
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "server/info": self._handle_server_info,
            "server/capabilities": self._handle_server_capabilities
        })
        
    async def handle_request(self, request_data: str) -> str:
        """
        Handle incoming MCP request.
        
        Args:
            request_data: JSON string containing MCP request
            
        Returns:
            JSON string containing MCP response
        """
        try:
            request_dict = json.loads(request_data)
            request = MCPRequest(**request_dict)
            
            # Route request to appropriate handler
            handler = self.request_handlers.get(request.method)
            if not handler:
                response = MCPResponse(
                    error=asdict(MCPError(
                        code=-32601,
                        message=f"Method not found: {request.method}"
                    )),
                    id=request.id
                )
            else:
                try:
                    result = await handler(request.params or {})
                    response = MCPResponse(result=result, id=request.id)
                except Exception as e:
                    self.logger.error(f"Handler error for {request.method}: {str(e)}")
                    response = MCPResponse(
                        error=asdict(MCPError(
                            code=-32603,
                            message="Internal error",
                            data={"details": str(e)}
                        )),
                        id=request.id
                    )
                    
            return json.dumps(asdict(response))
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in request: {str(e)}")
            response = MCPResponse(
                error=asdict(MCPError(
                    code=-32700,
                    message="Parse error"
                ))
            )
            return json.dumps(asdict(response))
            
        except Exception as e:
            self.logger.error(f"Unexpected error handling request: {str(e)}")
            response = MCPResponse(
                error=asdict(MCPError(
                    code=-32603,
                    message="Internal error"
                ))
            )
            return json.dumps(asdict(response))
            
    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools_info = []
        
        for tool_name, tool in self.tools.items():
            tools_info.append({
                "name": tool_name,
                "description": tool.description,
                "inputSchema": tool.get_parameters_schema()
            })
            
        return {"tools": tools_info}
        
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
            
        tool = self.tools.get(tool_name)
        if not tool:
            # Return a tool result indicating the tool was not found
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                data={},
                error_message=f"Tool not found: {tool_name}"
            )
        else:
            # Execute tool
            result = await tool.safe_execute(**arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "success": result.success,
                        "data": result.data,
                        "error": result.error_message,
                        "execution_time": result.execution_time
                    })
                }
            ]
        }
        
    async def _handle_server_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle server/info request."""
        return {
            "name": self.server_name,
            "version": self.version,
            "description": "Mortgage AI Processing MCP Server",
            "author": "Mortgage AI Processing Team"
        }
        
    async def _handle_server_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle server/capabilities request."""
        return {
            "capabilities": {
                "tools": {
                    "listChanged": False
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                },
                "prompts": {
                    "listChanged": False
                },
                "logging": {}
            }
        }
        
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the MCP server."""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered MCP tool: {tool.name}")
        
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the MCP server."""
        self.agents[agent.agent_id] = agent
        
        # Register all agent tools
        for tool_name in agent.get_tool_names():
            tool = agent.get_tool(tool_name)
            if tool:
                self.register_tool(tool)
                
        self.logger.info(f"Registered MCP agent: {agent.name}")
        
    def register_handler(self, method: str, handler: Callable) -> None:
        """Register a custom request handler."""
        self.request_handlers[method] = handler
        self.logger.info(f"Registered MCP handler: {method}")
        
    def get_tool_metadata(self) -> List[ToolMetadata]:
        """Get metadata for all registered tools."""
        return [tool.metadata for tool in self.tools.values()]
        
    async def start_server(self, host: str = "localhost", port: int = 8000) -> None:
        """Start the MCP server (placeholder for actual server implementation)."""
        self.logger.info(f"Starting MCP server on {host}:{port}")
        # Actual server implementation would go here
        
    async def stop_server(self) -> None:
        """Stop the MCP server."""
        self.logger.info("Stopping MCP server")
        # Cleanup logic would go here