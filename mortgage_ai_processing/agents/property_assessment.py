"""
Property Assessment Agent implementation.

This agent specializes in property assessment tasks including property valuation,
loan-to-value calculations, and property risk analysis for mortgage applications.
"""

from typing import Dict, List, Any
import logging
from datetime import datetime
from decimal import Decimal

from .base import BaseAgent
from ..models.core import MortgageApplication, Document, DocumentType
from ..models.assessment import AssessmentResult, RiskLevel
from ..tools.base import ToolResult


class PropertyAssessmentAgent(BaseAgent):
    """
    Agent specialized in property assessment for mortgage applications.
    
    This agent coordinates property assessment workflows including:
    - Property valuation analysis using external services
    - Loan-to-value (LTV) ratio calculations and risk assessment
    - Property-specific risk factor identification and analysis
    - Market condition and location risk evaluation
    
    Tools used:
    - property_valuation_tool: Automated property valuation with confidence scoring
    - ltv_calculator: Loan-to-value ratio calculation and compliance checking
    - property_risk_analyzer: Comprehensive property risk evaluation
    """
    
    def __init__(self, agent_id: str = "property_assessment_agent"):
        super().__init__(agent_id, "Property Assessment Agent")
        self.logger = logging.getLogger("agent.property_assessment")
        
    def get_tool_names(self) -> List[str]:
        """Return list of tool names this agent uses."""
        return [
            "property_valuation_tool",
            "ltv_calculator",
            "property_risk_analyzer"
        ]
        
    async def process(self, application: MortgageApplication, context: Dict[str, Any]) -> AssessmentResult:
        """
        Process mortgage application property assessment using specialized tools.
        
        Args:
            application: The mortgage application to process
            context: Additional context data from other agents
            
        Returns:
            AssessmentResult containing property assessment analysis
        """
        start_time = datetime.now()
        tool_results = {}
        errors = []
        warnings = []
        recommendations = []
        
        try:
            self.logger.info(f"Starting property assessment for application {application.application_id}")
            
            # Get property-related documents
            property_documents = self._get_property_documents(application.documents)
            
            if not property_documents:
                warnings.append("No property documents found for assessment")
            
            # Store tool results for cross-tool communication
            self._current_tool_results = {}
            
            # Step 1: Property valuation analysis
            valuation_result = await self._perform_property_valuation(application, property_documents, context)
            tool_results["property_valuation_tool"] = valuation_result
            self._current_tool_results["property_valuation_tool"] = valuation_result.data if valuation_result.success else {}
            
            if not valuation_result.success:
                errors.append(f"Property valuation failed: {valuation_result.error_message}")
            
            # Step 2: LTV calculation and analysis
            ltv_result = await self._calculate_loan_to_value(application, context)
            tool_results["ltv_calculator"] = ltv_result
            self._current_tool_results["ltv_calculator"] = ltv_result.data if ltv_result.success else {}
            
            if not ltv_result.success:
                errors.append(f"LTV calculation failed: {ltv_result.error_message}")
            
            # Step 3: Property risk analysis
            risk_result = await self._analyze_property_risk(application, property_documents, context)
            tool_results["property_risk_analyzer"] = risk_result
            self._current_tool_results["property_risk_analyzer"] = risk_result.data if risk_result.success else {}
            
            if not risk_result.success:
                errors.append(f"Property risk analysis failed: {risk_result.error_message}")
            
            # Generate overall assessment
            risk_score, risk_level = self._calculate_property_risk_score(tool_results, application)
            confidence_level = self._calculate_confidence_level(tool_results)
            recommendations = self._generate_recommendations(tool_results, application)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Property assessment completed for application {application.application_id}")
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="property_assessment",
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
            error_msg = f"Property assessment failed: {str(e)}"
            self.logger.error(error_msg)
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="property_assessment",
                tool_results=tool_results,
                risk_score=100.0,  # High risk due to processing failure
                risk_level=RiskLevel.HIGH,
                confidence_level=0.0,
                recommendations=["Manual property assessment required due to processing failure"],
                conditions=["Provide additional property documentation"],
                red_flags=["Property assessment system failure"],
                processing_time_seconds=processing_time,
                errors=[error_msg],
                warnings=warnings
            )
    
    def _get_property_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents to get property-related documents.
        
        Args:
            documents: List of all documents
            
        Returns:
            List of property-related documents
        """
        property_types = {DocumentType.PROPERTY}
        return [doc for doc in documents if doc.document_type in property_types]
    
    async def _perform_property_valuation(self, application: MortgageApplication, 
                                        property_documents: List[Document],
                                        context: Dict[str, Any]) -> ToolResult:
        """
        Perform property valuation using the property valuation tool.
        
        Args:
            application: The mortgage application
            property_documents: List of property-related documents
            context: Additional context from other agents
            
        Returns:
            ToolResult from property valuation analysis
        """
        valuation_tool = self.get_tool("property_valuation_tool")
        if not valuation_tool:
            return ToolResult(
                tool_name="property_valuation_tool",
                success=False,
                data={},
                error_message="Property valuation tool not available"
            )
        
        # Prepare property information
        property_info = {
            'address': application.property_info.address,
            'property_type': application.property_info.property_type,
            'stated_value': float(application.property_info.property_value),
            'square_footage': application.property_info.square_footage,
            'bedrooms': application.property_info.bedrooms,
            'bathrooms': float(application.property_info.bathrooms) if application.property_info.bathrooms else None,
            'year_built': application.property_info.year_built,
            'lot_size': float(application.property_info.lot_size) if application.property_info.lot_size else None
        }
        
        # Prepare document data for analysis
        document_data = []
        for doc in property_documents:
            document_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'file_path': doc.file_path
            })
        
        # Get loan information
        loan_info = {
            'loan_amount': float(application.loan_details.loan_amount),
            'loan_type': application.loan_details.loan_type.value,
            'purpose': application.loan_details.purpose
        }
        
        return await valuation_tool.safe_execute(
            application_id=application.application_id,
            property_information=property_info,
            loan_information=loan_info,
            property_documents=document_data,
            valuation_method="automated_comprehensive"
        )
    
    async def _calculate_loan_to_value(self, application: MortgageApplication,
                                     context: Dict[str, Any]) -> ToolResult:
        """
        Calculate loan-to-value ratio using the LTV calculator tool.
        
        Args:
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from LTV calculation
        """
        ltv_tool = self.get_tool("ltv_calculator")
        if not ltv_tool:
            return ToolResult(
                tool_name="ltv_calculator",
                success=False,
                data={},
                error_message="LTV calculator tool not available"
            )
        
        # Get appraised value from valuation if available
        appraised_value = float(application.property_info.property_value)  # Default to stated value
        if hasattr(self, '_current_tool_results') and 'property_valuation_tool' in self._current_tool_results:
            valuation_data = self._current_tool_results['property_valuation_tool'].get('data', {})
            if 'appraised_value' in valuation_data:
                appraised_value = valuation_data['appraised_value']
        
        # Prepare loan and property information
        loan_info = {
            'loan_amount': float(application.loan_details.loan_amount),
            'loan_type': application.loan_details.loan_type.value,
            'loan_term_years': application.loan_details.loan_term_years,
            'down_payment': float(application.loan_details.down_payment),
            'purpose': application.loan_details.purpose
        }
        
        property_info = {
            'address': application.property_info.address,
            'property_type': application.property_info.property_type,
            'appraised_value': appraised_value,
            'stated_value': float(application.property_info.property_value)
        }
        
        return await ltv_tool.safe_execute(
            application_id=application.application_id,
            loan_information=loan_info,
            property_information=property_info,
            calculation_method="comprehensive"
        )
    
    async def _analyze_property_risk(self, application: MortgageApplication,
                                   property_documents: List[Document],
                                   context: Dict[str, Any]) -> ToolResult:
        """
        Analyze property risk using the property risk analyzer tool.
        
        Args:
            application: The mortgage application
            property_documents: List of property-related documents
            context: Additional context from other agents
            
        Returns:
            ToolResult from property risk analysis
        """
        risk_tool = self.get_tool("property_risk_analyzer")
        if not risk_tool:
            return ToolResult(
                tool_name="property_risk_analyzer",
                success=False,
                data={},
                error_message="Property risk analyzer tool not available"
            )
        
        # Get valuation and LTV information from previous analyses
        valuation_info = {}
        ltv_info = {}
        
        if hasattr(self, '_current_tool_results'):
            if 'property_valuation_tool' in self._current_tool_results:
                valuation_info = self._current_tool_results['property_valuation_tool'].get('data', {})
            
            if 'ltv_calculator' in self._current_tool_results:
                ltv_info = self._current_tool_results['ltv_calculator'].get('data', {})
        
        # Prepare comprehensive property information
        property_info = {
            'address': application.property_info.address,
            'property_type': application.property_info.property_type,
            'property_value': float(application.property_info.property_value),
            'square_footage': application.property_info.square_footage,
            'bedrooms': application.property_info.bedrooms,
            'bathrooms': float(application.property_info.bathrooms) if application.property_info.bathrooms else None,
            'year_built': application.property_info.year_built,
            'lot_size': float(application.property_info.lot_size) if application.property_info.lot_size else None,
            'property_tax_annual': float(application.property_info.property_tax_annual) if application.property_info.property_tax_annual else None,
            'hoa_fees_monthly': float(application.property_info.hoa_fees_monthly) if application.property_info.hoa_fees_monthly else None
        }
        
        # Prepare document data for analysis
        document_data = []
        for doc in property_documents:
            document_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'file_path': doc.file_path
            })
        
        # Prepare loan information
        loan_info = {
            'loan_amount': float(application.loan_details.loan_amount),
            'loan_type': application.loan_details.loan_type.value,
            'purpose': application.loan_details.purpose
        }
        
        return await risk_tool.safe_execute(
            application_id=application.application_id,
            property_information=property_info,
            loan_information=loan_info,
            valuation_data=valuation_info,
            ltv_data=ltv_info,
            property_documents=document_data,
            analysis_scope="comprehensive"
        )
    
    def _calculate_property_risk_score(self, tool_results: Dict[str, ToolResult], 
                                     application: MortgageApplication) -> tuple[float, RiskLevel]:
        """
        Calculate overall property risk score based on tool results.
        
        Args:
            tool_results: Results from all property assessment tools
            application: The mortgage application
            
        Returns:
            Tuple of (risk_score, risk_level)
        """
        risk_factors = []
        
        # Property valuation risk factors
        valuation_result = tool_results.get("property_valuation_tool")
        if valuation_result and valuation_result.success:
            valuation_data = valuation_result.data
            
            # Valuation confidence risk
            confidence = valuation_data.get('confidence_score', 0.5)
            if confidence < 0.6:  # Low confidence in valuation
                risk_factors.append(20.0)
            elif confidence < 0.8:  # Medium confidence
                risk_factors.append(10.0)
            
            # Value variance risk
            stated_value = float(application.property_info.property_value)
            appraised_value = valuation_data.get('appraised_value', stated_value)
            variance = abs(appraised_value - stated_value) / stated_value
            
            if variance > 0.15:  # >15% variance
                risk_factors.append(25.0)
            elif variance > 0.10:  # >10% variance
                risk_factors.append(15.0)
            elif variance > 0.05:  # >5% variance
                risk_factors.append(8.0)
            
            # Market condition risks
            market_conditions = valuation_data.get('market_conditions', {})
            if market_conditions.get('market_trend') == 'declining':
                risk_factors.append(15.0)
            elif market_conditions.get('market_trend') == 'volatile':
                risk_factors.append(10.0)
        else:
            risk_factors.append(30.0)  # High risk if valuation failed
        
        # LTV risk factors
        ltv_result = tool_results.get("ltv_calculator")
        if ltv_result and ltv_result.success:
            ltv_data = ltv_result.data
            ltv_ratio = ltv_data.get('ltv_ratio', 0)
            
            if ltv_ratio > 0.95:  # LTV > 95%
                risk_factors.append(30.0)
            elif ltv_ratio > 0.90:  # LTV > 90%
                risk_factors.append(20.0)
            elif ltv_ratio > 0.80:  # LTV > 80%
                risk_factors.append(10.0)
            elif ltv_ratio > 0.70:  # LTV > 70%
                risk_factors.append(5.0)
            
            # Combined LTV (if applicable)
            cltv_ratio = ltv_data.get('cltv_ratio', ltv_ratio)
            if cltv_ratio > ltv_ratio and cltv_ratio > 0.90:
                risk_factors.append(15.0)
        else:
            risk_factors.append(25.0)  # High risk if LTV calculation failed
        
        # Property-specific risk factors
        risk_result = tool_results.get("property_risk_analyzer")
        if risk_result and risk_result.success:
            risk_data = risk_result.data
            
            # Location risks
            location_risk = risk_data.get('location_risk_score', 0)
            if location_risk > 80:
                risk_factors.append(20.0)
            elif location_risk > 60:
                risk_factors.append(12.0)
            elif location_risk > 40:
                risk_factors.append(6.0)
            
            # Property condition risks
            condition_risk = risk_data.get('condition_risk_score', 0)
            if condition_risk > 80:
                risk_factors.append(25.0)
            elif condition_risk > 60:
                risk_factors.append(15.0)
            elif condition_risk > 40:
                risk_factors.append(8.0)
            
            # Market risks
            market_risk = risk_data.get('market_risk_score', 0)
            if market_risk > 80:
                risk_factors.append(18.0)
            elif market_risk > 60:
                risk_factors.append(10.0)
            elif market_risk > 40:
                risk_factors.append(5.0)
            
            # Environmental risks
            environmental_risks = risk_data.get('environmental_risks', [])
            if environmental_risks:
                risk_factors.append(len(environmental_risks) * 5.0)  # 5 points per risk
        else:
            risk_factors.append(20.0)  # Medium risk if property risk analysis failed
        
        # Calculate overall risk score
        if not risk_factors:
            risk_score = 5.0  # Low baseline risk for excellent property
        else:
            # Use weighted average with diminishing returns
            risk_score = min(100.0, sum(risk_factors) * 0.8)
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return risk_score, risk_level
    
    def _calculate_confidence_level(self, tool_results: Dict[str, ToolResult]) -> float:
        """
        Calculate overall confidence level in property assessment results.
        
        Args:
            tool_results: Results from all property assessment tools
            
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
        Generate recommendations based on property assessment results.
        
        Args:
            tool_results: Results from all property assessment tools
            application: The mortgage application
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Property valuation recommendations
        valuation_result = tool_results.get("property_valuation_tool")
        if valuation_result and valuation_result.success:
            valuation_data = valuation_result.data
            
            confidence = valuation_data.get('confidence_score', 0.5)
            if confidence < 0.7:
                recommendations.append("Consider ordering full appraisal due to valuation uncertainty")
            
            # Value variance recommendations
            stated_value = float(application.property_info.property_value)
            appraised_value = valuation_data.get('appraised_value', stated_value)
            variance = abs(appraised_value - stated_value) / stated_value
            
            if variance > 0.10:
                recommendations.append("Significant value variance detected - verify property details and condition")
        
        # LTV recommendations
        ltv_result = tool_results.get("ltv_calculator")
        if ltv_result and ltv_result.success:
            ltv_data = ltv_result.data
            ltv_ratio = ltv_data.get('ltv_ratio', 0)
            
            if ltv_ratio > 0.80:
                recommendations.append("High LTV ratio - consider mortgage insurance requirements")
            
            if ltv_ratio > 0.95:
                recommendations.append("Very high LTV - evaluate loan program eligibility and risk factors")
        
        # Property risk recommendations
        risk_result = tool_results.get("property_risk_analyzer")
        if risk_result and risk_result.success:
            risk_data = risk_result.data
            
            location_risk = risk_data.get('location_risk_score', 0)
            if location_risk > 70:
                recommendations.append("High location risk identified - review market conditions and comparable sales")
            
            condition_risk = risk_data.get('condition_risk_score', 0)
            if condition_risk > 70:
                recommendations.append("Property condition concerns - consider requiring inspection or repair escrow")
            
            environmental_risks = risk_data.get('environmental_risks', [])
            if environmental_risks:
                recommendations.append("Environmental risks identified - verify insurance coverage and disclosure requirements")
        
        return recommendations
    
    def _generate_conditions(self, tool_results: Dict[str, ToolResult], 
                           application: MortgageApplication) -> List[str]:
        """
        Generate loan conditions based on property assessment results.
        
        Args:
            tool_results: Results from all property assessment tools
            application: The mortgage application
            
        Returns:
            List of condition strings
        """
        conditions = []
        
        # Property valuation conditions
        valuation_result = tool_results.get("property_valuation_tool")
        if valuation_result and valuation_result.success:
            valuation_data = valuation_result.data
            
            if valuation_data.get('requires_full_appraisal', False):
                conditions.append("Obtain full property appraisal from licensed appraiser")
        
        # LTV conditions
        ltv_result = tool_results.get("ltv_calculator")
        if ltv_result and ltv_result.success:
            ltv_data = ltv_result.data
            
            if ltv_data.get('requires_pmi', False):
                conditions.append("Obtain private mortgage insurance (PMI)")
            
            if ltv_data.get('requires_additional_down_payment', False):
                conditions.append("Provide additional down payment to meet LTV requirements")
        
        # Property risk conditions
        risk_result = tool_results.get("property_risk_analyzer")
        if risk_result and risk_result.success:
            risk_data = risk_result.data
            
            if risk_data.get('requires_inspection', False):
                conditions.append("Provide satisfactory property inspection report")
            
            if risk_data.get('requires_flood_insurance', False):
                conditions.append("Obtain flood insurance coverage")
            
            if risk_data.get('requires_environmental_clearance', False):
                conditions.append("Provide environmental clearance documentation")
        
        return conditions
    
    def _identify_red_flags(self, tool_results: Dict[str, ToolResult]) -> List[str]:
        """
        Identify red flags from property assessment results.
        
        Args:
            tool_results: Results from all property assessment tools
            
        Returns:
            List of red flag descriptions
        """
        red_flags = []
        
        # Property valuation red flags
        valuation_result = tool_results.get("property_valuation_tool")
        if valuation_result and valuation_result.success:
            valuation_data = valuation_result.data
            
            if valuation_data.get('valuation_red_flags', []):
                red_flags.extend(valuation_data['valuation_red_flags'])
            
            # Extreme value variance
            if 'appraised_value' in valuation_data:
                stated_value = float(application.property_info.property_value)
                appraised_value = valuation_data['appraised_value']
                variance = abs(appraised_value - stated_value) / stated_value
                
                if variance > 0.25:  # >25% variance
                    red_flags.append("Extreme variance between stated and appraised property value")
        
        # LTV red flags
        ltv_result = tool_results.get("ltv_calculator")
        if ltv_result and ltv_result.success:
            ltv_data = ltv_result.data
            
            ltv_ratio = ltv_data.get('ltv_ratio', 0)
            if ltv_ratio > 1.0:  # LTV > 100%
                red_flags.append("Loan amount exceeds property value (LTV > 100%)")
            
            if ltv_data.get('ltv_red_flags', []):
                red_flags.extend(ltv_data['ltv_red_flags'])
        
        # Property risk red flags
        risk_result = tool_results.get("property_risk_analyzer")
        if risk_result and risk_result.success:
            risk_data = risk_result.data
            
            if risk_data.get('critical_risks', []):
                red_flags.extend(risk_data['critical_risks'])
            
            # High overall risk scores
            if risk_data.get('overall_risk_score', 0) > 90:
                red_flags.append("Extremely high property risk score indicates potential lending concerns")
        
        return red_flags