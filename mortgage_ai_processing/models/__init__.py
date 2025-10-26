"""
Data models module for mortgage processing system.

Contains all data structures and enumerations used throughout the system:
- Core data models (MortgageApplication, Document, etc.)
- Assessment results and decision models
- Enumerations for types and statuses
- Validation schemas
"""

from .core import (
    MortgageApplication,
    BorrowerInfo,
    PropertyInfo,
    LoanDetails,
    Document,
    DocumentRelationship,
    ProcessingMetadata,
    ClassificationScore
)
from .assessment import (
    AssessmentResult, 
    LoanDecision, 
    LoanTerms,
    DecisionFactors,
    AdverseAction
)
from .enums import (
    DocumentType, 
    ProcessingStatus, 
    DecisionType,
    ValidationStatus,
    RiskLevel,
    LoanType
)
from .validation import (
    validate_mortgage_application, 
    validate_document,
    validate_loan_decision,
    calculate_ltv_ratio,
    calculate_dti_ratio
)

__all__ = [
    # Core models
    "MortgageApplication",
    "BorrowerInfo", 
    "PropertyInfo",
    "LoanDetails",
    "Document",
    "DocumentRelationship",
    "ProcessingMetadata",
    "ClassificationScore",
    
    # Assessment models
    "AssessmentResult",
    "LoanDecision",
    "LoanTerms",
    "DecisionFactors",
    "AdverseAction",
    
    # Enumerations
    "DocumentType",
    "ProcessingStatus", 
    "DecisionType",
    "ValidationStatus",
    "RiskLevel",
    "LoanType",
    
    # Validation functions
    "validate_mortgage_application",
    "validate_document",
    "validate_loan_decision",
    "calculate_ltv_ratio",
    "calculate_dti_ratio"
]