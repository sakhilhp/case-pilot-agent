"""
Underwriting Agent implementation.

This agent specializes in final loan decision making, loan structuring, and terms calculation
for mortgage applications. It coordinates the final underwriting workflow including decision
engine processing and loan letter generation.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from .base import BaseAgent
from ..models.core import MortgageApplication, LoanType
from ..models.assessment import AssessmentResult, RiskLevel, LoanDecision, DecisionType, LoanTerms, DecisionFactors, AdverseAction
from ..tools.base import ToolResult
# Enhanced tools will be registered separately to avoid circular imports


class UnderwritingAgent(BaseAgent):
    """
    Agent specialized in final loan decision making and underwriting for mortgage applications.
    
    This agent coordinates the final underwriting workflow including:
    - Multi-factor loan decision making using scoring algorithm
    - Loan structuring and terms calculation
    - Government-backed loan support and automated decisions
    - Loan letter generation for all decision types
    - Final decision documentation and rationale
    
    Tools used:
    - loan_decision_engine: Multi-factor scoring and automated decision making
    - loan_letter_generator: Automated documentation generation for all decision types
    """
    
    def __init__(self, agent_id: str = "underwriting_agent"):
        super().__init__(agent_id, "Underwriting Agent")
        self.logger = logging.getLogger("agent.underwriting")
        
    def get_tool_names(self) -> List[str]:
        """Return list of tool names this agent uses."""
        return [
            "loan_decision_engine",
            "loan_letter_generator"
        ]
        
    async def process(self, application: MortgageApplication, context: Dict[str, Any]) -> AssessmentResult:
        """
        Process mortgage application underwriting using specialized tools.
        
        Args:
            application: The mortgage application to process
            context: Additional context data from other agents
            
        Returns:
            AssessmentResult containing final underwriting decision and documentation
        """
        start_time = datetime.now()
        tool_results = {}
        errors = []
        warnings = []
        recommendations = []
        
        try:
            self.logger.info(f"Starting underwriting process for application {application.application_id}")
            
            # Validate that we have results from all required agents
            required_agents = [
                'document_processing_agent',
                'income_verification_agent', 
                'credit_assessment_agent',
                'property_assessment_agent',
                'risk_assessment_agent'
            ]
            
            missing_agents = [agent for agent in required_agents if agent not in context]
            if missing_agents:
                warnings.append(f"Missing results from agents: {', '.join(missing_agents)}")
            
            # Store tool results for cross-tool communication
            self._current_tool_results = {}
            
            # Step 1: Run loan decision engine with multi-factor scoring
            decision_result = await self._perform_loan_decision_analysis(application, context)
            tool_results["loan_decision_engine"] = decision_result
            self._current_tool_results["loan_decision_engine"] = decision_result.data if decision_result.success else {}
            
            if not decision_result.success:
                errors.append(f"Loan decision engine failed: {decision_result.error_message}")
                # Create fallback decision for manual review
                decision_data = self._create_fallback_decision(application, context)
                self._current_tool_results["loan_decision_engine"] = decision_data
            
            # Step 2: Generate loan letters and documentation
            letter_result = await self._generate_loan_documentation(application, context)
            tool_results["loan_letter_generator"] = letter_result
            self._current_tool_results["loan_letter_generator"] = letter_result.data if letter_result.success else {}
            
            if not letter_result.success:
                errors.append(f"Loan letter generation failed: {letter_result.error_message}")
            
            # Generate overall underwriting assessment
            risk_score, risk_level = self._calculate_underwriting_risk_score(tool_results, application, context)
            confidence_level = self._calculate_confidence_level(tool_results, context)
            recommendations = self._generate_underwriting_recommendations(tool_results, application, context)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Underwriting process completed for application {application.application_id}")
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="underwriting_decision",
                tool_results=tool_results,
                risk_score=risk_score,
                risk_level=risk_level,
                confidence_level=confidence_level,
                recommendations=recommendations,
                conditions=self._generate_underwriting_conditions(tool_results, application),
                red_flags=self._identify_underwriting_red_flags(tool_results),
                processing_time_seconds=processing_time,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Underwriting process failed: {str(e)}"
            self.logger.error(error_msg)
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="underwriting_decision",
                tool_results=tool_results,
                risk_score=100.0,  # Maximum risk due to processing failure
                risk_level=RiskLevel.HIGH,
                confidence_level=0.0,
                recommendations=["Manual underwriting review required due to system failure"],
                conditions=["Complete manual underwriting process"],
                red_flags=["Underwriting system failure"],
                processing_time_seconds=processing_time,
                errors=[error_msg],
                warnings=warnings
            )
    
    async def _perform_loan_decision_analysis(self, application: MortgageApplication,
                                            context: Dict[str, Any]) -> ToolResult:
        """
        Perform loan decision analysis using the loan decision engine tool.
        
        Args:
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from loan decision engine
        """
        decision_tool = self.get_tool("loan_decision_engine")
        if not decision_tool:
            return ToolResult(
                tool_name="loan_decision_engine",
                success=False,
                data={},
                error_message="Loan decision engine tool not available"
            )
        
        # Aggregate assessment data from all agents
        assessment_data = self._aggregate_assessment_data(context)
        
        # Prepare application data in the format expected by the loan decision engine
        application_data = {
            "documents": {
                "identity_verified": True,
                "income_documents_complete": True,
                "property_documents_complete": True,
                "document_authenticity_score": assessment_data.get("document_processing", {}).get("extraction_quality", 85.0)
            },
            "income": {
                "monthly_gross_income": float(application.borrower_info.annual_income) / 12,
                "verified_employment": assessment_data.get("income_verification", {}).get("employment_verified", True),
                "income_stability_score": assessment_data.get("income_verification", {}).get("income_consistency_score", 90.0),
                "debt_to_income_ratio": assessment_data.get("credit_assessment", {}).get("debt_to_income_ratio", 999.0),
                "qualified_income": assessment_data.get("income_verification", {}).get("qualified_income", float(application.borrower_info.annual_income))
            },
            "credit": {
                "credit_score": assessment_data.get("credit_assessment", {}).get("credit_score", 720),
                "credit_history_months": 60,  # Default to 5 years
                "payment_history_score": 85.0,
                "credit_utilization": 0.3,
                "public_records": [],
                "credit_risk_grade": assessment_data.get("credit_assessment", {}).get("credit_risk_level", "low")
            },
            "property": {
                "appraised_value": float(application.property_info.property_value),
                "loan_to_value_ratio": float(application.loan_details.loan_amount) / float(application.property_info.property_value),
                "property_type": application.property_info.property_type,
                "property_risk_score": assessment_data.get("property_assessment", {}).get("property_risk_score", 25.0),
                "market_trend_indicator": "stable"
            },
            "risk": {
                "overall_risk_score": assessment_data.get("risk_assessment", {}).get("kyc_risk_score", 15.0),
                "default_probability": 0.05,
                "fraud_risk_score": 10.0,
                "kyc_risk_level": assessment_data.get("risk_assessment", {}).get("overall_risk_level", "low"),
                "regulatory_compliance_status": True,
                "pep_sanctions_clear": assessment_data.get("risk_assessment", {}).get("pep_sanctions_status", "clear") == "clear"
            },
            "loan": {
                "requested_amount": float(application.loan_details.loan_amount),
                "loan_purpose": application.loan_details.purpose,
                "loan_term_months": application.loan_details.loan_term_years * 12,
                "loan_type": application.loan_details.loan_type.value,
                "down_payment_amount": float(application.loan_details.down_payment),
                "down_payment_percentage": float(application.loan_details.down_payment) / float(application.property_info.property_value)
            }
        }
        
        # Call with both old and new format parameters for compatibility
        return await decision_tool.execute(
            application_id=application.application_id,
            application_data=application_data,
            loan_program=application.loan_details.loan_type.value,
            underwriting_guidelines={
                "max_dti_ratio": 0.43,
                "min_credit_score": 620,
                "max_ltv_ratio": 0.95,
                "require_reserves": False,
                "manual_underwriting_required": False
            },
            # New format parameters - convert context to expected format
            assessment_results=self._convert_context_to_assessment_results(context),
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'stated_income': application.borrower_info.annual_income
            },
            loan_details={
                'loan_amount': application.loan_details.loan_amount,
                'loan_type': application.loan_details.loan_type,
                'loan_term_years': application.loan_details.loan_term_years
            }
        )
    
    async def _generate_loan_documentation(self, application: MortgageApplication,
                                         context: Dict[str, Any]) -> ToolResult:
        """
        Generate loan documentation using the loan letter generator tool.
        
        Args:
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from loan letter generator
        """
        letter_tool = self.get_tool("loan_letter_generator")
        if not letter_tool:
            return ToolResult(
                tool_name="loan_letter_generator",
                success=False,
                data={},
                error_message="Loan letter generator tool not available"
            )
        
        # Get decision data from loan decision engine
        decision_data = {}
        if hasattr(self, '_current_tool_results') and 'loan_decision_engine' in self._current_tool_results:
            decision_data = self._current_tool_results['loan_decision_engine']
        
        # Prepare borrower information for letters
        borrower_info = {
            'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
            'address': application.borrower_info.current_address,
            'email': application.borrower_info.email,
            'phone': application.borrower_info.phone
        }
        
        # Prepare loan information for letters
        loan_info = {
            'application_id': application.application_id,
            'loan_amount': float(application.loan_details.loan_amount),
            'loan_type': application.loan_details.loan_type.value,
            'property_address': application.property_info.address
        }
        
        return await letter_tool.safe_execute(
            borrower_information=borrower_info,
            loan_information=loan_info,
            decision_data=decision_data,
            letter_types=['approval', 'conditional_approval', 'denial'],
            include_adverse_action_notices=True,
            template_customization={
                'company_name': 'Mortgage AI Processing System',
                'include_contact_info': True,
                'include_appeal_process': True
            }
        )
    
    def _aggregate_assessment_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate assessment data from all agents for decision making.
        
        Args:
            context: Context containing results from all agents
            
        Returns:
            Aggregated assessment data
        """
        assessment_data = {
            'document_processing': {},
            'income_verification': {},
            'credit_assessment': {},
            'property_assessment': {},
            'risk_assessment': {}
        }
        
        # Document processing results (check both possible names)
        doc_agent_key = None
        for key in ['document_processing_agent', 'doc_agent']:
            if key in context:
                doc_agent_key = key
                break
        
        if doc_agent_key:
            doc_results = context[doc_agent_key]
            assessment_data['document_processing'] = {
                'documents_processed': len(doc_results),
                'classification_confidence': self._get_average_confidence(doc_results, 'classification_confidence'),
                'validation_success_rate': self._get_validation_success_rate(doc_results),
                'extraction_quality': self._get_average_confidence(doc_results, 'extraction_quality')
            }
        
        # Income verification results (check both possible names)
        income_agent_key = None
        for key in ['income_verification_agent', 'income_agent']:
            if key in context:
                income_agent_key = key
                break
        
        if income_agent_key:
            income_results = context[income_agent_key]
            assessment_data['income_verification'] = {
                'employment_verified': self._get_employment_verification_status(income_results),
                'income_consistency_score': self._get_income_consistency_score(income_results),
                'debt_to_income_ratio': self._get_dti_ratio(income_results),
                'qualified_income': self._get_qualified_income(income_results)
            }
        
        # Credit assessment results (check both possible names)
        credit_agent_key = None
        for key in ['credit_assessment_agent', 'credit_agent']:
            if key in context:
                credit_agent_key = key
                break
        
        if credit_agent_key:
            credit_results = context[credit_agent_key]
            assessment_data['credit_assessment'] = {
                'credit_score': self._get_credit_score(credit_results),
                'credit_history_quality': self._get_credit_history_quality(credit_results),
                'derogatory_marks': self._get_derogatory_marks(credit_results),
                'credit_risk_level': self._get_credit_risk_level(credit_results),
                'debt_to_income_ratio': self._get_dti_from_credit(credit_results)
            }
        
        # Property assessment results (check both possible names)
        property_agent_key = None
        for key in ['property_assessment_agent', 'property_agent']:
            if key in context:
                property_agent_key = key
                break
        
        if property_agent_key:
            property_results = context[property_agent_key]
            assessment_data['property_assessment'] = {
                'property_value': self._get_property_value(property_results),
                'loan_to_value_ratio': self._get_ltv_ratio(property_results),
                'property_risk_score': self._get_property_risk_score(property_results),
                'valuation_confidence': self._get_valuation_confidence(property_results)
            }
        
        # Risk assessment results (check both possible names)
        risk_agent_key = None
        for key in ['risk_assessment_agent', 'risk_agent']:
            if key in context:
                risk_agent_key = key
                break
        
        if risk_agent_key:
            risk_results = context[risk_agent_key]
            assessment_data['risk_assessment'] = {
                'kyc_risk_score': self._get_kyc_risk_score(risk_results),
                'pep_sanctions_status': self._get_pep_sanctions_status(risk_results),
                'overall_risk_level': self._get_overall_risk_level(risk_results),
                'compliance_issues': self._get_compliance_issues(risk_results)
            }
        
        return assessment_data
    
    def _create_fallback_decision(self, application: MortgageApplication, 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a fallback decision when the decision engine fails.
        
        Args:
            application: The mortgage application
            context: Context from other agents
            
        Returns:
            Fallback decision data
        """
        return {
            'decision': DecisionType.CONDITIONAL.value,
            'decision_score': 50.0,  # Neutral score requiring manual review
            'decision_factors': {
                'eligibility_score': 50.0,
                'risk_score': 50.0,
                'compliance_score': 50.0,
                'policy_score': 50.0
            },
            'conditions': [
                'Manual underwriting review required due to system failure',
                'Verify all documentation manually',
                'Complete enhanced risk assessment'
            ],
            'adverse_actions': [],
            'loan_terms': None,
            'requires_manual_review': True,
            'decision_rationale': 'Automated decision system unavailable - manual review required'
        }
    
    def _calculate_underwriting_risk_score(self, tool_results: Dict[str, ToolResult],
                                         application: MortgageApplication,
                                         context: Dict[str, Any]) -> tuple[float, RiskLevel]:
        """
        Calculate underwriting risk score based on decision results.
        
        Args:
            tool_results: Results from underwriting tools
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            Tuple of (risk_score, risk_level)
        """
        decision_result = tool_results.get("loan_decision_engine")
        
        if decision_result and decision_result.success:
            decision_data = decision_result.data
            decision_score = decision_data.get('decision_score', 50.0)
            
            # Convert decision score to risk score (inverse relationship)
            risk_score = 100.0 - decision_score
            
            # Adjust based on decision type
            decision_type = decision_data.get('decision', DecisionType.CONDITIONAL.value)
            if decision_type == DecisionType.DENY.value:
                risk_score = max(risk_score, 70.0)
            elif decision_type == DecisionType.CONDITIONAL.value:
                risk_score = max(risk_score, 40.0)
            
        else:
            risk_score = 80.0  # High risk if decision engine failed
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return risk_score, risk_level
    
    def _calculate_confidence_level(self, tool_results: Dict[str, ToolResult],
                                  context: Dict[str, Any]) -> float:
        """
        Calculate confidence level in underwriting decision.
        
        Args:
            tool_results: Results from underwriting tools
            context: Additional context from other agents
            
        Returns:
            Confidence level between 0 and 1
        """
        confidence_factors = []
        
        # Decision engine confidence
        decision_result = tool_results.get("loan_decision_engine")
        if decision_result and decision_result.success:
            decision_confidence = decision_result.data.get('confidence_score', 0.5)
            confidence_factors.append(decision_confidence)
        else:
            confidence_factors.append(0.0)
        
        # Letter generation confidence (indicates data completeness)
        letter_result = tool_results.get("loan_letter_generator")
        if letter_result and letter_result.success:
            letter_confidence = letter_result.data.get('generation_confidence', 0.8)
            confidence_factors.append(letter_confidence)
        else:
            confidence_factors.append(0.5)
        
        # Agent completeness confidence
        required_agents = ['document_processing_agent', 'income_verification_agent', 
                          'credit_assessment_agent', 'property_assessment_agent', 'risk_assessment_agent']
        available_agents = sum(1 for agent in required_agents if agent in context)
        agent_completeness = available_agents / len(required_agents)
        confidence_factors.append(agent_completeness)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
    def _generate_underwriting_recommendations(self, tool_results: Dict[str, ToolResult],
                                             application: MortgageApplication,
                                             context: Dict[str, Any]) -> List[str]:
        """
        Generate underwriting recommendations based on decision results.
        
        Args:
            tool_results: Results from underwriting tools
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        decision_result = tool_results.get("loan_decision_engine")
        if decision_result and decision_result.success:
            decision_data = decision_result.data
            
            decision_type = decision_data.get('decision', DecisionType.CONDITIONAL.value)
            decision_score = decision_data.get('decision_score', 50.0)
            
            if decision_type == DecisionType.APPROVE.value:
                recommendations.append("Loan approved - proceed with closing documentation")
                if decision_score < 85:
                    recommendations.append("Monitor loan performance closely due to moderate score")
            elif decision_type == DecisionType.CONDITIONAL.value:
                recommendations.append("Conditional approval - ensure all conditions are met before closing")
                recommendations.append("Verify condition completion with appropriate documentation")
            elif decision_type == DecisionType.DENY.value:
                recommendations.append("Loan denied - provide adverse action notices to borrower")
                recommendations.append("Document denial reasons thoroughly for compliance")
            
            # Score-based recommendations
            if decision_score < 60:
                recommendations.append("Consider enhanced risk mitigation measures")
            
            # Manual review recommendations
            if decision_data.get('requires_manual_review', False):
                recommendations.append("Route to senior underwriter for manual review")
                recommendations.append("Conduct additional verification as needed")
        
        else:
            recommendations.append("System failure - conduct complete manual underwriting")
            recommendations.append("Escalate to underwriting supervisor")
        
        return recommendations
    
    def _generate_underwriting_conditions(self, tool_results: Dict[str, ToolResult],
                                        application: MortgageApplication) -> List[str]:
        """
        Generate underwriting conditions based on decision results.
        
        Args:
            tool_results: Results from underwriting tools
            application: The mortgage application
            
        Returns:
            List of condition strings
        """
        conditions = []
        
        decision_result = tool_results.get("loan_decision_engine")
        if decision_result and decision_result.success:
            decision_data = decision_result.data
            
            # Get conditions from decision engine
            engine_conditions = decision_data.get('conditions', [])
            conditions.extend(engine_conditions)
            
            # Add standard conditions based on loan type
            loan_type = application.loan_details.loan_type
            if loan_type == LoanType.FHA:
                conditions.append("Obtain FHA case number assignment")
                conditions.append("Complete FHA-required property inspection")
            elif loan_type == LoanType.VA:
                conditions.append("Obtain VA eligibility certificate")
                conditions.append("Complete VA property appraisal")
            elif loan_type == LoanType.USDA:
                conditions.append("Verify property location eligibility")
                conditions.append("Complete USDA income verification")
        
        return conditions
    
    def _identify_underwriting_red_flags(self, tool_results: Dict[str, ToolResult]) -> List[str]:
        """
        Identify red flags from underwriting results.
        
        Args:
            tool_results: Results from underwriting tools
            
        Returns:
            List of red flag descriptions
        """
        red_flags = []
        
        decision_result = tool_results.get("loan_decision_engine")
        if decision_result and decision_result.success:
            decision_data = decision_result.data
            
            # Get red flags from decision engine
            engine_red_flags = decision_data.get('red_flags', [])
            red_flags.extend(engine_red_flags)
            
            # Decision-based red flags
            decision_score = decision_data.get('decision_score', 50.0)
            if decision_score < 30:
                red_flags.append("Extremely low decision score")
            
            # Adverse actions indicate red flags
            adverse_actions = decision_data.get('adverse_actions', [])
            if adverse_actions:
                red_flags.extend([f"Adverse action: {action.get('reason_description', 'Unknown')}" 
                                for action in adverse_actions])
        
        else:
            red_flags.append("Decision engine failure")
        
        return red_flags
    
    def _convert_context_to_assessment_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert workflow context to the format expected by loan decision engine.
        
        Args:
            context: Context containing AssessmentResult objects from agents
            
        Returns:
            Dictionary in the format expected by loan decision engine
        """
        assessment_results = {}
        
        # Map agent names to expected names
        agent_mapping = {
            'credit_agent': 'credit_assessment_agent',
            'income_agent': 'income_verification_agent',
            'property_agent': 'property_assessment_agent',
            'risk_agent': 'risk_assessment_agent',
            'doc_agent': 'document_processing_agent'
        }
        
        for agent_key, assessment_result in context.items():
            # Skip non-agent entries
            if not hasattr(assessment_result, 'tool_results'):
                continue
                
            # Map to expected agent name
            expected_agent_name = agent_mapping.get(agent_key, agent_key)
            
            # Convert tool results to expected format
            agent_tools = {}
            for tool_name, tool_result in assessment_result.tool_results.items():
                if hasattr(tool_result, 'data'):
                    agent_tools[tool_name] = {
                        'data': tool_result.data
                    }
                else:
                    agent_tools[tool_name] = {
                        'data': tool_result if isinstance(tool_result, dict) else {}
                    }
            
            assessment_results[expected_agent_name] = agent_tools
        
        # Debug logging - save conversion details
        import json
        debug_conversion = {
            'input_context_keys': list(context.keys()),
            'converted_assessment_results': assessment_results
        }
        
        # Add details about credit agent specifically
        if 'credit_agent' in context:
            credit_result = context['credit_agent']
            debug_conversion['credit_agent_details'] = {
                'has_tool_results': hasattr(credit_result, 'tool_results'),
                'tool_results_keys': list(credit_result.tool_results.keys()) if hasattr(credit_result, 'tool_results') else [],
            }
            
            if hasattr(credit_result, 'tool_results') and 'debt_to_income_calculator' in credit_result.tool_results:
                dti_tool_result = credit_result.tool_results['debt_to_income_calculator']
                debug_conversion['credit_agent_dti_tool'] = {
                    'has_data': hasattr(dti_tool_result, 'data'),
                    'data': dti_tool_result.data if hasattr(dti_tool_result, 'data') else str(dti_tool_result)
                }
        
        with open('underwriting_conversion_debug.json', 'w') as f:
            json.dump(debug_conversion, f, indent=2, default=str)
        
        return assessment_results
    
    # Helper methods for extracting data from agent results
    def _get_average_confidence(self, results: Dict[str, Any], field: str) -> float:
        """Get average confidence score from results."""
        confidences = []
        for tool_result in results.values():
            if isinstance(tool_result, dict) and 'data' in tool_result:
                confidence = tool_result['data'].get(field, 0.0)
                confidences.append(confidence)
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _get_validation_success_rate(self, results: Dict[str, Any]) -> float:
        """Get validation success rate from document processing results."""
        # Implementation would extract validation success rate
        return 0.85  # Placeholder
    
    def _get_employment_verification_status(self, results: Dict[str, Any]) -> bool:
        """Get employment verification status from income results."""
        # Implementation would extract employment verification status
        return True  # Placeholder
    
    def _get_income_consistency_score(self, results: Dict[str, Any]) -> float:
        """Get income consistency score from income results."""
        # Implementation would extract income consistency score
        return 0.9  # Placeholder
    
    def _get_dti_ratio(self, income_assessment_result) -> float:
        """Get debt-to-income ratio from income results."""
        # Access tool_results from the AssessmentResult object
        if hasattr(income_assessment_result, 'tool_results'):
            tool_results = income_assessment_result.tool_results
            if 'simple_income_calculator' in tool_results:
                income_result = tool_results['simple_income_calculator']
                # Handle both ToolResult objects and direct data
                if hasattr(income_result, 'data'):
                    income_data = income_result.data
                else:
                    income_data = income_result
                
                if isinstance(income_data, dict) and 'debt_to_income_ratio' in income_data:
                    return income_data['debt_to_income_ratio']
        
        # Fallback: Return 0 instead of 999.0 to trigger application-based calculation
        return 0.0
    
    def _get_qualified_income(self, income_assessment_result) -> float:
        """Get qualified income from income results."""
        # Access tool_results from the AssessmentResult object
        if hasattr(income_assessment_result, 'tool_results'):
            tool_results = income_assessment_result.tool_results
            if 'simple_income_calculator' in tool_results:
                income_result = tool_results['simple_income_calculator']
                # Handle both ToolResult objects and direct data
                if hasattr(income_result, 'data'):
                    income_data = income_result.data
                else:
                    income_data = income_result
                
                if isinstance(income_data, dict) and 'qualified_annual_income' in income_data:
                    return income_data['qualified_annual_income']
        
        # Fallback to 0 to ensure denial if no income found
        return 0.0
    
    def _get_dti_from_credit(self, credit_assessment_result) -> float:
        """Get debt-to-income ratio from credit assessment results."""
        # Access tool_results from the AssessmentResult object
        if hasattr(credit_assessment_result, 'tool_results'):
            tool_results = credit_assessment_result.tool_results
            if 'debt_to_income_calculator' in tool_results:
                dti_result = tool_results['debt_to_income_calculator']
                # Handle both ToolResult objects and direct data
                if hasattr(dti_result, 'data'):
                    dti_data = dti_result.data
                else:
                    dti_data = dti_result
                
                if isinstance(dti_data, dict) and 'total_dti_ratio' in dti_data:
                    return dti_data['total_dti_ratio']
        
        # Fallback: Return 0 instead of 999.0 to trigger application-based calculation
        return 0.0
    
    def _get_credit_score(self, results: Dict[str, Any]) -> int:
        """Get credit score from credit results."""
        # Implementation would extract credit score
        return 720  # Placeholder
    
    def _get_credit_history_quality(self, results: Dict[str, Any]) -> str:
        """Get credit history quality from credit results."""
        # Implementation would extract credit history quality
        return "good"  # Placeholder
    
    def _get_derogatory_marks(self, results: Dict[str, Any]) -> int:
        """Get number of derogatory marks from credit results."""
        # Implementation would extract derogatory marks
        return 0  # Placeholder
    
    def _get_credit_risk_level(self, results: Dict[str, Any]) -> str:
        """Get credit risk level from credit results."""
        # Implementation would extract credit risk level
        return "low"  # Placeholder
    
    def _get_property_value(self, results: Dict[str, Any]) -> float:
        """Get property value from property results."""
        # Implementation would extract property value
        return 350000.0  # Placeholder
    
    def _get_ltv_ratio(self, results: Dict[str, Any]) -> float:
        """Get loan-to-value ratio from property results."""
        # Implementation would extract LTV ratio
        return 0.8  # Placeholder
    
    def _get_property_risk_score(self, results: Dict[str, Any]) -> float:
        """Get property risk score from property results."""
        # Implementation would extract property risk score
        return 25.0  # Placeholder
    
    def _get_valuation_confidence(self, results: Dict[str, Any]) -> float:
        """Get valuation confidence from property results."""
        # Implementation would extract valuation confidence
        return 0.9  # Placeholder
    
    def _get_kyc_risk_score(self, results: Dict[str, Any]) -> float:
        """Get KYC risk score from risk results."""
        # Implementation would extract KYC risk score
        return 15.0  # Placeholder
    
    def _get_pep_sanctions_status(self, results: Dict[str, Any]) -> str:
        """Get PEP/sanctions status from risk results."""
        # Implementation would extract PEP/sanctions status
        return "clear"  # Placeholder
    
    def _get_overall_risk_level(self, results: Dict[str, Any]) -> str:
        """Get overall risk level from risk results."""
        # Implementation would extract overall risk level
        return "low"  # Placeholder
    
    def _get_compliance_issues(self, results: Dict[str, Any]) -> List[str]:
        """Get compliance issues from risk results."""
        # Implementation would extract compliance issues
        return []  # Placeholder