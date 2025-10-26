"""
Enhanced Loan Decision Engine - Comprehensive mortgage underwriting decisions.

Converted from TypeScript FSI Tools framework to Python.
Makes final loan approval decisions based on aggregated data from all agents.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass

from ..base import BaseTool, ToolResult, ToolCategory


class LoanDecision(Enum):
    """Loan decision types."""
    APPROVED = "approve"
    CONDITIONAL_APPROVAL = "conditional"
    DENIED = "deny"


class RiskGrade(Enum):
    """Risk grade categories."""
    A = "A"  # Excellent
    B = "B"  # Good
    C = "C"  # Fair
    D = "D"  # Poor
    F = "F"  # Fail


class PricingTier(Enum):
    """Pricing tier categories."""
    PRIME = "PRIME"
    NEAR_PRIME = "NEAR_PRIME"
    SUBPRIME = "SUBPRIME"
    INELIGIBLE = "INELIGIBLE"


@dataclass
class LoanApplicationData:
    """Complete loan application data structure."""
    documents: Dict[str, Any]
    income: Dict[str, Any]
    credit: Dict[str, Any]
    property: Dict[str, Any]
    risk: Dict[str, Any]
    loan: Dict[str, Any]


class EnhancedLoanDecisionEngine(BaseTool):
    """
    Enhanced Loan Decision Engine for comprehensive mortgage underwriting.
    
    Features:
    - Multi-factor risk assessment and scoring
    - Loan program specific decision logic
    - Regulatory compliance checking
    - Conditional approval with specific conditions
    - Comprehensive decision rationale and documentation
    - Risk-based pricing recommendations
    """
    
    def __init__(self):
        super().__init__(
            name="enhanced_loan_decision_engine",
            description="Comprehensive loan decision engine that makes final approve/deny/conditional decisions based on aggregated mortgage processing data",
            category=ToolCategory.UNDERWRITING,
            version="1.0.0",
            agent_domain="underwriting"
        )
        
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for loan decision parameters."""
        return {
            "type": "object",
            "required": ["application_id", "application_data"],
            "properties": {
                "application_id": {
                    "type": "string",
                    "description": "Unique application identifier"
                },
                "application_data": {
                    "type": "object",
                    "description": "Complete loan application data from all agents",
                    "required": ["documents", "income", "credit", "property", "risk", "loan"],
                    "properties": {
                        "documents": {
                            "type": "object",
                            "properties": {
                                "identity_verified": {"type": "boolean"},
                                "income_documents_complete": {"type": "boolean"},
                                "property_documents_complete": {"type": "boolean"},
                                "document_authenticity_score": {"type": "number", "minimum": 0, "maximum": 100}
                            }
                        },
                        "income": {
                            "type": "object",
                            "properties": {
                                "monthly_gross_income": {"type": "number"},
                                "verified_employment": {"type": "boolean"},
                                "income_stability_score": {"type": "number", "minimum": 0, "maximum": 100},
                                "debt_to_income_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                                "qualified_income": {"type": "number"}
                            }
                        },
                        "credit": {
                            "type": "object",
                            "properties": {
                                "credit_score": {"type": "number", "minimum": 300, "maximum": 850},
                                "credit_history_months": {"type": "number"},
                                "payment_history_score": {"type": "number", "minimum": 0, "maximum": 100},
                                "credit_utilization": {"type": "number", "minimum": 0, "maximum": 1},
                                "public_records": {"type": "array", "items": {"type": "string"}},
                                "credit_risk_grade": {"type": "string"}
                            }
                        },
                        "property": {
                            "type": "object",
                            "properties": {
                                "appraised_value": {"type": "number"},
                                "loan_to_value_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                                "property_type": {"type": "string"},
                                "property_risk_score": {"type": "number", "minimum": 0, "maximum": 100},
                                "market_trend_indicator": {"type": "string"}
                            }
                        },
                        "risk": {
                            "type": "object",
                            "properties": {
                                "overall_risk_score": {"type": "number", "minimum": 0, "maximum": 100},
                                "default_probability": {"type": "number", "minimum": 0, "maximum": 1},
                                "fraud_risk_score": {"type": "number", "minimum": 0, "maximum": 100},
                                "kyc_risk_level": {"type": "string"},
                                "regulatory_compliance_status": {"type": "boolean"},
                                "pep_sanctions_clear": {"type": "boolean"}
                            }
                        },
                        "loan": {
                            "type": "object",
                            "properties": {
                                "requested_amount": {"type": "number"},
                                "loan_purpose": {"type": "string"},
                                "loan_term_months": {"type": "number"},
                                "loan_type": {"type": "string"},
                                "down_payment_amount": {"type": "number"},
                                "down_payment_percentage": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    }
                },
                "loan_program": {
                    "type": "string",
                    "enum": ["conventional", "fha", "va", "usda", "jumbo", "non_qm"],
                    "description": "Loan program type"
                },
                "underwriting_guidelines": {
                    "type": "object",
                    "description": "Specific underwriting guidelines to apply",
                    "properties": {
                        "max_dti_ratio": {"type": "number"},
                        "min_credit_score": {"type": "number"},
                        "max_ltv_ratio": {"type": "number"},
                        "require_reserves": {"type": "boolean"},
                        "manual_underwriting_required": {"type": "boolean"}
                    }
                }
            }
        }
        
    def _calculate_overall_score(self, application_data: Dict[str, Any], loan_program: str) -> Dict[str, Any]:
        """Calculate overall application score based on multiple factors."""
        score = 0
        scoring_details = {}
        
        # Credit score evaluation (40% weight)
        credit_score = application_data.get("credit", {}).get("credit_score", 0)
        credit_points = 0
        
        if credit_score >= 740:
            credit_points = 40
        elif credit_score >= 680:
            credit_points = 35
        elif credit_score >= 640:
            credit_points = 25
        elif credit_score >= 620:
            credit_points = 20
        elif credit_score >= 580:
            credit_points = 15  # FHA eligible
        else:
            credit_points = 0
        
        score += credit_points
        scoring_details["credit_score_points"] = credit_points
        
        # DTI evaluation (30% weight)
        dti_ratio = application_data.get("income", {}).get("debt_to_income_ratio", 1.0)
        dti_points = 0
        
        if dti_ratio <= 0.28:
            dti_points = 30
        elif dti_ratio <= 0.36:
            dti_points = 25
        elif dti_ratio <= 0.43:
            dti_points = 15  # Allow higher DTI for strong cases
        elif dti_ratio <= 0.50:
            dti_points = 8   # Borderline acceptable
        else:
            dti_points = 0
        
        score += dti_points
        scoring_details["dti_points"] = dti_points
        
        # LTV evaluation (20% weight)
        ltv_ratio = application_data.get("property", {}).get("loan_to_value_ratio", 1.0)
        ltv_points = 0
        is_special_loan = loan_program in ["fha", "va"]
        
        if ltv_ratio <= 0.80:
            ltv_points = 20
        elif ltv_ratio <= 0.90:
            ltv_points = 15
        elif ltv_ratio <= 0.95:
            ltv_points = 10
        elif ltv_ratio <= 0.97 and is_special_loan:
            ltv_points = 8  # FHA/VA allows higher LTV
        else:
            ltv_points = 0
        
        score += ltv_points
        scoring_details["ltv_points"] = ltv_points
        
        # Loan type bonus for government-backed loans
        if is_special_loan:
            score += 7
            scoring_details["loan_type_bonus"] = 7
        
        # Compliance check (10% weight) - Critical for approval
        compliance_status = application_data.get("risk", {}).get("regulatory_compliance_status", False)
        sanctions_clear = application_data.get("risk", {}).get("pep_sanctions_clear", False)
        
        if compliance_status and sanctions_clear:
            score += 10
            scoring_details["compliance_points"] = 10
        else:
            scoring_details["compliance_points"] = 0
            scoring_details["compliance_failure"] = True
        
        # Income verification bonus (5% weight)
        income_verified = application_data.get("income", {}).get("verified_employment", False)
        if income_verified:
            score += 5
            scoring_details["income_verification_bonus"] = 5
        
        # Document quality bonus (5% weight)
        doc_authenticity = application_data.get("documents", {}).get("document_authenticity_score", 0)
        if doc_authenticity >= 80:
            score += 5
            scoring_details["document_quality_bonus"] = 5
        
        return {
            "total_score": min(100, score),
            "scoring_details": scoring_details,
            "max_possible_score": 100
        }
    
    def _determine_decision(self, score_info: Dict[str, Any], application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine loan decision based on score and other factors."""
        total_score = score_info["total_score"]
        scoring_details = score_info["scoring_details"]
        
        # Check for automatic denial conditions
        if scoring_details.get("compliance_failure", False):
            return {
                "decision": LoanDecision.DENIED,
                "decision_rationale": "Application denied due to regulatory compliance issues or sanctions concerns.",
                "key_factors": [
                    "Regulatory compliance check failed",
                    "Sanctions screening concerns identified",
                    "Unable to proceed with application"
                ],
                "conditions": [],
                "denial_reasons": [
                    "Regulatory compliance check failed",
                    "Sanctions screening concerns identified"
                ]
            }
        
        # Score-based decision logic
        credit_score = application_data.get("credit", {}).get("credit_score", 0)
        dti_ratio = application_data.get("income", {}).get("debt_to_income_ratio", 1.0)
        ltv_ratio = application_data.get("property", {}).get("loan_to_value_ratio", 1.0)
        
        if total_score >= 80:
            return {
                "decision": LoanDecision.APPROVED,
                "decision_rationale": f"Application approved with high score of {total_score}/100. Strong creditworthiness demonstrated.",
                "key_factors": [
                    f"Credit Score: {credit_score}",
                    f"DTI Ratio: {dti_ratio * 100:.1f}%",
                    f"LTV Ratio: {ltv_ratio * 100:.1f}%"
                ],
                "conditions": [],
                "denial_reasons": []
            }
        elif total_score >= 60:
            conditions = []
            
            # Generate specific conditions based on weaknesses
            if scoring_details.get("credit_score_points", 0) < 25:
                conditions.append("Provide letter of explanation for credit history")
            
            if scoring_details.get("dti_points", 0) < 20:
                conditions.append("Provide additional income documentation")
                conditions.append("Demonstrate 2 months reserves")
            
            if scoring_details.get("income_verification_bonus", 0) == 0:
                conditions.append("Complete employment verification")
            
            if not conditions:
                conditions.append("Final underwriter review required")
            
            return {
                "decision": LoanDecision.CONDITIONAL_APPROVAL,
                "decision_rationale": f"Conditional approval with score of {total_score}/100. Additional verification required.",
                "key_factors": [
                    f"Credit Score: {credit_score} (monitoring required)",
                    f"DTI Ratio: {dti_ratio * 100:.1f}% (at limit)",
                    "Additional conditions apply"
                ],
                "conditions": conditions,
                "denial_reasons": []
            }
        else:
            denial_reasons = []
            
            if credit_score < 620:
                denial_reasons.append(f"Credit score {credit_score} below minimum threshold")
            
            if dti_ratio > 0.43:
                denial_reasons.append(f"DTI ratio {dti_ratio * 100:.1f}% exceeds maximum allowed")
            
            if ltv_ratio > 0.95:
                denial_reasons.append(f"LTV ratio {ltv_ratio * 100:.1f}% exceeds maximum allowed")
            
            if not denial_reasons:
                denial_reasons.append("Overall risk assessment unfavorable")
            
            return {
                "decision": LoanDecision.DENIED,
                "decision_rationale": f"Application denied with score of {total_score}/100. Risk factors exceed acceptable limits.",
                "key_factors": [
                    f"Credit Score: {credit_score} (below threshold)",
                    f"DTI Ratio: {dti_ratio * 100:.1f}% (too high)",
                    "Overall risk assessment unfavorable"
                ],
                "conditions": [],
                "denial_reasons": denial_reasons
            }
    
    def _determine_risk_grade_and_pricing(self, total_score: int, decision: LoanDecision) -> Dict[str, Any]:
        """Determine risk grade and pricing tier."""
        if decision == LoanDecision.DENIED:
            return {
                "risk_grade": RiskGrade.F,
                "pricing_tier": PricingTier.INELIGIBLE
            }
        
        if total_score >= 90:
            risk_grade = RiskGrade.A
            pricing_tier = PricingTier.PRIME
        elif total_score >= 80:
            risk_grade = RiskGrade.B
            pricing_tier = PricingTier.PRIME
        elif total_score >= 60:
            risk_grade = RiskGrade.C
            pricing_tier = PricingTier.NEAR_PRIME
        else:
            risk_grade = RiskGrade.D
            pricing_tier = PricingTier.SUBPRIME
        
        return {
            "risk_grade": risk_grade,
            "pricing_tier": pricing_tier
        }
    
    def _generate_next_steps(self, decision: LoanDecision, conditions: List[str]) -> List[str]:
        """Generate next steps based on decision."""
        if decision == LoanDecision.APPROVED:
            return [
                "Loan commitment letter will be issued within 24 hours",
                "Schedule property appraisal if needed",
                "Finalize insurance arrangements",
                "Schedule closing"
            ]
        elif decision == LoanDecision.CONDITIONAL_APPROVAL:
            steps = ["Submit all required conditions within 30 days"]
            steps.extend([f"Complete: {condition}" for condition in conditions])
            return steps
        else:  # DENIED
            return [
                "Adverse action notice will be sent",
                "Review areas for improvement",
                "Consider reapplying after addressing issues"
            ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute comprehensive loan decision analysis."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting loan decision analysis for application: {kwargs.get('application_id', 'Unknown')}")
            
            # Extract parameters
            application_id = kwargs.get("application_id")
            application_data = kwargs.get("application_data", {})
            loan_program = kwargs.get("loan_program", "conventional")
            underwriting_guidelines = kwargs.get("underwriting_guidelines", {})
            
            # Validate required data
            required_sections = ["documents", "income", "credit", "property", "risk", "loan"]
            for section in required_sections:
                if section not in application_data:
                    raise ValueError(f"Missing required application data section: {section}")
            
            # Calculate overall application score
            score_info = self._calculate_overall_score(application_data, loan_program)
            total_score = score_info["total_score"]
            
            # Make loan decision
            decision_info = self._determine_decision(score_info, application_data)
            decision = decision_info["decision"]
            
            # Determine risk grade and pricing
            risk_pricing = self._determine_risk_grade_and_pricing(total_score, decision)
            
            # Generate next steps
            next_steps = self._generate_next_steps(decision, decision_info.get("conditions", []))
            
            # Calculate confidence score
            confidence_score = 95 if total_score >= 90 else 85 if total_score >= 70 else 75
            
            # Determine approval expiration
            approval_expiration = None
            if decision != LoanDecision.DENIED:
                expiration_date = datetime.now() + timedelta(days=120)  # 120 days
                approval_expiration = expiration_date.strftime("%Y-%m-%d")
            
            # Calculate recommended loan amount
            requested_amount = application_data.get("loan", {}).get("requested_amount", 0)
            recommended_loan_amount = requested_amount if decision != LoanDecision.DENIED else None
            
            # If conditional approval with high DTI, might recommend lower amount
            if decision == LoanDecision.CONDITIONAL_APPROVAL:
                dti_ratio = application_data.get("income", {}).get("debt_to_income_ratio", 0)
                if dti_ratio > 0.40:
                    # Reduce loan amount to improve DTI
                    monthly_income = application_data.get("income", {}).get("monthly_gross_income", 0)
                    max_housing_payment = monthly_income * 0.28  # Conservative front-end ratio
                    # This is simplified - would need payment calculation in practice
                    recommended_loan_amount = min(requested_amount, requested_amount * 0.9)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Generate loan terms for approved/conditional loans
            loan_terms = None
            if decision in [LoanDecision.APPROVED, LoanDecision.CONDITIONAL_APPROVAL]:
                loan_terms = self._generate_loan_terms(application_data, total_score, loan_program, recommended_loan_amount)

            # Compile comprehensive results
            result_data = {
                "application_id": application_id,
                "decision_timestamp": datetime.now().isoformat(),
                "loan_decision": {
                    "decision": decision.value,
                    "decision_confidence": confidence_score,
                    "decision_rationale": decision_info["decision_rationale"],
                    "key_factors": decision_info["key_factors"],
                    "conditions": decision_info.get("conditions", []),
                    "denial_reasons": decision_info.get("denial_reasons", []),
                    "recommended_loan_amount": recommended_loan_amount,
                    "risk_grade": risk_pricing["risk_grade"].value,
                    "pricing_tier": risk_pricing["pricing_tier"].value,
                    "approval_expiration": approval_expiration,
                    "next_steps": next_steps,
                    "loan_terms": loan_terms
                },
                "scoring_analysis": {
                    "total_score": total_score,
                    "max_possible_score": score_info["max_possible_score"],
                    "scoring_breakdown": score_info["scoring_details"],
                    "score_percentile": min(95, total_score + 10)  # Approximate percentile
                },
                "risk_assessment": {
                    "overall_risk_score": application_data.get("risk", {}).get("overall_risk_score", 0),
                    "fraud_risk_score": application_data.get("risk", {}).get("fraud_risk_score", 0),
                    "default_probability": application_data.get("risk", {}).get("default_probability", 0),
                    "risk_grade": risk_pricing["risk_grade"].value,
                    "risk_mitigation_factors": self._identify_risk_mitigation_factors(application_data)
                },
                "compliance_status": {
                    "regulatory_compliant": application_data.get("risk", {}).get("regulatory_compliance_status", False),
                    "sanctions_clear": application_data.get("risk", {}).get("pep_sanctions_clear", False),
                    "kyc_risk_level": application_data.get("risk", {}).get("kyc_risk_level", "unknown"),
                    "additional_reviews_required": decision == LoanDecision.CONDITIONAL_APPROVAL
                },
                "loan_terms_recommendation": {
                    "loan_program": loan_program,
                    "pricing_tier": risk_pricing["pricing_tier"].value,
                    "estimated_rate_adjustment": self._calculate_rate_adjustment(total_score, loan_program),
                    "required_reserves_months": 2 if total_score < 70 else 0,
                    "mortgage_insurance_required": self._requires_mortgage_insurance(application_data, loan_program)
                },
                "underwriter_notes": [
                    f"Application scored {total_score}/100 points",
                    f"Credit score: {application_data.get('credit', {}).get('credit_score', 0)}",
                    f"DTI ratio: {application_data.get('income', {}).get('debt_to_income_ratio', 0) * 100:.1f}%",
                    f"LTV ratio: {application_data.get('property', {}).get('loan_to_value_ratio', 0) * 100:.1f}%",
                    f"Decision: {decision.value}",
                    f"Risk grade: {risk_pricing['risk_grade'].value}"
                ]
            }
            
            self.logger.info(f"Loan decision completed for {application_id}: {decision.value} (Score: {total_score})")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data,
                execution_time=processing_time,
                metadata={
                    "confidence": confidence_score / 100,
                    "source": "enhanced_loan_decision_engine_v1.0.0",
                    "decision": decision.value,
                    "total_score": total_score,
                    "risk_grade": risk_pricing["risk_grade"].value,
                    "loan_program": loan_program
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Loan decision engine failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg,
                execution_time=processing_time,
                metadata={
                    "source": "enhanced_loan_decision_engine_v1.0.0",
                    "error_type": "decision_engine_error"
                }
            )
    def _identify_risk_mitigation_factors(self, application_data: Dict[str, Any]) -> List[str]:
        """Identify factors that mitigate risk."""
        factors = []
        
        # High income
        monthly_income = application_data.get("income", {}).get("monthly_gross_income", 0)
        if monthly_income > 10000:  # $120k+ annually
            factors.append("High income level provides payment stability")
        
        # Low LTV
        ltv_ratio = application_data.get("property", {}).get("loan_to_value_ratio", 1.0)
        if ltv_ratio <= 0.70:
            factors.append("Low loan-to-value ratio reduces default risk")
        
        # Strong credit history
        credit_score = application_data.get("credit", {}).get("credit_score", 0)
        if credit_score >= 760:
            factors.append("Excellent credit history demonstrates reliability")
        
        # Employment stability
        income_stability = application_data.get("income", {}).get("income_stability_score", 0)
        if income_stability >= 80:
            factors.append("Stable employment history")
        
        return factors
    
    def _calculate_rate_adjustment(self, total_score: int, loan_program: str) -> float:
        """Calculate estimated rate adjustment in basis points."""
        base_adjustment = 0
        
        if total_score >= 90:
            base_adjustment = -25  # Rate discount for excellent applications
        elif total_score >= 80:
            base_adjustment = 0     # Par pricing
        elif total_score >= 60:
            base_adjustment = 50    # Rate add-on for conditional approvals
        else:
            base_adjustment = 100   # Higher rate for marginal applications
        
        # Program-specific adjustments
        if loan_program == "fha":
            base_adjustment -= 25  # FHA typically has lower rates
        elif loan_program == "jumbo":
            base_adjustment += 25  # Jumbo typically has higher rates
        elif loan_program == "non_qm":
            base_adjustment += 200 # Non-QM has significantly higher rates
        
        return base_adjustment
    
    def _requires_mortgage_insurance(self, application_data: Dict[str, Any], loan_program: str) -> bool:
        """Determine if mortgage insurance is required."""
        ltv_ratio = application_data.get("property", {}).get("loan_to_value_ratio", 1.0)
        
        if loan_program == "conventional":
            return ltv_ratio > 0.80
        elif loan_program == "fha":
            return True  # FHA always requires MIP
        elif loan_program == "va":
            return False  # VA doesn't require MI but has funding fee
        elif loan_program == "usda":
            return True  # USDA requires guarantee fee
        else:
            return ltv_ratio > 0.80  # Default rule
    
    def _generate_loan_terms(self, application_data: Dict[str, Any], total_score: int, loan_program: str, loan_amount: float) -> Dict[str, Any]:
        """Generate detailed loan terms for approved/conditional loans."""
        from decimal import Decimal
        
        # Base interest rate calculation
        base_rate = 6.5  # Current market base rate
        rate_adjustment = self._calculate_rate_adjustment(total_score, loan_program) / 100  # Convert basis points to percentage
        interest_rate = base_rate + rate_adjustment
        
        # Loan term (typically 30 years for most mortgages)
        loan_term_years = application_data.get("loan", {}).get("loan_term_months", 360) // 12
        if loan_term_years <= 0:
            loan_term_years = 30  # Default to 30 years
        
        # Calculate monthly payment (Principal + Interest)
        monthly_rate = interest_rate / 100 / 12
        num_payments = loan_term_years * 12
        
        if monthly_rate > 0:
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        else:
            monthly_payment = loan_amount / num_payments  # If rate is 0
        
        # Down payment
        property_value = application_data.get("property", {}).get("appraised_value", 0)
        down_payment = property_value - loan_amount if property_value > loan_amount else 0
        
        # PMI calculation
        pmi_required = self._requires_mortgage_insurance(application_data, loan_program)
        pmi_monthly_amount = 0
        if pmi_required:
            # PMI is typically 0.3% to 1.5% of loan amount annually
            ltv_ratio = application_data.get("property", {}).get("loan_to_value_ratio", 0.8)
            if ltv_ratio > 0.95:
                pmi_rate = 0.015  # 1.5% for high LTV
            elif ltv_ratio > 0.90:
                pmi_rate = 0.010  # 1.0% for medium-high LTV
            else:
                pmi_rate = 0.005  # 0.5% for lower LTV
            
            pmi_monthly_amount = (loan_amount * pmi_rate) / 12
        
        # Closing costs (typically 2-5% of loan amount)
        closing_costs = loan_amount * 0.03  # 3% estimate
        
        # APR calculation (simplified - includes PMI and some closing costs)
        apr = interest_rate + 0.25  # Simplified APR calculation
        
        # Points (optional - could be 0 for this calculation)
        points = Decimal("0")
        
        # Escrow requirements
        escrow_required = loan_program in ["fha", "va", "usda"] or application_data.get("property", {}).get("loan_to_value_ratio", 0) > 0.80
        
        # Prepayment penalty (typically not allowed for QM loans)
        prepayment_penalty = loan_program == "non_qm"
        
        # Return dictionary with Decimal values for proper model validation
        return {
            "loan_amount": Decimal(str(round(loan_amount, 2))),
            "interest_rate": Decimal(str(round(interest_rate, 3))),
            "loan_term_years": loan_term_years,
            "monthly_payment": Decimal(str(round(monthly_payment, 2))),
            "down_payment_required": Decimal(str(round(down_payment, 2))),
            "closing_costs": Decimal(str(round(closing_costs, 2))),
            "points": points,
            "apr": Decimal(str(round(apr, 3))),
            "pmi_required": pmi_required,
            "pmi_monthly_amount": Decimal(str(round(pmi_monthly_amount, 2))) if pmi_required else None,
            "escrow_required": escrow_required,
            "prepayment_penalty": prepayment_penalty
        }