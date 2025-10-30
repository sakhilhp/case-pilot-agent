"""
Debt-to-Income Calculator Tool for mortgage processing.

This tool performs detailed DTI analysis separate from income calculations,
including debt categorization, analysis capabilities, and comprehensive DTI calculations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import statistics

from ..base import BaseTool, ToolResult


class DebtToIncomeCalculatorTool(BaseTool):
    """
    Tool for calculating detailed debt-to-income ratios for mortgage applications.
    
    This tool performs comprehensive DTI analysis including:
    - Total debt-to-income ratio calculation
    - Housing debt-to-income ratio calculation
    - Debt categorization and analysis
    - Monthly payment calculations
    - DTI compliance checking for various loan programs
    - Risk assessment based on DTI levels
    """
    
    def __init__(self):
        from ..base import ToolCategory
        super().__init__(
            name="debt_to_income_calculator",
            description="Detailed DTI analysis with debt categorization and loan program compliance checking",
            category=ToolCategory.FINANCIAL_ANALYSIS,
            agent_domain="credit_assessment"
        )
        
        # DTI thresholds for different loan programs
        self.dti_thresholds = {
            "conventional": {"max_total": 0.43, "max_housing": 0.28, "preferred_total": 0.36},
            "fha": {"max_total": 0.57, "max_housing": 0.31, "preferred_total": 0.43},
            "va": {"max_total": 0.41, "max_housing": 0.31, "preferred_total": 0.36},
            "usda": {"max_total": 0.41, "max_housing": 0.29, "preferred_total": 0.36},
            "jumbo": {"max_total": 0.43, "max_housing": 0.28, "preferred_total": 0.36}
        }
        
        # Risk levels based on DTI ratios
        self.risk_levels = {
            "low": {"total": 0.28, "housing": 0.25},
            "moderate": {"total": 0.36, "housing": 0.28},
            "elevated": {"total": 0.43, "housing": 0.31},
            "high": {"total": 0.50, "housing": 0.35}
        }
        
        # Debt categories for analysis
        self.debt_categories = {
            "revolving": ["credit_card", "line_of_credit", "heloc"],
            "installment": ["auto_loan", "student_loan", "personal_loan"],
            "mortgage": ["mortgage", "home_loan", "second_mortgage"],
            "other": ["child_support", "alimony", "other_debt"]
        }
        
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "string",
                    "description": "Unique identifier for the mortgage application"
                },
                "borrower_info": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "ssn": {"type": "string"}
                    },
                    "required": ["name", "ssn"]
                },
                "income_information": {
                    "type": "object",
                    "properties": {
                        "monthly_income": {"type": "number"},
                        "annual_income": {"type": "number"},
                        "income_sources": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["monthly_income"]
                },
                "debt_information": {
                    "type": "object",
                    "properties": {
                        "monthly_debts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "debt_type": {"type": "string"},
                                    "creditor": {"type": "string"},
                                    "monthly_payment": {"type": "number"},
                                    "balance": {"type": "number"},
                                    "minimum_payment": {"type": "number"}
                                },
                                "required": ["debt_type", "monthly_payment"]
                            }
                        },
                        "total_monthly_debt": {"type": "number"}
                    }
                },
                "loan_details": {
                    "type": "object",
                    "properties": {
                        "loan_amount": {"type": "number"},
                        "loan_term_years": {"type": "integer"},
                        "estimated_payment": {"type": "number"},
                        "loan_type": {"type": "string"}
                    },
                    "required": ["loan_amount"]
                }
            },
            "required": ["application_id", "borrower_info", "income_information"]
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for DTI calculation."""
        return {
            "type": "object",
            "required": ["applicant_id", "monthly_income", "monthly_debt_payments"],
            "properties": {
                "applicant_id": {
                    "type": "string",
                    "description": "Unique identifier for the applicant"
                },
                "monthly_income": {
                    "type": "number",
                    "description": "Total monthly income"
                },
                "monthly_debt_payments": {
                    "type": "number", 
                    "description": "Total monthly debt payments"
                },
                "proposed_mortgage_payment": {
                    "type": "number",
                    "description": "Proposed monthly mortgage payment"
                }
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute debt-to-income calculation and analysis.
        
        Args:
            application_id: Unique identifier for the mortgage application
            borrower_info: Information about the borrower
            income_information: Monthly and annual income data
            debt_information: Existing debt obligations
            loan_details: Details about the proposed loan
            
        Returns:
            ToolResult containing DTI analysis
        """
        try:
            application_id = kwargs["application_id"]
            borrower_info = kwargs["borrower_info"]
            income_info = kwargs["income_information"]
            debt_info = kwargs.get("debt_information", {})
            loan_details = kwargs.get("loan_details", {})
            
            self.logger.info(f"Starting DTI calculation for application {application_id}")
            
            # Extract and validate income data
            monthly_income = float(income_info["monthly_income"])
            if monthly_income <= 0:
                raise ValueError("Monthly income must be greater than zero")
            
            # Process existing debt information
            existing_debts = self._process_debt_information(debt_info)
            
            # Calculate proposed housing payment
            housing_payment = self._calculate_housing_payment(loan_details, monthly_income)
            
            # Calculate DTI ratios
            dti_calculations = self._calculate_dti_ratios(
                monthly_income, existing_debts, housing_payment
            )
            
            # Categorize and analyze debts
            debt_analysis = self._analyze_debt_structure(existing_debts)
            
            # Assess loan program compliance
            program_compliance = self._assess_program_compliance(
                dti_calculations, loan_details.get("loan_type", "conventional")
            )
            
            # Calculate risk assessment
            risk_assessment = self._calculate_dti_risk_assessment(dti_calculations, debt_analysis)
            
            # Generate recommendations
            recommendations = self._generate_dti_recommendations(
                dti_calculations, debt_analysis, program_compliance, risk_assessment
            )
            
            # Identify potential issues
            issues = self._identify_dti_issues(dti_calculations, debt_analysis)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                income_info, debt_info, existing_debts
            )
            
            result_data = {
                "total_dti_ratio": dti_calculations["total_dti"],
                "housing_dti_ratio": dti_calculations["housing_dti"],
                "monthly_debt_payments": dti_calculations["total_monthly_debt"],
                "monthly_housing_payment": housing_payment,
                "qualified_monthly_income": monthly_income,
                "debt_breakdown": debt_analysis["categorized_debts"],
                "debt_summary": debt_analysis["summary"],
                "program_compliance": program_compliance,
                "risk_level": risk_assessment["risk_level"],
                "risk_factors": risk_assessment["risk_factors"],
                "recommendations": recommendations,
                "potential_issues": issues,
                "confidence_score": confidence_score,
                "requires_verification": self._requires_additional_verification(
                    dti_calculations, debt_analysis, issues
                ),
                "compensating_factors_needed": self._assess_compensating_factors_needed(
                    dti_calculations, program_compliance
                ),
                "debt_ratios_by_category": debt_analysis["ratios_by_category"],
                "payment_shock_analysis": self._analyze_payment_shock(
                    housing_payment, existing_debts, monthly_income
                )
            }
            
            self.logger.info(f"DTI calculation completed for application {application_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"DTI calculation failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    def _process_debt_information(self, debt_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process and normalize debt information.
        
        Args:
            debt_info: Raw debt information
            
        Returns:
            List of normalized debt records
        """
        debts = []
        
        # Process individual debt items if provided
        monthly_debts = debt_info.get("monthly_debts", [])
        for debt in monthly_debts:
            normalized_debt = {
                "debt_type": debt.get("debt_type", "other").lower(),
                "creditor": debt.get("creditor", "Unknown"),
                "monthly_payment": float(debt.get("monthly_payment", 0)),
                "balance": float(debt.get("balance", 0)),
                "minimum_payment": float(debt.get("minimum_payment", debt.get("monthly_payment", 0)))
            }
            
            if normalized_debt["monthly_payment"] > 0:
                debts.append(normalized_debt)
        
        # If no individual debts but total provided, create a generic entry
        total_monthly_debt = debt_info.get("total_monthly_debt", 0)
        if not debts and total_monthly_debt > 0:
            debts.append({
                "debt_type": "other",
                "creditor": "Various",
                "monthly_payment": float(total_monthly_debt),
                "balance": 0,
                "minimum_payment": float(total_monthly_debt)
            })
        
        return debts
    
    def _calculate_housing_payment(self, loan_details: Dict[str, Any], 
                                 monthly_income: float) -> float:
        """
        Calculate estimated monthly housing payment.
        
        Args:
            loan_details: Loan details including amount and terms
            monthly_income: Borrower's monthly income
            
        Returns:
            Estimated monthly housing payment
        """
        # If estimated payment is provided, use it
        if "estimated_payment" in loan_details:
            return float(loan_details["estimated_payment"])
        
        # Otherwise calculate based on loan amount
        loan_amount = loan_details.get("loan_amount", 0)
        if loan_amount <= 0:
            # Estimate based on income (conservative approach)
            return monthly_income * 0.28  # 28% housing ratio
        
        # Simple payment calculation (in real implementation, would use proper amortization)
        loan_term_years = loan_details.get("loan_term_years", 30)
        estimated_rate = 0.07  # 7% estimated rate
        
        # Monthly payment calculation using standard formula
        monthly_rate = estimated_rate / 12
        num_payments = loan_term_years * 12
        
        if monthly_rate > 0:
            payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                     ((1 + monthly_rate) ** num_payments - 1)
        else:
            payment = loan_amount / num_payments
        
        # Add estimated taxes, insurance, and PMI (PITI)
        estimated_piti_addition = payment * 0.3  # Rough estimate for TI and PMI
        
        return payment + estimated_piti_addition
    
    def _calculate_dti_ratios(self, monthly_income: float, existing_debts: List[Dict[str, Any]], 
                            housing_payment: float) -> Dict[str, float]:
        """
        Calculate various DTI ratios.
        
        Args:
            monthly_income: Monthly gross income
            existing_debts: List of existing debt obligations
            housing_payment: Proposed monthly housing payment
            
        Returns:
            Dictionary containing DTI calculations
        """
        # Calculate total existing monthly debt payments
        total_existing_debt = sum(debt["monthly_payment"] for debt in existing_debts)
        
        # Calculate ratios
        housing_dti = housing_payment / monthly_income if monthly_income > 0 else 0
        total_dti = (total_existing_debt + housing_payment) / monthly_income if monthly_income > 0 else 0
        
        # Calculate back-end ratio (existing debt only)
        backend_dti = total_existing_debt / monthly_income if monthly_income > 0 else 0
        
        return {
            "housing_dti": round(housing_dti, 4),
            "total_dti": round(total_dti, 4),
            "backend_dti": round(backend_dti, 4),
            "total_monthly_debt": total_existing_debt,
            "housing_payment": housing_payment,
            "monthly_income": monthly_income
        }
    
    def _analyze_debt_structure(self, debts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze debt structure and categorization.
        
        Args:
            debts: List of debt obligations
            
        Returns:
            Dictionary containing debt analysis
        """
        categorized_debts = {category: [] for category in self.debt_categories.keys()}
        category_totals = {category: 0 for category in self.debt_categories.keys()}
        
        total_debt_payment = 0
        total_debt_balance = 0
        
        # Categorize debts
        for debt in debts:
            debt_type = debt["debt_type"].lower()
            monthly_payment = debt["monthly_payment"]
            balance = debt["balance"]
            
            total_debt_payment += monthly_payment
            total_debt_balance += balance
            
            # Find appropriate category
            category = "other"  # default
            for cat, types in self.debt_categories.items():
                if any(debt_type in dt or dt in debt_type for dt in types):
                    category = cat
                    break
            
            categorized_debts[category].append(debt)
            category_totals[category] += monthly_payment
        
        # Calculate ratios by category (will be calculated against income later)
        ratios_by_category = {}
        for category, total in category_totals.items():
            ratios_by_category[category] = {
                "monthly_payment": total,
                "debt_count": len(categorized_debts[category]),
                "percentage_of_total_debt": total / total_debt_payment if total_debt_payment > 0 else 0
            }
        
        # Analyze debt characteristics
        debt_characteristics = self._analyze_debt_characteristics(debts)
        
        return {
            "categorized_debts": categorized_debts,
            "category_totals": category_totals,
            "ratios_by_category": ratios_by_category,
            "summary": {
                "total_monthly_payment": total_debt_payment,
                "total_balance": total_debt_balance,
                "number_of_debts": len(debts),
                "average_payment": total_debt_payment / len(debts) if debts else 0,
                "largest_payment": max((debt["monthly_payment"] for debt in debts), default=0),
                "smallest_payment": min((debt["monthly_payment"] for debt in debts), default=0)
            },
            "characteristics": debt_characteristics
        }
    
    def _analyze_debt_characteristics(self, debts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze characteristics of the debt portfolio."""
        if not debts:
            return {
                "debt_diversity": "none",
                "payment_concentration": 0,
                "high_payment_debts": 0
            }
        
        # Calculate payment concentration (Gini-like coefficient)
        payments = [debt["monthly_payment"] for debt in debts]
        payments.sort()
        
        n = len(payments)
        total_payment = sum(payments)
        
        if total_payment == 0:
            concentration = 0
        else:
            # Simple concentration measure
            largest_payment = max(payments)
            concentration = largest_payment / total_payment
        
        # Count high payment debts (>$500/month)
        high_payment_debts = sum(1 for debt in debts if debt["monthly_payment"] > 500)
        
        # Assess debt diversity
        unique_types = len(set(debt["debt_type"] for debt in debts))
        if unique_types >= 4:
            diversity = "high"
        elif unique_types >= 2:
            diversity = "moderate"
        else:
            diversity = "low"
        
        return {
            "debt_diversity": diversity,
            "payment_concentration": round(concentration, 3),
            "high_payment_debts": high_payment_debts,
            "unique_debt_types": unique_types
        }
    
    def _assess_program_compliance(self, dti_calculations: Dict[str, float], 
                                 loan_type: str) -> Dict[str, Any]:
        """
        Assess compliance with loan program DTI requirements.
        
        Args:
            dti_calculations: DTI calculation results
            loan_type: Type of loan program
            
        Returns:
            Dictionary containing compliance assessment
        """
        loan_type = loan_type.lower()
        thresholds = self.dti_thresholds.get(loan_type, self.dti_thresholds["conventional"])
        
        total_dti = dti_calculations["total_dti"]
        housing_dti = dti_calculations["housing_dti"]
        
        # Check compliance
        total_compliant = total_dti <= thresholds["max_total"]
        housing_compliant = housing_dti <= thresholds["max_housing"]
        preferred_compliant = total_dti <= thresholds["preferred_total"]
        
        # Determine overall compliance status
        if total_compliant and housing_compliant:
            if preferred_compliant:
                compliance_status = "preferred"
            else:
                compliance_status = "acceptable"
        else:
            compliance_status = "non_compliant"
        
        # Calculate margins
        total_margin = thresholds["max_total"] - total_dti
        housing_margin = thresholds["max_housing"] - housing_dti
        preferred_margin = thresholds["preferred_total"] - total_dti
        
        return {
            "loan_program": loan_type,
            "compliance_status": compliance_status,
            "total_dti_compliant": total_compliant,
            "housing_dti_compliant": housing_compliant,
            "preferred_tier_compliant": preferred_compliant,
            "thresholds": thresholds,
            "margins": {
                "total_dti_margin": round(total_margin, 4),
                "housing_dti_margin": round(housing_margin, 4),
                "preferred_margin": round(preferred_margin, 4)
            },
            "exceeds_by": {
                "total_dti": max(0, total_dti - thresholds["max_total"]),
                "housing_dti": max(0, housing_dti - thresholds["max_housing"])
            }
        }
    
    def _calculate_dti_risk_assessment(self, dti_calculations: Dict[str, float],
                                     debt_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk assessment based on DTI levels and debt structure.
        
        Args:
            dti_calculations: DTI calculation results
            debt_analysis: Debt structure analysis
            
        Returns:
            Dictionary containing risk assessment
        """
        total_dti = dti_calculations["total_dti"]
        housing_dti = dti_calculations["housing_dti"]
        
        risk_factors = []
        risk_score = 0
        
        # Base risk from DTI levels
        if total_dti >= self.risk_levels["high"]["total"]:
            risk_level = "high"
            risk_score += 40
            risk_factors.append(f"Total DTI ({total_dti:.1%}) exceeds high-risk threshold")
        elif total_dti >= self.risk_levels["elevated"]["total"]:
            risk_level = "elevated"
            risk_score += 25
            risk_factors.append(f"Total DTI ({total_dti:.1%}) is elevated")
        elif total_dti >= self.risk_levels["moderate"]["total"]:
            risk_level = "moderate"
            risk_score += 15
        else:
            risk_level = "low"
            risk_score += 5
        
        # Housing DTI risk
        if housing_dti >= self.risk_levels["high"]["housing"]:
            risk_score += 20
            risk_factors.append(f"Housing DTI ({housing_dti:.1%}) is very high")
        elif housing_dti >= self.risk_levels["elevated"]["housing"]:
            risk_score += 10
            risk_factors.append(f"Housing DTI ({housing_dti:.1%}) is elevated")
        
        # Debt structure risks
        debt_summary = debt_analysis["summary"]
        characteristics = debt_analysis["characteristics"]
        
        if debt_summary["number_of_debts"] > 10:
            risk_score += 10
            risk_factors.append("High number of debt obligations")
        
        if characteristics["payment_concentration"] > 0.6:
            risk_score += 8
            risk_factors.append("High payment concentration in single debt")
        
        if characteristics["high_payment_debts"] > 2:
            risk_score += 5
            risk_factors.append("Multiple high-payment debt obligations")
        
        # Revolving debt risk
        revolving_payment = debt_analysis["category_totals"].get("revolving", 0)
        if revolving_payment > dti_calculations["monthly_income"] * 0.15:  # >15% of income
            risk_score += 10
            risk_factors.append("High revolving debt payments")
        
        # Final risk level adjustment
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "elevated"
        elif risk_score >= 15:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": min(100, risk_score),
            "risk_factors": risk_factors,
            "debt_structure_risk": self._assess_debt_structure_risk(debt_analysis),
            "payment_capacity_risk": self._assess_payment_capacity_risk(dti_calculations)
        }
    
    def _assess_debt_structure_risk(self, debt_analysis: Dict[str, Any]) -> str:
        """Assess risk from debt structure."""
        characteristics = debt_analysis["characteristics"]
        
        if characteristics["payment_concentration"] > 0.7:
            return "high"
        elif characteristics["debt_diversity"] == "low" and characteristics["high_payment_debts"] > 1:
            return "moderate"
        else:
            return "low"
    
    def _assess_payment_capacity_risk(self, dti_calculations: Dict[str, float]) -> str:
        """Assess payment capacity risk."""
        total_dti = dti_calculations["total_dti"]
        
        if total_dti > 0.50:
            return "high"
        elif total_dti > 0.43:
            return "moderate"
        else:
            return "low"
    
    def _generate_dti_recommendations(self, dti_calculations: Dict[str, float],
                                    debt_analysis: Dict[str, Any],
                                    program_compliance: Dict[str, Any],
                                    risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on DTI analysis."""
        recommendations = []
        
        # Compliance-based recommendations
        if program_compliance["compliance_status"] == "non_compliant":
            if not program_compliance["total_dti_compliant"]:
                exceed_amount = program_compliance["exceeds_by"]["total_dti"]
                recommendations.append(
                    f"Total DTI exceeds program limits by {exceed_amount:.1%} - "
                    "consider debt paydown or alternative loan programs"
                )
            
            if not program_compliance["housing_dti_compliant"]:
                exceed_amount = program_compliance["exceeds_by"]["housing_dti"]
                recommendations.append(
                    f"Housing DTI exceeds program limits by {exceed_amount:.1%} - "
                    "consider lower loan amount or increased down payment"
                )
        
        # Risk-based recommendations
        if risk_assessment["risk_level"] in ["high", "elevated"]:
            recommendations.append("High DTI ratios require compensating factors for approval")
            
            if "High revolving debt payments" in risk_assessment["risk_factors"]:
                recommendations.append("Consider requiring borrower to pay down revolving debt")
        
        # Debt structure recommendations
        debt_summary = debt_analysis["summary"]
        if debt_summary["number_of_debts"] > 8:
            recommendations.append("High number of debt obligations - verify all debts are included")
        
        characteristics = debt_analysis["characteristics"]
        if characteristics["payment_concentration"] > 0.6:
            recommendations.append("Payment concentration risk - verify largest debt obligation")
        
        # Program-specific recommendations
        loan_program = program_compliance["loan_program"]
        if loan_program == "fha" and dti_calculations["total_dti"] > 0.43:
            recommendations.append("FHA DTI above 43% requires manual underwriting")
        elif loan_program == "va" and dti_calculations["total_dti"] > 0.41:
            recommendations.append("VA DTI above 41% requires residual income analysis")
        
        return recommendations
    
    def _identify_dti_issues(self, dti_calculations: Dict[str, float],
                           debt_analysis: Dict[str, Any]) -> List[str]:
        """Identify potential issues with DTI calculations."""
        issues = []
        
        # Calculation issues
        if dti_calculations["total_dti"] > 1.0:  # >100% DTI
            issues.append("Total DTI exceeds 100% - verify income and debt calculations")
        
        if dti_calculations["housing_dti"] > 0.50:  # >50% housing DTI
            issues.append("Housing DTI exceeds 50% - verify housing payment calculation")
        
        # Debt structure issues
        debt_summary = debt_analysis["summary"]
        if debt_summary["total_monthly_payment"] == 0 and dti_calculations["backend_dti"] > 0:
            issues.append("Inconsistent debt information - verify debt calculations")
        
        # Income issues
        monthly_income = dti_calculations["monthly_income"]
        total_payments = debt_summary["total_monthly_payment"] + dti_calculations["housing_payment"]
        
        if total_payments > monthly_income * 0.8:  # >80% of income
            issues.append("Total payments exceed 80% of income - verify income documentation")
        
        return issues
    
    def _calculate_confidence_score(self, income_info: Dict[str, Any],
                                  debt_info: Dict[str, Any],
                                  processed_debts: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for DTI calculations."""
        base_confidence = 0.7
        
        # Adjust for income data completeness
        if "annual_income" in income_info:
            base_confidence += 0.1
        
        if income_info.get("income_sources"):
            base_confidence += 0.05
        
        # Adjust for debt data completeness
        if debt_info.get("monthly_debts"):
            base_confidence += 0.1
        elif debt_info.get("total_monthly_debt"):
            base_confidence += 0.05
        
        # Adjust for debt detail level
        if processed_debts:
            debts_with_balance = sum(1 for debt in processed_debts if debt["balance"] > 0)
            if debts_with_balance > len(processed_debts) * 0.5:
                base_confidence += 0.05
        
        return max(0.0, min(1.0, base_confidence))
    
    def _requires_additional_verification(self, dti_calculations: Dict[str, float],
                                        debt_analysis: Dict[str, Any],
                                        issues: List[str]) -> bool:
        """Determine if additional verification is required."""
        # High DTI requires verification
        if dti_calculations["total_dti"] > 0.45:
            return True
        
        # Issues require verification
        if issues:
            return True
        
        # High number of debts requires verification
        if debt_analysis["summary"]["number_of_debts"] > 8:
            return True
        
        # High payment concentration requires verification
        if debt_analysis["characteristics"]["payment_concentration"] > 0.6:
            return True
        
        return False
    
    def _assess_compensating_factors_needed(self, dti_calculations: Dict[str, float],
                                          program_compliance: Dict[str, Any]) -> bool:
        """Assess if compensating factors are needed for approval."""
        # Non-compliant DTI requires compensating factors
        if program_compliance["compliance_status"] == "non_compliant":
            return True
        
        # High DTI even if compliant may need compensating factors
        if dti_calculations["total_dti"] > 0.40:
            return True
        
        return False
    
    def _analyze_payment_shock(self, housing_payment: float, existing_debts: List[Dict[str, Any]],
                             monthly_income: float) -> Dict[str, Any]:
        """
        Analyze payment shock from current housing to proposed housing.
        
        Args:
            housing_payment: Proposed monthly housing payment
            existing_debts: List of existing debts
            monthly_income: Monthly income
            
        Returns:
            Dictionary containing payment shock analysis
        """
        # Look for current housing payment in existing debts
        current_housing_payment = 0
        for debt in existing_debts:
            debt_type = debt["debt_type"].lower()
            if any(housing_type in debt_type for housing_type in ["mortgage", "rent", "housing"]):
                current_housing_payment = max(current_housing_payment, debt["monthly_payment"])
        
        # If no current housing payment found, assume rent (conservative estimate)
        if current_housing_payment == 0:
            current_housing_payment = monthly_income * 0.20  # Assume 20% for rent
        
        # Calculate payment shock
        payment_increase = housing_payment - current_housing_payment
        payment_shock_ratio = payment_increase / monthly_income if monthly_income > 0 else 0
        
        # Assess shock level
        if payment_shock_ratio > 0.15:  # >15% of income increase
            shock_level = "high"
        elif payment_shock_ratio > 0.10:  # >10% of income increase
            shock_level = "moderate"
        elif payment_shock_ratio > 0.05:  # >5% of income increase
            shock_level = "low"
        else:
            shock_level = "minimal"
        
        return {
            "current_housing_payment": current_housing_payment,
            "proposed_housing_payment": housing_payment,
            "payment_increase": payment_increase,
            "payment_shock_ratio": round(payment_shock_ratio, 4),
            "shock_level": shock_level,
            "requires_analysis": shock_level in ["high", "moderate"]
        }