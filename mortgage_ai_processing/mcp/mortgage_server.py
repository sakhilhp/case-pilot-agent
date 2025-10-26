"""
Comprehensive MCP server implementation for mortgage processing system.

This module provides a complete MCP server that exposes all mortgage processing
tools and workflows as standardized MCP endpoints with full protocol compliance.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict

from .server import MCPServer, MCPRequest, MCPResponse, MCPError
from .protocol import MCPProtocolHandler, MCPToolInfo, MCPServerInfo, MCPCapabilities
from ..workflow_orchestrator import MortgageProcessingOrchestrator, WorkflowConfiguration
from ..models.core import MortgageApplication
from ..models.assessment import LoanDecision
from ..models.enums import ProcessingStatus, DecisionType
from ..tools.base import ToolResult


class MortgageProcessingMCPServer(MCPServer):
    """
    Complete MCP server for mortgage processing system.
    
    Exposes all mortgage processing capabilities through MCP protocol:
    - Individual tool execution
    - Complete workflow processing
    - Status monitoring and control
    - Tool discovery and metadata
    """
    
    def __init__(self, 
                 server_name: str = "mortgage-processing-server",
                 version: str = "1.0.0",
                 config: Optional[WorkflowConfiguration] = None):
        super().__init__(server_name, version)
        
        # Initialize orchestrator
        self.orchestrator = MortgageProcessingOrchestrator(config)
        self.protocol_handler = MCPProtocolHandler()
        
        # Register mortgage-specific handlers
        self._register_mortgage_handlers()
        
        # Register all tools from orchestrator
        self._register_orchestrator_tools()
        
        self.logger.info(f"Initialized Mortgage Processing MCP Server v{version}")
        
    def _register_mortgage_handlers(self) -> None:
        """Register mortgage-specific MCP handlers."""
        mortgage_handlers = {
            # Workflow management
            "mortgage/process": self._handle_mortgage_process,
            "mortgage/workflow/status": self._handle_workflow_status,
            "mortgage/workflow/cancel": self._handle_workflow_cancel,
            "mortgage/workflow/list": self._handle_workflow_list,
            
            # Agent operations
            "mortgage/agents/list": self._handle_agents_list,
            "mortgage/agents/info": self._handle_agent_info,
            
            # Tool operations (enhanced)
            "mortgage/tools/metadata": self._handle_tools_metadata,
            "mortgage/tools/execute": self._handle_tool_execute,
            
            # System operations
            "mortgage/system/health": self._handle_system_health,
            "mortgage/system/cleanup": self._handle_system_cleanup,
        }
        
        for method, handler in mortgage_handlers.items():
            self.register_handler(method, handler)
            
    def _register_orchestrator_tools(self) -> None:
        """Register all tools from the orchestrator."""
        # Register tools from tool manager
        for tool_name, tool in self.orchestrator.tool_manager.tools.items():
            self.register_tool(tool)
            
        # Register agents
        for agent in self.orchestrator.agent_manager.get_all_agents():
            self.register_agent(agent)
            
        self.logger.info(f"Registered {len(self.tools)} tools from orchestrator")
        
    async def _handle_mortgage_process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/process request - process complete mortgage application.
        
        Expected params:
        - application: MortgageApplication data
        - workflow_type: Optional workflow type ("standard" or "parallel")
        - execution_id: Optional custom execution ID
        """
        try:
            # Extract and validate parameters
            application_data = params.get("application")
            if not application_data:
                raise ValueError("Application data is required")
                
            workflow_type = params.get("workflow_type", "parallel_mortgage_processing")
            execution_id = params.get("execution_id")
            
            # Create MortgageApplication object
            application = MortgageApplication(**application_data)
            
            # Process the application
            execution, loan_decision = await self.orchestrator.process_mortgage_application(
                application, workflow_type, execution_id
            )
            
            # Format response
            return {
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "progress": execution.get_progress(),
                "loan_decision": {
                    "decision": loan_decision.decision.value,
                    "decision_factors": loan_decision.decision_factors,
                    "risk_score": loan_decision.risk_score,
                    "confidence_score": loan_decision.confidence_score,
                    "conditions": loan_decision.conditions,
                    "adverse_actions": loan_decision.adverse_actions,
                    "loan_terms": asdict(loan_decision.loan_terms) if loan_decision.loan_terms else None
                },
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
            }
            
        except Exception as e:
            self.logger.error(f"Error processing mortgage application: {str(e)}")
            raise ValueError(f"Failed to process mortgage application: {str(e)}")
            
    async def _handle_workflow_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/workflow/status request - get workflow execution status.
        
        Expected params:
        - execution_id: Workflow execution ID
        """
        execution_id = params.get("execution_id")
        if not execution_id:
            raise ValueError("Execution ID is required")
            
        status = await self.orchestrator.get_workflow_status(execution_id)
        if not status:
            raise ValueError(f"Workflow not found: {execution_id}")
            
        return status
        
    async def _handle_workflow_cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/workflow/cancel request - cancel workflow execution.
        
        Expected params:
        - execution_id: Workflow execution ID
        """
        execution_id = params.get("execution_id")
        if not execution_id:
            raise ValueError("Execution ID is required")
            
        success = await self.orchestrator.cancel_workflow(execution_id)
        
        return {
            "execution_id": execution_id,
            "cancelled": success
        }
        
    async def _handle_workflow_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/workflow/list request - list active workflows.
        """
        active_workflows = self.orchestrator.list_active_workflows()
        
        # Get detailed status for each workflow
        workflow_details = []
        for execution_id in active_workflows:
            status = await self.orchestrator.get_workflow_status(execution_id)
            if status:
                workflow_details.append(status)
                
        return {
            "active_workflows": workflow_details,
            "total_count": len(workflow_details)
        }
        
    async def _handle_agents_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/agents/list request - list available agents.
        """
        agents = self.orchestrator.agent_manager.get_all_agents()
        
        agents_info = []
        for agent in agents:
            agents_info.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "tools": agent.get_tool_names(),
                "tool_count": len(agent.get_tool_names())
            })
            
        return {
            "agents": agents_info,
            "total_count": len(agents_info)
        }
        
    async def _handle_agent_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/agents/info request - get detailed agent information.
        
        Expected params:
        - agent_id: Agent ID
        """
        agent_id = params.get("agent_id")
        if not agent_id:
            raise ValueError("Agent ID is required")
            
        agent = self.orchestrator.agent_manager.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
            
        # Get tool details
        tools_info = []
        for tool_name in agent.get_tool_names():
            tool = agent.get_tool(tool_name)
            if tool:
                tools_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters_schema": tool.get_parameters_schema()
                })
                
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "tools": tools_info,
            "state": agent.state
        }
        
    async def _handle_tools_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/tools/metadata request - get enhanced tool metadata.
        """
        tools_metadata = []
        
        for tool_name, tool in self.tools.items():
            metadata = {
                "name": tool.name,
                "description": tool.description,
                "parameters_schema": tool.get_parameters_schema(),
                "metadata": asdict(tool.metadata) if hasattr(tool, 'metadata') else {},
                "agent_id": None  # Find which agent owns this tool
            }
            
            # Find owning agent
            for agent in self.orchestrator.agent_manager.get_all_agents():
                if tool_name in agent.get_tool_names():
                    metadata["agent_id"] = agent.agent_id
                    break
                    
            tools_metadata.append(metadata)
            
        return {
            "tools": tools_metadata,
            "total_count": len(tools_metadata)
        }
        
    async def _handle_tool_execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/tools/execute request - execute individual tool.
        
        Expected params:
        - tool_name: Name of tool to execute
        - arguments: Tool arguments
        """
        tool_name = params.get("tool_name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
            
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
            
        # Execute tool
        result = await tool.safe_execute(**arguments)
        
        return {
            "tool_name": tool_name,
            "success": result.success,
            "data": result.data,
            "error_message": result.error_message,
            "execution_time": result.execution_time,
            "executed_at": datetime.now().isoformat()
        }
        
    async def _handle_system_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/system/health request - get system health status.
        """
        # Check orchestrator components
        agent_count = len(self.orchestrator.agent_manager.get_all_agents())
        tool_count = len(self.orchestrator.tool_manager.tools)
        workflow_count = len(self.orchestrator.workflow_engine.workflows)
        active_workflow_count = len(self.orchestrator.active_workflows)
        
        # Basic health checks
        health_status = "healthy"
        issues = []
        
        if agent_count == 0:
            health_status = "unhealthy"
            issues.append("No agents registered")
            
        if tool_count == 0:
            health_status = "unhealthy"
            issues.append("No tools registered")
            
        if workflow_count == 0:
            health_status = "unhealthy"
            issues.append("No workflows registered")
            
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "agents": {
                    "count": agent_count,
                    "status": "healthy" if agent_count > 0 else "unhealthy"
                },
                "tools": {
                    "count": tool_count,
                    "status": "healthy" if tool_count > 0 else "unhealthy"
                },
                "workflows": {
                    "registered_count": workflow_count,
                    "active_count": active_workflow_count,
                    "status": "healthy" if workflow_count > 0 else "unhealthy"
                }
            },
            "issues": issues
        }
        
    async def _handle_system_cleanup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mortgage/system/cleanup request - cleanup old workflow executions.
        
        Expected params:
        - older_than_hours: Optional hours threshold (default 24)
        """
        older_than_hours = params.get("older_than_hours", 24)
        
        if not isinstance(older_than_hours, (int, float)) or older_than_hours <= 0:
            raise ValueError("older_than_hours must be a positive number")
            
        removed_count = await self.orchestrator.cleanup_completed_workflows(older_than_hours)
        
        return {
            "removed_count": removed_count,
            "older_than_hours": older_than_hours,
            "cleaned_at": datetime.now().isoformat()
        }
        
    async def _handle_server_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced server capabilities including mortgage-specific features."""
        base_capabilities = await super()._handle_server_capabilities(params)
        
        # Add mortgage-specific capabilities
        mortgage_capabilities = {
            "mortgage_processing": {
                "workflow_types": ["standard_mortgage_processing", "parallel_mortgage_processing"],
                "supported_agents": [agent.agent_id for agent in self.orchestrator.agent_manager.get_all_agents()],
                "supported_tools": list(self.tools.keys()),
                "features": {
                    "parallel_processing": True,
                    "workflow_monitoring": True,
                    "error_recovery": True,
                    "progress_tracking": True,
                    "agent_communication": True
                }
            }
        }
        
        # Merge capabilities
        base_capabilities["capabilities"].update(mortgage_capabilities)
        
        return base_capabilities
        
    def get_supported_methods(self) -> List[str]:
        """Get all supported MCP methods including mortgage-specific ones."""
        base_methods = super().request_handlers.keys()
        return list(base_methods)
        
    async def validate_mortgage_application(self, application_data: Dict[str, Any]) -> bool:
        """
        Validate mortgage application data structure.
        
        Args:
            application_data: Application data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ["application_id", "borrower_info", "property_info", "loan_details"]
        
        for field in required_fields:
            if field not in application_data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate borrower info
        borrower_info = application_data.get("borrower_info", {})
        borrower_required = ["first_name", "last_name", "ssn", "date_of_birth", "email", "phone"]
        for field in borrower_required:
            if field not in borrower_info:
                raise ValueError(f"Missing required borrower field: {field}")
                
        # Validate property info
        property_info = application_data.get("property_info", {})
        property_required = ["address", "property_type", "property_value"]
        for field in property_required:
            if field not in property_info:
                raise ValueError(f"Missing required property field: {field}")
                
        # Validate loan details
        loan_details = application_data.get("loan_details", {})
        loan_required = ["loan_amount", "loan_type", "loan_term_years", "down_payment", "purpose"]
        for field in loan_required:
            if field not in loan_details:
                raise ValueError(f"Missing required loan field: {field}")
                
        return True
        
    async def create_sample_application(self) -> Dict[str, Any]:
        """
        Create a sample mortgage application for testing.
        
        Returns:
            Sample application data
        """
        from decimal import Decimal
        
        return {
            "application_id": f"SAMPLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "borrower_info": {
                "first_name": "John",
                "last_name": "Doe",
                "ssn": "123-45-6789",
                "date_of_birth": "1985-06-15T00:00:00",
                "email": "john.doe@example.com",
                "phone": "555-123-4567",
                "current_address": "123 Main St, Anytown, ST 12345",
                "employment_status": "Employed",
                "annual_income": "75000"
            },
            "property_info": {
                "address": "456 Oak Ave, Testville, ST 67890",
                "property_type": "Single Family Home",
                "property_value": "300000"
            },
            "loan_details": {
                "loan_amount": "240000",
                "loan_type": "CONVENTIONAL",
                "loan_term_years": 30,
                "down_payment": "60000",
                "purpose": "Purchase"
            },
            "documents": [],
            "processing_status": "PENDING"
        }


# Factory function for easy server creation
def create_mortgage_mcp_server(config: Optional[WorkflowConfiguration] = None) -> MortgageProcessingMCPServer:
    """
    Create and configure a mortgage processing MCP server.
    
    Args:
        config: Optional workflow configuration
        
    Returns:
        Configured MCP server instance
    """
    return MortgageProcessingMCPServer(config=config)


# Global server instance for easy access
_server_instance: Optional[MortgageProcessingMCPServer] = None


def get_mcp_server(config: Optional[WorkflowConfiguration] = None) -> MortgageProcessingMCPServer:
    """
    Get or create the global MCP server instance.
    
    Args:
        config: Optional configuration for the server
        
    Returns:
        MortgageProcessingMCPServer instance
    """
    global _server_instance
    
    if _server_instance is None:
        _server_instance = create_mortgage_mcp_server(config)
        
    return _server_instance