"""
Base tool classes and tool management functionality.
Enhanced to match FSI Tools framework pattern from TypeScript implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import inspect


class ToolCategory(Enum):
    """Tool categories for organization and filtering."""
    DOCUMENT_PROCESSING = "document_processing"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE = "compliance"
    UNDERWRITING = "underwriting"
    FRAUD_DETECTION = "fraud_detection"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"


@dataclass
class ToolMetadata:
    """Enhanced metadata about a tool following FSI pattern."""
    name: str
    description: str
    category: ToolCategory
    version: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    agent_domain: Optional[str] = None
    confidence_scoring: bool = True
    mock_data_available: bool = True


@dataclass
class ToolResult:
    """Enhanced result from tool execution following FSI pattern."""
    tool_name: str
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """
    Enhanced abstract base class for all mortgage processing tools.
    
    Each tool performs a specific function within an agent's domain
    and can be executed independently or as part of a workflow.
    
    Enhanced to match FSI Tools framework pattern with:
    - Comprehensive error handling and logging
    - Confidence scoring and risk assessment
    - Mock data support for development
    - Regulatory compliance tracking
    """
    
    def __init__(self, name: str, description: str, category: ToolCategory, version: str = "1.0.0", agent_domain: Optional[str] = None):
        self.name = name
        self.description = description
        self.category = category
        self.version = version
        self.agent_domain = agent_domain
        self.logger = logging.getLogger(f"tool.{name}")
        self.metadata = self._generate_metadata()
        
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult containing execution results
        """
        pass
        
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Return input schema for tool parameters.
        
        Returns:
            Dictionary containing parameter schema
        """
        pass
    
    def get_output_schema(self) -> Optional[Dict[str, Any]]:
        """
        Return output schema for tool results.
        
        Returns:
            Dictionary containing output schema or None
        """
        return None
        
    # Maintain backward compatibility
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Backward compatibility method."""
        return self.get_input_schema()
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters against tool schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid
        """
        schema = self.get_parameters_schema()
        # Basic validation - can be enhanced with jsonschema library
        required_params = schema.get("required", [])
        
        for param in required_params:
            if param not in parameters:
                self.logger.error(f"Missing required parameter: {param}")
                return False
                
        return True
        
    def _generate_metadata(self) -> ToolMetadata:
        """Generate metadata for this tool."""
        return ToolMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
            version=self.version,
            input_schema=self.get_input_schema(),
            agent_domain=self.agent_domain
        )
        
    async def safe_execute(self, **kwargs) -> ToolResult:
        """
        Execute tool with error handling and validation.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult with execution results or error information
        """
        start_time = datetime.now()
        
        try:
            # Validate parameters
            if not self.validate_parameters(kwargs):
                execution_time = (datetime.now() - start_time).total_seconds()
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="Parameter validation failed",
                    execution_time=execution_time
                )
                
            # Execute tool
            result = await self.execute(**kwargs)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            self.logger.info(f"Tool {self.name} executed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Tool execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg,
                execution_time=execution_time
            )


class ToolManager:
    """
    Manages tool registration, discovery, and execution.
    
    Responsible for:
    - Tool lifecycle management
    - Parameter validation
    - Result aggregation
    - Dynamic tool loading
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_metadata: Dict[str, ToolMetadata] = {}
        self.logger = logging.getLogger("tool_manager")
        
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the manager."""
        self.tools[tool.name] = tool
        self.tool_metadata[tool.name] = tool.metadata
        self.logger.info(f"Registered tool: {tool.name}")
        
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
        
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        return self.tool_metadata.get(tool_name)
        
    def list_tools(self, agent_domain: Optional[str] = None) -> List[str]:
        """
        List available tools, optionally filtered by agent domain.
        
        Args:
            agent_domain: Optional domain filter
            
        Returns:
            List of tool names
        """
        if agent_domain:
            return [
                name for name, metadata in self.tool_metadata.items()
                if metadata.agent_domain == agent_domain
            ]
        return list(self.tools.keys())
        
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
            
        Returns:
            ToolResult from execution
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data={},
                error_message=f"Tool not found: {tool_name}"
            )
            
        return await tool.safe_execute(**kwargs)
        
    def discover_tools(self, module_path: str) -> int:
        """
        Discover and register tools from a module.
        
        Args:
            module_path: Python module path to scan
            
        Returns:
            Number of tools discovered
        """
        # This would implement dynamic tool discovery
        # For now, return 0 as placeholder
        self.logger.info(f"Tool discovery from {module_path} not yet implemented")
        return 0
        
    def get_tools_by_domain(self, domain: str) -> List[BaseTool]:
        """Get all tools for a specific agent domain."""
        return [
            tool for tool in self.tools.values()
            if tool.agent_domain == domain
        ]
        
    def validate_tool_chain(self, tool_names: List[str]) -> bool:
        """
        Validate that a chain of tools can be executed.
        
        Args:
            tool_names: List of tool names in execution order
            
        Returns:
            True if tool chain is valid
        """
        for tool_name in tool_names:
            if tool_name not in self.tools:
                self.logger.error(f"Tool not found in chain: {tool_name}")
                return False
        return True
        
    def shutdown(self) -> None:
        """Shutdown tool manager and cleanup resources."""
        self.logger.info("Shutting down tool manager")
        self.tools.clear()
        self.tool_metadata.clear()