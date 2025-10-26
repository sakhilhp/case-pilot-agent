"""
Income Verification Agent implementation.

This agent specializes in income verification tasks including employment verification,
income calculation, and cross-document income consistency checking for mortgage applications.
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


class IncomeVerificationAgent(BaseAgent):
    """
    Agent specialized in income verification for mortgage applications.
    
    This agent coordinates income verification workflows including:
    - Employment verification across multiple sources
    - Income calculation with DTI analysis
    - Cross-document income consistency checking
    - Qualified income calculation with loan program compliance
    
    Tools used:
    - employment_verification_tool: Multi-source employment and income verification
    - simple_income_calculator: Qualified income calculation with DTI analysis
    - income_consistency_checker: Cross-document income validation
    """
    
    def __init__(self, agent_id: str = "income_verification_agent"):
        super().__init__(agent_id, "Income Verification Agent")
        self.logger = logging.getLogger("agent.income_verification")
        
        # Tools will be registered by the orchestrator to avoid circular imports
        
    def get_tool_names(self) -> List[str]:
        """Return list of tool names this agent uses."""
        return [
            "employment_verification_tool",
            "simple_income_calculator",
            "income_consistency_checker"
        ]
        
    async def process(self, application: MortgageApplication, context: Dict[str, Any]) -> AssessmentResult:
        """
        Process mortgage application income verification using specialized tools.
        
        Args:
            application: The mortgage application to process
            context: Additional context data from other agents
            
        Returns:
            AssessmentResult containing income verification analysis
        """
        start_time = datetime.now()
        tool_results = {}
        errors = []
        warnings = []
        recommendations = []
        
        try:
            self.logger.info(f"Starting income verification for application {application.application_id}")
            
            # Get income and employment related documents
            income_documents = self._get_income_documents(application.documents)
            employment_documents = self._get_employment_documents(application.documents)
            
            if not income_documents and not employment_documents:
                warnings.append("No income or employment documents found for verification")
            
            # Step 1: Employment verification across multiple sources
            if employment_documents:
                employment_result = await self._verify_employment(employment_documents, application)
                tool_results["employment_verification_tool"] = employment_result
                
                if not employment_result.success:
                    errors.append(f"Employment verification failed: {employment_result.error_message}")
            
            # Step 2: Income calculation with DTI analysis
            all_income_docs = income_documents + employment_documents
            if all_income_docs:
                income_calc_result = await self._calculate_income(all_income_docs, application, context)
                tool_results["simple_income_calculator"] = income_calc_result
                
                if not income_calc_result.success:
                    errors.append(f"Income calculation failed: {income_calc_result.error_message}")
            
            # Step 3: Cross-document income consistency checking
            if len(all_income_docs) > 1:
                consistency_result = await self._check_income_consistency(all_income_docs, application)
                tool_results["income_consistency_checker"] = consistency_result
                
                if not consistency_result.success:
                    errors.append(f"Income consistency check failed: {consistency_result.error_message}")
                elif consistency_result.data.get('has_discrepancies', False):
                    warnings.append("Income discrepancies detected across documents")
            
            # Generate overall assessment
            risk_score, risk_level = self._calculate_income_risk_score(tool_results, application)
            confidence_level = self._calculate_confidence_level(tool_results)
            recommendations = self._generate_recommendations(tool_results, application)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Income verification completed for application {application.application_id}")
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="income_verification",
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
            error_msg = f"Income verification failed: {str(e)}"
            self.logger.error(error_msg)
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="income_verification",
                tool_results=tool_results,
                risk_score=100.0,  # High risk due to processing failure
                risk_level=RiskLevel.HIGH,
                confidence_level=0.0,
                recommendations=["Manual income verification required due to processing failure"],
                conditions=["Provide additional income documentation"],
                red_flags=["Income verification system failure"],
                processing_time_seconds=processing_time,
                errors=[error_msg],
                warnings=warnings
            )
    
    def _get_income_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents to get income-related documents.
        
        Args:
            documents: List of all documents
            
        Returns:
            List of income-related documents
        """
        income_types = {DocumentType.INCOME}
        return [doc for doc in documents if doc.document_type in income_types]
    
    def _get_employment_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents to get employment-related documents.
        
        Args:
            documents: List of all documents
            
        Returns:
            List of employment-related documents
        """
        employment_types = {DocumentType.EMPLOYMENT}
        return [doc for doc in documents if doc.document_type in employment_types]
    
    async def _verify_employment(self, employment_documents: List[Document], 
                               application: MortgageApplication) -> ToolResult:
        """
        Verify employment using the employment verification tool.
        
        Args:
            employment_documents: List of employment documents
            application: The mortgage application
            
        Returns:
            ToolResult from employment verification
        """
        employment_tool = self.get_tool("employment_verification_tool")
        if not employment_tool:
            return ToolResult(
                tool_name="employment_verification_tool",
                success=False,
                data={},
                error_message="Employment verification tool not available"
            )
        
        # Prepare document data for verification
        document_data = []
        for doc in employment_documents:
            document_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'file_path': doc.file_path
            })
        
        return await employment_tool.safe_execute(
            application_id=application.application_id,
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'ssn': application.borrower_info.ssn,
                'employment_status': application.borrower_info.employment_status,
                'stated_income': float(application.borrower_info.annual_income)
            },
            employment_documents=document_data
        )
    
    async def _calculate_income(self, income_documents: List[Document], 
                              application: MortgageApplication, 
                              context: Dict[str, Any]) -> ToolResult:
        """
        Calculate income using the income calculator tool.
        
        Args:
            income_documents: List of income-related documents
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from income calculation
        """
        income_tool = self.get_tool("simple_income_calculator")
        if not income_tool:
            return ToolResult(
                tool_name="simple_income_calculator",
                success=False,
                data={},
                error_message="Income calculator tool not available"
            )
        
        # Prepare document data for calculation
        document_data = []
        for doc in income_documents:
            document_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'file_path': doc.file_path
            })
        
        # Get debt information from context if available (from credit assessment)
        debt_info = {}
        if 'credit_assessment_agent' in context:
            credit_results = context['credit_assessment_agent']
            if 'debt_to_income_calculator' in credit_results:
                debt_data = credit_results['debt_to_income_calculator'].get('data', {})
                debt_info = debt_data.get('debt_summary', {})
        
        return await income_tool.safe_execute(
            application_id=application.application_id,
            loan_details={
                'loan_amount': float(application.loan_details.loan_amount),
                'loan_type': application.loan_details.loan_type.value,
                'loan_term_years': application.loan_details.loan_term_years,
                'purpose': application.loan_details.purpose
            },
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'stated_income': float(application.borrower_info.annual_income),
                'employment_status': application.borrower_info.employment_status
            },
            income_documents=document_data,
            debt_information=debt_info
        )
    
    async def _check_income_consistency(self, income_documents: List[Document], 
                                      application: MortgageApplication) -> ToolResult:
        """
        Check income consistency using the consistency checker tool.
        
        Args:
            income_documents: List of income-related documents
            application: The mortgage application
            
        Returns:
            ToolResult from consistency checking
        """
        consistency_tool = self.get_tool("income_consistency_checker")
        if not consistency_tool:
            return ToolResult(
                tool_name="income_consistency_checker",
                success=False,
                data={},
                error_message="Income consistency checker tool not available"
            )
        
        # Prepare document data for consistency checking
        document_data = []
        for doc in income_documents:
            document_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'file_path': doc.file_path
            })
        
        return await consistency_tool.safe_execute(
            application_id=application.application_id,
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'stated_income': float(application.borrower_info.annual_income)
            },
            income_documents=document_data,
            verification_threshold=0.10  # 10% variance threshold
        )
    
    def _calculate_income_risk_score(self, tool_results: Dict[str, ToolResult], 
                                   application: MortgageApplication) -> tuple[float, RiskLevel]:
        """
        Calculate overall income risk score based on tool results.
        
        Args:
            tool_results: Results from all income verification tools
            application: The mortgage application
            
        Returns:
            Tuple of (risk_score, risk_level)
        """
        risk_factors = []
        
        # Employment verification risk factors
        employment_result = tool_results.get("employment_verification_tool")
        if employment_result and employment_result.success:
            employment_data = employment_result.data
            if not employment_data.get('employment_verified', True):
                risk_factors.append(30.0)  # High risk for unverified employment
            if employment_data.get('income_variance', 0) > 0.15:  # >15% variance
                risk_factors.append(20.0)  # Medium risk for income variance
            if employment_data.get('employment_stability_months', 24) < 12:
                risk_factors.append(15.0)  # Medium risk for short employment
        else:
            risk_factors.append(40.0)  # High risk if employment verification failed
        
        # Income calculation risk factors
        income_result = tool_results.get("simple_income_calculator")
        if income_result and income_result.success:
            income_data = income_result.data
            dti_ratio = income_data.get('debt_to_income_ratio', 0)
            if dti_ratio > 0.43:  # DTI > 43%
                risk_factors.append(25.0)  # High risk for high DTI
            elif dti_ratio > 0.36:  # DTI > 36%
                risk_factors.append(15.0)  # Medium risk for elevated DTI
            
            qualified_income = income_data.get('qualified_monthly_income', 0)
            stated_monthly = float(application.borrower_info.annual_income) / 12
            if qualified_income < stated_monthly * 0.8:  # Qualified < 80% of stated
                risk_factors.append(20.0)  # High risk for income reduction
        else:
            risk_factors.append(35.0)  # High risk if income calculation failed
        
        # Consistency check risk factors
        consistency_result = tool_results.get("income_consistency_checker")
        if consistency_result and consistency_result.success:
            consistency_data = consistency_result.data
            if consistency_data.get('has_discrepancies', False):
                variance = consistency_data.get('max_variance_percentage', 0)
                if variance > 0.20:  # >20% variance
                    risk_factors.append(25.0)  # High risk for major discrepancies
                elif variance > 0.10:  # >10% variance
                    risk_factors.append(15.0)  # Medium risk for moderate discrepancies
        
        # Calculate overall risk score
        if not risk_factors:
            risk_score = 10.0  # Low baseline risk
        else:
            # Use weighted average with diminishing returns
            risk_score = min(100.0, sum(risk_factors) * 0.8)
        
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
        Calculate overall confidence level in income verification results.
        
        Args:
            tool_results: Results from all income verification tools
            
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
        Generate recommendations based on income verification results.
        
        Args:
            tool_results: Results from all income verification tools
            application: The mortgage application
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Employment verification recommendations
        employment_result = tool_results.get("employment_verification_tool")
        if employment_result and employment_result.success:
            employment_data = employment_result.data
            if not employment_data.get('employment_verified', True):
                recommendations.append("Obtain additional employment verification documentation")
            if employment_data.get('income_variance', 0) > 0.10:
                recommendations.append("Review income variance and obtain explanation from borrower")
            if employment_data.get('employment_stability_months', 24) < 24:
                recommendations.append("Consider employment stability in underwriting decision")
        
        # Income calculation recommendations
        income_result = tool_results.get("simple_income_calculator")
        if income_result and income_result.success:
            income_data = income_result.data
            dti_ratio = income_data.get('debt_to_income_ratio', 0)
            if dti_ratio > 0.43:
                recommendations.append("DTI ratio exceeds standard guidelines - consider compensating factors")
            elif dti_ratio > 0.36:
                recommendations.append("Elevated DTI ratio - verify all income sources")
        
        # Consistency check recommendations
        consistency_result = tool_results.get("income_consistency_checker")
        if consistency_result and consistency_result.success:
            consistency_data = consistency_result.data
            if consistency_data.get('has_discrepancies', False):
                recommendations.append("Resolve income discrepancies before final approval")
                discrepant_docs = consistency_data.get('discrepant_documents', [])
                if discrepant_docs:
                    recommendations.append(f"Review specific documents: {', '.join(discrepant_docs)}")
        
        return recommendations
    
    def _generate_conditions(self, tool_results: Dict[str, ToolResult], 
                           application: MortgageApplication) -> List[str]:
        """
        Generate loan conditions based on income verification results.
        
        Args:
            tool_results: Results from all income verification tools
            application: The mortgage application
            
        Returns:
            List of condition strings
        """
        conditions = []
        
        # Employment verification conditions
        employment_result = tool_results.get("employment_verification_tool")
        if employment_result and employment_result.success:
            employment_data = employment_result.data
            if not employment_data.get('employment_verified', True):
                conditions.append("Provide written employment verification from current employer")
            if employment_data.get('employment_stability_months', 24) < 12:
                conditions.append("Provide 12 months employment history documentation")
        
        # Income calculation conditions
        income_result = tool_results.get("simple_income_calculator")
        if income_result and income_result.success:
            income_data = income_result.data
            if income_data.get('requires_additional_documentation', False):
                conditions.append("Provide additional income documentation as specified")
        
        # Consistency check conditions
        consistency_result = tool_results.get("income_consistency_checker")
        if consistency_result and consistency_result.success:
            consistency_data = consistency_result.data
            if consistency_data.get('has_discrepancies', False):
                conditions.append("Provide explanation and documentation for income discrepancies")
        
        return conditions
    
    def _identify_red_flags(self, tool_results: Dict[str, ToolResult]) -> List[str]:
        """
        Identify red flags from income verification results.
        
        Args:
            tool_results: Results from all income verification tools
            
        Returns:
            List of red flag descriptions
        """
        red_flags = []
        
        # Employment verification red flags
        employment_result = tool_results.get("employment_verification_tool")
        if employment_result and employment_result.success:
            employment_data = employment_result.data
            if employment_data.get('potential_fraud_indicators', []):
                red_flags.extend(employment_data['potential_fraud_indicators'])
            if employment_data.get('income_variance', 0) > 0.25:  # >25% variance
                red_flags.append("Significant income variance detected - potential misrepresentation")
        
        # Income calculation red flags
        income_result = tool_results.get("simple_income_calculator")
        if income_result and income_result.success:
            income_data = income_result.data
            if income_data.get('dti_ratio', 0) > 0.50:  # DTI > 50%
                red_flags.append("Debt-to-income ratio exceeds acceptable limits")
        
        # Consistency check red flags
        consistency_result = tool_results.get("income_consistency_checker")
        if consistency_result and consistency_result.success:
            consistency_data = consistency_result.data
            if consistency_data.get('max_variance_percentage', 0) > 0.30:  # >30% variance
                red_flags.append("Major income discrepancies suggest potential fraud")
            if consistency_data.get('suspicious_patterns', []):
                red_flags.extend(consistency_data['suspicious_patterns'])
        
        return red_flags