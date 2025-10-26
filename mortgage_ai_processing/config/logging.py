"""
Logging configuration for mortgage processing system.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .settings import LoggingConfig


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        config: Logging configuration. If None, uses default configuration.
    """
    if config is None:
        config = LoggingConfig()
        
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if configured)
    if config.file_path:
        file_path = Path(config.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    # Set specific logger levels
    _configure_specific_loggers()
    
    logging.info("Logging configuration initialized")


def _configure_specific_loggers() -> None:
    """Configure specific logger levels for different components."""
    
    # Set Azure SDK logging to WARNING to reduce noise
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("azure.core").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)
    
    # Set HTTP client logging to WARNING
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # Set our application loggers to appropriate levels
    logging.getLogger("mortgage_ai_processing").setLevel(logging.INFO)
    logging.getLogger("agent_manager").setLevel(logging.INFO)
    logging.getLogger("tool_manager").setLevel(logging.INFO)
    logging.getLogger("mcp_server").setLevel(logging.INFO)
    logging.getLogger("credential_manager").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_function_call(func_name: str, args: dict, result: any = None, error: Exception = None) -> None:
    """
    Log function call details for debugging.
    
    Args:
        func_name: Name of the function
        args: Function arguments
        result: Function result (if successful)
        error: Exception (if failed)
    """
    logger = logging.getLogger("function_calls")
    
    if error:
        logger.error(f"Function {func_name} failed with args {args}: {str(error)}")
    else:
        logger.debug(f"Function {func_name} called with args {args}, result: {result}")


def log_agent_activity(agent_name: str, activity: str, details: dict = None) -> None:
    """
    Log agent activity for monitoring and debugging.
    
    Args:
        agent_name: Name of the agent
        activity: Description of the activity
        details: Additional details
    """
    logger = logging.getLogger(f"agent.{agent_name}")
    
    if details:
        logger.info(f"{activity}: {details}")
    else:
        logger.info(activity)


def log_tool_execution(tool_name: str, execution_time: float, success: bool, error: str = None) -> None:
    """
    Log tool execution metrics.
    
    Args:
        tool_name: Name of the tool
        execution_time: Execution time in seconds
        success: Whether execution was successful
        error: Error message if failed
    """
    logger = logging.getLogger(f"tool.{tool_name}")
    
    if success:
        logger.info(f"Tool executed successfully in {execution_time:.2f}s")
    else:
        logger.error(f"Tool execution failed in {execution_time:.2f}s: {error}")


def log_mcp_request(method: str, params: dict, response_time: float, success: bool) -> None:
    """
    Log MCP request details.
    
    Args:
        method: MCP method name
        params: Request parameters
        response_time: Response time in seconds
        success: Whether request was successful
    """
    logger = logging.getLogger("mcp_requests")
    
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"MCP {method} - {status} - {response_time:.3f}s - params: {params}")


class ContextFilter(logging.Filter):
    """Custom logging filter to add context information."""
    
    def __init__(self, context: dict):
        super().__init__()
        self.context = context
        
    def filter(self, record):
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def add_context_to_logger(logger_name: str, context: dict) -> None:
    """
    Add context information to a logger.
    
    Args:
        logger_name: Name of the logger
        context: Context dictionary to add
    """
    logger = logging.getLogger(logger_name)
    context_filter = ContextFilter(context)
    logger.addFilter(context_filter)