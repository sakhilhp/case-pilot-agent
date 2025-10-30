"""
Fixed Tools Registry - Properly maps agent expected tool names to actual tool instances.

This module handles the registration of tools with the correct names that agents expect.
"""

import logging
from typing import Dict, List, Any, Optional

from .base import BaseTool, ToolManager


class FixedToolsRegistry:
    """Registry that properly maps agent expected tool names to actual tool instances."""
    
    def __init__(self):
        self.logger = logging.getLogger("fixed_tools_registry")
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False
        
    def initialize_tools(self) -> None:
        """Initialize all tools with the correct names that agents expect."""
        if self._initialized:
            return
            
        self.logger.info("Initializing tools with correct agent-expected names")
        
        try:
            # Credit assessment tools
            self._register_credit_tools()
            
            # Income verification tools  
            self._register_income_tools()
            
            # Property assessment tools
            self._register_property_tools()
            
            # Risk assessment tools
            self._register_risk_tools()
            
            # Underwriting tools
            self._register_underwriting_tools()
            
            # Document processing tools
            self._register_document_tools()
            
            self._initialized = True
            self.logger.info(f"Successfully initialized {len(self._tools)} tools with correct names")
            
        except Exception as e:
            self.logger.error(f"Error initializing tools: {e}")
            raise
    
    def _register_credit_tools(self) -> None:
        """Register credit assessment tools with agent-expected names."""
        try:
            # Use real implementations instead of mock tools
            from .credit.credit_score_analyzer import EnhancedCreditScoreAnalyzerTool
            from .credit.history_analyzer import CreditHistoryAnalyzerTool
            from .credit.dti_calculator import DebtToIncomeCalculatorTool
            
            self._tools["credit_score_analyzer"] = EnhancedCreditScoreAnalyzerTool()
            self._tools["credit_history_analyzer"] = CreditHistoryAnalyzerTool()
            self._tools["debt_to_income_calculator"] = DebtToIncomeCalculatorTool()
            
            self.logger.info("Registered real credit assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering credit tools: {e}")
            # Emergency fallback only if real implementations fail
            self.logger.warning("Falling back to simple credit tools")
            from .simple_working_tools import (
                CreditScoreAnalyzerTool,
                CreditHistoryAnalyzerTool,
                DebtToIncomeCalculatorTool
            )
            self._tools["credit_score_analyzer"] = CreditScoreAnalyzerTool()
            self._tools["credit_history_analyzer"] = CreditHistoryAnalyzerTool()
            self._tools["debt_to_income_calculator"] = DebtToIncomeCalculatorTool()
    
    def _register_income_tools(self) -> None:
        """Register income verification tools with agent-expected names."""
        try:
            # Use real implementations instead of mock tools
            from .income.employment_verification import EmploymentVerificationTool
            from .income.income_calculator import EnhancedIncomeCalculatorTool
            from .income.consistency_checker import IncomeConsistencyCheckerTool
            
            self._tools["employment_verification_tool"] = EmploymentVerificationTool()
            self._tools["simple_income_calculator"] = EnhancedIncomeCalculatorTool()
            self._tools["income_consistency_checker"] = IncomeConsistencyCheckerTool()
            
            self.logger.info("Registered real income verification tools")
            
        except Exception as e:
            self.logger.error(f"Error registering income tools: {e}")
            # Emergency fallback only if real implementations fail
            self.logger.warning("Falling back to simple income tools")
            from .simple_working_tools import (
                EmploymentVerificationTool,
                SimpleIncomeCalculatorTool,
                IncomeConsistencyCheckerTool
            )
            self._tools["employment_verification_tool"] = EmploymentVerificationTool()
            self._tools["simple_income_calculator"] = SimpleIncomeCalculatorTool()
            self._tools["income_consistency_checker"] = IncomeConsistencyCheckerTool()
    
    def _register_property_tools(self) -> None:
        """Register property assessment tools with agent-expected names."""
        try:
            # Use real implementations instead of mock tools
            from .property.property_value_estimator import PropertyValueEstimatorTool
            from .property.ltv_calculator import LTVCalculatorTool
            from .property.risk_analyzer import PropertyRiskAnalyzerTool
            
            self._tools["property_valuation_tool"] = PropertyValueEstimatorTool()
            self._tools["ltv_calculator"] = LTVCalculatorTool()
            self._tools["property_risk_analyzer"] = PropertyRiskAnalyzerTool()
            
            self.logger.info("Registered real property assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering property tools: {e}")
            # Emergency fallback only if real implementations fail
            self.logger.warning("Falling back to simple property tools")
            from .simple_working_tools import (
                PropertyValuationTool,
                LTVCalculatorTool,
                PropertyRiskAnalyzerTool
            )
            self._tools["property_valuation_tool"] = PropertyValuationTool()
            self._tools["ltv_calculator"] = LTVCalculatorTool()
            self._tools["property_risk_analyzer"] = PropertyRiskAnalyzerTool()
    
    def _register_risk_tools(self) -> None:
        """Register risk assessment tools with agent-expected names."""
        try:
            # Use real implementations instead of mock tools
            from .risk.kyc_risk_scorer import KYCRiskScorerTool
            from .risk.pep_sanctions_checker import PEPSanctionsCheckerTool
            
            self._tools["kyc_risk_scorer"] = KYCRiskScorerTool()
            self._tools["pep_sanctions_checker"] = PEPSanctionsCheckerTool()
            
            self.logger.info("Registered real risk assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering risk tools: {e}")
            # Emergency fallback only if real implementations fail
            self.logger.warning("Falling back to simple risk tools")
            from .simple_working_tools import (
                KYCRiskScorerTool,
                PEPSanctionsCheckerTool
            )
            self._tools["kyc_risk_scorer"] = KYCRiskScorerTool()
            self._tools["pep_sanctions_checker"] = PEPSanctionsCheckerTool()
    
    def _register_underwriting_tools(self) -> None:
        """Register underwriting tools with agent-expected names."""
        try:
            # Use real implementations instead of mock tools
            from .underwriting.loan_decision_engine import EnhancedLoanDecisionEngine
            from .underwriting.loan_letter_generator import LoanLetterGeneratorTool
            
            self._tools["loan_decision_engine"] = EnhancedLoanDecisionEngine()
            self._tools["loan_letter_generator"] = LoanLetterGeneratorTool()
            
            self.logger.info("Registered real underwriting tools")
            
        except Exception as e:
            self.logger.error(f"Error registering underwriting tools: {e}")
            # Emergency fallback only if real implementations fail
            self.logger.warning("Falling back to simple underwriting tools")
            from .simple_working_tools import (
                LoanDecisionEngineTool,
                LoanLetterGeneratorTool
            )
            self._tools["loan_decision_engine"] = LoanDecisionEngineTool()
            self._tools["loan_letter_generator"] = LoanLetterGeneratorTool()
    
    def _register_document_tools(self) -> None:
        """Register document processing tools with agent-expected names."""
        try:
            self.logger.info("🔄 Starting document tools registration...")
            
            # Import OCR extractor first
            from .document.ocr_extractor import DocumentOCRExtractor
            self.logger.info("✅ Successfully imported DocumentOCRExtractor")
            
            # Try to import and instantiate DocumentClassifier with detailed error handling
            DocumentClassifier = None
            try:
                self.logger.info("🔄 Attempting to import DocumentClassifier...")
                from .document.classifier import DocumentClassifier as RealDocumentClassifier
                self.logger.info("✅ Successfully imported DocumentClassifier class")
                
                self.logger.info("🔄 Attempting to instantiate DocumentClassifier...")
                test_classifier = RealDocumentClassifier()
                self.logger.info("✅ Successfully instantiated DocumentClassifier")
                DocumentClassifier = RealDocumentClassifier
                
            except Exception as e:
                self.logger.error(f"❌ Failed to import/instantiate DocumentClassifier: {e}")
                import traceback
                self.logger.error(f"Full traceback: {traceback.format_exc()}")
                
                # Fallback to simple version
                self.logger.info("⚠️ Falling back to simple DocumentClassifierTool")
                from .simple_working_tools import DocumentClassifierTool as DocumentClassifier
            
            # Try AddressProofValidator
            AddressProofValidator = None
            try:
                from .document.address_proof_validator import AddressProofValidator as RealAddressValidator
                self.logger.info("✅ Successfully imported AddressProofValidator")
                AddressProofValidator = RealAddressValidator
            except Exception as e:
                self.logger.error(f"❌ Failed to import AddressProofValidator: {e}")
                from .simple_working_tools import AddressProofValidatorTool as AddressProofValidator
                self.logger.info("⚠️ Using fallback AddressProofValidatorTool")
            
            # Import simple tools
            from .simple_working_tools import (
                IdentityDocumentValidatorTool,
                DocumentExtractorTool
            )
            
            # Register all tools
            self.logger.info("🔄 Registering tools in registry...")
            
            self._tools["document_ocr_extractor"] = DocumentOCRExtractor()
            self.logger.info("✅ Registered document_ocr_extractor")
            
            self._tools["document_classifier"] = DocumentClassifier()
            self.logger.info("✅ Registered document_classifier")
            
            self._tools["identity_document_validator"] = IdentityDocumentValidatorTool()
            self.logger.info("✅ Registered identity_document_validator")
            
            self._tools["document_extractor"] = DocumentExtractorTool()
            self.logger.info("✅ Registered document_extractor")
            
            self._tools["address_proof_validator"] = AddressProofValidator()
            self.logger.info("✅ Registered address_proof_validator")
            
            self.logger.info(f"✅ Successfully registered {len(self._tools)} document processing tools")
            
        except Exception as e:
            self.logger.error(f"❌ Critical error registering document tools: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Emergency fallback - register at least the working tools
            try:
                from .document.ocr_extractor import DocumentOCRExtractor
                from .simple_working_tools import (
                    DocumentClassifierTool,
                    IdentityDocumentValidatorTool,
                    DocumentExtractorTool,
                    AddressProofValidatorTool
                )
                
                self._tools["document_ocr_extractor"] = DocumentOCRExtractor()
                self._tools["document_classifier"] = DocumentClassifierTool()
                self._tools["identity_document_validator"] = IdentityDocumentValidatorTool()
                self._tools["document_extractor"] = DocumentExtractorTool()
                self._tools["address_proof_validator"] = AddressProofValidatorTool()
                
                self.logger.info("⚠️ Emergency fallback: registered simple document tools")
                
            except Exception as fallback_error:
                self.logger.error(f"❌ Even fallback registration failed: {fallback_error}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        if not self._initialized:
            self.initialize_tools()
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        if not self._initialized:
            self.initialize_tools()
        return self._tools.copy()
    
    def register_tools_with_manager(self, tool_manager: ToolManager) -> None:
        """Register all tools with a tool manager."""
        if not self._initialized:
            self.initialize_tools()
            
        for tool_name, tool in self._tools.items():
            tool_manager.register_tool(tool)
            
        self.logger.info(f"Registered {len(self._tools)} tools with tool manager")
    
    def register_tools_with_agents(self, agent_manager) -> None:
        """Register tools with appropriate agents based on their expected tool names."""
        if not self._initialized:
            self.initialize_tools()
            
        # Get all agents
        agents = agent_manager.get_all_agents()
        
        for agent in agents:
            # Get the tool names this agent expects
            expected_tool_names = agent.get_tool_names()
            
            # Register each expected tool with the agent
            for tool_name in expected_tool_names:
                tool = self._tools.get(tool_name)
                if tool:
                    agent.register_tool(tool_name, tool)
                    self.logger.info(f"Registered tool '{tool_name}' with agent '{agent.name}'")
                else:
                    self.logger.warning(f"Tool '{tool_name}' not found for agent '{agent.name}'")
        
        self.logger.info("Completed tool registration with agents")


# Global registry instance
_fixed_registry_instance: Optional[FixedToolsRegistry] = None


def get_fixed_tools_registry() -> FixedToolsRegistry:
    """Get or create the global fixed tools registry."""
    global _fixed_registry_instance
    
    if _fixed_registry_instance is None:
        _fixed_registry_instance = FixedToolsRegistry()
        
    return _fixed_registry_instance