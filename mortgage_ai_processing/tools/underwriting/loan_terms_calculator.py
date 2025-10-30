"""Loan Terms Calculator Tool - Converted from TypeScript.

Calculate optimal loan terms, rates, and structure with automatic loan product matching
based on borrower profile and market conditions.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import math

from ..base import BaseTool, ToolResult, ToolMetadata


class LoanPurpose(Enum):
    """Loan purpose types."""
    PURCHASE = "purchase"
    REFINANCE = "refinance"
    CASH_OUT_REFINANCE = "cash_out_refinance"


class OccupancyType(Enum):
    """Property occupancy types."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    INVESTMENT = "investment"


class LoanProgram(Enum):
    """Loan program types."""
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    USDA = "usda"
    JUMBO = "jumbo"


class LoanType(Enum):
    """Loan types."""
    FIXED = "fixed"
    ARM = "arm"


class RiskGrade(Enum):
    """Risk grades."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class PricingTier(Enum):
    """Pricing tiers."""
    PRIME = "PRIME"
    NEAR_PRIME = "NEAR_PRIME"
    SUBPRIME = "SUBPRIME"


class MarketCondition(Enum):
    """Market conditions."""
    NORMAL = "normal"
    VOLATILE = "volatile"
    TIGHTENING = "tightening"
    LOOSENING = "loosening"


class MortgageInsuranceType(Enum):
    """Mortgage insurance types."""
    NONE = "none"
    PMI = "pmi"
    MIP = "mip"
    FUNDING_FEE = "funding_fee"


@dataclass
class PricingAdjustments:
    """Pricing adjustments structure."""
    credit_score_adjustment: float = 0.0
    ltv_adjustment: float = 0.0
    cash_out_adjustment: float = 0.0
    occupancy_adjustment: float = 0.0
    reserves_adjustment: float = 0.0
    debt_ratio_adjustment: float = 0.0
    total_adjustments: float = 0.0


@dataclass
class MortgageInsurance:
    """Mortgage insurance details."""
    monthly_premium: float = 0.0
    upfront_premium: float = 0.0
    insurance_type: str = MortgageInsuranceType.NONE.value
    cancellation_threshold: Optional[float] = None


@dataclass
class LoanFees:
    """Loan fees structure."""
    origination_fee: float = 0.0
    processing_fee: float = 450.0
    underwriting_fee: float = 850.0
    appraisal_fee: float = 500.0
    credit_report_fee: float = 75.0
    total_closing_costs: float = 0.0


@dataclass
class PaymentBreakdown:
    """Monthly payment breakdown."""
    principal_and_interest: float = 0.0
    property_taxes: float = 0.0
    homeowners_insurance: float = 0.0
    mortgage_insurance: float = 0.0
    hoa_fees: float = 0.0
    total_payment: float = 0.0


@dataclass
class ProductMatching:
    """Product matching results."""
    recommended_program: str
    eligibility_score: float
    alternative_programs: List[Dict[str, Any]]
    matching_rationale: List[str]


class LoanTermsCalculatorTool(BaseTool):
    """Tool for calculating optimal loan terms and structure."""
    
    def __init__(self):
        from ..base import ToolCategory
        super().__init__(
            name="loan_terms_calculator",
            description="Calculate optimal loan terms, rates, and structure with automatic loan product matching based on borrower profile and market conditions",
            category=ToolCategory.UNDERWRITING,
            version="1.0.0",
            agent_domain="underwriting"
        )
        
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "loan_amount": {
                    "type": "number",
                    "description": "Loan amount requested",
                    "minimum": 1000
                },
                "property_value": {
                    "type": "number",
                    "description": "Property value or purchase price",
                    "minimum": 1000
                },
                "loan_purpose": {
                    "type": "string",
                    "enum": [purpose.value for purpose in LoanPurpose],
                    "description": "Purpose of the loan"
                },
                "occupancy_type": {
                    "type": "string",
                    "enum": [occ.value for occ in OccupancyType],
                    "description": "Property occupancy type"
                },
                "credit_score": {
                    "type": "integer",
                    "description": "Borrower's credit score",
                    "minimum": 300,
                    "maximum": 850
                },
                "debt_to_income_ratio": {
                    "type": "number",
                    "description": "Debt-to-income ratio as decimal (e.g., 0.43 for 43%)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "liquid_reserves": {
                    "type": "number",
                    "description": "Liquid reserves in months of payments",
                    "minimum": 0.0
                },
                "down_payment_percentage": {
                    "type": "number",
                    "description": "Down payment as percentage (e.g., 0.20 for 20%)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "loan_program": {
                    "type": "string",
                    "enum": [program.value for program in LoanProgram],
                    "description": "Specific loan program (optional - will auto-match if not provided)"
                },
                "loan_type": {
                    "type": "string",
                    "enum": [loan_type.value for loan_type in LoanType],
                    "description": "Loan type (fixed or ARM)",
                    "default": "fixed"
                },
                "term_years": {
                    "type": "integer",
                    "enum": [15, 20, 30],
                    "description": "Loan term in years",
                    "default": 30
                },
                "risk_grade": {
                    "type": "string",
                    "enum": [grade.value for grade in RiskGrade],
                    "description": "Risk grade assessment",
                    "default": "B"
                },
                "pricing_tier": {
                    "type": "string",
                    "enum": [tier.value for tier in PricingTier],
                    "description": "Pricing tier classification",
                    "default": "PRIME"
                },
                "base_rate": {
                    "type": "number",
                    "description": "Base rate override (optional)",
                    "minimum": 0.0,
                    "maximum": 0.20
                },
                "market_conditions": {
                    "type": "string",
                    "enum": [condition.value for condition in MarketCondition],
                    "description": "Current market conditions",
                    "default": "normal"
                },
                "first_time_buyer": {
                    "type": "boolean",
                    "description": "Is borrower a first-time buyer",
                    "default": False
                },
                "self_employed": {
                    "type": "boolean",
                    "description": "Is borrower self-employed",
                    "default": False
                },
                "has_private_mortgage_insurance": {
                    "type": "boolean",
                    "description": "Does loan require private mortgage insurance",
                    "default": False
                },
                "property_taxes_annual": {
                    "type": "number",
                    "description": "Annual property taxes (optional)",
                    "minimum": 0.0
                },
                "homeowners_insurance_annual": {
                    "type": "number",
                    "description": "Annual homeowners insurance (optional)",
                    "minimum": 0.0
                },
                "hoa_fees_monthly": {
                    "type": "number",
                    "description": "Monthly HOA fees (optional)",
                    "minimum": 0.0,
                    "default": 0.0
                }
            },
            "required": [
                "loan_amount", "property_value", "loan_purpose", "occupancy_type",
                "credit_score", "debt_to_income_ratio", "liquid_reserves", "down_payment_percentage"
            ],
            "additionalProperties": False
        }
        
    async def _execute(self, **kwargs) -> ToolResult:
        """Execute loan terms calculation."""
        try:
            # Extract parameters
            loan_amount = kwargs.get("loan_amount")
            property_value = kwargs.get("property_value")
            loan_purpose = kwargs.get("loan_purpose")
            occupancy_type = kwargs.get("occupancy_type")
            credit_score = kwargs.get("credit_score")
            debt_to_income_ratio = kwargs.get("debt_to_income_ratio")
            liquid_reserves = kwargs.get("liquid_reserves")
            down_payment_percentage = kwargs.get("down_payment_percentage")
            loan_program = kwargs.get("loan_program")
            loan_type = kwargs.get("loan_type", "fixed")
            term_years = kwargs.get("term_years", 30)
            risk_grade = kwargs.get("risk_grade", "B")
            pricing_tier = kwargs.get("pricing_tier", "PRIME")
            base_rate = kwargs.get("base_rate")
            market_conditions = kwargs.get("market_conditions", "normal")
            first_time_buyer = kwargs.get("first_time_buyer", False)
            self_employed = kwargs.get("self_employed", False)
            has_private_mortgage_insurance = kwargs.get("has_private_mortgage_insurance", False)
            property_taxes_annual = kwargs.get("property_taxes_annual")
            homeowners_insurance_annual = kwargs.get("homeowners_insurance_annual")
            hoa_fees_monthly = kwargs.get("hoa_fees_monthly", 0.0)
            
            # Validate inputs
            if loan_amount <= 0 or property_value <= 0:
                raise ValueError("Loan amount and property value must be positive")
            if loan_amount > property_value:
                raise ValueError("Loan amount cannot exceed property value")
                
            # Simulate processing time
            await asyncio.sleep(0.3)
            
            # Perform loan terms calculation
            result = await self._calculate_loan_terms(
                loan_amount=loan_amount,
                property_value=property_value,
                loan_purpose=loan_purpose,
                occupancy_type=occupancy_type,
                credit_score=credit_score,
                debt_to_income_ratio=debt_to_income_ratio,
                liquid_reserves=liquid_reserves,
                down_payment_percentage=down_payment_percentage,
                loan_program=loan_program,
                loan_type=loan_type,
                term_years=term_years,
                risk_grade=risk_grade,
                pricing_tier=pricing_tier,
                base_rate=base_rate,
                market_conditions=market_conditions,
                first_time_buyer=first_time_buyer,
                self_employed=self_employed,
                has_private_mortgage_insurance=has_private_mortgage_insurance,
                property_taxes_annual=property_taxes_annual,
                homeowners_insurance_annual=homeowners_insurance_annual,
                hoa_fees_monthly=hoa_fees_monthly
            )
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result,
                execution_time=0.3
            )
            
        except Exception as e:
            self.logger.error(f"Loan terms calculation failed: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=f"Loan terms calculation failed: {str(e)}",
                execution_time=0.0
            )
            
    async def _calculate_loan_terms(self, **params) -> Dict[str, Any]:
        """Calculate comprehensive loan terms."""
        
        # 1. Product matching - determine optimal loan program if not specified
        product_matching = await self._match_loan_products(params)
        selected_program = params.get("loan_program") or product_matching.recommended_program
        
        # Update parameters with selected program
        params["loan_program"] = selected_program
        
        # 2. Calculate base rate and adjustments
        base_rate = params.get("base_rate") or self._get_base_rate(
            selected_program, params["term_years"], params["market_conditions"]
        )
        
        pricing_adjustments = self._calculate_pricing_adjustments(params)
        final_rate = max(0.01, base_rate + pricing_adjustments.total_adjustments)
        
        # 3. Calculate mortgage insurance
        mortgage_insurance = self._calculate_mortgage_insurance(params)
        
        # 4. Calculate fees and costs
        fees = self._calculate_fees(params)
        
        # 5. Calculate monthly payments
        monthly_pi = self._calculate_monthly_payment(
            params["loan_amount"], final_rate, params["term_years"]
        )
        
        payment_breakdown = self._calculate_payment_breakdown(
            params, monthly_pi, mortgage_insurance
        )
        
        # 6. Calculate APR
        apr = self._calculate_apr(
            params["loan_amount"], final_rate, fees.total_closing_costs, params["term_years"]
        )
        
        # 7. Generate alternatives
        alternatives = self._generate_alternatives(params, base_rate)
        
        # 8. Generate recommendations
        recommendations = self._generate_recommendations(params, final_rate, pricing_adjustments)
        
        # Compile results
        result = {
            "product_matching": {
                "recommended_program": product_matching.recommended_program,
                "eligibility_score": product_matching.eligibility_score,
                "alternative_programs": product_matching.alternative_programs,
                "matching_rationale": product_matching.matching_rationale
            },
            "selected_program": selected_program,
            "loan_terms": {
                "interest_rate": self._round_to_eighth(final_rate),
                "apr": round(apr, 3),
                "monthly_principal_and_interest": round(monthly_pi, 2),
                "total_monthly_payment": round(payment_breakdown.total_payment, 2),
                "loan_amount": params["loan_amount"],
                "term_years": params["term_years"],
                "ltv_ratio": round((params["loan_amount"] / params["property_value"]) * 100, 1),
                "origination_fee": fees.origination_fee,
                "processing_fee": fees.processing_fee,
                "underwriting_fee": fees.underwriting_fee,
                "appraisal_fee": fees.appraisal_fee,
                "credit_report_fee": fees.credit_report_fee,
                "total_closing_costs": fees.total_closing_costs,
                "mortgage_insurance": {
                    "monthly_premium": mortgage_insurance.monthly_premium,
                    "upfront_premium": mortgage_insurance.upfront_premium,
                    "type": mortgage_insurance.insurance_type,
                    "cancellation_threshold": mortgage_insurance.cancellation_threshold
                },
                "pricing_adjustments": {
                    "credit_score_adjustment": pricing_adjustments.credit_score_adjustment,
                    "ltv_adjustment": pricing_adjustments.ltv_adjustment,
                    "cash_out_adjustment": pricing_adjustments.cash_out_adjustment,
                    "occupancy_adjustment": pricing_adjustments.occupancy_adjustment,
                    "reserves_adjustment": pricing_adjustments.reserves_adjustment,
                    "debt_ratio_adjustment": pricing_adjustments.debt_ratio_adjustment,
                    "total_adjustments": pricing_adjustments.total_adjustments
                },
                "payment_breakdown": {
                    "principal_and_interest": payment_breakdown.principal_and_interest,
                    "property_taxes": payment_breakdown.property_taxes,
                    "homeowners_insurance": payment_breakdown.homeowners_insurance,
                    "mortgage_insurance": payment_breakdown.mortgage_insurance,
                    "hoa_fees": payment_breakdown.hoa_fees,
                    "total_payment": payment_breakdown.total_payment
                },
                "program_details": self._get_program_details(selected_program, params["loan_amount"])
            },
            "alternatives": alternatives,
            "pricing_rationale": {
                "base_rate": round(base_rate, 3),
                "risk_premium": round(pricing_adjustments.total_adjustments, 3),
                "market_premium": self._get_market_premium(params["market_conditions"]),
                "program_discount": self._get_program_discount(selected_program),
                "total_rate": self._round_to_eighth(final_rate),
                "key_factors": self._get_key_pricing_factors(params, pricing_adjustments)
            },
            "recommendations": recommendations,
            "calculation_date": datetime.now().isoformat(),
            "loan_summary": {
                "monthly_payment": round(payment_breakdown.total_payment, 2),
                "total_interest_paid": round(monthly_pi * params["term_years"] * 12 - params["loan_amount"], 2),
                "total_cost_of_loan": round(monthly_pi * params["term_years"] * 12 + fees.total_closing_costs, 2),
                "break_even_months": self._calculate_break_even_months(params, fees),
                "affordability_analysis": self._analyze_affordability(params, payment_breakdown)
            }
        }
        
        return result
        
    async def _match_loan_products(self, params: Dict[str, Any]) -> ProductMatching:
        """Match optimal loan products based on borrower profile."""
        
        loan_amount = params["loan_amount"]
        property_value = params["property_value"]
        credit_score = params["credit_score"]
        down_payment_pct = params["down_payment_percentage"]
        occupancy_type = params["occupancy_type"]
        first_time_buyer = params.get("first_time_buyer", False)
        
        ltv = loan_amount / property_value
        
        # Determine conforming loan limits (2025 limits)
        conforming_limit = 766550  # Base conforming limit
        high_cost_limit = 1149825  # High-cost area limit
        
        programs = []
        rationale = []
        
        # Conventional loan eligibility
        if loan_amount <= conforming_limit:
            eligibility_score = 80.0
            if credit_score >= 620:
                eligibility_score += 10.0
            if ltv <= 0.80:
                eligibility_score += 5.0
            if down_payment_pct >= 0.20:
                eligibility_score += 5.0
                
            programs.append({
                "program": LoanProgram.CONVENTIONAL.value,
                "eligibility_score": min(100.0, eligibility_score),
                "benefits": ["Competitive rates", "No upfront mortgage insurance if 20% down"],
                "requirements": ["Credit score 620+", "Standard debt ratios"]
            })
            
        # FHA loan eligibility
        if credit_score >= 580 and ltv <= 0.965:
            eligibility_score = 85.0
            if first_time_buyer:
                eligibility_score += 10.0
            if credit_score < 640:
                eligibility_score += 5.0  # Better for lower credit scores
                
            programs.append({
                "program": LoanProgram.FHA.value,
                "eligibility_score": min(100.0, eligibility_score),
                "benefits": ["Low down payment (3.5%)", "Flexible credit requirements"],
                "requirements": ["Credit score 580+", "Mortgage insurance required"]
            })
            
        # VA loan eligibility (assuming veteran status for demo)
        if occupancy_type == OccupancyType.PRIMARY.value:
            programs.append({
                "program": LoanProgram.VA.value,
                "eligibility_score": 95.0,
                "benefits": ["No down payment", "No mortgage insurance", "Competitive rates"],
                "requirements": ["Military service eligibility", "Primary residence only"]
            })
            
        # USDA loan eligibility
        if occupancy_type == OccupancyType.PRIMARY.value and property_value <= 500000:
            programs.append({
                "program": LoanProgram.USDA.value,
                "eligibility_score": 75.0,
                "benefits": ["No down payment", "Below-market rates"],
                "requirements": ["Rural/suburban location", "Income limits apply"]
            })
            
        # Jumbo loan eligibility
        if loan_amount > conforming_limit:
            eligibility_score = 70.0
            if credit_score >= 700:
                eligibility_score += 15.0
            if down_payment_pct >= 0.20:
                eligibility_score += 10.0
                
            programs.append({
                "program": LoanProgram.JUMBO.value,
                "eligibility_score": min(100.0, eligibility_score),
                "benefits": ["Higher loan amounts", "Competitive rates for qualified borrowers"],
                "requirements": ["Higher credit scores", "Larger down payments", "Lower debt ratios"]
            })
            
        # Sort programs by eligibility score
        programs.sort(key=lambda x: x["eligibility_score"], reverse=True)
        
        # Determine recommended program
        recommended_program = programs[0]["program"] if programs else LoanProgram.CONVENTIONAL.value
        
        # Generate rationale
        if recommended_program == LoanProgram.FHA.value:
            rationale.append("FHA recommended due to lower credit score or down payment requirements")
        elif recommended_program == LoanProgram.VA.value:
            rationale.append("VA loan offers best terms with no down payment and no mortgage insurance")
        elif recommended_program == LoanProgram.CONVENTIONAL.value:
            rationale.append("Conventional loan offers competitive terms for qualified borrower")
        elif recommended_program == LoanProgram.JUMBO.value:
            rationale.append("Jumbo loan required due to loan amount exceeding conforming limits")
            
        return ProductMatching(
            recommended_program=recommended_program,
            eligibility_score=programs[0]["eligibility_score"] if programs else 50.0,
            alternative_programs=programs[1:4],  # Top 3 alternatives
            matching_rationale=rationale
        )
        
    def _get_base_rate(self, program: str, term_years: int, market_conditions: str) -> float:
        """Get base interest rate for loan program and term."""
        
        # Base rates by program and term (2025 rates)
        base_rates = {
            LoanProgram.CONVENTIONAL.value: {15: 0.0625, 20: 0.0675, 30: 0.0725},
            LoanProgram.FHA.value: {15: 0.0600, 20: 0.0650, 30: 0.0700},
            LoanProgram.VA.value: {15: 0.0575, 20: 0.0625, 30: 0.0675},
            LoanProgram.USDA.value: {15: 0.0580, 20: 0.0630, 30: 0.0680},
            LoanProgram.JUMBO.value: {15: 0.0650, 20: 0.0700, 30: 0.0750}
        }
        
        rate = base_rates.get(program, {}).get(term_years, 0.0725)
        
        # Market condition adjustments
        market_adjustments = {
            MarketCondition.NORMAL.value: 0.0,
            MarketCondition.VOLATILE.value: 0.0025,
            MarketCondition.TIGHTENING.value: 0.005,
            MarketCondition.LOOSENING.value: -0.0025
        }
        
        rate += market_adjustments.get(market_conditions, 0.0)
        return rate
        
    def _calculate_pricing_adjustments(self, params: Dict[str, Any]) -> PricingAdjustments:
        """Calculate pricing adjustments based on risk factors."""
        
        credit_score = params["credit_score"]
        loan_amount = params["loan_amount"]
        property_value = params["property_value"]
        loan_purpose = params["loan_purpose"]
        occupancy_type = params["occupancy_type"]
        liquid_reserves = params["liquid_reserves"]
        debt_to_income_ratio = params["debt_to_income_ratio"]
        loan_program = params["loan_program"]
        
        ltv = loan_amount / property_value
        
        adjustments = PricingAdjustments()
        
        # Credit score adjustment
        adjustments.credit_score_adjustment = self._get_credit_score_adjustment(credit_score)
        
        # LTV adjustment
        adjustments.ltv_adjustment = self._get_ltv_adjustment(ltv, loan_program)
        
        # Cash-out refinance adjustment
        if loan_purpose == LoanPurpose.CASH_OUT_REFINANCE.value:
            adjustments.cash_out_adjustment = 0.0025
            
        # Occupancy adjustment
        adjustments.occupancy_adjustment = self._get_occupancy_adjustment(occupancy_type)
        
        # Reserves adjustment
        adjustments.reserves_adjustment = self._get_reserves_adjustment(liquid_reserves)
        
        # Debt ratio adjustment
        adjustments.debt_ratio_adjustment = self._get_debt_ratio_adjustment(debt_to_income_ratio)
        
        # Calculate total adjustments
        adjustments.total_adjustments = (
            adjustments.credit_score_adjustment +
            adjustments.ltv_adjustment +
            adjustments.cash_out_adjustment +
            adjustments.occupancy_adjustment +
            adjustments.reserves_adjustment +
            adjustments.debt_ratio_adjustment
        )
        
        return adjustments
        
    def _get_credit_score_adjustment(self, score: int) -> float:
        """Get credit score pricing adjustment."""
        if score >= 740:
            return -0.0025
        elif score >= 720:
            return 0.0
        elif score >= 700:
            return 0.0025
        elif score >= 680:
            return 0.005
        elif score >= 660:
            return 0.0075
        elif score >= 640:
            return 0.015
        elif score >= 620:
            return 0.025
        else:
            return 0.05
            
    def _get_ltv_adjustment(self, ltv: float, program: str) -> float:
        """Get LTV pricing adjustment."""
        ltv_percent = ltv * 100
        
        if program in [LoanProgram.FHA.value, LoanProgram.VA.value]:
            # Government programs have different LTV pricing
            if ltv_percent <= 80:
                return -0.0025
            elif ltv_percent <= 90:
                return 0.0
            elif ltv_percent <= 95:
                return 0.0025
            else:
                return 0.005
        else:
            # Conventional pricing
            if ltv_percent <= 60:
                return -0.005
            elif ltv_percent <= 70:
                return -0.0025
            elif ltv_percent <= 75:
                return 0.0
            elif ltv_percent <= 80:
                return 0.0025
            elif ltv_percent <= 85:
                return 0.01
            elif ltv_percent <= 90:
                return 0.015
            elif ltv_percent <= 95:
                return 0.025
            else:
                return 0.035
                
    def _get_occupancy_adjustment(self, occupancy: str) -> float:
        """Get occupancy pricing adjustment."""
        adjustments = {
            OccupancyType.PRIMARY.value: 0.0,
            OccupancyType.SECONDARY.value: 0.005,
            OccupancyType.INVESTMENT.value: 0.0075
        }
        return adjustments.get(occupancy, 0.0)
        
    def _get_reserves_adjustment(self, reserves: float) -> float:
        """Get reserves pricing adjustment."""
        if reserves >= 6:
            return -0.0025
        elif reserves >= 4:
            return 0.0
        elif reserves >= 2:
            return 0.0025
        else:
            return 0.005
            
    def _get_debt_ratio_adjustment(self, dti: float) -> float:
        """Get debt-to-income ratio pricing adjustment."""
        if dti <= 0.28:
            return -0.0025
        elif dti <= 0.36:
            return 0.0
        elif dti <= 0.43:
            return 0.0025
        elif dti <= 0.50:
            return 0.005
        else:
            return 0.01
            
    def _calculate_mortgage_insurance(self, params: Dict[str, Any]) -> MortgageInsurance:
        """Calculate mortgage insurance requirements."""
        
        loan_amount = params["loan_amount"]
        property_value = params["property_value"]
        loan_program = params["loan_program"]
        
        ltv = loan_amount / property_value
        
        if loan_program == LoanProgram.VA.value:
            return MortgageInsurance(
                monthly_premium=0.0,
                upfront_premium=loan_amount * 0.0228,  # VA funding fee
                insurance_type=MortgageInsuranceType.FUNDING_FEE.value
            )
            
        elif loan_program == LoanProgram.FHA.value:
            return MortgageInsurance(
                monthly_premium=(loan_amount * 0.0085) / 12,
                upfront_premium=loan_amount * 0.0175,
                insurance_type=MortgageInsuranceType.MIP.value
            )
            
        elif loan_program == LoanProgram.CONVENTIONAL.value and ltv > 0.80:
            if ltv > 0.95:
                rate = 0.0058
            elif ltv > 0.90:
                rate = 0.0052
            else:
                rate = 0.0045
                
            return MortgageInsurance(
                monthly_premium=(loan_amount * rate) / 12,
                upfront_premium=0.0,
                insurance_type=MortgageInsuranceType.PMI.value,
                cancellation_threshold=0.78
            )
            
        return MortgageInsurance()
        
    def _calculate_fees(self, params: Dict[str, Any]) -> LoanFees:
        """Calculate loan fees and closing costs."""
        
        loan_amount = params["loan_amount"]
        property_value = params["property_value"]
        
        fees = LoanFees()
        fees.origination_fee = min(loan_amount * 0.01, 5000)  # 1% or $5000 max
        fees.processing_fee = 450.0
        fees.underwriting_fee = 850.0
        fees.appraisal_fee = 750.0 if property_value > 1000000 else 500.0
        fees.credit_report_fee = 75.0
        
        fees.total_closing_costs = (
            fees.origination_fee + fees.processing_fee + fees.underwriting_fee +
            fees.appraisal_fee + fees.credit_report_fee
        )
        
        return fees
        
    def _calculate_monthly_payment(self, loan_amount: float, annual_rate: float, term_years: int) -> float:
        """Calculate monthly principal and interest payment."""
        
        monthly_rate = annual_rate / 12
        num_payments = term_years * 12
        
        if monthly_rate == 0:
            return loan_amount / num_payments
            
        return loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
    def _calculate_payment_breakdown(
        self, params: Dict[str, Any], monthly_pi: float, mortgage_insurance: MortgageInsurance
    ) -> PaymentBreakdown:
        """Calculate detailed monthly payment breakdown."""
        
        property_value = params["property_value"]
        property_taxes_annual = params.get("property_taxes_annual")
        homeowners_insurance_annual = params.get("homeowners_insurance_annual")
        hoa_fees_monthly = params.get("hoa_fees_monthly", 0.0)
        
        # Estimate property taxes if not provided (1.25% annually)
        if property_taxes_annual is None:
            property_taxes_annual = property_value * 0.0125
            
        # Estimate homeowners insurance if not provided (0.35% annually)
        if homeowners_insurance_annual is None:
            homeowners_insurance_annual = property_value * 0.0035
            
        breakdown = PaymentBreakdown()
        breakdown.principal_and_interest = monthly_pi
        breakdown.property_taxes = property_taxes_annual / 12
        breakdown.homeowners_insurance = homeowners_insurance_annual / 12
        breakdown.mortgage_insurance = mortgage_insurance.monthly_premium
        breakdown.hoa_fees = hoa_fees_monthly
        
        breakdown.total_payment = (
            breakdown.principal_and_interest + breakdown.property_taxes +
            breakdown.homeowners_insurance + breakdown.mortgage_insurance + breakdown.hoa_fees
        )
        
        return breakdown
        
    def _calculate_apr(self, loan_amount: float, interest_rate: float, closing_costs: float, term_years: int) -> float:
        """Calculate Annual Percentage Rate (APR)."""
        
        # Simplified APR calculation
        # In practice, this would be more complex with exact timing of fees
        monthly_rate = interest_rate / 12
        num_payments = term_years * 12
        
        # Effective loan amount after closing costs
        effective_loan_amount = loan_amount - closing_costs
        
        # Monthly payment based on full loan amount
        monthly_payment = self._calculate_monthly_payment(loan_amount, interest_rate, term_years)
        
        # Calculate APR using iterative method (simplified)
        # This is an approximation - real APR calculation is more complex
        apr_estimate = interest_rate + (closing_costs / loan_amount) / term_years
        
        return apr_estimate
        
    def _generate_alternatives(self, params: Dict[str, Any], base_rate: float) -> List[Dict[str, Any]]:
        """Generate alternative loan scenarios."""
        
        alternatives = []
        current_term = params["term_years"]
        loan_amount = params["loan_amount"]
        
        # Alternative terms
        for term in [15, 20, 30]:
            if term != current_term:
                alt_rate = self._get_base_rate(params["loan_program"], term, params["market_conditions"])
                alt_payment = self._calculate_monthly_payment(loan_amount, alt_rate, term)
                
                alternatives.append({
                    "scenario": f"{term}-year term",
                    "term_years": term,
                    "interest_rate": self._round_to_eighth(alt_rate),
                    "monthly_payment": round(alt_payment, 2),
                    "total_interest": round(alt_payment * term * 12 - loan_amount, 2),
                    "benefits": self._get_term_benefits(term, current_term),
                    "considerations": self._get_term_considerations(term, current_term)
                })
                
        # Alternative programs (if not already selected)
        current_program = params["loan_program"]
        for program in [LoanProgram.CONVENTIONAL.value, LoanProgram.FHA.value]:
            if program != current_program:
                alt_params = params.copy()
                alt_params["loan_program"] = program
                alt_rate = self._get_base_rate(program, current_term, params["market_conditions"])
                alt_adjustments = self._calculate_pricing_adjustments(alt_params)
                final_alt_rate = alt_rate + alt_adjustments.total_adjustments
                alt_payment = self._calculate_monthly_payment(loan_amount, final_alt_rate, current_term)
                
                alternatives.append({
                    "scenario": f"{program.upper()} loan",
                    "loan_program": program,
                    "interest_rate": self._round_to_eighth(final_alt_rate),
                    "monthly_payment": round(alt_payment, 2),
                    "benefits": self._get_program_benefits(program),
                    "considerations": self._get_program_considerations(program)
                })
                
        return alternatives[:4]  # Return top 4 alternatives
        
    def _generate_recommendations(
        self, params: Dict[str, Any], final_rate: float, pricing_adjustments: PricingAdjustments
    ) -> Dict[str, Any]:
        """Generate recommendations based on loan analysis."""
        
        recommendations = {
            "rate_improvement_opportunities": [],
            "cost_savings_strategies": [],
            "risk_mitigation_suggestions": [],
            "timing_considerations": []
        }
        
        # Rate improvement opportunities
        if pricing_adjustments.credit_score_adjustment > 0:
            recommendations["rate_improvement_opportunities"].append(
                "Improve credit score to qualify for better rates"
            )
            
        if pricing_adjustments.ltv_adjustment > 0.005:
            recommendations["rate_improvement_opportunities"].append(
                "Consider larger down payment to reduce LTV and improve pricing"
            )
            
        if pricing_adjustments.reserves_adjustment > 0:
            recommendations["rate_improvement_opportunities"].append(
                "Increase liquid reserves to improve loan terms"
            )
            
        # Cost savings strategies
        if params["term_years"] == 30:
            recommendations["cost_savings_strategies"].append(
                "Consider 15-year term to save significantly on total interest"
            )
            
        recommendations["cost_savings_strategies"].append(
            "Shop multiple lenders to compare rates and fees"
        )
        
        # Risk mitigation
        if params["debt_to_income_ratio"] > 0.43:
            recommendations["risk_mitigation_suggestions"].append(
                "Consider reducing debt-to-income ratio before applying"
            )
            
        # Timing considerations
        if params["market_conditions"] == MarketCondition.VOLATILE.value:
            recommendations["timing_considerations"].append(
                "Consider rate lock due to volatile market conditions"
            )
            
        return recommendations
        
    def _get_program_details(self, program: str, loan_amount: float) -> Dict[str, Any]:
        """Get detailed program information."""
        
        details = {
            "program_name": program.upper(),
            "loan_limits": {},
            "down_payment_requirements": {},
            "credit_requirements": {},
            "special_features": []
        }
        
        if program == LoanProgram.CONVENTIONAL.value:
            details.update({
                "loan_limits": {"conforming": 766550, "high_cost": 1149825},
                "down_payment_requirements": {"minimum": "3%", "no_pmi": "20%"},
                "credit_requirements": {"minimum": 620, "preferred": 740},
                "special_features": ["No upfront mortgage insurance with 20% down", "Competitive rates"]
            })
        elif program == LoanProgram.FHA.value:
            details.update({
                "loan_limits": {"standard": 472030, "high_cost": 1089300},
                "down_payment_requirements": {"minimum": "3.5%"},
                "credit_requirements": {"minimum": 580, "with_10_percent_down": 500},
                "special_features": ["Low down payment", "Flexible credit requirements", "Assumable loans"]
            })
        elif program == LoanProgram.VA.value:
            details.update({
                "loan_limits": {"no_limit": "Based on entitlement"},
                "down_payment_requirements": {"minimum": "0%"},
                "credit_requirements": {"minimum": "Varies by lender"},
                "special_features": ["No down payment", "No mortgage insurance", "No prepayment penalty"]
            })
            
        return details
        
    def _round_to_eighth(self, rate: float) -> float:
        """Round rate to nearest eighth (0.125%)."""
        return round(rate * 8) / 8
        
    def _get_market_premium(self, market_conditions: str) -> float:
        """Get market premium for current conditions."""
        premiums = {
            MarketCondition.NORMAL.value: 0.0,
            MarketCondition.VOLATILE.value: 0.0025,
            MarketCondition.TIGHTENING.value: 0.005,
            MarketCondition.LOOSENING.value: -0.0025
        }
        return premiums.get(market_conditions, 0.0)
        
    def _get_program_discount(self, program: str) -> float:
        """Get program-specific discount."""
        discounts = {
            LoanProgram.VA.value: -0.0025,
            LoanProgram.USDA.value: -0.0025,
            LoanProgram.FHA.value: -0.001,
            LoanProgram.CONVENTIONAL.value: 0.0,
            LoanProgram.JUMBO.value: 0.0025
        }
        return discounts.get(program, 0.0)
        
    def _get_key_pricing_factors(self, params: Dict[str, Any], adjustments: PricingAdjustments) -> List[str]:
        """Get key factors affecting pricing."""
        
        factors = []
        
        if abs(adjustments.credit_score_adjustment) >= 0.005:
            factors.append(f"Credit score ({params['credit_score']})")
            
        ltv = params["loan_amount"] / params["property_value"]
        if abs(adjustments.ltv_adjustment) >= 0.005:
            factors.append(f"Loan-to-value ratio ({ltv:.1%})")
            
        if adjustments.occupancy_adjustment > 0:
            factors.append(f"Occupancy type ({params['occupancy_type']})")
            
        if adjustments.debt_ratio_adjustment > 0:
            factors.append(f"Debt-to-income ratio ({params['debt_to_income_ratio']:.1%})")
            
        return factors
        
    def _get_term_benefits(self, alt_term: int, current_term: int) -> List[str]:
        """Get benefits of alternative term."""
        if alt_term < current_term:
            return ["Lower total interest paid", "Build equity faster", "Debt-free sooner"]
        else:
            return ["Lower monthly payment", "More cash flow flexibility"]
            
    def _get_term_considerations(self, alt_term: int, current_term: int) -> List[str]:
        """Get considerations for alternative term."""
        if alt_term < current_term:
            return ["Higher monthly payment", "Less cash flow flexibility"]
        else:
            return ["Higher total interest paid", "Longer debt commitment"]
            
    def _get_program_benefits(self, program: str) -> List[str]:
        """Get benefits of loan program."""
        benefits = {
            LoanProgram.CONVENTIONAL.value: ["Competitive rates", "No upfront MI with 20% down"],
            LoanProgram.FHA.value: ["Low down payment", "Flexible credit requirements"],
            LoanProgram.VA.value: ["No down payment", "No mortgage insurance"],
            LoanProgram.USDA.value: ["No down payment", "Below-market rates"]
        }
        return benefits.get(program, [])
        
    def _get_program_considerations(self, program: str) -> List[str]:
        """Get considerations for loan program."""
        considerations = {
            LoanProgram.CONVENTIONAL.value: ["Higher down payment for best terms"],
            LoanProgram.FHA.value: ["Mortgage insurance required", "Loan limits apply"],
            LoanProgram.VA.value: ["Military service required", "Funding fee applies"],
            LoanProgram.USDA.value: ["Geographic restrictions", "Income limits apply"]
        }
        return considerations.get(program, [])
        
    def _calculate_break_even_months(self, params: Dict[str, Any], fees: LoanFees) -> Optional[int]:
        """Calculate break-even months for refinance scenarios."""
        if params["loan_purpose"] != LoanPurpose.REFINANCE.value:
            return None
            
        # Simplified break-even calculation
        # Would need current payment info for accurate calculation
        monthly_savings = 200  # Mock savings
        if monthly_savings > 0:
            return int(fees.total_closing_costs / monthly_savings)
        return None
        
    def _analyze_affordability(self, params: Dict[str, Any], payment_breakdown: PaymentBreakdown) -> Dict[str, Any]:
        """Analyze loan affordability."""
        
        # Mock income calculation based on DTI
        estimated_monthly_income = params["loan_amount"] * 0.0001  # Rough estimate
        
        payment_to_income_ratio = payment_breakdown.total_payment / estimated_monthly_income if estimated_monthly_income > 0 else 0
        
        return {
            "payment_to_income_ratio": round(payment_to_income_ratio, 3),
            "affordability_rating": "comfortable" if payment_to_income_ratio < 0.28 else "moderate" if payment_to_income_ratio < 0.36 else "stretched",
            "recommended_income": round(payment_breakdown.total_payment / 0.28, 0),
            "stress_test_payment": round(payment_breakdown.total_payment * 1.02, 2)  # 2% rate increase
        }
        
    def get_tool_info(self) -> Dict[str, Any]:
        """Get comprehensive tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.metadata.version,
            "loan_programs": [program.value for program in LoanProgram],
            "loan_purposes": [purpose.value for purpose in LoanPurpose],
            "occupancy_types": [occ.value for occ in OccupancyType],
            "loan_types": [loan_type.value for loan_type in LoanType],
            "term_options": [15, 20, 30],
            "features": {
                "automatic_product_matching": True,
                "pricing_adjustments": True,
                "mortgage_insurance_calculation": True,
                "fee_calculation": True,
                "apr_calculation": True,
                "payment_breakdown": True,
                "alternative_scenarios": True,
                "recommendations": True,
                "affordability_analysis": True
            },
            "pricing_factors": [
                "credit_score",
                "loan_to_value_ratio",
                "debt_to_income_ratio",
                "occupancy_type",
                "liquid_reserves",
                "loan_purpose",
                "market_conditions"
            ],
            "parameters_schema": self.get_parameters_schema()
        }