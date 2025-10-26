"""
Tool registry for MCP server.

Manages tool registration, discovery, metadata, and execution
with comprehensive error handling and validation.
"""

from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, asdict
import logging
import inspect
import importlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncio

from ..tools.base import BaseTool, ToolResult, ToolMetadata
from ..agents.base import BaseAgent
from .protocol import MCPToolInfo


@dataclass
class ToolExecutionContext:
    """Context information for tool execution."""
    tool_name: str
    parameters: Dict[str, Any]
    execution_id: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class ToolExecutionLog:
    """Log entry for tool execution."""
    context: ToolExecutionContext
    result: ToolResult
    duration_ms: float
    success: bool
    error_details: Optional[str] = None


class ToolRegistry:
    """
    Manages tool registration, discovery, and execution for MCP server.
    
    Provides:
    - Dynamic tool loading and registration
    - Tool metadata management and validation
    - Tool execution with error handling and logging
    - Tool discovery from modules and agents
    """
    
    def __init__(self, max_concurrent_executions: int = 10):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_metadata: Dict[str, ToolMetadata] = {}
        self.execution_logs: List[ToolExecutionLog] = []
        self.execution_hooks: Dict[str, List[Callable]] = {
            "pre_execution": [],
            "post_execution": [],
            "on_error": []
        }
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_executions)
        self.logger = logging.getLogger("tool_registry")
        
    def register_tool(self, tool: BaseTool) -> bool:
        """
        Register a tool with the registry.
        
        Args:
            tool: Tool instance to register
            
        Returns:
            True if registration successful
        """
        try:
            # Validate tool
            if not self._validate_tool(tool):
                return False
                
            # Check for name conflicts
            if tool.name in self.tools:
                self.logger.warning(f"Tool {tool.name} already registered, overwriting")
                
            # Register tool
            self.tools[tool.name] = tool
            self.tool_metadata[tool.name] = tool.metadata
            
            self.logger.info(f"Registered tool: {tool.name} (domain: {tool.agent_domain})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register tool {tool.name}: {str(e)}")
            return False
            
    def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry.
        
        Args:
            tool_name: Name of tool to unregister
            
        Returns:
            True if unregistration successful
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            del self.tool_metadata[tool_name]
            self.logger.info(f"Unregistered tool: {tool_name}")
            return True
        else:
            self.logger.warning(f"Tool not found for unregistration: {tool_name}")
            return False
            
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a registered tool by name.
        
        Args:
            tool_name: Name of tool to retrieve
            
        Returns:
            Tool instance if found
        """
        return self.tools.get(tool_name)
        
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a tool.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            Tool metadata if found
        """
        return self.tool_metadata.get(tool_name)
        
    def list_tools(self, domain_filter: Optional[str] = None) -> List[str]:
        """
        List registered tools, optionally filtered by domain.
        
        Args:
            domain_filter: Optional domain to filter by
            
        Returns:
            List of tool names
        """
        if domain_filter:
            return [
                name for name, metadata in self.tool_metadata.items()
                if metadata.agent_domain == domain_filter
            ]
        return list(self.tools.keys())
        
    def get_mcp_tool_info(self, tool_name: str) -> Optional[MCPToolInfo]:
        """
        Get MCP-formatted tool information.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            MCP tool info if tool exists
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None
            
        return MCPToolInfo(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.get_parameters_schema()
        )
        
    def get_all_mcp_tool_info(self) -> List[MCPToolInfo]:
        """
        Get MCP-formatted information for all tools.
        
        Returns:
            List of MCP tool info objects
        """
        tool_info = []
        for tool_name in self.tools:
            info = self.get_mcp_tool_info(tool_name)
            if info:
                tool_info.append(info)
        return tool_info
        
    async def execute_tool(self, 
                          tool_name: str,
                          parameters: Dict[str, Any],
                          context: Optional[ToolExecutionContext] = None) -> ToolResult:
        """
        Execute a tool with error handling and logging.
        
        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            context: Optional execution context
            
        Returns:
            Tool execution result
        """
        start_time = datetime.now()
        
        # Create execution context if not provided
        if context is None:
            context = ToolExecutionContext(
                tool_name=tool_name,
                parameters=parameters,
                execution_id=f"{tool_name}_{start_time.timestamp()}",
                timestamp=start_time
            )
            
        try:
            # Get tool
            tool = self.get_tool(tool_name)
            if not tool:
                result = ToolResult(
                    tool_name=tool_name,
                    success=False,
                    data={},
                    error_message=f"Tool not found: {tool_name}"
                )
                self._log_execution(context, result, 0, False, "Tool not found")
                return result
                
            # Execute pre-execution hooks
            await self._execute_hooks("pre_execution", context)
            
            # Execute tool
            result = await tool.safe_execute(**parameters)
            
            # Calculate duration (use tool's execution time if available, otherwise calculate)
            if hasattr(result, 'execution_time') and result.execution_time > 0:
                duration_ms = result.execution_time * 1000
            else:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Execute appropriate hooks based on result
            if result.success:
                await self._execute_hooks("post_execution", context, result)
            else:
                # Create a mock exception for error hooks
                error = Exception(result.error_message or "Tool execution failed")
                await self._execute_hooks("on_error", context, error)
            
            # Log execution
            self._log_execution(context, result, duration_ms, result.success)
            
            return result
            
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Tool execution failed: {str(e)}"
            
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                data={},
                error_message=error_msg,
                execution_time=duration_ms / 1000
            )
            
            # Execute error hooks
            await self._execute_hooks("on_error", context, e)
            
            # Log execution
            self._log_execution(context, result, duration_ms, False, error_msg)
            
            return result
            
    def register_agent_tools(self, agent: BaseAgent) -> int:
        """
        Register all tools from an agent.
        
        Args:
            agent: Agent whose tools to register
            
        Returns:
            Number of tools registered
        """
        registered_count = 0
        
        for tool_name in agent.get_tool_names():
            tool = agent.get_tool(tool_name)
            if tool and self.register_tool(tool):
                registered_count += 1
                
        self.logger.info(f"Registered {registered_count} tools from agent: {agent.name}")
        return registered_count
        
    def discover_tools_from_module(self, module_path: str) -> int:
        """
        Discover and register tools from a Python module.
        
        Args:
            module_path: Python module path to scan
            
        Returns:
            Number of tools discovered and registered
        """
        try:
            module = importlib.import_module(module_path)
            registered_count = 0
            
            # Scan module for BaseTool subclasses
            for name in dir(module):
                obj = getattr(module, name)
                
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTool) and 
                    obj != BaseTool):
                    
                    try:
                        # Instantiate tool (assuming default constructor)
                        tool_instance = obj()
                        if self.register_tool(tool_instance):
                            registered_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to instantiate tool {name}: {str(e)}")
                        
            self.logger.info(f"Discovered {registered_count} tools from module: {module_path}")
            return registered_count
            
        except Exception as e:
            self.logger.error(f"Failed to discover tools from module {module_path}: {str(e)}")
            return 0
            
    def add_execution_hook(self, hook_type: str, hook_func: Callable) -> None:
        """
        Add an execution hook.
        
        Args:
            hook_type: Type of hook (pre_execution, post_execution, on_error)
            hook_func: Hook function to add
        """
        if hook_type in self.execution_hooks:
            self.execution_hooks[hook_type].append(hook_func)
            self.logger.info(f"Added {hook_type} hook")
        else:
            self.logger.error(f"Invalid hook type: {hook_type}")
            
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary containing execution statistics
        """
        total_executions = len(self.execution_logs)
        successful_executions = sum(1 for log in self.execution_logs if log.success)
        
        if total_executions == 0:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "tool_usage": {}
            }
            
        success_rate = successful_executions / total_executions
        average_duration = sum(log.duration_ms for log in self.execution_logs) / total_executions
        
        # Tool usage statistics
        tool_usage = {}
        for log in self.execution_logs:
            tool_name = log.context.tool_name
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {"count": 0, "success_count": 0}
            tool_usage[tool_name]["count"] += 1
            if log.success:
                tool_usage[tool_name]["success_count"] += 1
                
        return {
            "total_executions": total_executions,
            "success_rate": success_rate,
            "average_duration_ms": average_duration,
            "tool_usage": tool_usage
        }
        
    def _validate_tool(self, tool: BaseTool) -> bool:
        """
        Validate a tool before registration.
        
        Args:
            tool: Tool to validate
            
        Returns:
            True if tool is valid
        """
        if not isinstance(tool, BaseTool):
            self.logger.error(f"Tool must be instance of BaseTool: {type(tool)}")
            return False
            
        if not tool.name or not isinstance(tool.name, str):
            self.logger.error(f"Tool must have valid name: {tool.name}")
            return False
            
        if not tool.description or not isinstance(tool.description, str):
            self.logger.error(f"Tool must have valid description: {tool.description}")
            return False
            
        try:
            # Validate that tool can provide parameter schema
            schema = tool.get_parameters_schema()
            if not isinstance(schema, dict):
                self.logger.error(f"Tool parameter schema must be dict: {type(schema)}")
                return False
        except Exception as e:
            self.logger.error(f"Tool parameter schema validation failed: {str(e)}")
            return False
            
        return True
        
    async def _execute_hooks(self, hook_type: str, *args) -> None:
        """
        Execute hooks of a specific type.
        
        Args:
            hook_type: Type of hook to execute
            *args: Arguments to pass to hooks
        """
        hooks = self.execution_hooks.get(hook_type, [])
        for hook in hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(*args)
                else:
                    hook(*args)
            except Exception as e:
                self.logger.error(f"Hook execution failed ({hook_type}): {str(e)}")
                
    def _log_execution(self, 
                      context: ToolExecutionContext,
                      result: ToolResult,
                      duration_ms: float,
                      success: bool,
                      error_details: Optional[str] = None) -> None:
        """
        Log tool execution.
        
        Args:
            context: Execution context
            result: Execution result
            duration_ms: Execution duration in milliseconds
            success: Whether execution was successful
            error_details: Error details if any
        """
        log_entry = ToolExecutionLog(
            context=context,
            result=result,
            duration_ms=duration_ms,
            success=success,
            error_details=error_details
        )
        
        self.execution_logs.append(log_entry)
        
        # Keep only last 1000 log entries to prevent memory issues
        if len(self.execution_logs) > 1000:
            self.execution_logs = self.execution_logs[-1000:]
            
    def shutdown(self) -> None:
        """Shutdown the tool registry and cleanup resources."""
        self.logger.info("Shutting down tool registry")
        self.executor.shutdown(wait=True)
        self.tools.clear()
        self.tool_metadata.clear()
        self.execution_logs.clear()
        self.execution_hooks.clear()