"""
Loan-to-Value (LTV) Calculator Tool for mortgage processing.

This tool calculates accurate LTV ratios, performs LTV risk assessment,
and checks compliance with loan program requirements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from ..base import BaseTool, ToolResult


class LTVCalculatorTool(BaseTool):
    """
    Tool for calculating loan-to-value ratios and risk assessment.
    
    This tool performs LTV calculations to:
    - Calculate accurate LTV and CLTV (Combined LTV) ratios
    - Assess LTV risk levels and compliance requirements
    - Determine mortgage insurance (PMI) requirements
    - Evaluate loan program eligibility based on LTV
    - Identify LTV-related red flags and conditions
    - Support multiple loan types and programs
    """
    
    def __init__(self):

    
        from ..base import ToolCategory
        super().__init__(
            name="ltv_calculator",
            description="Loan-to-value ratio calculation and compliance checking",
            category=ToolCategory.FINANCIAL_ANALYSIS,
            agent_domain="property_assessment"
        )
        
        # LTV risk thresholds by loan type
        self.ltv_risk_thresholds = {
            "conventional": {
                "low": 0.70,      # LTV <= 70%
                "medium": 0.80,   # 70% < LTV <= 80%
                "high": 0.90,     # 80% < LTV <= 90%
                "very_high": 0.95 # 90% < LTV <= 95%
            },
            "fha": {
                "low": 0.80,
                "medium": 0.90,
                "high": 0.96,
                "very_high": 0.965
            },
            "va": {
                "low": 0.90,
                "medium": 0.95,
                "high": 1.00,
                "very_high": 1.00
            },
            "usda": {
                "low": 0.90,
                "medium": 0.95,
                "high": 1.00,
                "very_high": 1.00
            },
            "jumbo": {
                "low": 0.70,
                "medium": 0.75,
                "high": 0.80,
                "very_high": 0.85
            }
        }
        
        # Maximum LTV limits by loan type
        self.max_ltv_limits = {
            "conventional": 0.97,  # 97% max for conventional
            "fha": 0.965,          # 96.5% max for FHA
            "va": 1.00,            # 100% max for VA
            "usda": 1.00,          # 100% max for USDA
            "jumbo": 0.80          # 80% max for jumbo (typical)
        }
        
        # PMI requirements by loan type
        self.pmi_requirements = {
            "conventional": {
                "required_above": 0.80,    # PMI required if LTV > 80%
                "removal_threshold": 0.78, # Can remove PMI when LTV <= 78%
                "automatic_removal": 0.78  # Automatic removal at 78%
            },
            "fha": {
                "required_above": 0.78,    # MIP required if LTV > 78%
                "removal_threshold": None, # FHA MIP typically for life of loan
                "automatic_removal": None
            },
            "va": {
                "required_above": None,    # VA loans don't require PMI
                "removal_threshold": None,
                "automatic_removal": None
            },
            "usda": {
                "required_above": None,    # USDA loans don't require PMI
                "removal_threshold": None,
                "automatic_removal": None
            },
            "jumbo": {
                "required_above": 0.80,
                "removal_threshold": 0.78,
                "automatic_removal": 0.78
            }
        }
        
        # Typical PMI rates by LTV range (annual rates)
        self.pmi_rates = {
            (0.80, 0.85): 0.0045,  # 0.45% annually
            (0.85, 0.90): 0.0055,  # 0.55% annually
            (0.90, 0.95): 0.0070,  # 0.70% annually
            (0.95, 1.00): 0.0085   # 0.85% annually
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
                "loan_information": {
                    "type": "object",
                    "properties": {
                        "loan_amount": {"type": "number"},
                        "loan_type": {"type": "string"},
                        "loan_term_years": {"type": "integer"},
                        "down_payment": {"type": "number"},
                        "purpose": {"type": "string"}
                    },
                    "required": ["loan_amount", "loan_type"]
                },
                "property_information": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string"},
                        "property_type": {"type": "string"},
                        "appraised_value": {"type": "number"},
                        "stated_value": {"type": "number"}
                    },
                    "required": ["appraised_value"]
                },
                "additional_financing": {
                    "type": "object",
                    "properties": {
                        "second_mortgage": {"type": "number"},
                        "heloc_amount": {"type": "number"},
                        "other_liens": {"type": "number"}
                    }
                },
                "calculation_method": {
                    "type": "string",
                    "enum": ["standard", "comprehensive", "program_specific"],
                    "default": "comprehensive"
                }
            },
            "required": ["application_id", "loan_information", "property_information"]
        }
    
    def get_input_schema(self) -> Dict[str, Any]:

    
        """Return input schema for the tool."""

    
        return {

    
            "type": "object",

    
            "required": ["applicant_id"],

    
            "properties": {

    
                "applicant_id": {

    
                    "type": "string",

    
                    "description": "Unique identifier for the applicant"

    
                }

    
            }

    
        }

    
    

    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute LTV calculation and risk assessment.
        
        Args:
            application_id: Unique identifier for the mortgage application
            loan_information: Loan details including amount and type
            property_information: Property details including appraised value
            additional_financing: Additional financing amounts (optional)
            calculation_method: Method for LTV calculation
            
        Returns:
            ToolResult containing LTV analysis
        """
        try:
            application_id = kwargs["application_id"]
            loan_info = kwargs["loan_information"]
            property_info = kwargs["property_information"]
            additional_financing = kwargs.get("additional_financing", {})
            calculation_method = kwargs.get("calculation_method", "comprehensive")
            
            self.logger.info(f"Starting LTV calculation for application {application_id}")
            
            # Extract key values
            loan_amount = loan_info["loan_amount"]
            loan_type = loan_info.get("loan_type", "conventional").lower()
            appraised_value = property_info["appraised_value"]
            
            # Calculate basic LTV ratio
            ltv_calculation = self._calculate_basic_ltv(loan_amount, appraised_value)
            
            # Calculate Combined LTV (CLTV) if additional financing exists
            cltv_calculation = self._calculate_combined_ltv(
                loan_amount, appraised_value, additional_financing
            )
            
            # Assess LTV risk level
            risk_assessment = self._assess_ltv_risk(
                ltv_calculation["ltv_ratio"], loan_type, loan_info
            )
            
            # Check loan program compliance
            compliance_check = self._check_loan_program_compliance(
                ltv_calculation["ltv_ratio"], cltv_calculation["cltv_ratio"], 
                loan_type, loan_info
            )
            
            # Determine PMI requirements
            pmi_analysis = self._analyze_pmi_requirements(
                ltv_calculation["ltv_ratio"], loan_type, loan_amount
            )
            
            # Calculate down payment requirements
            down_payment_analysis = self._analyze_down_payment_requirements(
                loan_amount, appraised_value, loan_type
            )
            
            # Identify LTV red flags and conditions
            red_flags = self._identify_ltv_red_flags(
                ltv_calculation, cltv_calculation, compliance_check, loan_type
            )
            
            # Generate recommendations
            recommendations = self._generate_ltv_recommendations(
                ltv_calculation, risk_assessment, compliance_check, pmi_analysis
            )
            
            result_data = {
                "ltv_ratio": ltv_calculation["ltv_ratio"],
                "ltv_percentage": ltv_calculation["ltv_percentage"],
                "cltv_ratio": cltv_calculation["cltv_ratio"],
                "cltv_percentage": cltv_calculation["cltv_percentage"],
                "loan_amount": loan_amount,
                "appraised_value": appraised_value,
                "total_financing": cltv_calculation["total_financing"],
                "risk_assessment": risk_assessment,
                "compliance_status": compliance_check,
                "pmi_analysis": pmi_analysis,
                "down_payment_analysis": down_payment_analysis,
                "requires_pmi": pmi_analysis["required"],
                "pmi_rate": pmi_analysis.get("estimated_rate", 0.0),
                "requires_additional_down_payment": down_payment_analysis["additional_required"],
                "ltv_risk_level": risk_assessment["risk_level"],
                "program_eligible": compliance_check["eligible"],
                "max_ltv_allowed": compliance_check["max_ltv_allowed"],
                "ltv_red_flags": red_flags,
                "recommendations": recommendations,
                "calculation_method": calculation_method,
                "calculation_date": datetime.now().isoformat(),
                "confidence_score": self._calculate_confidence_score(
                    ltv_calculation, property_info, loan_info
                )
            }
            
            self.logger.info(f"LTV calculation completed for application {application_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"LTV calculation failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    def _calculate_basic_ltv(self, loan_amount: float, appraised_value: float) -> Dict[str, Any]:
        """
        Calculate basic loan-to-value ratio.
        
        Args:
            loan_amount: Primary loan amount
            appraised_value: Property appraised value
            
        Returns:
            Dictionary containing LTV calculation details
        """
        if appraised_value <= 0:
            raise ValueError("Appraised value must be greater than zero")
        
        ltv_ratio = loan_amount / appraised_value
        ltv_percentage = ltv_ratio * 100
        
        return {
            "ltv_ratio": round(ltv_ratio, 4),
            "ltv_percentage": round(ltv_percentage, 2),
            "loan_amount": loan_amount,
            "appraised_value": appraised_value,
            "calculation_method": "loan_amount / appraised_value"
        }
    
    def _calculate_combined_ltv(self, loan_amount: float, appraised_value: float,
                              additional_financing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Combined Loan-to-Value (CLTV) ratio including additional financing.
        
        Args:
            loan_amount: Primary loan amount
            appraised_value: Property appraised value
            additional_financing: Additional financing amounts
            
        Returns:
            Dictionary containing CLTV calculation details
        """
        # Sum all financing amounts
        second_mortgage = additional_financing.get("second_mortgage", 0)
        heloc_amount = additional_financing.get("heloc_amount", 0)
        other_liens = additional_financing.get("other_liens", 0)
        
        total_financing = loan_amount + second_mortgage + heloc_amount + other_liens
        
        if appraised_value <= 0:
            raise ValueError("Appraised value must be greater than zero")
        
        cltv_ratio = total_financing / appraised_value
        cltv_percentage = cltv_ratio * 100
        
        return {
            "cltv_ratio": round(cltv_ratio, 4),
            "cltv_percentage": round(cltv_percentage, 2),
            "total_financing": total_financing,
            "primary_loan": loan_amount,
            "second_mortgage": second_mortgage,
            "heloc_amount": heloc_amount,
            "other_liens": other_liens,
            "appraised_value": appraised_value,
            "has_additional_financing": total_financing > loan_amount
        }
    
    def _assess_ltv_risk(self, ltv_ratio: float, loan_type: str, 
                        loan_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk level based on LTV ratio and loan type.
        
        Args:
            ltv_ratio: Calculated LTV ratio
            loan_type: Type of loan
            loan_info: Additional loan information
            
        Returns:
            Dictionary containing risk assessment
        """
        # Get risk thresholds for loan type
        thresholds = self.ltv_risk_thresholds.get(
            loan_type, self.ltv_risk_thresholds["conventional"]
        )
        
        # Determine risk level
        if ltv_ratio <= thresholds["low"]:
            risk_level = "low"
            risk_description = "Low LTV risk - Strong equity position"
        elif ltv_ratio <= thresholds["medium"]:
            risk_level = "medium"
            risk_description = "Medium LTV risk - Adequate equity position"
        elif ltv_ratio <= thresholds["high"]:
            risk_level = "high"
            risk_description = "High LTV risk - Limited equity position"
        else:
            risk_level = "very_high"
            risk_description = "Very high LTV risk - Minimal equity position"
        
        # Calculate risk score (0-100)
        max_ltv = self.max_ltv_limits.get(loan_type, 0.97)
        risk_score = min(100, (ltv_ratio / max_ltv) * 100)
        
        # Additional risk factors
        risk_factors = []
        
        if ltv_ratio > 0.95:
            risk_factors.append("LTV exceeds 95% - High default risk")
        
        if ltv_ratio > 0.90:
            risk_factors.append("LTV exceeds 90% - Elevated default risk")
        
        # Loan purpose risk adjustment
        loan_purpose = loan_info.get("purpose", "").lower()
        if loan_purpose == "cash_out_refinance" and ltv_ratio > 0.80:
            risk_factors.append("High LTV cash-out refinance increases risk")
            risk_score += 5
        
        return {
            "risk_level": risk_level,
            "risk_score": min(100, round(risk_score, 1)),
            "risk_description": risk_description,
            "risk_factors": risk_factors,
            "thresholds": thresholds,
            "ltv_ratio": ltv_ratio
        }
    
    def _check_loan_program_compliance(self, ltv_ratio: float, cltv_ratio: float,
                                     loan_type: str, loan_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance with loan program LTV requirements.
        
        Args:
            ltv_ratio: Primary LTV ratio
            cltv_ratio: Combined LTV ratio
            loan_type: Type of loan program
            loan_info: Additional loan information
            
        Returns:
            Dictionary containing compliance status
        """
        max_ltv = self.max_ltv_limits.get(loan_type, 0.97)
        
        # Check primary LTV compliance
        ltv_compliant = ltv_ratio <= max_ltv
        
        # Check CLTV compliance (typically same as LTV for most programs)
        cltv_compliant = cltv_ratio <= max_ltv
        
        # Overall eligibility
        eligible = ltv_compliant and cltv_compliant
        
        # Compliance notes
        compliance_notes = []
        
        if not ltv_compliant:
            ltv_excess = ltv_ratio - max_ltv
            compliance_notes.append(
                f"LTV ({ltv_ratio:.1%}) exceeds maximum allowed ({max_ltv:.1%}) by {ltv_excess:.1%}"
            )
        
        if not cltv_compliant and cltv_ratio != ltv_ratio:
            cltv_excess = cltv_ratio - max_ltv
            compliance_notes.append(
                f"CLTV ({cltv_ratio:.1%}) exceeds maximum allowed ({max_ltv:.1%}) by {cltv_excess:.1%}"
            )
        
        # Program-specific compliance checks
        program_specific_notes = self._check_program_specific_requirements(
            ltv_ratio, loan_type, loan_info
        )
        compliance_notes.extend(program_specific_notes)
        
        if eligible:
            compliance_notes.append(f"Meets {loan_type.upper()} program LTV requirements")
        
        return {
            "eligible": eligible,
            "ltv_compliant": ltv_compliant,
            "cltv_compliant": cltv_compliant,
            "max_ltv_allowed": max_ltv,
            "ltv_ratio": ltv_ratio,
            "cltv_ratio": cltv_ratio,
            "compliance_notes": compliance_notes,
            "loan_type": loan_type
        }
    
    def _check_program_specific_requirements(self, ltv_ratio: float, loan_type: str,
                                           loan_info: Dict[str, Any]) -> List[str]:
        """
        Check program-specific LTV requirements.
        
        Args:
            ltv_ratio: LTV ratio
            loan_type: Loan program type
            loan_info: Loan information
            
        Returns:
            List of program-specific compliance notes
        """
        notes = []
        loan_purpose = loan_info.get("purpose", "").lower()
        
        if loan_type == "fha":
            # FHA specific requirements
            if loan_purpose == "purchase" and ltv_ratio > 0.965:
                notes.append("FHA purchase loans limited to 96.5% LTV")
            elif loan_purpose == "refinance" and ltv_ratio > 0.975:
                notes.append("FHA refinance loans limited to 97.5% LTV")
        
        elif loan_type == "va":
            # VA specific requirements
            if ltv_ratio > 1.00:
                notes.append("VA loans cannot exceed 100% LTV")
        
        elif loan_type == "usda":
            # USDA specific requirements
            if ltv_ratio > 1.00:
                notes.append("USDA loans cannot exceed 100% LTV")
            if loan_purpose != "purchase":
                notes.append("USDA loans typically limited to purchase transactions")
        
        elif loan_type == "jumbo":
            # Jumbo loan requirements (typically more restrictive)
            if ltv_ratio > 0.80:
                notes.append("Jumbo loans typically limited to 80% LTV")
            if ltv_ratio > 0.70 and loan_purpose == "cash_out_refinance":
                notes.append("Jumbo cash-out refinance typically limited to 70% LTV")
        
        elif loan_type == "conventional":
            # Conventional loan requirements
            if ltv_ratio > 0.97:
                notes.append("Conventional loans limited to 97% LTV")
            if ltv_ratio > 0.95 and loan_purpose == "cash_out_refinance":
                notes.append("Conventional cash-out refinance typically limited to 95% LTV")
        
        return notes
    
    def _analyze_pmi_requirements(self, ltv_ratio: float, loan_type: str,
                                loan_amount: float) -> Dict[str, Any]:
        """
        Analyze private mortgage insurance (PMI) requirements.
        
        Args:
            ltv_ratio: LTV ratio
            loan_type: Loan program type
            loan_amount: Loan amount
            
        Returns:
            Dictionary containing PMI analysis
        """
        pmi_config = self.pmi_requirements.get(loan_type, self.pmi_requirements["conventional"])
        
        # Determine if PMI is required
        required_threshold = pmi_config.get("required_above")
        pmi_required = required_threshold is not None and ltv_ratio > required_threshold
        
        # Estimate PMI rate
        estimated_rate = 0.0
        if pmi_required:
            estimated_rate = self._estimate_pmi_rate(ltv_ratio, loan_type)
        
        # Calculate monthly PMI payment
        monthly_pmi = 0.0
        annual_pmi = 0.0
        if pmi_required and estimated_rate > 0:
            annual_pmi = loan_amount * estimated_rate
            monthly_pmi = annual_pmi / 12
        
        # PMI removal information
        removal_info = {}
        if pmi_config.get("removal_threshold"):
            removal_info = {
                "removal_threshold": pmi_config["removal_threshold"],
                "automatic_removal": pmi_config.get("automatic_removal"),
                "can_request_removal": True,
                "estimated_removal_ltv": pmi_config["removal_threshold"]
            }
        elif loan_type == "fha":
            removal_info = {
                "removal_threshold": None,
                "automatic_removal": None,
                "can_request_removal": False,
                "notes": "FHA MIP typically required for life of loan"
            }
        
        return {
            "required": pmi_required,
            "type": self._get_pmi_type(loan_type),
            "estimated_rate": estimated_rate,
            "monthly_payment": round(monthly_pmi, 2),
            "annual_payment": round(annual_pmi, 2),
            "required_threshold": required_threshold,
            "current_ltv": ltv_ratio,
            "removal_info": removal_info,
            "pmi_factor": f"{estimated_rate:.3%}" if estimated_rate > 0 else "N/A"
        }
    
    def _estimate_pmi_rate(self, ltv_ratio: float, loan_type: str) -> float:
        """
        Estimate PMI rate based on LTV ratio and loan type.
        
        Args:
            ltv_ratio: LTV ratio
            loan_type: Loan program type
            
        Returns:
            Estimated annual PMI rate
        """
        if loan_type in ["va", "usda"]:
            return 0.0  # These programs don't require PMI
        
        # Find appropriate rate range
        for (min_ltv, max_ltv), rate in self.pmi_rates.items():
            if min_ltv < ltv_ratio <= max_ltv:
                return rate
        
        # Default rates for edge cases
        if ltv_ratio <= 0.80:
            return 0.0  # No PMI required
        elif ltv_ratio > 0.95:
            return 0.0085  # Highest rate for very high LTV
        else:
            return 0.0055  # Default middle rate
    
    def _get_pmi_type(self, loan_type: str) -> str:
        """Get the type of mortgage insurance for the loan program."""
        pmi_types = {
            "conventional": "PMI",
            "fha": "MIP",
            "va": "None",
            "usda": "None",
            "jumbo": "PMI"
        }
        return pmi_types.get(loan_type, "PMI")
    
    def _analyze_down_payment_requirements(self, loan_amount: float, appraised_value: float,
                                         loan_type: str) -> Dict[str, Any]:
        """
        Analyze down payment requirements and recommendations.
        
        Args:
            loan_amount: Loan amount
            appraised_value: Property appraised value
            loan_type: Loan program type
            
        Returns:
            Dictionary containing down payment analysis
        """
        current_down_payment = appraised_value - loan_amount
        current_down_payment_pct = current_down_payment / appraised_value
        
        # Minimum down payment requirements by loan type
        min_down_payment_pct = {
            "conventional": 0.03,  # 3% minimum
            "fha": 0.035,          # 3.5% minimum
            "va": 0.00,            # 0% minimum
            "usda": 0.00,          # 0% minimum
            "jumbo": 0.20          # 20% typical minimum
        }.get(loan_type, 0.03)
        
        min_down_payment_amount = appraised_value * min_down_payment_pct
        
        # Check if additional down payment is needed
        additional_required = current_down_payment < min_down_payment_amount
        additional_amount = max(0, min_down_payment_amount - current_down_payment)
        
        # Recommended down payment for optimal terms
        recommended_pct = {
            "conventional": 0.20,  # 20% to avoid PMI
            "fha": 0.10,           # 10% for better terms
            "va": 0.00,            # No recommendation needed
            "usda": 0.00,          # No recommendation needed
            "jumbo": 0.25          # 25% for best rates
        }.get(loan_type, 0.20)
        
        recommended_amount = appraised_value * recommended_pct
        
        return {
            "current_down_payment": current_down_payment,
            "current_down_payment_percentage": round(current_down_payment_pct, 4),
            "minimum_required_percentage": min_down_payment_pct,
            "minimum_required_amount": min_down_payment_amount,
            "additional_required": additional_required,
            "additional_amount_needed": additional_amount,
            "recommended_percentage": recommended_pct,
            "recommended_amount": recommended_amount,
            "meets_minimum": not additional_required,
            "benefits_of_recommended": self._get_down_payment_benefits(
                current_down_payment_pct, recommended_pct, loan_type
            )
        }
    
    def _get_down_payment_benefits(self, current_pct: float, recommended_pct: float,
                                 loan_type: str) -> List[str]:
        """Get benefits of increasing down payment to recommended level."""
        benefits = []
        
        if current_pct < recommended_pct:
            if loan_type in ["conventional", "jumbo"] and recommended_pct >= 0.20:
                benefits.append("Avoid private mortgage insurance (PMI)")
                benefits.append("Lower monthly payment")
                benefits.append("Better interest rates")
            
            benefits.append("Lower loan amount and total interest paid")
            benefits.append("Stronger equity position")
            benefits.append("Reduced lending risk")
        
        return benefits
    
    def _identify_ltv_red_flags(self, ltv_calculation: Dict[str, Any],
                              cltv_calculation: Dict[str, Any],
                              compliance_check: Dict[str, Any],
                              loan_type: str) -> List[str]:
        """
        Identify LTV-related red flags.
        
        Args:
            ltv_calculation: LTV calculation results
            cltv_calculation: CLTV calculation results
            compliance_check: Compliance check results
            loan_type: Loan program type
            
        Returns:
            List of red flag descriptions
        """
        red_flags = []
        
        ltv_ratio = ltv_calculation["ltv_ratio"]
        cltv_ratio = cltv_calculation["cltv_ratio"]
        
        # Extreme LTV red flags
        if ltv_ratio > 1.00:
            red_flags.append("Loan amount exceeds property value (LTV > 100%)")
        elif ltv_ratio > 0.98:
            red_flags.append("Extremely high LTV ratio indicates minimal equity")
        
        # CLTV red flags
        if cltv_ratio > ltv_ratio and cltv_ratio > 1.00:
            red_flags.append("Combined financing exceeds property value (CLTV > 100%)")
        elif cltv_ratio > 1.05:
            red_flags.append("Total financing significantly exceeds property value")
        
        # Program compliance red flags
        if not compliance_check["eligible"]:
            red_flags.append(f"LTV exceeds {loan_type.upper()} program maximum limits")
        
        # Loan type specific red flags
        if loan_type == "jumbo" and ltv_ratio > 0.85:
            red_flags.append("Jumbo loan LTV exceeds typical investor guidelines")
        
        if loan_type == "conventional" and ltv_ratio > 0.95:
            red_flags.append("High-LTV conventional loan may face additional scrutiny")
        
        # Additional financing red flags
        if cltv_calculation["has_additional_financing"]:
            additional_financing = cltv_calculation["total_financing"] - cltv_calculation["primary_loan"]
            if additional_financing > ltv_calculation["appraised_value"] * 0.20:
                red_flags.append("Significant additional financing increases overall risk")
        
        return red_flags
    
    def _generate_ltv_recommendations(self, ltv_calculation: Dict[str, Any],
                                    risk_assessment: Dict[str, Any],
                                    compliance_check: Dict[str, Any],
                                    pmi_analysis: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on LTV analysis.
        
        Args:
            ltv_calculation: LTV calculation results
            risk_assessment: Risk assessment results
            compliance_check: Compliance check results
            pmi_analysis: PMI analysis results
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        ltv_ratio = ltv_calculation["ltv_ratio"]
        risk_level = risk_assessment["risk_level"]
        
        # Risk-based recommendations
        if risk_level == "very_high":
            recommendations.append("Consider increasing down payment to reduce LTV risk")
            recommendations.append("Evaluate compensating factors for high LTV")
        elif risk_level == "high":
            recommendations.append("Review borrower qualifications for high LTV loan")
        
        # Compliance recommendations
        if not compliance_check["eligible"]:
            max_ltv = compliance_check["max_ltv_allowed"]
            current_ltv = compliance_check["ltv_ratio"]
            excess_ltv = current_ltv - max_ltv
            additional_down_needed = ltv_calculation["appraised_value"] * excess_ltv
            
            recommendations.append(
                f"Increase down payment by ${additional_down_needed:,.0f} to meet program requirements"
            )
        
        # PMI recommendations
        if pmi_analysis["required"]:
            if pmi_analysis["type"] == "PMI":
                recommendations.append("Private mortgage insurance (PMI) will be required")
                recommendations.append("Consider 20% down payment to avoid PMI")
            elif pmi_analysis["type"] == "MIP":
                recommendations.append("FHA mortgage insurance premium (MIP) will be required")
        
        # LTV optimization recommendations
        if 0.80 < ltv_ratio <= 0.85:
            recommendations.append("Consider additional down payment to reach 80% LTV and avoid PMI")
        elif ltv_ratio > 0.90:
            recommendations.append("High LTV may result in higher interest rates")
        
        # Program-specific recommendations
        loan_type = compliance_check["loan_type"]
        if loan_type == "jumbo" and ltv_ratio > 0.75:
            recommendations.append("Consider reducing LTV for better jumbo loan pricing")
        
        return recommendations
    
    def _calculate_confidence_score(self, ltv_calculation: Dict[str, Any],
                                  property_info: Dict[str, Any],
                                  loan_info: Dict[str, Any]) -> float:
        """
        Calculate confidence score for LTV calculation.
        
        Args:
            ltv_calculation: LTV calculation results
            property_info: Property information
            loan_info: Loan information
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.9  # Base confidence for LTV calculation
        
        # Adjust for property valuation confidence
        if "stated_value" in property_info and "appraised_value" in property_info:
            stated_value = property_info["stated_value"]
            appraised_value = property_info["appraised_value"]
            
            if stated_value > 0:
                value_variance = abs(appraised_value - stated_value) / stated_value
                if value_variance > 0.10:  # >10% variance
                    confidence -= 0.15
                elif value_variance > 0.05:  # >5% variance
                    confidence -= 0.08
        
        # Adjust for loan complexity
        if ltv_calculation["ltv_ratio"] > 0.95:
            confidence -= 0.05  # High LTV adds uncertainty
        
        # Ensure confidence is within valid range
        return max(0.5, min(1.0, confidence))