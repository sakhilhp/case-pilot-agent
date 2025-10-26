"""
Risk Assessment Agent implementation.

This agent specializes in comprehensive risk assessment tasks including KYC risk scoring,
PEP and sanctions screening, and consolidated risk evaluation for mortgage applications.
"""

from typing import Dict, List, Any
import logging
from datetime import datetime
from decimal import Decimal

from .base import BaseAgent
from ..models.core import MortgageApplication, Document, DocumentType
from ..models.assessment import AssessmentResult, RiskLevel
from ..tools.base import ToolResult


class RiskAssessmentAgent(BaseAgent):
    """
    Agent specialized in comprehensive risk assessment for mortgage applications.
    
    This agent coordinates risk assessment workflows including:
    - KYC (Know Your Customer) risk scoring and factor identification
    - PEP (Politically Exposed Person) and sanctions screening
    - Consolidated risk assessment and reporting
    - Risk level categorization and mitigation recommendations
    
    Tools used:
    - kyc_risk_scorer: Comprehensive KYC analysis and risk scoring
    - pep_sanctions_checker: PEP detection and sanctions list screening
    """
    
    def __init__(self, agent_id: str = "risk_assessment_agent"):
        super().__init__(agent_id, "Risk Assessment Agent")
        self.logger = logging.getLogger("agent.risk_assessment")
        
    def get_tool_names(self) -> List[str]:
        """Return list of tool names this agent uses."""
        return [
            "kyc_risk_scorer",
            "pep_sanctions_checker"
        ]
        
    async def process(self, application: MortgageApplication, context: Dict[str, Any]) -> AssessmentResult:
        """
        Process mortgage application risk assessment using specialized tools.
        
        Args:
            application: The mortgage application to process
            context: Additional context data from other agents
            
        Returns:
            AssessmentResult containing comprehensive risk assessment analysis
        """
        start_time = datetime.now()
        tool_results = {}
        errors = []
        warnings = []
        recommendations = []
        
        try:
            self.logger.info(f"Starting risk assessment for application {application.application_id}")
            
            # Get identity and address documents for KYC analysis
            identity_documents = self._get_identity_documents(application.documents)
            address_documents = self._get_address_documents(application.documents)
            
            if not identity_documents:
                warnings.append("No identity documents found for KYC assessment")
            if not address_documents:
                warnings.append("No address proof documents found for KYC assessment")
            
            # Store tool results for cross-tool communication
            self._current_tool_results = {}
            
            # Step 1: KYC risk scoring with comprehensive analysis
            kyc_result = await self._perform_kyc_risk_scoring(application, identity_documents, address_documents, context)
            tool_results["kyc_risk_scorer"] = kyc_result
            self._current_tool_results["kyc_risk_scorer"] = kyc_result.data if kyc_result.success else {}
            
            if not kyc_result.success:
                errors.append(f"KYC risk scoring failed: {kyc_result.error_message}")
            
            # Step 2: PEP and sanctions screening
            pep_sanctions_result = await self._perform_pep_sanctions_screening(application, context)
            tool_results["pep_sanctions_checker"] = pep_sanctions_result
            self._current_tool_results["pep_sanctions_checker"] = pep_sanctions_result.data if pep_sanctions_result.success else {}
            
            if not pep_sanctions_result.success:
                errors.append(f"PEP/sanctions screening failed: {pep_sanctions_result.error_message}")
            
            # Generate overall risk assessment
            risk_score, risk_level = self._calculate_consolidated_risk_score(tool_results, application, context)
            confidence_level = self._calculate_confidence_level(tool_results)
            recommendations = self._generate_recommendations(tool_results, application, context)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Risk assessment completed for application {application.application_id}")
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="risk_assessment",
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
            error_msg = f"Risk assessment failed: {str(e)}"
            self.logger.error(error_msg)
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="risk_assessment",
                tool_results=tool_results,
                risk_score=100.0,  # Maximum risk due to processing failure
                risk_level=RiskLevel.HIGH,
                confidence_level=0.0,
                recommendations=["Manual risk assessment required due to processing failure"],
                conditions=["Provide additional documentation for manual risk review"],
                red_flags=["Risk assessment system failure"],
                processing_time_seconds=processing_time,
                errors=[error_msg],
                warnings=warnings
            )
    
    def _get_identity_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents to get identity-related documents.
        
        Args:
            documents: List of all documents
            
        Returns:
            List of identity-related documents
        """
        identity_types = {DocumentType.IDENTITY}
        return [doc for doc in documents if doc.document_type in identity_types]
    
    def _get_address_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents to get address proof documents.
        
        Args:
            documents: List of all documents
            
        Returns:
            List of address proof documents
        """
        address_types = {DocumentType.ADDRESS_PROOF}
        return [doc for doc in documents if doc.document_type in address_types]
    
    async def _perform_kyc_risk_scoring(self, application: MortgageApplication, 
                                      identity_documents: List[Document],
                                      address_documents: List[Document],
                                      context: Dict[str, Any]) -> ToolResult:
        """
        Perform KYC risk scoring using the KYC risk scorer tool.
        
        Args:
            application: The mortgage application
            identity_documents: List of identity documents
            address_documents: List of address proof documents
            context: Additional context from other agents
            
        Returns:
            ToolResult from KYC risk scoring
        """
        kyc_tool = self.get_tool("kyc_risk_scorer")
        if not kyc_tool:
            return ToolResult(
                tool_name="kyc_risk_scorer",
                success=False,
                data={},
                error_message="KYC risk scorer tool not available"
            )
        
        # Prepare identity document data
        identity_data = []
        for doc in identity_documents:
            identity_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'validation_status': doc.validation_status.value if doc.validation_status else 'unknown',
                'file_path': doc.file_path
            })
        
        # Prepare address document data
        address_data = []
        for doc in address_documents:
            address_data.append({
                'document_id': doc.document_id,
                'document_type': doc.document_type.value,
                'extracted_data': doc.extracted_data,
                'validation_status': doc.validation_status.value if doc.validation_status else 'unknown',
                'file_path': doc.file_path
            })
        
        # Get additional context from other agents
        income_info = {}
        credit_info = {}
        property_info = {}
        
        if 'income_verification_agent' in context:
            income_results = context['income_verification_agent']
            if 'simple_income_calculator' in income_results:
                income_data = income_results['simple_income_calculator'].get('data', {})
                income_info = {
                    'annual_income': income_data.get('qualified_annual_income', 0),
                    'employment_verified': income_data.get('employment_verified', False),
                    'income_sources': income_data.get('income_sources', [])
                }
        
        if 'credit_assessment_agent' in context:
            credit_results = context['credit_assessment_agent']
            if 'credit_score_analyzer' in credit_results:
                credit_data = credit_results['credit_score_analyzer'].get('data', {})
                credit_info = {
                    'credit_score': credit_data.get('credit_score', 0),
                    'credit_history_length': credit_data.get('credit_history_length_months', 0),
                    'derogatory_marks': credit_data.get('derogatory_marks', 0)
                }
        
        if 'property_assessment_agent' in context:
            property_results = context['property_assessment_agent']
            if 'property_valuation_tool' in property_results:
                property_data = property_results['property_valuation_tool'].get('data', {})
                property_info = {
                    'property_value': property_data.get('estimated_value', 0),
                    'property_type': property_data.get('property_type', 'unknown'),
                    'location_risk': property_data.get('location_risk_score', 0)
                }
        
        return await kyc_tool.safe_execute(
            application_id=application.application_id,
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'ssn': application.borrower_info.ssn,
                'date_of_birth': application.borrower_info.date_of_birth.isoformat(),
                'current_address': application.borrower_info.current_address,
                'phone_number': application.borrower_info.phone_number,
                'email': application.borrower_info.email
            },
            identity_documents=identity_data,
            address_documents=address_data,
            loan_details={
                'loan_amount': float(application.loan_details.loan_amount),
                'loan_type': application.loan_details.loan_type.value,
                'purpose': application.loan_details.purpose
            },
            income_information=income_info,
            credit_information=credit_info,
            property_information=property_info,
            analysis_depth="comprehensive"
        )
    
    async def _perform_pep_sanctions_screening(self, application: MortgageApplication,
                                             context: Dict[str, Any]) -> ToolResult:
        """
        Perform PEP and sanctions screening using the PEP sanctions checker tool.
        
        Args:
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            ToolResult from PEP and sanctions screening
        """
        pep_tool = self.get_tool("pep_sanctions_checker")
        if not pep_tool:
            return ToolResult(
                tool_name="pep_sanctions_checker",
                success=False,
                data={},
                error_message="PEP sanctions checker tool not available"
            )
        
        # Get KYC information from previous analysis if available
        kyc_info = {}
        if hasattr(self, '_current_tool_results') and 'kyc_risk_scorer' in self._current_tool_results:
            kyc_data = self._current_tool_results['kyc_risk_scorer'].get('data', {})
            kyc_info = {
                'identity_verified': kyc_data.get('identity_verified', False),
                'address_verified': kyc_data.get('address_verified', False),
                'risk_factors': kyc_data.get('risk_factors', []),
                'verification_confidence': kyc_data.get('verification_confidence', 0.0)
            }
        
        # Prepare additional names for screening (aliases, previous names, etc.)
        additional_names = []
        if hasattr(application.borrower_info, 'previous_names'):
            additional_names.extend(application.borrower_info.previous_names)
        if hasattr(application.borrower_info, 'aliases'):
            additional_names.extend(application.borrower_info.aliases)
        
        return await pep_tool.safe_execute(
            application_id=application.application_id,
            borrower_info={
                'name': f"{application.borrower_info.first_name} {application.borrower_info.last_name}",
                'first_name': application.borrower_info.first_name,
                'last_name': application.borrower_info.last_name,
                'date_of_birth': application.borrower_info.date_of_birth.isoformat(),
                'nationality': getattr(application.borrower_info, 'nationality', 'unknown'),
                'country_of_residence': getattr(application.borrower_info, 'country_of_residence', 'US'),
                'additional_names': additional_names
            },
            kyc_information=kyc_info,
            screening_depth="enhanced",  # Enhanced screening for mortgage applications
            include_family_associates=True,  # Include family and business associates
            sanctions_lists=[
                "OFAC_SDN",  # Office of Foreign Assets Control Specially Designated Nationals
                "OFAC_CONS",  # OFAC Consolidated List
                "UN_SANCTIONS",  # United Nations Sanctions List
                "EU_SANCTIONS",  # European Union Sanctions List
                "UK_SANCTIONS",  # UK HM Treasury Sanctions List
                "FATF_GREYLIST"  # Financial Action Task Force Grey List
            ]
        )
    
    def _calculate_consolidated_risk_score(self, tool_results: Dict[str, ToolResult], 
                                         application: MortgageApplication,
                                         context: Dict[str, Any]) -> tuple[float, RiskLevel]:
        """
        Calculate consolidated risk score based on all risk assessment results.
        
        Args:
            tool_results: Results from all risk assessment tools
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            Tuple of (risk_score, risk_level)
        """
        risk_factors = []
        
        # KYC risk factors
        kyc_result = tool_results.get("kyc_risk_scorer")
        if kyc_result and kyc_result.success:
            kyc_data = kyc_result.data
            
            # Identity verification risk
            if not kyc_data.get('identity_verified', False):
                risk_factors.append(25.0)
            elif kyc_data.get('identity_confidence', 1.0) < 0.8:
                risk_factors.append(15.0)
            
            # Address verification risk
            if not kyc_data.get('address_verified', False):
                risk_factors.append(20.0)
            elif kyc_data.get('address_confidence', 1.0) < 0.8:
                risk_factors.append(10.0)
            
            # Document authenticity risk
            if kyc_data.get('document_authenticity_score', 1.0) < 0.7:
                risk_factors.append(30.0)
            elif kyc_data.get('document_authenticity_score', 1.0) < 0.9:
                risk_factors.append(15.0)
            
            # Fraud indicators
            fraud_indicators = kyc_data.get('fraud_indicators', [])
            if fraud_indicators:
                risk_factors.append(min(50.0, len(fraud_indicators) * 10.0))
            
            # Inconsistency risk
            inconsistencies = kyc_data.get('data_inconsistencies', [])
            if inconsistencies:
                risk_factors.append(min(25.0, len(inconsistencies) * 5.0))
            
            # Overall KYC risk score
            kyc_risk_score = kyc_data.get('overall_risk_score', 0)
            if kyc_risk_score > 70:
                risk_factors.append(35.0)
            elif kyc_risk_score > 50:
                risk_factors.append(20.0)
            elif kyc_risk_score > 30:
                risk_factors.append(10.0)
        else:
            risk_factors.append(40.0)  # High risk if KYC analysis failed
        
        # PEP and sanctions risk factors
        pep_result = tool_results.get("pep_sanctions_checker")
        if pep_result and pep_result.success:
            pep_data = pep_result.data
            
            # Direct PEP matches
            if pep_data.get('is_pep', False):
                pep_risk_level = pep_data.get('pep_risk_level', 'medium')
                if pep_risk_level == 'high':
                    risk_factors.append(60.0)
                elif pep_risk_level == 'medium':
                    risk_factors.append(35.0)
                else:
                    risk_factors.append(20.0)
            
            # Sanctions matches
            sanctions_matches = pep_data.get('sanctions_matches', [])
            if sanctions_matches:
                # Any sanctions match is extremely high risk
                risk_factors.append(80.0)
            
            # Family/associate matches
            family_matches = pep_data.get('family_associate_matches', [])
            if family_matches:
                risk_factors.append(min(40.0, len(family_matches) * 15.0))
            
            # Watchlist matches
            watchlist_matches = pep_data.get('watchlist_matches', [])
            if watchlist_matches:
                risk_factors.append(min(30.0, len(watchlist_matches) * 10.0))
            
            # Overall screening risk score
            screening_risk = pep_data.get('overall_risk_score', 0)
            if screening_risk > 80:
                risk_factors.append(50.0)
            elif screening_risk > 60:
                risk_factors.append(30.0)
            elif screening_risk > 40:
                risk_factors.append(15.0)
        else:
            risk_factors.append(30.0)  # Medium-high risk if screening failed
        
        # Additional risk factors from other agents
        self._add_contextual_risk_factors(risk_factors, context)
        
        # Calculate overall risk score
        if not risk_factors:
            risk_score = 5.0  # Low baseline risk
        else:
            # Use weighted average with diminishing returns for multiple factors
            risk_score = min(100.0, sum(risk_factors) * 0.6)
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return risk_score, risk_level
    
    def _add_contextual_risk_factors(self, risk_factors: List[float], context: Dict[str, Any]) -> None:
        """
        Add risk factors based on context from other agents.
        
        Args:
            risk_factors: List to append additional risk factors to
            context: Context from other agents
        """
        # Credit-related risk factors
        if 'credit_assessment_agent' in context:
            credit_results = context['credit_assessment_agent']
            if 'credit_score_analyzer' in credit_results:
                credit_data = credit_results['credit_score_analyzer'].get('data', {})
                credit_score = credit_data.get('credit_score', 0)
                
                if credit_score < 500:  # Very poor credit adds risk
                    risk_factors.append(15.0)
                elif credit_score < 580:  # Poor credit adds moderate risk
                    risk_factors.append(8.0)
        
        # Income-related risk factors
        if 'income_verification_agent' in context:
            income_results = context['income_verification_agent']
            if 'income_consistency_checker' in income_results:
                consistency_data = income_results['income_consistency_checker'].get('data', {})
                
                if consistency_data.get('major_discrepancies', []):
                    risk_factors.append(12.0)
                elif consistency_data.get('minor_discrepancies', []):
                    risk_factors.append(6.0)
        
        # Property-related risk factors
        if 'property_assessment_agent' in context:
            property_results = context['property_assessment_agent']
            if 'property_risk_analyzer' in property_results:
                property_data = property_results['property_risk_analyzer'].get('data', {})
                property_risk = property_data.get('overall_risk_score', 0)
                
                if property_risk > 70:
                    risk_factors.append(10.0)
                elif property_risk > 50:
                    risk_factors.append(5.0)
    
    def _calculate_confidence_level(self, tool_results: Dict[str, ToolResult]) -> float:
        """
        Calculate overall confidence level in risk assessment results.
        
        Args:
            tool_results: Results from all risk assessment tools
            
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
                                application: MortgageApplication,
                                context: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on risk assessment results.
        
        Args:
            tool_results: Results from all risk assessment tools
            application: The mortgage application
            context: Additional context from other agents
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # KYC recommendations
        kyc_result = tool_results.get("kyc_risk_scorer")
        if kyc_result and kyc_result.success:
            kyc_data = kyc_result.data
            
            if not kyc_data.get('identity_verified', False):
                recommendations.append("Require additional identity verification documentation")
            
            if not kyc_data.get('address_verified', False):
                recommendations.append("Obtain additional address proof documentation")
            
            if kyc_data.get('document_authenticity_score', 1.0) < 0.8:
                recommendations.append("Conduct enhanced document authenticity verification")
            
            fraud_indicators = kyc_data.get('fraud_indicators', [])
            if fraud_indicators:
                recommendations.append("Investigate potential fraud indicators before proceeding")
            
            inconsistencies = kyc_data.get('data_inconsistencies', [])
            if inconsistencies:
                recommendations.append("Resolve data inconsistencies with borrower")
        
        # PEP/sanctions recommendations
        pep_result = tool_results.get("pep_sanctions_checker")
        if pep_result and pep_result.success:
            pep_data = pep_result.data
            
            if pep_data.get('is_pep', False):
                recommendations.append("Implement enhanced due diligence procedures for PEP status")
            
            sanctions_matches = pep_data.get('sanctions_matches', [])
            if sanctions_matches:
                recommendations.append("CRITICAL: Sanctions match detected - escalate immediately")
            
            family_matches = pep_data.get('family_associate_matches', [])
            if family_matches:
                recommendations.append("Review family/associate connections and assess risk")
            
            watchlist_matches = pep_data.get('watchlist_matches', [])
            if watchlist_matches:
                recommendations.append("Investigate watchlist matches and document findings")
        
        # Risk level-based recommendations
        _, risk_level = self._calculate_consolidated_risk_score(tool_results, application, context)
        
        if risk_level == RiskLevel.HIGH:
            recommendations.append("Consider declining application due to high risk profile")
            recommendations.append("If proceeding, implement maximum risk mitigation measures")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Implement enhanced monitoring and risk mitigation measures")
            recommendations.append("Consider additional collateral or guarantees")
        
        return recommendations
    
    def _generate_conditions(self, tool_results: Dict[str, ToolResult], 
                           application: MortgageApplication) -> List[str]:
        """
        Generate loan conditions based on risk assessment results.
        
        Args:
            tool_results: Results from all risk assessment tools
            application: The mortgage application
            
        Returns:
            List of condition strings
        """
        conditions = []
        
        # KYC conditions
        kyc_result = tool_results.get("kyc_risk_scorer")
        if kyc_result and kyc_result.success:
            kyc_data = kyc_result.data
            
            if kyc_data.get('identity_confidence', 1.0) < 0.9:
                conditions.append("Provide additional identity verification documents")
            
            if kyc_data.get('address_confidence', 1.0) < 0.9:
                conditions.append("Provide additional address verification documents")
            
            if kyc_data.get('requires_enhanced_verification', False):
                conditions.append("Complete enhanced customer verification process")
        
        # PEP/sanctions conditions
        pep_result = tool_results.get("pep_sanctions_checker")
        if pep_result and pep_result.success:
            pep_data = pep_result.data
            
            if pep_data.get('is_pep', False):
                conditions.append("Complete enhanced due diligence documentation")
                conditions.append("Provide source of funds documentation")
            
            if pep_data.get('requires_ongoing_monitoring', False):
                conditions.append("Subject to ongoing enhanced monitoring")
        
        return conditions
    
    def _identify_red_flags(self, tool_results: Dict[str, ToolResult]) -> List[str]:
        """
        Identify red flags from risk assessment results.
        
        Args:
            tool_results: Results from all risk assessment tools
            
        Returns:
            List of red flag descriptions
        """
        red_flags = []
        
        # KYC red flags
        kyc_result = tool_results.get("kyc_risk_scorer")
        if kyc_result and kyc_result.success:
            kyc_data = kyc_result.data
            
            fraud_indicators = kyc_data.get('fraud_indicators', [])
            if fraud_indicators:
                red_flags.extend([f"Fraud indicator: {indicator}" for indicator in fraud_indicators])
            
            if kyc_data.get('document_authenticity_score', 1.0) < 0.5:
                red_flags.append("Questionable document authenticity")
            
            if kyc_data.get('identity_theft_risk', False):
                red_flags.append("Potential identity theft indicators detected")
            
            synthetic_identity_risk = kyc_data.get('synthetic_identity_risk_score', 0)
            if synthetic_identity_risk > 0.7:
                red_flags.append("High synthetic identity risk detected")
        
        # PEP/sanctions red flags
        pep_result = tool_results.get("pep_sanctions_checker")
        if pep_result and pep_result.success:
            pep_data = pep_result.data
            
            sanctions_matches = pep_data.get('sanctions_matches', [])
            if sanctions_matches:
                red_flags.extend([f"SANCTIONS MATCH: {match['list_name']}" for match in sanctions_matches])
            
            if pep_data.get('is_pep', False) and pep_data.get('pep_risk_level') == 'high':
                red_flags.append("High-risk PEP status detected")
            
            criminal_matches = pep_data.get('criminal_matches', [])
            if criminal_matches:
                red_flags.extend([f"Criminal record match: {match}" for match in criminal_matches])
            
            if pep_data.get('terrorism_financing_risk', False):
                red_flags.append("Terrorism financing risk indicators detected")
        
        return red_flags