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
            # Use simple working tools that implement the interface correctly
            from .simple_working_tools import (
                CreditScoreAnalyzerTool,
                CreditHistoryAnalyzerTool,
                DebtToIncomeCalculatorTool
            )
            
            self._tools["credit_score_analyzer"] = CreditScoreAnalyzerTool()
            self._tools["credit_history_analyzer"] = CreditHistoryAnalyzerTool()
            self._tools["debt_to_income_calculator"] = DebtToIncomeCalculatorTool()
            
            self.logger.info("Registered credit assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering credit tools: {e}")
    
    def _register_income_tools(self) -> None:
        """Register income verification tools with agent-expected names."""
        try:
            # Use simple working tools that implement the interface correctly
            from .simple_working_tools import (
                EmploymentVerificationTool,
                SimpleIncomeCalculatorTool,
                IncomeConsistencyCheckerTool
            )
            
            self._tools["employment_verification_tool"] = EmploymentVerificationTool()
            self._tools["simple_income_calculator"] = SimpleIncomeCalculatorTool()
            self._tools["income_consistency_checker"] = IncomeConsistencyCheckerTool()
            
            self.logger.info("Registered income verification tools")
            
        except Exception as e:
            self.logger.error(f"Error registering income tools: {e}")
    
    def _register_property_tools(self) -> None:
        """Register property assessment tools with agent-expected names."""
        try:
            # Use simple working tools that implement the interface correctly
            from .simple_working_tools import (
                PropertyValuationTool,
                LTVCalculatorTool,
                PropertyRiskAnalyzerTool
            )
            
            self._tools["property_valuation_tool"] = PropertyValuationTool()
            self._tools["ltv_calculator"] = LTVCalculatorTool()
            self._tools["property_risk_analyzer"] = PropertyRiskAnalyzerTool()
            
            self.logger.info("Registered property assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering property tools: {e}")
    
    def _register_risk_tools(self) -> None:
        """Register risk assessment tools with agent-expected names."""
        try:
            # Use simple working tools that implement the interface correctly
            from .simple_working_tools import (
                KYCRiskScorerTool,
                PEPSanctionsCheckerTool
            )
            
            self._tools["kyc_risk_scorer"] = KYCRiskScorerTool()
            self._tools["pep_sanctions_checker"] = PEPSanctionsCheckerTool()
            
            self.logger.info("Registered risk assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering risk tools: {e}")
    
    def _register_underwriting_tools(self) -> None:
        """Register underwriting tools with agent-expected names."""
        try:
            # Use simple working tools that implement the interface correctly
            from .simple_working_tools import (
                LoanDecisionEngineTool,
                LoanLetterGeneratorTool
            )
            
            self._tools["loan_decision_engine"] = LoanDecisionEngineTool()
            self._tools["loan_letter_generator"] = LoanLetterGeneratorTool()
            
            self.logger.info("Registered underwriting tools")
            
        except Exception as e:
            self.logger.error(f"Error registering underwriting tools: {e}")
    
    def _register_document_tools(self) -> None:
        """Register document processing tools with agent-expected names."""
        try:
            # Use the actual OCR extractor we fixed
            from .document.ocr_extractor import DocumentOCRExtractor
            
            # Use simple working tools for the others
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
            
            self.logger.info("Registered document processing tools")
            
        except Exception as e:
            self.logger.error(f"Error registering document tools: {e}")
    
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