"""
Complete end-to-end mortgage processing workflow orchestrator.

This module provides the main entry point for executing complete mortgage processing
workflows that coordinate all agents and handle the full application lifecycle.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .agents.base import AgentManager
from .agents.document_processing import DocumentProcessingAgent
from .agents.income_verification import IncomeVerificationAgent
from .agents.credit_assessment import CreditAssessmentAgent
from .agents.property_assessment import PropertyAssessmentAgent
from .agents.risk_assessment import RiskAssessmentAgent
from .agents.underwriting import UnderwritingAgent
from .mcp.workflow import WorkflowEngine, WorkflowDefinition, WorkflowStep, WorkflowExecution, WorkflowStatus
from .tools.base import ToolManager
from .models.core import MortgageApplication
from .models.assessment import AssessmentResult, LoanDecision, DecisionFactors, AdverseAction
from .models.enums import ProcessingStatus, DecisionType, RiskLevel


class ProcessingPhase(Enum):
    """Phases of mortgage processing workflow."""
    INITIALIZATION = "initialization"
    DOCUMENT_PROCESSING = "document_processing"
    INCOME_VERIFICATION = "income_verification"
    CREDIT_ASSESSMENT = "credit_assessment"
    PROPERTY_ASSESSMENT = "property_assessment"
    RISK_ASSESSMENT = "risk_assessment"
    UNDERWRITING = "underwriting"
    FINALIZATION = "finalization"


@dataclass
class WorkflowProgress:
    """Progress tracking for workflow execution."""
    current_phase: ProcessingPhase
    completed_phases: List[ProcessingPhase] = field(default_factory=list)
    phase_results: Dict[ProcessingPhase, AssessmentResult] = field(default_factory=dict)
    phase_errors: Dict[ProcessingPhase, List[str]] = field(default_factory=dict)
    overall_progress_percent: float = 0.0
    estimated_completion_time: Optional[datetime] = None
    
    def get_phase_status(self, phase: ProcessingPhase) -> str:
        """Get status of a specific phase."""
        if phase in self.completed_phases:
            return "completed"
        elif phase == self.current_phase:
            return "in_progress"
        else:
            return "pending"


@dataclass
class WorkflowConfiguration:
    """Configuration for workflow execution."""
    parallel_assessment: bool = True  # Run credit, income, property assessment in parallel
    timeout_seconds: float = 1800.0  # 30 minutes total timeout
    retry_failed_steps: bool = True
    max_retries: int = 3
    continue_on_non_critical_errors: bool = True
    generate_intermediate_reports: bool = False
    enable_state_persistence: bool = True


class MortgageProcessingOrchestrator:
    """
    Main orchestrator for complete mortgage processing workflows.
    
    This class coordinates the entire mortgage processing pipeline:
    1. Document Processing - Extract and validate all documents
    2. Parallel Assessment Phase:
       - Income Verification - Verify employment and income
       - Credit Assessment - Analyze credit history and scores
       - Property Assessment - Evaluate property value and risk
    3. Risk Assessment - Consolidate all risk factors
    4. Underwriting - Make final loan decision
    
    Features:
    - Progress tracking and state management
    - Error handling and recovery mechanisms
    - Parallel execution where appropriate
    - Comprehensive logging and audit trails
    - Integration with MCP server endpoints
    """
    
    def __init__(self, config: Optional[WorkflowConfiguration] = None):
        self.config = config or WorkflowConfiguration()
        self.logger = logging.getLogger("mortgage_orchestrator")
        
        # Initialize core components
        self.agent_manager = AgentManager()
        self.tool_manager = ToolManager()
        self.workflow_engine = WorkflowEngine(self.agent_manager)
        
        # Track active workflows
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_progress: Dict[str, WorkflowProgress] = {}
        
        # Initialize agents and tools
        self._initialize_agents()
        self._register_workflows()
        
    def _initialize_agents(self) -> None:
        """Initialize and register all mortgage processing agents."""
        self.logger.info("Initializing mortgage processing agents")
        
        # Create agent instances
        agents = [
            DocumentProcessingAgent("doc_agent"),
            IncomeVerificationAgent("income_agent"),
            CreditAssessmentAgent("credit_agent"),
            PropertyAssessmentAgent("property_agent"),
            RiskAssessmentAgent("risk_agent"),
            UnderwritingAgent("underwriting_agent")
        ]
        
        # Register agents with manager
        for agent in agents:
            self.agent_manager.register_agent(agent)
        
        # Register tools with agents and tool manager
        self._register_enhanced_tools()
                    
        self.logger.info(f"Initialized {len(agents)} agents with {len(self.tool_manager.tools)} tools")
    
    def _register_enhanced_tools(self) -> None:
        """Register tools with agents and tool manager using the fixed registry."""
        try:
            from .tools.tool_registry_fixed import get_fixed_tools_registry
            
            registry = get_fixed_tools_registry()
            
            # Register tools with tool manager
            registry.register_tools_with_manager(self.tool_manager)
            
            # Register tools with agents
            registry.register_tools_with_agents(self.agent_manager)
            
            self.logger.info("Successfully registered tools with correct agent-expected names")
            
        except Exception as e:
            self.logger.error(f"Could not register tools: {e}")
            # This is critical - agents won't work without tools
            raise
        
    def _register_workflows(self) -> None:
        """Register standard mortgage processing workflows."""
        # Register the standard mortgage processing workflow
        standard_workflow = self._create_standard_workflow()
        self.workflow_engine.register_workflow(standard_workflow)
        
        # Register parallel assessment workflow
        parallel_workflow = self._create_parallel_assessment_workflow()
        self.workflow_engine.register_workflow(parallel_workflow)
        
        self.logger.info("Registered standard mortgage processing workflows")
        
    def _create_standard_workflow(self) -> WorkflowDefinition:
        """Create the standard sequential mortgage processing workflow."""
        steps = [
            WorkflowStep(
                step_id="document_processing",
                name="Document Processing and Validation",
                agent_id="doc_agent",
                timeout_seconds=300.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="income_verification",
                name="Income and Employment Verification",
                agent_id="income_agent",
                depends_on=["document_processing"],
                timeout_seconds=180.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="credit_assessment",
                name="Credit History and Score Analysis",
                agent_id="credit_agent",
                depends_on=["document_processing"],
                timeout_seconds=120.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="property_assessment",
                name="Property Valuation and Risk Analysis",
                agent_id="property_agent",
                depends_on=["document_processing"],
                timeout_seconds=240.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="risk_assessment",
                name="Consolidated Risk Assessment",
                agent_id="risk_agent",
                depends_on=["income_verification", "credit_assessment", "property_assessment"],
                timeout_seconds=150.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="underwriting",
                name="Final Underwriting Decision",
                agent_id="underwriting_agent",
                depends_on=["risk_assessment"],
                timeout_seconds=120.0,
                max_retries=self.config.max_retries
            )
        ]
        
        return WorkflowDefinition(
            workflow_id="standard_mortgage_processing",
            name="Standard Mortgage Processing Workflow",
            description="Complete sequential mortgage processing with document validation, assessment, and underwriting",
            steps=steps,
            parallel_execution=False,
            timeout_seconds=self.config.timeout_seconds,
            error_handling="continue" if self.config.continue_on_non_critical_errors else "stop"
        )
        
    def _create_parallel_assessment_workflow(self) -> WorkflowDefinition:
        """Create workflow with parallel assessment phase for faster processing."""
        steps = [
            WorkflowStep(
                step_id="document_processing",
                name="Document Processing and Validation",
                agent_id="doc_agent",
                timeout_seconds=300.0,
                max_retries=self.config.max_retries
            ),
            # Parallel assessment phase
            WorkflowStep(
                step_id="income_verification",
                name="Income and Employment Verification",
                agent_id="income_agent",
                depends_on=["document_processing"],
                timeout_seconds=180.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="credit_assessment",
                name="Credit History and Score Analysis",
                agent_id="credit_agent",
                depends_on=["document_processing"],
                timeout_seconds=120.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="property_assessment",
                name="Property Valuation and Risk Analysis",
                agent_id="property_agent",
                depends_on=["document_processing"],
                timeout_seconds=240.0,
                max_retries=self.config.max_retries
            ),
            # Sequential final phases
            WorkflowStep(
                step_id="risk_assessment",
                name="Consolidated Risk Assessment",
                agent_id="risk_agent",
                depends_on=["income_verification", "credit_assessment", "property_assessment"],
                timeout_seconds=150.0,
                max_retries=self.config.max_retries
            ),
            WorkflowStep(
                step_id="underwriting",
                name="Final Underwriting Decision",
                agent_id="underwriting_agent",
                depends_on=["risk_assessment"],
                timeout_seconds=120.0,
                max_retries=self.config.max_retries
            )
        ]
        
        return WorkflowDefinition(
            workflow_id="parallel_mortgage_processing",
            name="Parallel Assessment Mortgage Processing",
            description="Mortgage processing with parallel income, credit, and property assessment",
            steps=steps,
            parallel_execution=True,
            timeout_seconds=self.config.timeout_seconds,
            error_handling="continue" if self.config.continue_on_non_critical_errors else "stop"
        )
        
    async def process_mortgage_application(
        self,
        application: MortgageApplication,
        workflow_type: str = "parallel_mortgage_processing",
        execution_id: Optional[str] = None
    ) -> Tuple[WorkflowExecution, LoanDecision]:
        """
        Process a complete mortgage application through the full workflow.
        
        Args:
            application: The mortgage application to process
            workflow_type: Type of workflow to use ("standard_mortgage_processing" or "parallel_mortgage_processing")
            execution_id: Optional custom execution ID
            
        Returns:
            Tuple of (WorkflowExecution, LoanDecision)
        """
        if execution_id is None:
            execution_id = f"mortgage_{application.application_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        self.logger.info(f"Starting mortgage processing for application {application.application_id}")
        
        # Initialize progress tracking
        progress = WorkflowProgress(current_phase=ProcessingPhase.INITIALIZATION)
        self.workflow_progress[execution_id] = progress
        
        try:
            # Update application status
            application.processing_status = ProcessingStatus.IN_PROGRESS
            
            # Execute the workflow
            execution = await self.workflow_engine.execute_workflow(
                workflow_type,
                application,
                execution_id
            )
            
            self.active_workflows[execution_id] = execution
            
            # Update progress tracking
            await self._update_progress_tracking(execution_id, execution)
            
            # Extract final loan decision from underwriting results
            loan_decision = self._extract_loan_decision(execution)
            
            # Update application with final status
            if execution.status == WorkflowStatus.COMPLETED:
                if loan_decision.decision == DecisionType.APPROVE:
                    application.processing_status = ProcessingStatus.APPROVED
                elif loan_decision.decision == DecisionType.DENY:
                    application.processing_status = ProcessingStatus.DENIED
                else:
                    application.processing_status = ProcessingStatus.REQUIRES_REVIEW
            else:
                application.processing_status = ProcessingStatus.FAILED
                
            self.logger.info(f"Mortgage processing completed for application {application.application_id}: {loan_decision.decision}")
            
            return execution, loan_decision
            
        except Exception as e:
            self.logger.error(f"Mortgage processing failed for application {application.application_id}: {str(e)}")
            application.processing_status = ProcessingStatus.FAILED
            
            # Create detailed error loan decision
            from .models.assessment import DecisionFactors, AdverseAction
            import traceback
            
            # Get detailed error information
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            # Try to get partial execution results if available
            execution = self.active_workflows.get(execution_id)
            failed_steps = []
            completed_steps = []
            
            if execution:
                completed_steps = list(execution.completed_steps)
                # Identify which step likely failed
                all_steps = [step.step_id for step in execution.workflow_definition.steps]
                failed_steps = [step for step in all_steps if step not in completed_steps]
            
            # Create detailed adverse actions
            adverse_actions = [
                AdverseAction(
                    reason_code="SYS001",
                    reason_description=f"System error during processing: {error_type} - {error_message}",
                    category="system_error"
                )
            ]
            
            # Add step-specific information if available
            if failed_steps:
                for i, step in enumerate(failed_steps):
                    step_name = self._get_step_display_name(step)
                    adverse_actions.append(AdverseAction(
                        reason_code=f"STEP{i+1:03d}",
                        reason_description=f"Processing failed at {step_name}",
                        category="processing_error"
                    ))
            
            # Build detailed rationale
            rationale_parts = [
                f"Application processing failed with {error_type}: {error_message}"
            ]
            
            if completed_steps:
                rationale_parts.append(f"Successfully completed steps: {', '.join([self._get_step_display_name(s) for s in completed_steps])}")
            
            if failed_steps:
                rationale_parts.append(f"Failed at steps: {', '.join([self._get_step_display_name(s) for s in failed_steps])}")
            
            error_decision = LoanDecision(
                application_id=application.application_id,
                decision=DecisionType.DENY,
                decision_factors=DecisionFactors(
                    eligibility_score=0.0,
                    risk_score=100.0,
                    compliance_score=0.0,
                    policy_score=0.0
                ),
                overall_score=0.0,
                conditions=[],
                adverse_actions=adverse_actions,
                loan_terms=None,
                generated_letters={},
                decision_rationale=" | ".join(rationale_parts),
                created_by="system_orchestrator"
            )
            
            # Create failed execution if not already created
            if execution_id not in self.active_workflows:
                from .mcp.workflow import WorkflowExecution, WorkflowContext
                context = WorkflowContext(application=application)
                execution = WorkflowExecution(
                    execution_id=execution_id,
                    workflow_definition=self.workflow_engine.get_workflow(workflow_type),
                    context=context,
                    status=WorkflowStatus.FAILED,
                    error_message=f"{error_type}: {error_message}"
                )
                self.active_workflows[execution_id] = execution
            
            return self.active_workflows[execution_id], error_decision
            
    async def _update_progress_tracking(self, execution_id: str, execution: WorkflowExecution) -> None:
        """Update progress tracking for a workflow execution."""
        progress = self.workflow_progress.get(execution_id)
        if not progress:
            return
            
        # Map workflow steps to processing phases
        step_to_phase = {
            "document_processing": ProcessingPhase.DOCUMENT_PROCESSING,
            "income_verification": ProcessingPhase.INCOME_VERIFICATION,
            "credit_assessment": ProcessingPhase.CREDIT_ASSESSMENT,
            "property_assessment": ProcessingPhase.PROPERTY_ASSESSMENT,
            "risk_assessment": ProcessingPhase.RISK_ASSESSMENT,
            "underwriting": ProcessingPhase.UNDERWRITING
        }
        
        # Update completed phases
        for step_id in execution.completed_steps:
            phase = step_to_phase.get(step_id)
            if phase and phase not in progress.completed_phases:
                progress.completed_phases.append(phase)
                
                # Store phase results
                agent_id = self._get_agent_id_for_step(step_id)
                if agent_id:
                    result = execution.context.get_result(agent_id)
                    if result:
                        progress.phase_results[phase] = result
        
        # Update current phase
        if execution.status == WorkflowStatus.COMPLETED:
            progress.current_phase = ProcessingPhase.FINALIZATION
        else:
            # Find the current phase based on running steps
            for step in execution.workflow_definition.steps:
                if step.step_id not in execution.completed_steps:
                    phase = step_to_phase.get(step.step_id)
                    if phase:
                        progress.current_phase = phase
                        break
        
        # Calculate overall progress
        total_phases = len(ProcessingPhase)
        completed_count = len(progress.completed_phases)
        progress.overall_progress_percent = (completed_count / total_phases) * 100.0
        
    def _get_agent_id_for_step(self, step_id: str) -> Optional[str]:
        """Get agent ID for a workflow step."""
        step_to_agent = {
            "document_processing": "doc_agent",
            "income_verification": "income_agent",
            "credit_assessment": "credit_agent",
            "property_assessment": "property_agent",
            "risk_assessment": "risk_agent",
            "underwriting": "underwriting_agent"
        }
        return step_to_agent.get(step_id)
        
    def _extract_loan_decision(self, execution: WorkflowExecution) -> LoanDecision:
        """Extract loan decision from workflow execution results with detailed error tracking."""
        # Collect all step failures and errors for detailed reporting
        step_failures = []
        step_errors = {}
        
        # Check each workflow step for failures
        for step in execution.workflow_definition.steps:
            step_id = step.step_id
            agent_id = step.agent_id
            
            # Check if step completed successfully
            if step_id not in execution.completed_steps:
                step_failures.append(step_id)
                
                # Get agent result to check for errors
                agent_result = execution.context.get_result(agent_id)
                if agent_result and agent_result.error_message:
                    step_errors[step_id] = agent_result.error_message
                elif execution.error_message:
                    step_errors[step_id] = execution.error_message
                else:
                    step_errors[step_id] = f"Step '{step.name}' did not complete successfully"
        
        # Get underwriting agent results
        underwriting_result = execution.context.get_result("underwriting_agent")
        
        if underwriting_result and underwriting_result.tool_results:
            # Look for loan decision engine results
            decision_engine_result = None
            for tool_name, tool_result in underwriting_result.tool_results.items():
                if "loan_decision_engine" in tool_name and tool_result.success:
                    decision_engine_result = tool_result.data
                    break
            
            if decision_engine_result:
                # Handle both nested and flattened structures
                if "loan_decision" in decision_engine_result:
                    # Nested structure from direct loan decision engine call
                    loan_decision_data = decision_engine_result["loan_decision"]
                    scoring_analysis = decision_engine_result.get("scoring_analysis", {})
                    total_score = scoring_analysis.get("total_score", 0.0)
                else:
                    # Flattened structure from underwriting agent
                    loan_decision_data = decision_engine_result
                    total_score = decision_engine_result.get("overall_score", 0.0)
                
                # Extract decision
                decision_type_str = loan_decision_data.get("decision", "deny")
                try:
                    decision_type = DecisionType(decision_type_str.lower())
                except ValueError:
                    decision_type = DecisionType.DENY
                
                # Extract or create decision factors
                if "decision_factors" in decision_engine_result:
                    decision_factors_data = decision_engine_result["decision_factors"]
                    decision_factors = DecisionFactors(
                        eligibility_score=decision_factors_data.get("eligibility_score", 0.0),
                        risk_score=decision_factors_data.get("risk_score", 100.0),
                        compliance_score=decision_factors_data.get("compliance_score", 0.0),
                        policy_score=decision_factors_data.get("policy_score", 0.0)
                    )
                else:
                    # Create decision factors from total score
                    decision_factors = DecisionFactors(
                        eligibility_score=total_score * 0.35,
                        risk_score=100.0 - total_score,
                        compliance_score=total_score * 0.20,
                        policy_score=total_score * 0.15
                    )
                
                # Extract adverse actions - handle both structures
                adverse_actions_data = loan_decision_data.get("denial_reasons", [])
                if not adverse_actions_data:
                    adverse_actions_data = decision_engine_result.get("adverse_actions", [])
                adverse_actions = []
                
                # Add step failure adverse actions first
                for i, failed_step in enumerate(step_failures):
                    step_name = self._get_step_display_name(failed_step)
                    error_detail = step_errors.get(failed_step, "Step failed to complete")
                    adverse_actions.append(AdverseAction(
                        reason_code=f"STEP{i+1:03d}",
                        reason_description=f"Failed at {step_name}: {error_detail}",
                        category="processing_error"
                    ))
                
                # Add original adverse actions
                for i, action in enumerate(adverse_actions_data):
                    if isinstance(action, str):
                        adverse_actions.append(AdverseAction(
                            reason_code=f"UW{i+1:03d}",
                            reason_description=action,
                            category="underwriting"
                        ))
                    elif isinstance(action, dict):
                        adverse_actions.append(AdverseAction(**action))
                
                # Build detailed decision rationale
                rationale_parts = []
                if step_failures:
                    rationale_parts.append(f"Processing failed at steps: {', '.join([self._get_step_display_name(s) for s in step_failures])}")
                
                original_rationale = loan_decision_data.get("decision_rationale", 
                                                           decision_engine_result.get("decision_rationale", "Decision based on underwriting analysis"))
                rationale_parts.append(original_rationale)
                
                # Create LoanTerms object if loan terms data is present
                loan_terms_obj = None
                loan_terms_data = loan_decision_data.get("loan_terms")
                if not loan_terms_data:
                    loan_terms_data = decision_engine_result.get("loan_terms")
                
                if loan_terms_data and isinstance(loan_terms_data, dict):
                    from .models.assessment import LoanTerms
                    try:
                        loan_terms_obj = LoanTerms(**loan_terms_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to create LoanTerms object: {str(e)}")
                        loan_terms_obj = None
                elif decision_type == DecisionType.APPROVE:
                    # If decision is approve but no loan terms, create default ones
                    from .models.assessment import LoanTerms
                    from decimal import Decimal
                    
                    # Get loan amount from application
                    loan_amount = float(execution.context.application.loan_details.loan_amount)
                    
                    try:
                        loan_terms_obj = LoanTerms(
                            loan_amount=Decimal(str(loan_amount)),
                            interest_rate=Decimal("6.5"),  # Default rate
                            loan_term_years=30,
                            monthly_payment=Decimal(str(loan_amount * 0.006)),  # Approximate payment
                            down_payment_required=Decimal(str(float(execution.context.application.loan_details.down_payment))),
                            closing_costs=Decimal(str(loan_amount * 0.03)),
                            points=Decimal("0"),
                            apr=Decimal("6.75"),
                            pmi_required=False,
                            pmi_monthly_amount=None,
                            escrow_required=True,
                            prepayment_penalty=False
                        )
                        self.logger.info("Created default loan terms for approved loan")
                    except Exception as e:
                        self.logger.error(f"Failed to create default loan terms: {str(e)}")
                        loan_terms_obj = None

                return LoanDecision(
                    application_id=execution.context.application.application_id,
                    decision=decision_type,
                    decision_factors=decision_factors,
                    overall_score=total_score,
                    conditions=loan_decision_data.get("conditions", decision_engine_result.get("conditions", [])),
                    adverse_actions=adverse_actions,
                    loan_terms=loan_terms_obj,
                    generated_letters=decision_engine_result.get("generated_letters", {}),
                    decision_rationale=" | ".join(rationale_parts),
                    created_by="underwriting_agent"
                )
        
        # Fallback: create detailed denial decision with step failure information
        adverse_actions = []
        
        # Add specific step failure adverse actions
        for i, failed_step in enumerate(step_failures):
            step_name = self._get_step_display_name(failed_step)
            error_detail = step_errors.get(failed_step, "Step failed to complete")
            adverse_actions.append(AdverseAction(
                reason_code=f"STEP{i+1:03d}",
                reason_description=f"Failed at {step_name}: {error_detail}",
                category="processing_error"
            ))
        
        # Add general failure if no specific step failures identified
        if not adverse_actions:
            adverse_actions.append(AdverseAction(
                reason_code="SYS001",
                reason_description="Unable to complete underwriting assessment - no results from underwriting agent",
                category="system_error"
            ))
        
        # Build detailed rationale
        if step_failures:
            rationale = f"Application denied due to processing failures at: {', '.join([self._get_step_display_name(s) for s in step_failures])}. Specific errors: {'; '.join([f'{self._get_step_display_name(k)}: {v}' for k, v in step_errors.items()])}"
        else:
            rationale = "Unable to complete underwriting assessment due to insufficient data or processing errors."
        
        return LoanDecision(
            application_id=execution.context.application.application_id,
            decision=DecisionType.DENY,
            decision_factors=DecisionFactors(
                eligibility_score=0.0,
                risk_score=100.0,
                compliance_score=0.0,
                policy_score=0.0
            ),
            overall_score=0.0,
            conditions=[],
            adverse_actions=adverse_actions,
            loan_terms=None,
            generated_letters={},
            decision_rationale=rationale,
            created_by="system_orchestrator"
        )
    
    def _get_step_display_name(self, step_id: str) -> str:
        """Get human-readable display name for workflow step."""
        step_names = {
            "document_processing": "Document Processing",
            "income_verification": "Income Verification", 
            "credit_assessment": "Credit Assessment",
            "property_assessment": "Property Assessment",
            "risk_assessment": "Risk Assessment",
            "underwriting": "Underwriting Decision"
        }
        return step_names.get(step_id, step_id.replace("_", " ").title())
        
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a workflow execution.
        
        Args:
            execution_id: ID of the workflow execution
            
        Returns:
            Dictionary with workflow status information
        """
        execution = self.active_workflows.get(execution_id)
        progress = self.workflow_progress.get(execution_id)
        
        if not execution:
            return None
            
        status_info = {
            "execution_id": execution_id,
            "status": execution.status.value,
            "progress_percent": execution.get_progress(),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "error_message": execution.error_message,
            "completed_steps": list(execution.completed_steps),
            "total_steps": len(execution.workflow_definition.steps)
        }
        
        if progress:
            status_info.update({
                "current_phase": progress.current_phase.value,
                "completed_phases": [phase.value for phase in progress.completed_phases],
                "phase_progress_percent": progress.overall_progress_percent
            })
            
        return status_info
        
    async def cancel_workflow(self, execution_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            execution_id: ID of the workflow execution to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        success = self.workflow_engine.cancel_workflow(execution_id)
        if success:
            # Clean up tracking data
            self.active_workflows.pop(execution_id, None)
            self.workflow_progress.pop(execution_id, None)
            
        return success
        
    def list_active_workflows(self) -> List[str]:
        """
        List all active workflow execution IDs.
        
        Returns:
            List of active workflow execution IDs
        """
        return list(self.active_workflows.keys())
        
    async def cleanup_completed_workflows(self, older_than_hours: int = 24) -> int:
        """
        Clean up completed workflow executions and their tracking data.
        
        Args:
            older_than_hours: Remove workflows older than this many hours
            
        Returns:
            Number of workflows cleaned up
        """
        # Clean up workflow engine executions
        removed_count = self.workflow_engine.cleanup_completed_executions(older_than_hours)
        
        # Clean up local tracking data
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        
        execution_ids_to_remove = []
        for execution_id, execution in self.active_workflows.items():
            if (execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                execution.completed_at and execution.completed_at.timestamp() < cutoff_time):
                execution_ids_to_remove.append(execution_id)
                
        for execution_id in execution_ids_to_remove:
            self.active_workflows.pop(execution_id, None)
            self.workflow_progress.pop(execution_id, None)
            
        total_removed = removed_count + len(execution_ids_to_remove)
        if total_removed > 0:
            self.logger.info(f"Cleaned up {total_removed} completed workflow executions")
            
        return total_removed
        
    def get_agent_manager(self) -> AgentManager:
        """Get the agent manager instance."""
        return self.agent_manager
        
    def get_tool_manager(self) -> ToolManager:
        """Get the tool manager instance."""
        return self.tool_manager
        
    def get_workflow_engine(self) -> WorkflowEngine:
        """Get the workflow engine instance."""
        return self.workflow_engine


# Global orchestrator instance for easy access
_orchestrator_instance: Optional[MortgageProcessingOrchestrator] = None


def get_orchestrator(config: Optional[WorkflowConfiguration] = None) -> MortgageProcessingOrchestrator:
    """
    Get or create the global mortgage processing orchestrator instance.
    
    Args:
        config: Optional configuration for the orchestrator
        
    Returns:
        MortgageProcessingOrchestrator instance
    """
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = MortgageProcessingOrchestrator(config)
        
    return _orchestrator_instance


async def process_mortgage_application_simple(
    application: MortgageApplication,
    use_parallel_processing: bool = True
) -> Tuple[WorkflowExecution, LoanDecision]:
    """
    Simple convenience function to process a mortgage application.
    
    Args:
        application: The mortgage application to process
        use_parallel_processing: Whether to use parallel assessment workflow
        
    Returns:
        Tuple of (WorkflowExecution, LoanDecision)
    """
    orchestrator = get_orchestrator()
    workflow_type = "parallel_mortgage_processing" if use_parallel_processing else "standard_mortgage_processing"
    
    return await orchestrator.process_mortgage_application(application, workflow_type)