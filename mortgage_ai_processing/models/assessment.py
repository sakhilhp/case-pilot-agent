"""
Assessment and decision models for the mortgage processing system.

Contains data structures for storing assessment results, loan decisions,
and related analysis outputs from various agents and tools.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from .enums import DecisionType, RiskLevel


class LoanTerms(BaseModel):
    """Terms and conditions for an approved loan."""
    loan_amount: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., ge=0, le=100)
    loan_term_years: int = Field(..., gt=0, le=50)
    monthly_payment: Decimal = Field(..., gt=0)
    down_payment_required: Decimal = Field(..., ge=0)
    closing_costs: Optional[Decimal] = Field(None, ge=0)
    points: Optional[Decimal] = Field(None, ge=0)
    apr: Optional[Decimal] = Field(None, ge=0, le=100)
    pmi_required: bool = Field(default=False)
    pmi_monthly_amount: Optional[Decimal] = Field(None, ge=0)
    escrow_required: bool = Field(default=True)
    prepayment_penalty: bool = Field(default=False)
    
    @field_validator('interest_rate')
    @classmethod
    def validate_interest_rate(cls, v):
        """Ensure interest rate is reasonable."""
        if v < 0 or v > 50:  # Reasonable bounds for mortgage rates
            raise ValueError('Interest rate must be between 0% and 50%')
        return v


class AssessmentResult(BaseModel):
    """Result from an agent's assessment of a mortgage application."""
    agent_name: str = Field(..., min_length=1, max_length=100)
    assessment_type: str = Field(..., min_length=1, max_length=100)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    confidence_level: float = Field(..., ge=0, le=1)
    recommendations: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    processing_time_seconds: float = Field(..., ge=0)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('risk_score')
    @classmethod
    def validate_risk_score(cls, v):
        """Ensure risk score is within valid range."""
        if not 0 <= v <= 100:
            raise ValueError('Risk score must be between 0 and 100')
        return v
    
    @field_validator('confidence_level')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence level is within valid range."""
        if not 0 <= v <= 1:
            raise ValueError('Confidence level must be between 0 and 1')
        return v


class DecisionFactors(BaseModel):
    """Factors that contributed to the loan decision."""
    eligibility_score: float = Field(..., ge=0, le=100)
    risk_score: float = Field(..., ge=0, le=100)
    compliance_score: float = Field(..., ge=0, le=100)
    policy_score: float = Field(..., ge=0, le=100)
    
    # Weighted scores (as per requirements: eligibility 35%, risk 30%, compliance 20%, policy 15%)
    eligibility_weight: float = Field(default=0.35, ge=0, le=1)
    risk_weight: float = Field(default=0.30, ge=0, le=1)
    compliance_weight: float = Field(default=0.20, ge=0, le=1)
    policy_weight: float = Field(default=0.15, ge=0, le=1)
    
    @field_validator('eligibility_weight', 'risk_weight', 'compliance_weight', 'policy_weight')
    @classmethod
    def validate_weights(cls, v):
        """Ensure all weights are reasonable."""
        if not 0 <= v <= 1:
            raise ValueError('Weight must be between 0 and 1')
        return v
    
    def calculate_overall_score(self) -> float:
        """Calculate the overall weighted decision score."""
        return (
            self.eligibility_score * self.eligibility_weight +
            self.risk_score * self.risk_weight +
            self.compliance_score * self.compliance_weight +
            self.policy_score * self.policy_weight
        )


class AdverseAction(BaseModel):
    """Adverse action notice information."""
    reason_code: str = Field(..., min_length=1, max_length=10)
    reason_description: str = Field(..., min_length=1, max_length=500)
    category: str = Field(..., min_length=1, max_length=100)  # credit, income, property, etc.
    impact_level: RiskLevel = Field(default=RiskLevel.MEDIUM)


class LoanDecision(BaseModel):
    """Final decision on a mortgage loan application."""
    application_id: str = Field(..., min_length=1, max_length=100)
    decision: DecisionType
    decision_factors: DecisionFactors
    overall_score: float = Field(..., ge=0, le=100)
    conditions: List[str] = Field(default_factory=list)
    adverse_actions: List[AdverseAction] = Field(default_factory=list)
    loan_terms: Optional[LoanTerms] = None
    generated_letters: Dict[str, str] = Field(default_factory=dict)
    decision_rationale: str = Field(..., min_length=1, max_length=2000)
    underwriter_notes: List[str] = Field(default_factory=list)
    requires_manual_review: bool = Field(default=False)
    expiration_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., min_length=1, max_length=100)  # agent or user ID
    
    @field_validator('overall_score')
    @classmethod
    def validate_overall_score(cls, v):
        """Ensure overall score is within valid range."""
        if not 0 <= v <= 100:
            raise ValueError('Overall score must be between 0 and 100')
        return v
    
    @model_validator(mode='after')
    def validate_decision_consistency(self):
        """Validate decision consistency with loan terms and adverse actions."""
        if self.decision == DecisionType.APPROVE.value and self.loan_terms is None:
            raise ValueError('Loan terms must be provided for approved loans')
        if self.decision == DecisionType.DENY.value and self.loan_terms is not None:
            raise ValueError('Loan terms should not be provided for denied loans')
        if self.decision == DecisionType.DENY.value and not self.adverse_actions:
            raise ValueError('Adverse actions must be provided for denied loans')
        return self
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )