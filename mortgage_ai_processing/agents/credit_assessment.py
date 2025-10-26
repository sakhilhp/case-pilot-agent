"""
Credit Assessment Agent implementation.

This agent specializes in credit assessment tasks including credit score analysis,
credit history evaluation, and debt-to-income calculations for mortgage applications.
"""

from typing import Dict, List, Any
import logging
from datetime import datetime
from decimal import Decimal

from .base import BaseAgent
from ..models.core import MortgageApplication, Document, DocumentType
from ..models.assessment import AssessmentResult, RiskLevel
from ..tools.base import ToolResult
# Enhanced tools will be registered separately to avoid circular imports


class CreditAssessmentAgent(BaseAgent):
    """
    Agent specialized in credit assessment for mortgage applications.
    
    This agent coordinates credit assessment workflows including:
    - Credit score analysis with mortgage lending risk evaluation
    - Credit history analysis including payment patterns and utilization
    - Debt-to-income calculations and analysis
    - Loan program eligibility assessment based on credit factors
    
    Tools used:
    - credit_score_analyzer: Credit score analysis with risk assessment
    - credit_history_analyzer: Comprehensive credit history evaluation
    - debt_to_income_calculator: Standalone DTI calculation and analysis
    """
    
    def __init__(self, agent_id: str = "credit_assessment_agent"):
        super().__init__(agent_id, "Credit Assessment Agent")
        self.logger = logging.getLogger("agent.credit_assessment")
        
    def get_tool_names(self) -> List[str]:
        """Return list of tool names this agent uses."""
        return [
            "credit_score_analyzer",
            "credit_history_analyzer",
            "debt_to_income_calculator"
        ]
        
    async def process(self, application: MortgageApplication, context: Dict[str, Any]) -> AssessmentResult:
        """
        Process mortgage application credit assessment using specialized tools.
        
        Args:
            application: The mortgage application to process
            context: Additional context data from other agents
            
        Returns:
            AssessmentResult containing credit assessment analysis
        """
        start_time = datetime.now()
        tool_results = {}
        errors = []
        warnings = []
        recommendations = []
        
        try:
            self.logger.info(f"Starting credit assessment for application {application.application_id}")
            
            # Get credit-related documents
            credit_documents = self._get_credit_documents(application.documents)
            
            if not credit_documents:
                warnings.append("No credit documents found for assessment")
            
            # Store tool results for cross-tool communication
            self._current_tool_results = {}
            
            # Step 1: Credit score analysis with risk assessment
            credit_score_result = await self._analyze_credit_score(application, context)
            tool_results["credit_score_analyzer"] = credit_score_result
            self._current_tool_results["credit_score_analyzer"] = credit_score_result.data if credit_score_result.success else {}
            
            if not credit_score_result.success:
                errors.append(f"Credit score analysis failed: {credit_score_result.error_message}")
            
            # Step 2: Credit history analysis
            if credit_documents:
                credit_history_result = await self._analyze_credit_history(credit_documents, application, context)
                tool_results["credit_history_analyzer"] = credit_history_result
                self._current_tool_results["credit_history_analyzer"] = credit_history_result.data if credit_history_result.success else {}
                
                if not credit_history_result.success:
                    errors.append(f"Credit history analysis failed: {credit_history_result.error_message}")
            else:
                # Still attempt analysis with available data
                credit_history_result = await self._analyze_credit_history([], application, context)
                tool_results["credit_history_analyzer"] = credit_history_result
                self._current_tool_results["credit_history_analyzer"] = credit_history_result.data if credit_history_result.success else {}
            
            # Step 3: Debt-to-income calculation
            dti_result = await self._calculate_debt_to_income(application, context)
            tool_results["debt_to_income_calculator"] = dti_result
            self._current_tool_results["debt_to_income_calculator"] = dti_result.data if dti_result.success else {}
            
            if not dti_result.success:
                errors.append(f"DTI calculation failed: {dti_result.error_message}")
            
            # Generate overall assessment
            risk_score, risk_level = self._calculate_credit_risk_score(tool_results, application)
            confidence_level = self._calculate_confidence_level(tool_results)
            recommendations = self._generate_recommendations(tool_results, application)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Credit assessment completed for application {application.application_id}")
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="credit_assessment",
                tool_results=tool_results,
                risk_score=risk_score,
                risk_level=risk_level,
                confidence_level=confidence_level,
                recommendations=recommendations,
                conditions=self._generate_conditions(tool_results, application),
                red_flags=self._identify_red_flags(tool_results),
                processing_time_seconds=processing_time,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Credit assessment failed: {str(e)}"
            self.logger.error(error_msg)
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="credit_assessment",
                tool_results=tool_results,
                risk_score=100.0,  # High risk due to processing failure
                risk_level=RiskLevel.HIGH,
                confidence_level=0.0,
                recommendations=["Manual credit assessment required due to processing failure"],
                conditions=["Provide additional credit documentation"],
                red_flags=["Credit assessment system failure"],
                processing_time_seconds=processing_time,
                errors=[error_msg],
                warnings=warnings
            )
    
    def _get_credit_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents to get credit-related documents.
        
        Args:
            documents: List of all documents
            
        Returns:
            List of credit-related documents
        """
        credit_types = {DocumentType.CREDIT}
        return [doc for doc in documents if doc.document_type in credit_types]
    
    async def _analyze_credit_score(self, application: MortgageApplication, 
                                  context: Dict[str, Any]) -> ToolResult:
        """
        Analyze credit score using the credit score analyzer tool.
        
        Args:
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from credit score analysis
        """
        credit_score_tool = self.get_tool("credit_score_analyzer")
        if not credit_score_tool:
            return ToolResult(
                tool_name="credit_score_analyzer",
                success=False,
                data={},
                error_message="Credit score analyzer tool not available"
            )
        
        # Get income information from context if available
        income_info = {}
        if 'income_verification_agent' in context:
            income_results = context['income_verification_agent']
            if 'simple_income_calculator' in income_results:
                income_data = income_results['simple_income_calculator'].get('data', {})
                income_info = {
                    'monthly_income': income_data.get('qualified_monthly_income', 0),
                    'annual_income': income_data.get('qualified_annual_income', 0),
                    'employment_verified': income_data.get('employment_verified', False)
                }
        
        return await credit_score_tool.safe_execute(
            application_id=application.application_id,
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'ssn': application.borrower_info.ssn,
                'date_of_birth': application.borrower_info.date_of_birth.isoformat(),
                'current_address': application.borrower_info.current_address
            },
            loan_details={
                'loan_amount': float(application.loan_details.loan_amount),
                'loan_type': application.loan_details.loan_type.value,
                'loan_term_years': application.loan_details.loan_term_years,
                'down_payment': float(application.loan_details.down_payment),
                'purpose': application.loan_details.purpose
            },
            income_information=income_info
        )
    
    async def _analyze_credit_history(self, credit_documents: List[Document], 
                                    application: MortgageApplication,
                                    context: Dict[str, Any]) -> ToolResult:
        """
        Analyze credit history using the credit history analyzer tool.
        
        Args:
            credit_documents: List of credit-related documents
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from credit history analysis
        """
        credit_history_tool = self.get_tool("credit_history_analyzer")
        if not credit_history_tool:
            return ToolResult(
                tool_name="credit_history_analyzer",
                success=False,
                data={},
                error_message="Credit history analyzer tool not available"
            )
        
        # Prepare document data for analysis
        document_data = []
        for doc in credit_documents:
            document_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'file_path': doc.file_path
            })
        
        # Get credit score information from previous analysis if available
        credit_score_info = {}
        if hasattr(self, '_current_tool_results') and 'credit_score_analyzer' in self._current_tool_results:
            score_data = self._current_tool_results['credit_score_analyzer'].get('data', {})
            credit_score_info = {
                'credit_score': score_data.get('credit_score', 0),
                'score_model': score_data.get('score_model', 'FICO'),
                'score_date': score_data.get('score_date', datetime.now().isoformat())
            }
        
        return await credit_history_tool.safe_execute(
            application_id=application.application_id,
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'ssn': application.borrower_info.ssn,
                'date_of_birth': application.borrower_info.date_of_birth.isoformat()
            },
            credit_documents=document_data,
            credit_score_info=credit_score_info,
            analysis_depth="comprehensive"  # Request full analysis
        )
    
    async def _calculate_debt_to_income(self, application: MortgageApplication,
                                      context: Dict[str, Any]) -> ToolResult:
        """
        Calculate debt-to-income ratio using the DTI calculator tool.
        
        Args:
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from DTI calculation
        """
        dti_tool = self.get_tool("debt_to_income_calculator")
        if not dti_tool:
            return ToolResult(
                tool_name="debt_to_income_calculator",
                success=False,
                data={},
                error_message="Debt-to-income calculator tool not available"
            )
        
        # Get income information from context if available
        income_info = {}
        
        # Check for income agent results (try multiple possible keys)
        income_agent_key = None
        for key in ['income_verification_agent', 'income_agent']:
            if key in context:
                income_agent_key = key
                break
        
        if income_agent_key:
            income_results = context[income_agent_key]
            # Handle AssessmentResult objects
            if hasattr(income_results, 'tool_results'):
                tool_results = income_results.tool_results
                if 'simple_income_calculator' in tool_results:
                    income_tool_result = tool_results['simple_income_calculator']
                    if hasattr(income_tool_result, 'data'):
                        income_data = income_tool_result.data
                    else:
                        income_data = income_tool_result
                    
                    income_info = {
                        'monthly_income': income_data.get('qualified_monthly_income', 0),
                        'annual_income': income_data.get('qualified_annual_income', 0),
                        'income_sources': income_data.get('income_sources', [])
                    }
            # Handle direct dictionary access (old format)
            elif isinstance(income_results, dict) and 'simple_income_calculator' in income_results:
                income_data = income_results['simple_income_calculator'].get('data', {})
                income_info = {
                    'monthly_income': income_data.get('qualified_monthly_income', 0),
                    'annual_income': income_data.get('qualified_annual_income', 0),
                    'income_sources': income_data.get('income_sources', [])
                }
        
        # Use stated income if verified income not available
        if not income_info.get('monthly_income'):
            income_info = {
                'monthly_income': float(application.borrower_info.annual_income) / 12,
                'annual_income': float(application.borrower_info.annual_income),
                'income_sources': ['stated_income']
            }
        
        # Debug logging - create a simple debug file
        debug_info = {
            'income_info': income_info,
            'context_keys': list(context.keys()),
            'income_agent_key': income_agent_key,
            'stated_income': application.borrower_info.annual_income
        }
        
        # Write debug info to file
        import json
        with open('credit_agent_debug.json', 'w') as f:
            json.dump(debug_info, f, indent=2, default=str)
        
        # Get credit information for debt calculation
        debt_info = {}
        if hasattr(self, '_current_tool_results'):
            if 'credit_score_analyzer' in self._current_tool_results:
                score_data = self._current_tool_results['credit_score_analyzer'].get('data', {})
                debt_info.update(score_data.get('debt_summary', {}))
            
            if 'credit_history_analyzer' in self._current_tool_results:
                history_data = self._current_tool_results['credit_history_analyzer'].get('data', {})
                debt_info.update(history_data.get('debt_analysis', {}))
        
        # Debug: Save the exact parameters being passed to DTI tool
        dti_params = {
            'application_id': application.application_id,
            'borrower_info': {
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'ssn': application.borrower_info.ssn
            },
            'income_information': income_info,
            'debt_information': debt_info,
            'loan_details': {
                'loan_amount': float(application.loan_details.loan_amount),
                'loan_term_years': application.loan_details.loan_term_years,
                'estimated_payment': float(application.loan_details.loan_amount) * 0.005  # Rough estimate
            }
        }
        
        import json
        with open('dti_tool_params.json', 'w') as f:
            json.dump(dti_params, f, indent=2, default=str)
        
        dti_result = await dti_tool.execute(**dti_params)
        
        # Debug: Save the DTI tool result
        import json
        with open('dti_tool_result.json', 'w') as f:
            json.dump({
                'success': dti_result.success,
                'data': dti_result.data,
                'error_message': dti_result.error_message
            }, f, indent=2, default=str)
        
        return dti_result
    
    def _calculate_credit_risk_score(self, tool_results: Dict[str, ToolResult], 
                                   application: MortgageApplication) -> tuple[float, RiskLevel]:
        """
        Calculate overall credit risk score based on tool results.
        
        Args:
            tool_results: Results from all credit assessment tools
            application: The mortgage application
            
        Returns:
            Tuple of (risk_score, risk_level)
        """
        risk_factors = []
        
        # Credit score risk factors
        credit_score_result = tool_results.get("credit_score_analyzer")
        if credit_score_result and credit_score_result.success:
            score_data = credit_score_result.data
            credit_score = score_data.get('credit_score', 0)
            
            if credit_score < 580:  # Poor credit
                risk_factors.append(40.0)
            elif credit_score < 620:  # Fair credit
                risk_factors.append(25.0)
            elif credit_score < 680:  # Good credit
                risk_factors.append(15.0)
            elif credit_score < 740:  # Very good credit
                risk_factors.append(8.0)
            # Excellent credit (740+) adds minimal risk
            
            # Additional score-based risk factors
            if score_data.get('recent_inquiries', 0) > 6:  # Many recent inquiries
                risk_factors.append(10.0)
            if score_data.get('new_accounts_6_months', 0) > 3:  # Too many new accounts
                risk_factors.append(8.0)
        else:
            risk_factors.append(35.0)  # High risk if credit score analysis failed
        
        # Credit history risk factors
        history_result = tool_results.get("credit_history_analyzer")
        if history_result and history_result.success:
            history_data = history_result.data
            
            # Payment history factors
            late_payments = history_data.get('late_payments_12_months', 0)
            if late_payments > 3:
                risk_factors.append(20.0)
            elif late_payments > 1:
                risk_factors.append(10.0)
            
            # Utilization factors
            utilization = history_data.get('credit_utilization_ratio', 0)
            if utilization > 0.80:  # >80% utilization
                risk_factors.append(15.0)
            elif utilization > 0.50:  # >50% utilization
                risk_factors.append(10.0)
            elif utilization > 0.30:  # >30% utilization
                risk_factors.append(5.0)
            
            # Derogatory marks
            if history_data.get('bankruptcies', 0) > 0:
                risk_factors.append(30.0)
            if history_data.get('foreclosures', 0) > 0:
                risk_factors.append(25.0)
            if history_data.get('collections', 0) > 0:
                risk_factors.append(15.0)
        else:
            risk_factors.append(20.0)  # Medium risk if history analysis failed
        
        # DTI risk factors
        dti_result = tool_results.get("debt_to_income_calculator")
        if dti_result and dti_result.success:
            dti_data = dti_result.data
            total_dti = dti_data.get('total_dti_ratio', 0)
            
            if total_dti > 0.50:  # DTI > 50%
                risk_factors.append(25.0)
            elif total_dti > 0.43:  # DTI > 43%
                risk_factors.append(15.0)
            elif total_dti > 0.36:  # DTI > 36%
                risk_factors.append(8.0)
            
            # Housing DTI factors
            housing_dti = dti_data.get('housing_dti_ratio', 0)
            if housing_dti > 0.31:  # Housing DTI > 31%
                risk_factors.append(10.0)
            elif housing_dti > 0.28:  # Housing DTI > 28%
                risk_factors.append(5.0)
        else:
            risk_factors.append(20.0)  # Medium risk if DTI calculation failed
        
        # Calculate overall risk score
        if not risk_factors:
            risk_score = 5.0  # Low baseline risk for excellent credit
        else:
            # Use weighted average with diminishing returns
            risk_score = min(100.0, sum(risk_factors) * 0.7)
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return risk_score, risk_level
    
    def _calculate_confidence_level(self, tool_results: Dict[str, ToolResult]) -> float:
        """
        Calculate overall confidence level in credit assessment results.
        
        Args:
            tool_results: Results from all credit assessment tools
            
        Returns:
            Confidence level between 0 and 1
        """
        confidence_scores = []
        
        for tool_name, result in tool_results.items():
            if result.success:
                confidence = result.data.get('confidence_score', 0.5)
                confidence_scores.append(confidence)
            else:
                confidence_scores.append(0.0)  # Failed tools have zero confidence
        
        if not confidence_scores:
            return 0.0
            
        return sum(confidence_scores) / len(confidence_scores)
    
    def _generate_recommendations(self, tool_results: Dict[str, ToolResult], 
                                application: MortgageApplication) -> List[str]:
        """
        Generate recommendations based on credit assessment results.
        
        Args:
            tool_results: Results from all credit assessment tools
            application: The mortgage application
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Credit score recommendations
        credit_score_result = tool_results.get("credit_score_analyzer")
        if credit_score_result and credit_score_result.success:
            score_data = credit_score_result.data
            credit_score = score_data.get('credit_score', 0)
            
            if credit_score < 620:
                recommendations.append("Consider credit enhancement programs or alternative loan products")
            elif credit_score < 680:
                recommendations.append("Review pricing adjustments for credit score tier")
            
            if score_data.get('recent_inquiries', 0) > 4:
                recommendations.append("Investigate reason for multiple recent credit inquiries")
        
        # Credit history recommendations
        history_result = tool_results.get("credit_history_analyzer")
        if history_result and history_result.success:
            history_data = history_result.data
            
            if history_data.get('late_payments_12_months', 0) > 0:
                recommendations.append("Obtain letter of explanation for recent late payments")
            
            utilization = history_data.get('credit_utilization_ratio', 0)
            if utilization > 0.50:
                recommendations.append("Consider requiring borrower to pay down credit card balances")
            
            if history_data.get('collections', 0) > 0:
                recommendations.append("Verify collection accounts are resolved or obtain payment plan")
        
        # DTI recommendations
        dti_result = tool_results.get("debt_to_income_calculator")
        if dti_result and dti_result.success:
            dti_data = dti_result.data
            total_dti = dti_data.get('total_dti_ratio', 0)
            
            if total_dti > 0.43:
                recommendations.append("DTI exceeds standard guidelines - evaluate compensating factors")
            elif total_dti > 0.36:
                recommendations.append("Elevated DTI - verify all debt obligations are included")
        
        return recommendations
    
    def _generate_conditions(self, tool_results: Dict[str, ToolResult], 
                           application: MortgageApplication) -> List[str]:
        """
        Generate loan conditions based on credit assessment results.
        
        Args:
            tool_results: Results from all credit assessment tools
            application: The mortgage application
            
        Returns:
            List of condition strings
        """
        conditions = []
        
        # Credit score conditions
        credit_score_result = tool_results.get("credit_score_analyzer")
        if credit_score_result and credit_score_result.success:
            score_data = credit_score_result.data
            
            if score_data.get('requires_explanation', False):
                conditions.append("Provide written explanation for credit score factors")
        
        # Credit history conditions
        history_result = tool_results.get("credit_history_analyzer")
        if history_result and history_result.success:
            history_data = history_result.data
            
            if history_data.get('late_payments_12_months', 0) > 0:
                conditions.append("Provide letter of explanation for late payments")
            
            if history_data.get('collections', 0) > 0:
                conditions.append("Provide proof of collection account resolution")
            
            if history_data.get('bankruptcies', 0) > 0:
                conditions.append("Provide complete bankruptcy documentation and discharge papers")
        
        # DTI conditions
        dti_result = tool_results.get("debt_to_income_calculator")
        if dti_result and dti_result.success:
            dti_data = dti_result.data
            
            if dti_data.get('requires_verification', False):
                conditions.append("Provide additional debt verification documentation")
        
        return conditions
    
    def _identify_red_flags(self, tool_results: Dict[str, ToolResult]) -> List[str]:
        """
        Identify red flags from credit assessment results.
        
        Args:
            tool_results: Results from all credit assessment tools
            
        Returns:
            List of red flag descriptions
        """
        red_flags = []
        
        # Credit score red flags
        credit_score_result = tool_results.get("credit_score_analyzer")
        if credit_score_result and credit_score_result.success:
            score_data = credit_score_result.data
            
            if score_data.get('fraud_indicators', []):
                red_flags.extend(score_data['fraud_indicators'])
            
            if score_data.get('credit_score', 0) < 500:
                red_flags.append("Extremely low credit score indicates high default risk")
        
        # Credit history red flags
        history_result = tool_results.get("credit_history_analyzer")
        if history_result and history_result.success:
            history_data = history_result.data
            
            if history_data.get('recent_bankruptcy', False):
                red_flags.append("Recent bankruptcy filing")
            
            if history_data.get('pattern_of_late_payments', False):
                red_flags.append("Consistent pattern of late payments indicates payment issues")
            
            if history_data.get('suspicious_activity', []):
                red_flags.extend(history_data['suspicious_activity'])
        
        # DTI red flags
        dti_result = tool_results.get("debt_to_income_calculator")
        if dti_result and dti_result.success:
            dti_data = dti_result.data
            
            if dti_data.get('total_dti_ratio', 0) > 0.60:  # DTI > 60%
                red_flags.append("Debt-to-income ratio exceeds acceptable lending limits")
            
            if dti_data.get('undisclosed_debts', []):
                red_flags.append("Potential undisclosed debt obligations detected")
        
        return red_flags