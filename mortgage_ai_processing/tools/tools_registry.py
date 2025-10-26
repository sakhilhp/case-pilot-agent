"""
Enhanced Tools Registry - Manages registration of all enhanced FSI tools.

This module handles the registration of enhanced tools converted from TypeScript
to avoid circular import issues and provide centralized tool management.
"""

import logging
from typing import Dict, List, Any, Optional

from .base import BaseTool, ToolManager
# from .income.income_calculator_simple import SimpleIncomeCalculatorTool  # File not found


class EnhancedToolsRegistry:
    """Registry for all enhanced FSI tools."""
    
    def __init__(self):
        self.logger = logging.getLogger("enhanced_tools_registry")
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False
        
    def initialize_tools(self) -> None:
        """Initialize all enhanced tools."""
        if self._initialized:
            return
            
        self.logger.info("Initializing enhanced FSI tools")
        
        try:
            # Income verification tools
            self._register_income_tools()
            
            # Credit assessment tools  
            self._register_credit_tools()
            
            # Property assessment tools
            self._register_property_tools()
            
            # Risk assessment tools
            self._register_risk_tools()
            
            # Underwriting tools
            self._register_underwriting_tools()
            
            # Document processing tools (enhanced versions)
            self._register_document_tools()
            
            self._initialized = True
            self.logger.info(f"Successfully initialized {len(self._tools)} enhanced tools")
            
        except Exception as e:
            self.logger.error(f"Error initializing enhanced tools: {e}")
            raise
    
    def _register_income_tools(self) -> None:
        """Register income verification tools."""
        try:
            # Simple income calculator (working) - commented out due to missing file
            # simple_calc = SimpleIncomeCalculatorTool()
            # self._tools[simple_calc.name] = simple_calc
            
            # Enhanced income calculator
            try:
                from .income.income_calculator_enhanced import EnhancedIncomeCalculatorTool
                enhanced_calc = EnhancedIncomeCalculatorTool()
                self._tools[enhanced_calc.name] = enhanced_calc
            except ImportError as e:
                self.logger.warning(f"Could not import enhanced income calculator: {e}")
            
            # Enhanced employment verification tool
            try:
                from .income.employment_verification_enhanced import EmploymentVerificationTool
                emp_verification = EmploymentVerificationTool()
                self._tools[emp_verification.name] = emp_verification
            except ImportError as e:
                self.logger.warning(f"Could not import employment verification tool: {e}")
            
            self.logger.info("Registered income verification tools")
            
        except Exception as e:
            self.logger.error(f"Error registering income tools: {e}")
    
    def _register_credit_tools(self) -> None:
        """Register credit assessment tools."""
        try:
            # Enhanced credit score analyzer
            try:
                from .credit.credit_score_analyzer_enhanced import EnhancedCreditScoreAnalyzerTool
                credit_analyzer = EnhancedCreditScoreAnalyzerTool()
                self._tools[credit_analyzer.name] = credit_analyzer
            except ImportError as e:
                self.logger.warning(f"Could not import credit score analyzer: {e}")
            
            self.logger.info("Registered credit assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering credit tools: {e}")
    
    def _register_property_tools(self) -> None:
        """Register property assessment tools."""
        try:
            # Enhanced property value estimator
            try:
                from .property.property_value_estimator_enhanced import PropertyValueEstimatorTool
                prop_estimator = PropertyValueEstimatorTool()
                self._tools[prop_estimator.name] = prop_estimator
            except ImportError as e:
                self.logger.warning(f"Could not import property value estimator: {e}")
            
            self.logger.info("Registered property assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering property tools: {e}")
    
    def _register_risk_tools(self) -> None:
        """Register risk assessment tools."""
        try:
            # Enhanced fraud detection analyzer
            try:
                from .risk.fraud_detection_analyzer_enhanced import FraudDetectionAnalyzerTool
                fraud_analyzer = FraudDetectionAnalyzerTool()
                self._tools[fraud_analyzer.name] = fraud_analyzer
            except ImportError as e:
                self.logger.warning(f"Could not import fraud detection analyzer: {e}")
            
            self.logger.info("Registered risk assessment tools")
            
        except Exception as e:
            self.logger.error(f"Error registering risk tools: {e}")
    
    def _register_underwriting_tools(self) -> None:
        """Register underwriting tools."""
        try:
            # Enhanced loan decision engine
            try:
                from .underwriting.loan_decision_engine_enhanced import EnhancedLoanDecisionEngine
                loan_engine = EnhancedLoanDecisionEngine()
                self._tools[loan_engine.name] = loan_engine
            except ImportError as e:
                self.logger.warning(f"Could not import loan decision engine: {e}")
            
            # Enhanced loan terms calculator
            try:
                from .underwriting.loan_terms_calculator_enhanced import LoanTermsCalculatorTool
                loan_calc = LoanTermsCalculatorTool()
                self._tools[loan_calc.name] = loan_calc
            except ImportError as e:
                self.logger.warning(f"Could not import loan terms calculator: {e}")
            
            self.logger.info("Registered underwriting tools")
            
        except Exception as e:
            self.logger.error(f"Error registering underwriting tools: {e}")
    
    def _register_document_tools(self) -> None:
        """Register enhanced document processing tools."""
        try:
            # TODO: Add enhanced document tools
            self.logger.info("Document tools registration placeholder")
            
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
            tool_manager.register_tool(tool_name, tool)
            
        self.logger.info(f"Registered {len(self._tools)} enhanced tools with tool manager")
    
    def register_tools_with_agents(self, agent_manager) -> None:
        """Register tools with appropriate agents."""
        if not self._initialized:
            self.initialize_tools()
            
        # Get agents
        agents = agent_manager.get_all_agents()
        
        for agent in agents:
            # Register tools based on agent domain
            if "income" in agent.name.lower():
                for tool_name, tool in self._tools.items():
                    if tool.agent_domain == "income_verification":
                        agent.register_tool(tool_name, tool)
                        
            elif "credit" in agent.name.lower():
                for tool_name, tool in self._tools.items():
                    if tool.agent_domain == "credit_assessment":
                        agent.register_tool(tool_name, tool)
                        
            elif "underwriting" in agent.name.lower():
                for tool_name, tool in self._tools.items():
                    if tool.agent_domain == "underwriting":
                        agent.register_tool(tool_name, tool)
        
        self.logger.info("Registered enhanced tools with agents")


# Global registry instance
_registry_instance: Optional[EnhancedToolsRegistry] = None


def get_enhanced_tools_registry() -> EnhancedToolsRegistry:
    """Get or create the global enhanced tools registry."""
    global _registry_instance
    
    if _registry_instance is None:
        _registry_instance = EnhancedToolsRegistry()
        
    return _registry_instance