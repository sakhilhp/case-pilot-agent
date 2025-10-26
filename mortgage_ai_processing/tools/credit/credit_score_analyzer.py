"""
Enhanced Credit Score Analyzer Tool - Comprehensive credit analysis for mortgage lending.

Converted from TypeScript FSI Tools framework to Python.
Implements mortgage lending guidelines for credit score analysis with risk assessment.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass

from ..base import BaseTool, ToolResult, ToolCategory


class CreditScoreType(Enum):
    """Credit score types used in mortgage lending."""
    FICO_8 = "fico_8"
    FICO_9 = "fico_9"
    FICO_10 = "fico_10"
    FICO_BANKCARD_8 = "fico_bankcard_8"
    FICO_AUTO_8 = "fico_auto_8"
    FICO_MORTGAGE_SCORE = "fico_mortgage_score"
    VANTAGESCORE_3 = "vantagescore_3"
    VANTAGESCORE_4 = "vantagescore_4"
    BEACON_5 = "beacon_5"
    EMPIRICA = "empirica"
    OTHER = "other"


class CreditBureau(Enum):
    """Credit bureaus."""
    EXPERIAN = "experian"
    EQUIFAX = "equifax"
    TRANSUNION = "transunion"


class RiskRating(Enum):
    """Risk rating categories."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    BAD_CREDIT = "bad_credit"


class LoanProgram(Enum):
    """Loan programs with different credit requirements."""
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    USDA = "usda"
    JUMBO = "jumbo"
    NON_QM = "non_qm"
    BANK_STATEMENT = "bank_statement"
    ASSET_BASED = "asset_based"


@dataclass
class CreditScore:
    """Individual credit score from a bureau."""
    bureau: CreditBureau
    score_type: CreditScoreType
    score_value: int
    score_date: datetime
    score_factors: Optional[List[str]] = None
    model_version: Optional[str] = None


@dataclass
class PricingAdjustment:
    """Pricing adjustment details."""
    adjustment_type: str  # llpa, rate_add_on, pricing_hit, overlay
    adjustment_amount: float  # In basis points
    reason: str
    description: str


class EnhancedCreditScoreAnalyzerTool(BaseTool):
    """
    Enhanced Credit Score Analyzer Tool for mortgage lending decisions.
    
    Features:
    - FICO and VantageScore analysis and interpretation
    - Risk categorization (Excellent, Good, Fair, Poor, Bad Credit)
    - Loan program eligibility determination
    - Rate and terms recommendations based on credit tiers
    - Credit-based pricing adjustments and overlays
    - Multi-bureau score analysis with representative score selection
    - Compensating factor recommendations for lower scores
    """
    
    def __init__(self):
        super().__init__(
            name="enhanced_credit_score_analyzer",
            description="Analyze credit scores and provide mortgage lending risk assessment, loan program eligibility, and pricing guidance",
            category=ToolCategory.RISK_ASSESSMENT,
            version="1.0.0",
            agent_domain="credit_assessment"
        )
        
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for credit score analysis parameters."""
        return {
            "type": "object",
            "required": ["borrower_name", "credit_scores", "loan_amount", "loan_purpose", "property_type", "target_loan_programs"],
            "properties": {
                "borrower_name": {
                    "type": "string",
                    "description": "Name of the borrower"
                },
                "credit_scores": {
                    "type": "array",
                    "description": "Array of credit scores from different bureaus",
                    "items": {
                        "type": "object",
                        "required": ["bureau", "score_type", "score_value", "score_date"],
                        "properties": {
                            "bureau": {
                                "type": "string",
                                "enum": [e.value for e in CreditBureau],
                                "description": "Credit bureau name"
                            },
                            "score_type": {
                                "type": "string",
                                "enum": [e.value for e in CreditScoreType],
                                "description": "Type of credit score"
                            },
                            "score_value": {
                                "type": "integer",
                                "minimum": 300,
                                "maximum": 850,
                                "description": "Credit score value (300-850)"
                            },
                            "score_date": {
                                "type": "string",
                                "description": "Date when credit score was generated (ISO format)"
                            },
                            "score_factors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Factors affecting the credit score"
                            }
                        }
                    }
                },
                "loan_amount": {
                    "type": "number",
                    "description": "Loan amount requested"
                },
                "loan_purpose": {
                    "type": "string",
                    "enum": ["purchase", "refinance", "cash_out_refinance"],
                    "description": "Purpose of the loan"
                },
                "property_type": {
                    "type": "string",
                    "enum": ["primary", "secondary", "investment"],
                    "description": "Type of property occupancy"
                },
                "target_loan_programs": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [e.value for e in LoanProgram]
                    },
                    "description": "Target loan programs to evaluate"
                },
                "down_payment_percent": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Down payment as percentage (0-100)"
                },
                "loan_to_value_ratio": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Loan to value ratio (0-100)"
                },
                "debt_to_income_ratio": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Debt to income ratio (0-100)"
                },
                "first_time_buyer": {
                    "type": "boolean",
                    "description": "Whether borrower is a first-time buyer"
                }
            }
        }    
        
    def _get_representative_score(self, scores: List[CreditScore]) -> Dict[str, Any]:
        """Determine representative credit score using mortgage lending rules."""
        if not scores:
            raise ValueError("No credit scores provided")
        
        sorted_scores = sorted([s.score_value for s in scores])
        
        if len(sorted_scores) == 1:
            return {"score": sorted_scores[0], "method": "single_score"}
        elif len(sorted_scores) == 2:
            return {"score": min(sorted_scores), "method": "lowest_score"}
        else:
            # Use middle score for 3+ scores (mortgage industry standard)
            middle_index = len(sorted_scores) // 2
            return {"score": sorted_scores[middle_index], "method": "middle_score"}
        
    def _get_risk_rating(self, score: int) -> Dict[str, Any]:
        """Categorize credit risk based on FICO score ranges."""
        if score >= 740:
            return {
                "rating": RiskRating.EXCELLENT,
                "description": "Excellent credit - qualifies for best rates and terms"
            }
        elif score >= 680:
            return {
                "rating": RiskRating.GOOD,
                "description": "Good credit - qualifies for competitive rates with minimal overlays"
            }
        elif score >= 620:
            return {
                "rating": RiskRating.FAIR,
                "description": "Fair credit - may qualify but with higher rates and additional requirements"
            }
        elif score >= 580:
            return {
                "rating": RiskRating.POOR,
                "description": "Poor credit - limited loan options, likely requires compensating factors"
            }
        else:
            return {
                "rating": RiskRating.BAD_CREDIT,
                "description": "Bad credit - very limited options, may require alternative lending"
            }
    
    def _get_rate_tier(self, score: int, program: LoanProgram) -> str:
        """Determine rate tier based on credit score and loan program."""
        if program == LoanProgram.NON_QM:
            if score >= 720:
                return "prime"
            elif score >= 680:
                return "near_prime"
            elif score >= 620:
                return "subprime"
            else:
                return "deep_subprime"
        
        if score >= 760:
            return "super_prime"
        elif score >= 720:
            return "prime"
        elif score >= 680:
            return "near_prime"
        elif score >= 620:
            return "subprime"
        else:
            return "deep_subprime"
    
    def _analyze_loan_program_eligibility(self, score: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine loan program eligibility based on credit score and other factors."""
        eligibility_results = []
        target_programs = [LoanProgram(p) for p in params.get("target_loan_programs", [])]
        ltv = params.get("loan_to_value_ratio", 80)
        
        for program in target_programs:
            if program == LoanProgram.CONVENTIONAL:
                min_score = 620
                eligible = score >= min_score
                eligibility_results.append({
                    "program": program.value,
                    "eligible": eligible,
                    "minimum_score_required": min_score,
                    "score_margin": score - min_score,
                    "rate_tier": self._get_rate_tier(score, program),
                    "pricing_adjustments": self._get_conventional_pricing_adjustments(score, ltv),
                    "compensating_factors_needed": [] if eligible else ["Higher down payment", "Lower DTI", "Reserves"],
                    "overlay_considerations": ["Manual underwriting likely required"] if score < 660 else []
                })
            
            elif program == LoanProgram.FHA:
                min_score = 580
                eligible = score >= min_score
                eligibility_results.append({
                    "program": program.value,
                    "eligible": eligible,
                    "minimum_score_required": min_score,
                    "score_margin": score - min_score,
                    "rate_tier": self._get_rate_tier(score, program),
                    "pricing_adjustments": self._get_fha_pricing_adjustments(score),
                    "compensating_factors_needed": [] if eligible else ["Manual underwriting with 3.5% down"],
                    "overlay_considerations": ["10% down payment if score 580-619"] if score < 620 else []
                })
            
            elif program == LoanProgram.VA:
                min_score = 620  # Most lenders overlay
                eligible = score >= min_score
                eligibility_results.append({
                    "program": program.value,
                    "eligible": eligible,
                    "minimum_score_required": min_score,
                    "score_margin": score - min_score,
                    "rate_tier": self._get_rate_tier(score, program),
                    "pricing_adjustments": [],  # VA loans don't have LLPA adjustments
                    "compensating_factors_needed": ["Manual underwriting", "Residual income"] if score < min_score else [],
                    "overlay_considerations": ["Lender overlays common below 620"] if score < 620 else []
                })
            
            elif program == LoanProgram.USDA:
                min_score = 640
                eligible = score >= min_score
                eligibility_results.append({
                    "program": program.value,
                    "eligible": eligible,
                    "minimum_score_required": min_score,
                    "score_margin": score - min_score,
                    "rate_tier": self._get_rate_tier(score, program),
                    "pricing_adjustments": self._get_usda_pricing_adjustments(score),
                    "compensating_factors_needed": ["Manual underwriting"] if score < min_score else [],
                    "overlay_considerations": ["Property must be in eligible rural area", "Income limits apply"]
                })
            
            elif program == LoanProgram.JUMBO:
                min_score = 700
                loan_amount = params.get("loan_amount", 0)
                eligible = score >= min_score and loan_amount > 766550  # 2024 limit
                eligibility_results.append({
                    "program": program.value,
                    "eligible": eligible,
                    "minimum_score_required": min_score,
                    "score_margin": score - min_score,
                    "rate_tier": self._get_rate_tier(score, program),
                    "pricing_adjustments": self._get_jumbo_pricing_adjustments(score),
                    "compensating_factors_needed": ["Higher down payment", "Lower DTI", "Significant reserves"] if score < min_score else [],
                    "overlay_considerations": ["Higher reserve requirements", "Stricter DTI limits"]
                })
            
            elif program == LoanProgram.NON_QM:
                min_score = 550
                eligible = score >= min_score
                eligibility_results.append({
                    "program": program.value,
                    "eligible": eligible,
                    "minimum_score_required": min_score,
                    "score_margin": score - min_score,
                    "rate_tier": self._get_rate_tier(score, program),
                    "pricing_adjustments": self._get_non_qm_pricing_adjustments(score),
                    "compensating_factors_needed": ["Asset verification", "Bank statements", "Higher down payment"],
                    "overlay_considerations": ["Higher rates", "Alternative documentation", "Prepayment penalties possible"]
                })
        
        return eligibility_results
        
    def _get_conventional_pricing_adjustments(self, score: int, ltv: float) -> List[PricingAdjustment]:
        """Get conventional loan pricing adjustments based on credit score and LTV."""
        adjustments = []
        
        if score < 720:
            adjustment = 0
            if 680 <= score < 700:
                adjustment = 25
            elif 660 <= score < 680:
                adjustment = 50
            elif 640 <= score < 660:
                adjustment = 75
            elif 620 <= score < 640:
                adjustment = 100
            elif score < 620:
                adjustment = 150
            
            # LTV adjustments
            if ltv > 80:
                adjustment += 25
            if ltv > 90:
                adjustment += 25
            
            if adjustment > 0:
                adjustments.append(PricingAdjustment(
                    adjustment_type="llpa",
                    adjustment_amount=adjustment,
                    reason="Credit Score LLPA",
                    description=f"Credit score {score} with {ltv}% LTV pricing adjustment"
                ))
        
        return adjustments
    
    def _get_fha_pricing_adjustments(self, score: int) -> List[PricingAdjustment]:
        """Get FHA loan pricing adjustments."""
        adjustments = []
        
        if score < 620:
            adjustments.append(PricingAdjustment(
                adjustment_type="rate_add_on",
                adjustment_amount=25,
                reason="Low Credit Score",
                description="Additional rate adjustment for credit score below 620"
            ))
        
        return adjustments
    
    def _get_usda_pricing_adjustments(self, score: int) -> List[PricingAdjustment]:
        """Get USDA loan pricing adjustments."""
        adjustments = []
        
        if score < 680:
            adjustments.append(PricingAdjustment(
                adjustment_type="rate_add_on",
                adjustment_amount=12.5,
                reason="USDA Credit Score Adjustment",
                description="Rate adjustment for credit score below 680"
            ))
        
        return adjustments
    
    def _get_jumbo_pricing_adjustments(self, score: int) -> List[PricingAdjustment]:
        """Get jumbo loan pricing adjustments."""
        adjustments = []
        
        if score < 740:
            adjustment = 0
            if score >= 720:
                adjustment = 25
            elif score >= 700:
                adjustment = 50
            else:
                adjustment = 100
            
            adjustments.append(PricingAdjustment(
                adjustment_type="pricing_hit",
                adjustment_amount=adjustment,
                reason="Jumbo Credit Score Pricing",
                description=f"Jumbo loan credit score pricing for score {score}"
            ))
        
        return adjustments
    
    def _get_non_qm_pricing_adjustments(self, score: int) -> List[PricingAdjustment]:
        """Get Non-QM loan pricing adjustments."""
        adjustments = []
        
        # Non-QM loans typically have higher base rates
        adjustment = 200  # Base Non-QM adjustment
        
        if score < 680:
            adjustment += 50
        if score < 620:
            adjustment += 100
        if score < 580:
            adjustment += 150
        
        adjustments.append(PricingAdjustment(
            adjustment_type="rate_add_on",
            adjustment_amount=adjustment,
            reason="Non-QM Loan Pricing",
            description=f"Non-QM loan pricing based on credit score {score}"
        ))
        
        return adjustments
    
    def _generate_improvement_recommendations(self, score: int, risk_rating: RiskRating) -> List[str]:
        """Generate credit improvement recommendations."""
        recommendations = []
        
        if score < 740:
            recommendations.extend([
                "Pay down credit card balances to improve utilization ratio",
                "Make all payments on time to build positive payment history"
            ])
        
        if score < 680:
            recommendations.extend([
                "Consider becoming an authorized user on a family member's account",
                "Avoid applying for new credit before mortgage application",
                "Review credit report for errors and dispute if necessary"
            ])
        
        if score < 620:
            recommendations.extend([
                "Consider waiting 6-12 months to improve credit before applying",
                "Work with a credit counselor to develop improvement strategy",
                "Consider secured credit cards to rebuild credit history"
            ])
        
        return recommendations
    
    def _calculate_confidence_score(self, scores: List[CreditScore], params: Dict[str, Any]) -> int:
        """Calculate confidence score based on available data quality."""
        confidence = 70  # Base confidence
        
        # Credit score data quality
        if len(scores) >= 3:
            confidence += 15
        elif len(scores) == 2:
            confidence += 10
        else:
            confidence -= 10
        
        # Recent scores boost confidence
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_scores = [s for s in scores if s.score_date >= thirty_days_ago]
        
        if len(recent_scores) == len(scores):
            confidence += 10
        
        # Complete loan parameters
        if params.get("debt_to_income_ratio"):
            confidence += 5
        if params.get("loan_to_value_ratio"):
            confidence += 5
        
        return min(max(confidence, 0), 100)
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute comprehensive credit score analysis."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting credit score analysis for borrower: {kwargs.get('borrower_name', 'Unknown')}")
            
            # Extract parameters
            borrower_name = kwargs.get("borrower_name")
            credit_scores_data = kwargs.get("credit_scores", [])
            loan_amount = kwargs.get("loan_amount", 0)
            loan_purpose = kwargs.get("loan_purpose", "purchase")
            property_type = kwargs.get("property_type", "primary")
            target_loan_programs = kwargs.get("target_loan_programs", ["conventional"])
            
            # Convert credit scores
            credit_scores = []
            for score_data in credit_scores_data:
                try:
                    score = CreditScore(
                        bureau=CreditBureau(score_data.get("bureau", "experian")),
                        score_type=CreditScoreType(score_data.get("score_type", "fico_8")),
                        score_value=int(score_data.get("score_value", 0)),
                        score_date=datetime.fromisoformat(score_data.get("score_date", datetime.now().isoformat())),
                        score_factors=score_data.get("score_factors", [])
                    )
                    credit_scores.append(score)
                except Exception as e:
                    self.logger.warning(f"Error processing credit score: {e}")
                    continue
            
            if not credit_scores:
                raise ValueError("No valid credit scores provided")
            
            # Get representative credit score
            rep_score_info = self._get_representative_score(credit_scores)
            representative_score = rep_score_info["score"]
            selection_method = rep_score_info["method"]
            
            # Analyze risk rating
            risk_info = self._get_risk_rating(representative_score)
            risk_rating = risk_info["rating"]
            risk_description = risk_info["description"]
            
            # Analyze loan program eligibility
            program_eligibility = self._analyze_loan_program_eligibility(representative_score, kwargs)
            
            # Calculate total pricing adjustments
            total_pricing_adjustments = 0
            for program in program_eligibility:
                if program["eligible"]:
                    program_adjustments = sum(adj.adjustment_amount for adj in program["pricing_adjustments"])
                    total_pricing_adjustments += program_adjustments
            
            # Generate recommendations
            improvement_recommendations = self._generate_improvement_recommendations(representative_score, risk_rating)
            
            # Get eligible programs for recommendations
            eligible_programs = [p["program"] for p in program_eligibility if p["eligible"]]
            eligible_programs.sort(key=lambda p: sum(adj.adjustment_amount for adj in 
                                                   next(prog for prog in program_eligibility if prog["program"] == p)["pricing_adjustments"]))
            
            # Estimate rate range
            base_rate = 7.0  # Current approximate market rate
            eligible_adjustments = [sum(adj.adjustment_amount for adj in p["pricing_adjustments"]) 
                                  for p in program_eligibility if p["eligible"]]
            
            if eligible_adjustments:
                min_adjustment = min(eligible_adjustments) / 100
                max_adjustment = max(eligible_adjustments) / 100
                avg_adjustment = sum(eligible_adjustments) / len(eligible_adjustments) / 100
            else:
                min_adjustment = max_adjustment = avg_adjustment = 0
            
            # Calculate confidence
            confidence_score = self._calculate_confidence_score(credit_scores, kwargs)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Compile results
            result_data = {
                "borrower_name": borrower_name,
                "analysis_date": datetime.now().isoformat(),
                "credit_analysis": {
                    "representative_score": representative_score,
                    "score_selection_method": selection_method,
                    "risk_rating": risk_rating.value,
                    "risk_category_description": risk_description,
                    "score_strengths": ["Strong credit history", "Excellent payment record"] if representative_score >= 720 else 
                                     ["Good payment history", "Stable credit profile"] if representative_score >= 680 else [],
                    "score_weaknesses": ["Below prime credit threshold"] if representative_score < 680 else 
                                      ["Subprime credit rating", "Limited loan options"] if representative_score < 620 else [],
                    "improvement_recommendations": improvement_recommendations
                },
                "program_eligibility": [
                    {
                        **prog,
                        "pricing_adjustments": [
                            {
                                "adjustment_type": adj.adjustment_type,
                                "adjustment_amount": adj.adjustment_amount,
                                "reason": adj.reason,
                                "description": adj.description
                            } for adj in prog["pricing_adjustments"]
                        ]
                    } for prog in program_eligibility
                ],
                "overall_creditworthiness": risk_rating.value,
                "recommended_programs": eligible_programs[:3],  # Top 3 recommendations
                "estimated_rate_range": {
                    "min_rate": round(base_rate + min_adjustment, 3),
                    "max_rate": round(base_rate + max_adjustment, 3),
                    "most_likely_rate": round(base_rate + avg_adjustment, 3)
                },
                "total_pricing_adjustments": total_pricing_adjustments,
                "action_recommendations": [
                    "Proceed with loan application - excellent credit profile" if representative_score >= 740 else
                    "Good candidate for most loan programs" if representative_score >= 680 else
                    "Consider FHA or VA loan programs for better terms" if representative_score >= 620 else
                    "Focus on credit improvement before applying or consider alternative lending"
                ],
                "additional_documentation_needed": ["Letter of explanation for credit issues", "Proof of extenuating circumstances"] if representative_score < 640 else [],
                "confidence_score": confidence_score,
                "analysis_notes": [
                    f"Analysis based on {len(credit_scores)} credit score(s)",
                    f"Representative score: {representative_score} using {selection_method} method",
                    f"Risk rating: {risk_rating.value.upper()}",
                    f"{len([p for p in program_eligibility if p['eligible']])} loan programs eligible"
                ]
            }
            
            self.logger.info(f"Credit score analysis completed for {borrower_name}: Score {representative_score}, Risk {risk_rating.value}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data,
                execution_time=processing_time,
                metadata={
                    "confidence": confidence_score / 100,
                    "source": "enhanced_credit_score_analyzer_v1.0.0",
                    "representative_score": representative_score,
                    "risk_rating": risk_rating.value,
                    "eligible_programs": len(eligible_programs)
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Credit score analysis failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg,
                execution_time=processing_time,
                metadata={
                    "source": "enhanced_credit_score_analyzer_v1.0.0",
                    "error_type": "analysis_error"
                }
            )