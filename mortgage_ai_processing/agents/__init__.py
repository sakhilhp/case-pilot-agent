"""
Agent module for mortgage processing system.

Contains all agent implementations including:
- Document Processing Agent
- Income Verification Agent  
- Credit Assessment Agent
- Property Assessment Agent
- Risk Assessment Agent
- Underwriting Agent
"""

from .base import BaseAgent, AgentManager

# Agent implementations will be imported when they are completed
# from .document_processing import DocumentProcessingAgent
# from .income_verification import IncomeVerificationAgent
# from .credit_assessment import CreditAssessmentAgent
# from .property_assessment import PropertyAssessmentAgent
# from .risk_assessment import RiskAssessmentAgent
# from .underwriting import UnderwritingAgent

__all__ = [
    "BaseAgent",
    "AgentManager"
    # "DocumentProcessingAgent",
    # "IncomeVerificationAgent", 
    # "CreditAssessmentAgent",
    # "PropertyAssessmentAgent",
    # "RiskAssessmentAgent",
    # "UnderwritingAgent"
]