"""
Enhanced Income Calculator Tool - Comprehensive mortgage income calculation.

Converted from TypeScript FSI Tools framework to Python.
Implements mortgage lending guidelines for income calculation with DTI analysis.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field

from ..base import BaseTool, ToolResult, ToolCategory
from ...models.enums import LoanType


class IncomeSourceType(Enum):
    """Income source types following mortgage lending guidelines."""
    BASE_SALARY = "base_salary"
    HOURLY_WAGES = "hourly_wages"
    OVERTIME = "overtime"
    BONUS = "bonus"
    COMMISSION = "commission"
    SELF_EMPLOYMENT = "self_employment"
    RENTAL_INCOME = "rental_income"
    INVESTMENT_INCOME = "investment_income"
    PENSION = "pension"
    SOCIAL_SECURITY = "social_security"
    DISABILITY = "disability"
    UNEMPLOYMENT = "unemployment"
    CHILD_SUPPORT = "child_support"
    ALIMONY = "alimony"
    OTHER = "other"


class DebtType(Enum):
    """Debt types for DTI calculation."""
    PROPOSED_MORTGAGE = "proposed_mortgage"
    EXISTING_MORTGAGE = "existing_mortgage"
    CREDIT_CARD = "credit_card"
    AUTO_LOAN = "auto_loan"
    STUDENT_LOAN = "student_loan"
    PERSONAL_LOAN = "personal_loan"
    CHILD_SUPPORT_OBLIGATION = "child_support_obligation"
    ALIMONY_OBLIGATION = "alimony_obligation"
    OTHER_MONTHLY_DEBT = "other_monthly_debt"


class LoanProgram(Enum):
    """Mortgage loan programs with different DTI requirements."""
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    USDA = "usda"
    JUMBO = "jumbo"
    NON_QM = "non_qm"


@dataclass
class IncomeSource:
    """Individual income source with detailed attributes."""
    source_type: IncomeSourceType
    monthly_amount: Decimal
    annual_amount: Decimal
    frequency: str  # weekly, bi_weekly, semi_monthly, monthly, quarterly, annually
    employer_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_continuing: bool = True
    is_variable: bool = False
    stability_months: int = 0
    year_over_year_change: Optional[float] = None
    documentation_quality: str = "good"  # excellent, good, fair, poor
    verification_source: str = "paystub"  # paystub, w2, tax_return, bank_statement, voe, other
    notes: Optional[str] = None


@dataclass
class DebtObligation:
    """Monthly debt obligation details."""
    debt_type: DebtType
    creditor_name: str
    monthly_payment: Decimal
    current_balance: Decimal
    remaining_months: Optional[int] = None
    interest_rate: Optional[float] = None
    is_revolving: bool = False
    notes: Optional[str] = None


class EnhancedIncomeCalculatorTool(BaseTool):
    """
    Enhanced Income Calculator Tool for mortgage lending.
    
    Features:
    - Multi-source income aggregation and qualification
    - DTI (Debt-to-Income) ratio calculations
    - Mortgage lending rule compliance (Fannie Mae, Freddie Mac, FHA)
    - Variable income averaging and stability analysis
    - Self-employment income qualification
    - Bonus/commission income treatment
    """
    
    def __init__(self):
        super().__init__(
            name="enhanced_income_calculator",
            description="Calculate qualified income for mortgage lending with comprehensive DTI analysis and loan program compliance",
            category=ToolCategory.FINANCIAL_ANALYSIS,
            version="1.0.0",
            agent_domain="income_verification"
        )    
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for income calculation parameters."""
        return {
            "type": "object",
            "required": ["borrower_name", "income_sources", "debt_obligations", "proposed_housing_payment", "loan_program"],
            "properties": {
                "borrower_name": {
                    "type": "string",
                    "description": "Name of the borrower"
                },
                "income_sources": {
                    "type": "array",
                    "description": "Array of income sources for qualification",
                    "items": {
                        "type": "object",
                        "required": ["source_type", "monthly_amount", "annual_amount", "frequency", "is_continuing"],
                        "properties": {
                            "source_type": {
                                "type": "string",
                                "enum": [e.value for e in IncomeSourceType],
                                "description": "Type of income source"
                            },
                            "employer_name": {
                                "type": "string",
                                "description": "Name of employer or income source"
                            },
                            "monthly_amount": {
                                "type": "number",
                                "description": "Monthly income amount"
                            },
                            "annual_amount": {
                                "type": "number", 
                                "description": "Annual income amount"
                            },
                            "frequency": {
                                "type": "string",
                                "enum": ["weekly", "bi_weekly", "semi_monthly", "monthly", "quarterly", "annually"],
                                "description": "Payment frequency"
                            },
                            "is_continuing": {
                                "type": "boolean",
                                "description": "Whether income will continue"
                            },
                            "is_variable": {
                                "type": "boolean",
                                "description": "Whether income amount varies"
                            },
                            "stability_months": {
                                "type": "number",
                                "description": "Months of income stability/history"
                            },
                            "year_over_year_change": {
                                "type": "number",
                                "description": "Year over year change percentage"
                            },
                            "documentation_quality": {
                                "type": "string",
                                "enum": ["excellent", "good", "fair", "poor"],
                                "description": "Quality of income documentation"
                            }
                        }
                    }
                },
                "debt_obligations": {
                    "type": "array",
                    "description": "Array of monthly debt obligations",
                    "items": {
                        "type": "object",
                        "required": ["debt_type", "creditor_name", "monthly_payment", "current_balance", "is_revolving"],
                        "properties": {
                            "debt_type": {
                                "type": "string",
                                "enum": [e.value for e in DebtType],
                                "description": "Type of debt obligation"
                            },
                            "creditor_name": {
                                "type": "string",
                                "description": "Name of creditor"
                            },
                            "monthly_payment": {
                                "type": "number",
                                "description": "Monthly payment amount"
                            },
                            "current_balance": {
                                "type": "number",
                                "description": "Current outstanding balance"
                            },
                            "remaining_months": {
                                "type": "number",
                                "description": "Remaining months if installment debt"
                            },
                            "is_revolving": {
                                "type": "boolean",
                                "description": "Whether debt is revolving (credit card)"
                            }
                        }
                    }
                },
                "proposed_housing_payment": {
                    "type": "number",
                    "description": "Proposed total housing payment (PITI)"
                },
                "loan_program": {
                    "type": "string",
                    "enum": [e.value for e in LoanProgram],
                    "description": "Type of mortgage loan program"
                },
                "loan_amount": {
                    "type": "number",
                    "description": "Requested loan amount"
                },
                "property_value": {
                    "type": "number",
                    "description": "Property purchase price or appraised value"
                },
                "calculation_method": {
                    "type": "string",
                    "enum": ["conservative", "aggressive", "standard"],
                    "description": "Income calculation approach",
                    "default": "standard"
                }
            }
        }
        
    def _get_dti_limits(self, loan_program: LoanProgram) -> Dict[str, Any]:
        """Get DTI limits for specific loan program."""
        limits = {
            LoanProgram.CONVENTIONAL: {
                "front_end_max": 28,
                "back_end_max": 36,
                "compensating_factors_available": True
            },
            LoanProgram.FHA: {
                "front_end_max": 31,
                "back_end_max": 43,
                "compensating_factors_available": True
            },
            LoanProgram.VA: {
                "front_end_max": 100,  # VA doesn't have front-end ratio requirement
                "back_end_max": 41,
                "compensating_factors_available": True
            },
            LoanProgram.USDA: {
                "front_end_max": 29,
                "back_end_max": 41,
                "compensating_factors_available": True
            },
            LoanProgram.JUMBO: {
                "front_end_max": 28,
                "back_end_max": 36,
                "compensating_factors_available": False
            },
            LoanProgram.NON_QM: {
                "front_end_max": 50,
                "back_end_max": 50,
                "compensating_factors_available": False
            }
        }
        return limits.get(loan_program, limits[LoanProgram.CONVENTIONAL])

    def _calculate_qualified_income(self, income_sources: List[IncomeSource], calculation_method: str) -> Dict[str, Any]:
        """Calculate qualified income from all sources."""
        base_income = Decimal('0')
        variable_income = Decimal('0')
        other_income = Decimal('0')
        excluded_income = Decimal('0')
        exclusion_reasons = []
        averaging_applied = False
        
        for source in income_sources:
            qualified_amount = Decimal('0')
            include_income = True
            
            # Check income stability requirements
            if source.stability_months < 12 and source.source_type != IncomeSourceType.UNEMPLOYMENT:
                if calculation_method == "conservative":
                    include_income = False
                    exclusion_reasons.append(f"{source.source_type.value}: Less than 12 months stability")
                elif source.stability_months < 6:
                    include_income = False
                    exclusion_reasons.append(f"{source.source_type.value}: Less than 6 months stability")
            
            # Check if income is continuing
            if not source.is_continuing:
                include_income = False
                exclusion_reasons.append(f"{source.source_type.value}: Income not continuing")
            
            # Handle variable income with averaging
            if source.is_variable and include_income:
                averaging_applied = True
                if source.year_over_year_change and source.year_over_year_change < -10:
                    # Declining income - use conservative approach
                    qualified_amount = source.monthly_amount * Decimal('0.75')
                else:
                    qualified_amount = source.monthly_amount
            elif include_income:
                qualified_amount = source.monthly_amount
            
            # Apply documentation quality adjustments
            if include_income and source.documentation_quality == "poor":
                if calculation_method == "conservative":
                    qualified_amount *= Decimal('0.8')
            
            # Categorize income by type
            if include_income:
                if source.source_type in [IncomeSourceType.BASE_SALARY, IncomeSourceType.HOURLY_WAGES]:
                    base_income += qualified_amount
                elif source.source_type in [IncomeSourceType.OVERTIME, IncomeSourceType.BONUS, 
                                          IncomeSourceType.COMMISSION, IncomeSourceType.SELF_EMPLOYMENT]:
                    variable_income += qualified_amount
                else:
                    other_income += qualified_amount
            else:
                excluded_income += source.monthly_amount
        
        return {
            "base_income": float(base_income),
            "variable_income": float(variable_income),
            "other_income": float(other_income),
            "total_qualified_income": float(base_income + variable_income + other_income),
            "excluded_income": float(excluded_income),
            "exclusion_reasons": exclusion_reasons,
            "averaging_applied": averaging_applied
        }    
        
    def _calculate_dti_analysis(self, qualified_income: float, debt_obligations: List[DebtObligation], 
                               proposed_housing_payment: float, dti_limits: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate DTI ratios and compliance analysis."""
        total_monthly_debts = Decimal('0')
        
        for debt in debt_obligations:
            # Exclude proposed mortgage from debt calculation
            if debt.debt_type == DebtType.PROPOSED_MORTGAGE:
                continue
            
            # For installment debts with less than 10 months remaining, may exclude from DTI
            if not debt.is_revolving and debt.remaining_months and debt.remaining_months <= 10:
                continue  # Exclude short-term debts
            
            total_monthly_debts += debt.monthly_payment
        
        qualified_income_decimal = Decimal(str(qualified_income))
        proposed_housing_decimal = Decimal(str(proposed_housing_payment))
        
        front_end_ratio = float((proposed_housing_decimal / qualified_income_decimal) * 100)
        back_end_ratio = float(((proposed_housing_decimal + total_monthly_debts) / qualified_income_decimal) * 100)
        
        front_end_compliant = front_end_ratio <= dti_limits["front_end_max"]
        back_end_compliant = back_end_ratio <= dti_limits["back_end_max"]
        
        available_income = float(qualified_income_decimal - proposed_housing_decimal - total_monthly_debts)
        
        # Identify compensating factors
        compensating_factors = []
        if available_income > qualified_income * 0.3:
            compensating_factors.append("High residual income after housing and debt payments")
        if qualified_income > 75000:
            compensating_factors.append("High income level")
        
        # Generate recommendations
        recommendations = []
        if not front_end_compliant:
            reduction = float(proposed_housing_decimal - (qualified_income_decimal * Decimal(str(dti_limits["front_end_max"])) / 100))
            recommendations.append(f"Reduce housing payment by ${reduction:.2f} to meet front-end DTI")
        if not back_end_compliant:
            reduction = float((proposed_housing_decimal + total_monthly_debts) - (qualified_income_decimal * Decimal(str(dti_limits["back_end_max"])) / 100))
            recommendations.append(f"Reduce total debt payments by ${reduction:.2f} to meet back-end DTI")
        
        return {
            "monthly_gross_income": qualified_income,
            "total_monthly_debts": float(total_monthly_debts),
            "proposed_housing_payment": proposed_housing_payment,
            "front_end_ratio": round(front_end_ratio, 2),
            "back_end_ratio": round(back_end_ratio, 2),
            "front_end_limit": dti_limits["front_end_max"],
            "back_end_limit": dti_limits["back_end_max"],
            "front_end_compliant": front_end_compliant,
            "back_end_compliant": back_end_compliant,
            "available_income": available_income,
            "compensating_factors": compensating_factors,
            "recommendations": recommendations
        }
        
    def _assess_income_stability(self, income_sources: List[IncomeSource]) -> Dict[str, Any]:
        """Assess income stability and risk factors."""
        stability_score = 100
        stability_factors = []
        risk_factors = []
        
        for source in income_sources:
            # Check employment tenure
            if source.stability_months >= 24:
                stability_factors.append(f"{source.source_type.value}: 2+ years employment history")
            elif source.stability_months < 12:
                stability_score -= 15
                risk_factors.append(f"{source.source_type.value}: Less than 12 months employment")
            
            # Check income trend
            if source.year_over_year_change:
                if source.year_over_year_change > 10:
                    stability_factors.append(f"{source.source_type.value}: Growing income trend (+{source.year_over_year_change}%)")
                elif source.year_over_year_change < -10:
                    stability_score -= 20
                    risk_factors.append(f"{source.source_type.value}: Declining income trend ({source.year_over_year_change}%)")
            
            # Check income type risk
            if source.is_variable:
                stability_score -= 10
                risk_factors.append(f"{source.source_type.value}: Variable income source")
            
            if source.source_type == IncomeSourceType.SELF_EMPLOYMENT:
                stability_score -= 15
                risk_factors.append("Self-employment income carries higher risk")
            
            # Check documentation quality
            if source.documentation_quality == "excellent":
                stability_factors.append(f"{source.source_type.value}: Excellent documentation quality")
            elif source.documentation_quality == "poor":
                stability_score -= 10
                risk_factors.append(f"{source.source_type.value}: Poor documentation quality")
        
        # Determine risk level
        if stability_score >= 80:
            risk_level = "low"
        elif stability_score >= 60:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "score": max(0, stability_score),
            "risk_level": risk_level,
            "stability_factors": stability_factors,
            "risk_factors": risk_factors
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute income calculation with comprehensive analysis."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting income calculation for borrower: {kwargs.get('borrower_name', 'Unknown')}")
            
            # Extract parameters
            borrower_name = kwargs.get("borrower_name")
            income_sources_data = kwargs.get("income_sources", [])
            debt_obligations_data = kwargs.get("debt_obligations", [])
            proposed_housing_payment = float(kwargs.get("proposed_housing_payment", 0))
            loan_program_str = kwargs.get("loan_program", "conventional")
            calculation_method = kwargs.get("calculation_method", "standard")
            
            # Convert to enum
            try:
                loan_program = LoanProgram(loan_program_str)
            except ValueError:
                loan_program = LoanProgram.CONVENTIONAL
            
            # Convert income sources
            income_sources = []
            for source_data in income_sources_data:
                try:
                    source = IncomeSource(
                        source_type=IncomeSourceType(source_data.get("source_type", "base_salary")),
                        monthly_amount=Decimal(str(source_data.get("monthly_amount", 0))),
                        annual_amount=Decimal(str(source_data.get("annual_amount", 0))),
                        frequency=source_data.get("frequency", "monthly"),
                        employer_name=source_data.get("employer_name"),
                        is_continuing=source_data.get("is_continuing", True),
                        is_variable=source_data.get("is_variable", False),
                        stability_months=source_data.get("stability_months", 12),
                        year_over_year_change=source_data.get("year_over_year_change"),
                        documentation_quality=source_data.get("documentation_quality", "good"),
                        verification_source=source_data.get("verification_source", "paystub")
                    )
                    income_sources.append(source)
                except Exception as e:
                    self.logger.warning(f"Error processing income source: {e}")
                    continue
            
            # Convert debt obligations
            debt_obligations = []
            for debt_data in debt_obligations_data:
                try:
                    debt = DebtObligation(
                        debt_type=DebtType(debt_data.get("debt_type", "credit_card")),
                        creditor_name=debt_data.get("creditor_name", "Unknown"),
                        monthly_payment=Decimal(str(debt_data.get("monthly_payment", 0))),
                        current_balance=Decimal(str(debt_data.get("current_balance", 0))),
                        remaining_months=debt_data.get("remaining_months"),
                        interest_rate=debt_data.get("interest_rate"),
                        is_revolving=debt_data.get("is_revolving", False)
                    )
                    debt_obligations.append(debt)
                except Exception as e:
                    self.logger.warning(f"Error processing debt obligation: {e}")
                    continue
            
            # Get DTI limits for loan program
            dti_limits = self._get_dti_limits(loan_program)
            
            # Calculate qualified income
            qualified_income = self._calculate_qualified_income(income_sources, calculation_method)
            
            # Calculate DTI analysis
            dti_analysis = self._calculate_dti_analysis(
                qualified_income["total_qualified_income"],
                debt_obligations,
                proposed_housing_payment,
                dti_limits
            )
            
            # Assess income stability
            stability_assessment = self._assess_income_stability(income_sources)
            
            # Check loan program compliance
            program_compliant = dti_analysis["front_end_compliant"] and dti_analysis["back_end_compliant"]
            issues = []
            recommendations = []
            
            if not program_compliant:
                if not dti_analysis["front_end_compliant"]:
                    issues.append(f"Front-end DTI {dti_analysis['front_end_ratio']}% exceeds {dti_limits['front_end_max']}% limit")
                if not dti_analysis["back_end_compliant"]:
                    issues.append(f"Back-end DTI {dti_analysis['back_end_ratio']}% exceeds {dti_limits['back_end_max']}% limit")
                
                if dti_limits["compensating_factors_available"] and dti_analysis["compensating_factors"]:
                    recommendations.append("Consider compensating factors for DTI exceptions")
                    recommendations.extend(dti_analysis["compensating_factors"])
            
            # Calculate confidence level
            confidence_level = 85
            if stability_assessment["risk_level"] == "high":
                confidence_level -= 20
            elif stability_assessment["risk_level"] == "medium":
                confidence_level -= 10
            if qualified_income["excluded_income"] > 0:
                confidence_level -= 5
            if not program_compliant:
                confidence_level -= 15
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Compile results
            result_data = {
                "borrower_name": borrower_name,
                "qualified_income": qualified_income,
                "dti_analysis": dti_analysis,
                "loan_program_compliance": {
                    "program": loan_program.value,
                    "compliant": program_compliant,
                    "issues": issues,
                    "recommendations": recommendations
                },
                "income_stability_assessment": stability_assessment,
                "calculation_summary": {
                    "calculation_date": datetime.now().isoformat(),
                    "method_used": calculation_method,
                    "confidence_level": max(0, confidence_level),
                    "processing_time_seconds": processing_time,
                    "reviewer_notes": [
                        f"Qualified income: ${qualified_income['total_qualified_income']:,.2f}/month",
                        f"Front-end DTI: {dti_analysis['front_end_ratio']}%",
                        f"Back-end DTI: {dti_analysis['back_end_ratio']}%",
                        f"Income stability: {stability_assessment['risk_level']} risk"
                    ]
                }
            }
            
            self.logger.info(f"Income calculation completed successfully for {borrower_name}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data,
                execution_time=processing_time,
                metadata={
                    "confidence": confidence_level / 100,
                    "source": "enhanced_income_calculator_v1.0.0",
                    "loan_program": loan_program.value,
                    "program_compliant": program_compliant
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Income calculation failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg,
                execution_time=processing_time,
                metadata={
                    "source": "enhanced_income_calculator_v1.0.0",
                    "error_type": "calculation_error"
                }
            )