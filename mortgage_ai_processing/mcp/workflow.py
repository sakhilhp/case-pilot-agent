"""
Workflow orchestration engine for mortgage processing.

Provides workflow definition, execution sequencing, conditional workflow support,
and comprehensive error handling for coordinating multi-agent mortgage processing.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
from contextlib import asynccontextmanager

from ..models.core import MortgageApplication
from ..models.assessment import AssessmentResult
from ..agents.base import BaseAgent, AgentManager


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Status of individual workflow steps."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class WorkflowContext:
    """Context data shared across workflow steps."""
    application: MortgageApplication
    results: Dict[str, AssessmentResult] = field(default_factory=dict)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_result(self, agent_name: str) -> Optional[AssessmentResult]:
        """Get assessment result from a specific agent."""
        return self.results.get(agent_name)
        
    def set_result(self, agent_name: str, result: AssessmentResult) -> None:
        """Set assessment result for an agent."""
        self.results[agent_name] = result
        
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Get shared data by key."""
        return self.shared_data.get(key, default)
        
    def set_shared_data(self, key: str, value: Any) -> None:
        """Set shared data."""
        self.shared_data[key] = value


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    step_id: str
    name: str
    agent_id: Optional[str] = None
    condition: Optional[Callable[[WorkflowContext], bool]] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[float] = None
    depends_on: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def can_execute(self, context: WorkflowContext, completed_steps: set) -> bool:
        """Check if step can be executed based on dependencies and conditions."""
        # Check dependencies
        for dep in self.depends_on:
            if dep not in completed_steps:
                return False
                
        # Check condition if provided
        if self.condition and not self.condition(context):
            return False
            
        return True
        
    def should_retry(self) -> bool:
        """Check if step should be retried."""
        return self.status == StepStatus.FAILED and self.retry_count < self.max_retries


@dataclass
class WorkflowDefinition:
    """Definition of a workflow with steps and configuration."""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    parallel_execution: bool = False
    timeout_seconds: Optional[float] = None
    error_handling: str = "continue"  # "continue", "stop", "retry"
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
        
    def get_executable_steps(self, context: WorkflowContext, completed_steps: set) -> List[WorkflowStep]:
        """Get steps that can be executed now."""
        return [
            step for step in self.steps
            if (step.status == StepStatus.PENDING and 
                step.step_id not in completed_steps and 
                step.can_execute(context, completed_steps))
        ]


@dataclass
class WorkflowExecution:
    """Runtime execution state of a workflow."""
    execution_id: str
    workflow_definition: WorkflowDefinition
    context: WorkflowContext
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    completed_steps: set = field(default_factory=set)
    
    def get_progress(self) -> float:
        """Get workflow progress as percentage."""
        if not self.workflow_definition.steps:
            return 100.0
        return (len(self.completed_steps) / len(self.workflow_definition.steps)) * 100.0


class WorkflowEngine:
    """
    Orchestrates workflow execution with support for:
    - Sequential and parallel execution
    - Conditional steps
    - Error handling and retries
    - State management
    """
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.logger = logging.getLogger("workflow_engine")
        
    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition."""
        self.workflows[workflow.workflow_id] = workflow
        self.logger.info(f"Registered workflow: {workflow.name}")
        
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID."""
        return self.workflows.get(workflow_id)
        
    async def execute_workflow(
        self, 
        workflow_id: str, 
        application: MortgageApplication,
        execution_id: Optional[str] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow with the given application.
        
        Args:
            workflow_id: ID of workflow to execute
            application: Mortgage application to process
            execution_id: Optional custom execution ID
            
        Returns:
            WorkflowExecution with results
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        if execution_id is None:
            execution_id = f"{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        # Create execution context
        context = WorkflowContext(application=application)
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_definition=workflow,
            context=context,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        self.logger.info(f"Starting workflow execution: {execution_id}")
        
        try:
            if workflow.parallel_execution:
                await self._execute_parallel(execution)
            else:
                await self._execute_sequential(execution)
                
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            self.logger.info(f"Workflow execution completed: {execution_id}")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            self.logger.error(f"Workflow execution failed: {execution_id} - {str(e)}")
            
            # Don't re-raise - let the caller check the execution status
                
        return execution
        
    async def _execute_sequential(self, execution: WorkflowExecution) -> None:
        """Execute workflow steps sequentially."""
        workflow = execution.workflow_definition
        context = execution.context
        
        while True:
            executable_steps = workflow.get_executable_steps(context, execution.completed_steps)
            
            if not executable_steps:
                # Check for retry opportunities first
                retry_steps = [s for s in workflow.steps if s.should_retry()]
                if retry_steps:
                    for step in retry_steps:
                        step.status = StepStatus.PENDING
                        step.retry_count += 1
                        step.error_message = None
                        step.started_at = None
                        step.completed_at = None
                    continue
                    
                # Check if there are any pending steps that might become executable
                pending_steps = [s for s in workflow.steps if s.status == StepStatus.PENDING]
                if not pending_steps:
                    # Check if all steps are either completed or failed beyond retry
                    all_steps_final = all(
                        s.status == StepStatus.COMPLETED or 
                        (s.status == StepStatus.FAILED and not s.should_retry())
                        for s in workflow.steps
                    )
                    if all_steps_final:
                        break  # All steps completed or failed beyond retry
                    
                # No executable steps and no retries - workflow stuck
                raise RuntimeError("Workflow execution stuck - no executable steps")
                
            # Execute next available step
            step = executable_steps[0]
            await self._execute_step(step, context)
            
            if step.status == StepStatus.COMPLETED:
                execution.completed_steps.add(step.step_id)
            elif step.status == StepStatus.FAILED:
                if workflow.error_handling == "stop":
                    raise RuntimeError(f"Step failed: {step.name} - {step.error_message}")
                # For "continue" error handling, the step will be retried if possible
                
    async def _execute_parallel(self, execution: WorkflowExecution) -> None:
        """Execute workflow steps in parallel where possible."""
        workflow = execution.workflow_definition
        context = execution.context
        
        while True:
            executable_steps = workflow.get_executable_steps(context, execution.completed_steps)
            
            if not executable_steps:
                # Handle retries first
                retry_steps = [s for s in workflow.steps if s.should_retry()]
                if retry_steps:
                    for step in retry_steps:
                        step.status = StepStatus.PENDING
                        step.retry_count += 1
                        step.error_message = None
                        step.started_at = None
                        step.completed_at = None
                    continue
                    
                pending_steps = [s for s in workflow.steps if s.status == StepStatus.PENDING]
                if not pending_steps:
                    # Check if all steps are either completed or failed beyond retry
                    all_steps_final = all(
                        s.status == StepStatus.COMPLETED or 
                        (s.status == StepStatus.FAILED and not s.should_retry())
                        for s in workflow.steps
                    )
                    if all_steps_final:
                        break  # All steps completed or failed beyond retry
                    
                raise RuntimeError("Workflow execution stuck - no executable steps")
                
            # Execute all available steps in parallel
            tasks = [self._execute_step(step, context) for step in executable_steps]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update completed steps
            for step in executable_steps:
                if step.status == StepStatus.COMPLETED:
                    execution.completed_steps.add(step.step_id)
                elif step.status == StepStatus.FAILED:
                    if workflow.error_handling == "stop":
                        raise RuntimeError(f"Step failed: {step.name} - {step.error_message}")
                    # For "continue" error handling, the step will be retried if possible
                    
    async def _execute_step(self, step: WorkflowStep, context: WorkflowContext) -> None:
        """Execute an individual workflow step."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        try:
            self.logger.info(f"Executing step: {step.name}")
            
            if step.agent_id:
                # Execute agent-based step
                agent = self.agent_manager.get_agent(step.agent_id)
                if not agent:
                    raise ValueError(f"Agent not found: {step.agent_id}")
                    
                # Execute with timeout if specified
                if step.timeout_seconds:
                    result = await asyncio.wait_for(
                        agent.process(context.application, context.shared_data),
                        timeout=step.timeout_seconds
                    )
                else:
                    result = await agent.process(context.application, context.shared_data)
                    
                # Store result in context
                context.set_result(step.agent_id, result)
                
            else:
                # Custom step execution (can be extended for non-agent steps)
                self.logger.info(f"Executing custom step: {step.name}")
                
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            self.logger.info(f"Step completed: {step.name}")
            
        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.error_message = f"Step timed out after {step.timeout_seconds} seconds"
            step.completed_at = datetime.now()
            self.logger.error(f"Step timed out: {step.name}")
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.completed_at = datetime.now()
            self.logger.error(f"Step failed: {step.name} - {str(e)}")
            
    def pause_workflow(self, execution_id: str) -> bool:
        """Pause a running workflow."""
        execution = self.executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.PAUSED
            self.logger.info(f"Workflow paused: {execution_id}")
            return True
        return False
        
    def resume_workflow(self, execution_id: str) -> bool:
        """Resume a paused workflow."""
        execution = self.executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.PAUSED:
            execution.status = WorkflowStatus.RUNNING
            self.logger.info(f"Workflow resumed: {execution_id}")
            return True
        return False
        
    def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running or paused workflow."""
        execution = self.executions.get(execution_id)
        if execution and execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            self.logger.info(f"Workflow cancelled: {execution_id}")
            return True
        return False
        
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        return self.executions.get(execution_id)
        
    def list_executions(self, status: Optional[WorkflowStatus] = None) -> List[WorkflowExecution]:
        """List workflow executions, optionally filtered by status."""
        executions = list(self.executions.values())
        if status:
            executions = [e for e in executions if e.status == status]
        return executions
        
    def create_mortgage_processing_workflow(self) -> WorkflowDefinition:
        """
        Create the standard mortgage processing workflow.
        
        Returns:
            WorkflowDefinition for complete mortgage processing
        """
        steps = [
            WorkflowStep(
                step_id="document_processing",
                name="Document Processing",
                agent_id="doc_agent",
                timeout_seconds=300.0
            ),
            WorkflowStep(
                step_id="income_verification",
                name="Income Verification",
                agent_id="income_agent",
                depends_on=["document_processing"],
                timeout_seconds=180.0
            ),
            WorkflowStep(
                step_id="credit_assessment",
                name="Credit Assessment",
                agent_id="credit_agent",
                depends_on=["document_processing"],
                timeout_seconds=120.0
            ),
            WorkflowStep(
                step_id="property_assessment",
                name="Property Assessment",
                agent_id="property_agent",
                depends_on=["document_processing"],
                timeout_seconds=240.0
            ),
            WorkflowStep(
                step_id="risk_assessment",
                name="Risk Assessment",
                agent_id="risk_agent",
                depends_on=["income_verification", "credit_assessment", "property_assessment"],
                timeout_seconds=150.0
            ),
            WorkflowStep(
                step_id="underwriting",
                name="Underwriting Decision",
                agent_id="underwriting_agent",
                depends_on=["risk_assessment"],
                timeout_seconds=120.0
            )
        ]
        
        return WorkflowDefinition(
            workflow_id="mortgage_processing",
            name="Complete Mortgage Processing",
            description="End-to-end mortgage application processing workflow",
            steps=steps,
            parallel_execution=False,
            timeout_seconds=1800.0,  # 30 minutes total
            error_handling="continue"
        )
        
    def cleanup_completed_executions(self, older_than_hours: int = 24) -> int:
        """
        Clean up completed workflow executions older than specified hours.
        
        Args:
            older_than_hours: Remove executions older than this many hours
            
        Returns:
            Number of executions removed
        """
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        removed_count = 0
        
        execution_ids_to_remove = []
        for execution_id, execution in self.executions.items():
            if (execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                execution.completed_at and execution.completed_at.timestamp() < cutoff_time):
                execution_ids_to_remove.append(execution_id)
                
        for execution_id in execution_ids_to_remove:
            del self.executions[execution_id]
            removed_count += 1
            
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} old workflow executions")
            
        return removed_count