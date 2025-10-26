"""
Base agent classes and agent management functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..models.core import MortgageApplication
from ..models.assessment import AssessmentResult
from ..tools.base import BaseTool


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime


class BaseAgent(ABC):
    """
    Abstract base class for all mortgage processing agents.
    
    Each agent specializes in a specific domain of mortgage processing
    and is equipped with dedicated tools to perform their tasks.
    """
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger(f"agent.{name}")
        self.state: Dict[str, Any] = {}
        
    @abstractmethod
    def get_tool_names(self) -> List[str]:
        """Return list of tool names this agent uses."""
        pass
        
    @abstractmethod
    async def process(self, application: MortgageApplication, context: Dict[str, Any]) -> AssessmentResult:
        """
        Process mortgage application data using agent's specialized tools.
        
        Args:
            application: The mortgage application to process
            context: Additional context data from other agents
            
        Returns:
            AssessmentResult containing the agent's analysis
        """
        pass
        
    def register_tool(self, tool_name: str, tool: BaseTool) -> None:
        """Register a tool with this agent."""
        self.tools[tool_name] = tool
        self.logger.info(f"Registered tool: {tool_name}")
        
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a registered tool by name."""
        return self.tools.get(tool_name)
        
    async def send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]) -> None:
        """Send message to another agent."""
        message = AgentMessage(
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now()
        )
        # Message will be handled by AgentManager
        await self._send_message_via_manager(message)
        
    async def _send_message_via_manager(self, message: AgentMessage) -> None:
        """Internal method to send message via agent manager."""
        # This will be implemented when AgentManager is created
        pass
        
    async def handle_message(self, message: AgentMessage) -> None:
        """
        Handle incoming message from another agent.
        
        Args:
            message: The message to handle
        """
        self.logger.info(f"Received message from {message.sender}: {message.message_type}")
        
        # Default implementation - subclasses can override for specific behavior
        if message.message_type == "state_update":
            # Update local state with shared data
            for key, value in message.payload.items():
                self.update_state(f"shared_{key}", value)
        elif message.message_type == "request_data":
            # Respond with requested data
            requested_keys = message.payload.get("keys", [])
            response_data = {key: self.get_state(key) for key in requested_keys if self.get_state(key) is not None}
            await self.send_message(message.sender, "data_response", response_data)
        else:
            self.logger.warning(f"Unknown message type: {message.message_type}")
        
    def update_state(self, key: str, value: Any) -> None:
        """Update agent state."""
        self.state[key] = value
        
    def get_state(self, key: str) -> Any:
        """Get value from agent state."""
        return self.state.get(key)


class AgentManager:
    """
    Manages agent lifecycle, communication, and coordination.
    
    Responsible for:
    - Agent instantiation and registration
    - Message routing between agents
    - State synchronization
    - Workflow coordination
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: List[AgentMessage] = []
        self.logger = logging.getLogger("agent_manager")
        self._setup_agent_manager_reference()
        
    def _setup_agent_manager_reference(self) -> None:
        """Set up reference to this manager in BaseAgent class."""
        BaseAgent._agent_manager = self
        
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the manager."""
        self.agents[agent.agent_id] = agent
        # Set up the agent's message sending capability
        agent._send_message_via_manager = self._route_message_from_agent
        self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
        
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
        
    async def _route_message_from_agent(self, message: AgentMessage) -> None:
        """Route message from an agent to another agent."""
        await self.route_message(message)
        
    async def route_message(self, message: AgentMessage) -> None:
        """Route message to the appropriate agent."""
        recipient_agent = self.get_agent(message.recipient)
        if recipient_agent:
            await recipient_agent.handle_message(message)
            self.logger.info(f"Routed message from {message.sender} to {message.recipient}")
        else:
            self.logger.error(f"Agent not found: {message.recipient}")
            
    async def broadcast_message(self, sender_id: str, message_type: str, payload: Dict[str, Any]) -> None:
        """Broadcast message to all agents except sender."""
        for agent_id, agent in self.agents.items():
            if agent_id != sender_id:
                message = AgentMessage(
                    sender=sender_id,
                    recipient=agent_id,
                    message_type=message_type,
                    payload=payload,
                    timestamp=datetime.now()
                )
                await agent.handle_message(message)
            
    async def coordinate_workflow(self, application: MortgageApplication) -> Dict[str, AssessmentResult]:
        """
        Coordinate workflow execution across all agents.
        
        Args:
            application: The mortgage application to process
            
        Returns:
            Dictionary of assessment results from each agent
        """
        results = {}
        context = {}
        
        # Process agents in sequence, passing context between them
        for agent_id, agent in self.agents.items():
            try:
                result = await agent.process(application, context)
                results[agent_id] = result
                
                # Update context with results for next agents
                context[agent_id] = result.tool_results
                
                self.logger.info(f"Completed processing for agent: {agent.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing agent {agent.name}: {str(e)}")
                # Continue with other agents even if one fails
                
        return results
        
    def get_all_agents(self) -> List[BaseAgent]:
        """Get list of all registered agents."""
        return list(self.agents.values())
        
    def shutdown(self) -> None:
        """Shutdown all agents and cleanup resources."""
        self.logger.info("Shutting down agent manager")
        self.agents.clear()
        self.message_queue.clear()