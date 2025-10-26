"""
Mortgage AI Processing System

A Python-based agentic AI solution that automates the end-to-end mortgage processing workflow.
Built with MCP (Model Context Protocol) architecture for flexible integration.
"""

__version__ = "0.1.0"
__author__ = "Mortgage AI Processing Team"

# Import core components
from .agents.base import BaseAgent, AgentManager
from .tools.base import BaseTool, ToolManager, ToolResult
from .models.core import MortgageApplication, Document
from .mcp.server import MCPServer
from .mcp.protocol import MCPProtocolHandler
from .mcp.registry import ToolRegistry
from .mcp.mortgage_server import MortgageProcessingMCPServer, create_mortgage_mcp_server, get_mcp_server
from .workflow_orchestrator import (
    MortgageProcessingOrchestrator, WorkflowConfiguration, 
    get_orchestrator, process_mortgage_application_simple
)