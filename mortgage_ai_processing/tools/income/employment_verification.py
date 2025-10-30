"""Employment Verification Tool - Converted from TypeScript.

Verifies employment status and income consistency using data extracted
from documents by the document_extractor tool. Performs validation
against employment verification letters, pay stubs, and tax documents.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import re
import math

from ..base import BaseTool, ToolResult, ToolMetadata


class VerificationLevel(Enum):
    """Employment verification levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    COMPREHENSIVE = "comprehensive"


class EmploymentStatus(Enum):
    """Employment verification status."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    INCONSISTENT = "inconsistent"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class EmploymentData:
    """Employment data structure."""
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    employment_status: Optional[str] = None
    start_date: Optional[str] = None
    employment_years: Optional[int] = None
    annual_income: Optional[float] = None
    monthly_income: Optional[float] = None
    employment_type: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    hr_contact: Optional[str] = None
    verification_date: Optional[str] = None


@dataclass
class PayStubData:
    """Pay stub data structure."""
    employer_name: Optional[str] = None
    employee_name: Optional[str] = None
    pay_period_start: Optional[str] = None
    pay_period_end: Optional[str] = None
    gross_pay: Optional[float] = None
    net_pay: Optional[float] = None
    ytd_gross: Optional[float] = None
    ytd_net: Optional[float] = None
    pay_frequency: Optional[str] = None


@dataclass
class TaxData:
    """Tax document data structure."""
    employer_name: Optional[str] = None
    annual_wages: Optional[float] = None
    tax_year: Optional[str] = None
    w2_wages: Optional[float] = None
    federal_withholding: Optional[float] = None
    state_withholding: Optional[float] = None


@dataclass
class VerificationDetails:
    """Detailed verification results."""
    employer: Dict[str, Any]
    income: Dict[str, Any]
    employment: Dict[str, Any]
    document_consistency: Dict[str, Any]


@dataclass
class EmploymentVerificationResult:
    """Complete employment verification result."""
    is_employed: bool
    employment_status: str
    verification_details: VerificationDetails
    recommendations: List[str]
    confidence: float
    risk_factors: List[str]


class EmploymentVerificationTool(BaseTool):
    """Tool for verifying employment status and income consistency."""
    
    def __init__(self):
        from ..base import ToolCategory
        super().__init__(
            name="employment_verification_tool",
            description="Verifies employment status and income consistency using extracted document data. Validates employment information across multiple document sources including employment letters, pay stubs, and tax documents.",
            category=ToolCategory.FINANCIAL_ANALYSIS,
            version="1.0.0",
            agent_domain="income_verification"
        )
        
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool input parameters."""
        return self.get_parameters_schema()
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "extracted_employment_data": {
                    "type": "object",
                    "description": "Employment data extracted from employment verification letters or HR documents",
                    "properties": {
                        "employer_name": {"type": "string"},
                        "job_title": {"type": "string"},
                        "employment_status": {"type": "string"},
                        "start_date": {"type": "string"},
                        "employment_years": {"type": "integer"},
                        "annual_income": {"type": "number"},
                        "monthly_income": {"type": "number"},
                        "employment_type": {"type": "string"},
                        "department": {"type": "string"},
                        "employee_id": {"type": "string"},
                        "hr_contact": {"type": "string"},
                        "verification_date": {"type": "string"}
                    }
                },
                "extracted_paystub_data": {
                    "type": "array",
                    "description": "Array of pay stub data extracted from pay stub documents",
                    "items": {
                        "type": "object",
                        "properties": {
                            "employer_name": {"type": "string"},
                            "employee_name": {"type": "string"},
                            "pay_period_start": {"type": "string"},
                            "pay_period_end": {"type": "string"},
                            "gross_pay": {"type": "number"},
                            "net_pay": {"type": "number"},
                            "ytd_gross": {"type": "number"},
                            "ytd_net": {"type": "number"},
                            "pay_frequency": {"type": "string"}
                        }
                    }
                },
                "extracted_tax_data": {
                    "type": "array",
                    "description": "Array of tax document data (W-2, 1099, etc.) extracted from tax documents",
                    "items": {
                        "type": "object",
                        "properties": {
                            "employer_name": {"type": "string"},
                            "annual_wages": {"type": "number"},
                            "tax_year": {"type": "string"},
                            "w2_wages": {"type": "number"},
                            "federal_withholding": {"type": "number"},
                            "state_withholding": {"type": "number"}
                        }
                    }
                },
                "verification_level": {
                    "type": "string",
                    "description": "Level of verification thoroughness to perform",
                    "enum": ["basic", "enhanced", "comprehensive"],
                    "default": "enhanced"
                },
                "expected_employer": {
                    "type": "string",
                    "description": "Expected employer name for validation"
                },
                "expected_income": {
                    "type": "number",
                    "description": "Expected annual income for validation"
                },
                "verification_date": {
                    "type": "string",
                    "description": "Date for which employment should be verified"
                }
            },
            "required": [],
            "additionalProperties": False
        }
        
    async def execute(self, **kwargs) -> ToolResult:
        """Execute employment verification."""
        try:
            extracted_employment_data = kwargs.get("extracted_employment_data")
            extracted_paystub_data = kwargs.get("extracted_paystub_data", [])
            extracted_tax_data = kwargs.get("extracted_tax_data", [])
            verification_level = kwargs.get("verification_level", "enhanced")
            expected_employer = kwargs.get("expected_employer")
            expected_income = kwargs.get("expected_income")
            verification_date = kwargs.get("verification_date", datetime.now().strftime("%Y-%m-%d"))
            
            # Validate input parameters
            if not extracted_employment_data and not extracted_paystub_data and not extracted_tax_data:
                raise ValueError("At least one data source (employment data, pay stub data, or tax data) must be provided")
                
            # Convert dictionaries to dataclasses
            employment_data = None
            if extracted_employment_data:
                employment_data = EmploymentData(**extracted_employment_data)
                
            paystub_data = [PayStubData(**ps) for ps in extracted_paystub_data]
            tax_data = [TaxData(**td) for td in extracted_tax_data]
            
            # Simulate processing time
            await asyncio.sleep(0.3)
            
            # Perform verification
            result = await self._verify_employment(
                employment_data,
                paystub_data,
                tax_data,
                VerificationLevel(verification_level),
                expected_employer,
                expected_income,
                verification_date
            )
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "is_employed": result.is_employed,
                    "employment_status": result.employment_status,
                    "verification_details": {
                        "employer": result.verification_details.employer,
                        "income": result.verification_details.income,
                        "employment": result.verification_details.employment,
                        "document_consistency": result.verification_details.document_consistency
                    },
                    "recommendations": result.recommendations,
                    "confidence": result.confidence,
                    "risk_factors": result.risk_factors,
                    "verification_summary": {
                        "verification_level": verification_level,
                        "document_sources": [
                            *([f"employment_letter"] if employment_data else []),
                            *([f"{len(paystub_data)}_pay_stubs"] if paystub_data else []),
                            *([f"{len(tax_data)}_tax_documents"] if tax_data else [])
                        ],
                        "overall_assessment": self._get_overall_assessment(result),
                        "key_findings": self._get_key_findings(result)
                    }
                },
                execution_time=0.3
            )
            
        except Exception as e:
            self.logger.error(f"Employment verification failed: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=f"Employment verification failed: {str(e)}",
                execution_time=0.0
            )
            
    async def _verify_employment(
        self,
        employment_data: Optional[EmploymentData],
        paystub_data: List[PayStubData],
        tax_data: List[TaxData],
        verification_level: VerificationLevel,
        expected_employer: Optional[str],
        expected_income: Optional[float],
        verification_date: str
    ) -> EmploymentVerificationResult:
        """Perform comprehensive employment verification."""
        
        # Initialize result structure
        verification_details = VerificationDetails(
            employer={
                "name": "",
                "verified": False,
                "confidence": 0.0,
                "sources": []
            },
            income={
                "annual": 0.0,
                "monthly": 0.0,
                "verified": False,
                "confidence": 0.0,
                "consistency": 0.0,
                "sources": []
            },
            employment={
                "title": "",
                "start_date": "",
                "employment_type": "",
                "verified": False,
                "confidence": 0.0
            },
            document_consistency={
                "score": 0.0,
                "issues": [],
                "warnings": []
            }
        )
        
        result = EmploymentVerificationResult(
            is_employed=False,
            employment_status=EmploymentStatus.INSUFFICIENT_DATA.value,
            verification_details=verification_details,
            recommendations=[],
            confidence=0.0,
            risk_factors=[]
        )
        
        # Step 1: Verify Employer Information
        await self._verify_employer_information(
            employment_data, paystub_data, tax_data, expected_employer, result
        )
        
        # Step 2: Verify Income Information
        await self._verify_income_information(
            employment_data, paystub_data, tax_data, expected_income, result
        )
        
        # Step 3: Verify Employment Details
        await self._verify_employment_details(employment_data, result)
        
        # Step 4: Check Document Consistency
        await self._check_document_consistency(
            employment_data, paystub_data, tax_data, verification_level, result
        )
        
        # Step 5: Calculate Overall Status
        self._calculate_overall_status(result)
        
        # Step 6: Generate Recommendations
        self._generate_recommendations(result, employment_data, paystub_data, tax_data)
        
        return result
        
    async def _verify_employer_information(
        self,
        employment_data: Optional[EmploymentData],
        paystub_data: List[PayStubData],
        tax_data: List[TaxData],
        expected_employer: Optional[str],
        result: EmploymentVerificationResult
    ) -> None:
        """Verify employer information across all sources."""
        
        employers = []
        sources = []
        
        # Collect employer names from all sources
        if employment_data and employment_data.employer_name:
            employers.append(employment_data.employer_name)
            sources.append("employment_letter")
            
        for i, paystub in enumerate(paystub_data):
            if paystub.employer_name:
                employers.append(paystub.employer_name)
                sources.append(f"pay_stub_{i + 1}")
                
        for i, tax_doc in enumerate(tax_data):
            if tax_doc.employer_name:
                employers.append(tax_doc.employer_name)
                sources.append(f"tax_document_{i + 1}")
                
        if not employers:
            result.verification_details.employer["confidence"] = 0.0
            result.verification_details.document_consistency["issues"].append(
                "No employer information found in any document"
            )
            return
            
        # Normalize employer names for comparison
        normalized_employers = [self._normalize_employer_name(emp) for emp in employers]
        unique_employers = list(set(normalized_employers))
        
        if len(unique_employers) == 1:
            # Consistent employer across all documents
            result.verification_details.employer.update({
                "name": employers[0],
                "verified": True,
                "confidence": 1.0,
                "sources": sources
            })
        else:
            # Inconsistent employer names
            result.verification_details.employer.update({
                "name": employers[0],
                "verified": False,
                "confidence": 0.3,
                "sources": sources
            })
            result.verification_details.document_consistency["issues"].append(
                f"Inconsistent employer names found: {', '.join(unique_employers)}"
            )
            
        # Check against expected employer if provided
        if expected_employer:
            expected_normalized = self._normalize_employer_name(expected_employer)
            found_match = any(
                self._calculate_string_similarity(emp, expected_normalized) > 0.8
                for emp in unique_employers
            )
            
            if not found_match:
                result.verification_details.employer["confidence"] *= 0.5
                result.verification_details.document_consistency["warnings"].append(
                    f"Employer name doesn't match expected: {expected_employer}"
                )
                
    async def _verify_income_information(
        self,
        employment_data: Optional[EmploymentData],
        paystub_data: List[PayStubData],
        tax_data: List[TaxData],
        expected_income: Optional[float],
        result: EmploymentVerificationResult
    ) -> None:
        """Verify income information across all sources."""
        
        annual_incomes = []
        sources = []
        
        # Collect income from employment letter
        if employment_data:
            if employment_data.annual_income:
                annual_incomes.append(employment_data.annual_income)
                sources.append("employment_letter")
            elif employment_data.monthly_income:
                annual_incomes.append(employment_data.monthly_income * 12)
                sources.append("employment_letter_monthly")
                
        # Collect income from pay stubs
        for i, paystub in enumerate(paystub_data):
            if paystub.ytd_gross and paystub.pay_period_end:
                annual_estimate = self._estimate_annual_from_ytd(paystub)
                if annual_estimate > 0:
                    annual_incomes.append(annual_estimate)
                    sources.append(f"pay_stub_ytd_{i + 1}")
                    
            if paystub.gross_pay and paystub.pay_frequency:
                annual_from_period = self._calculate_annual_from_pay_period(paystub)
                if annual_from_period > 0:
                    annual_incomes.append(annual_from_period)
                    sources.append(f"pay_stub_period_{i + 1}")
                    
        # Collect income from tax documents
        for i, tax_doc in enumerate(tax_data):
            wages = tax_doc.annual_wages or tax_doc.w2_wages
            if wages:
                annual_incomes.append(wages)
                sources.append(f"tax_document_{i + 1}")
                
        if not annual_incomes:
            result.verification_details.income["confidence"] = 0.0
            result.verification_details.document_consistency["issues"].append(
                "No income information found in any document"
            )
            return
            
        # Analyze income consistency
        avg_annual = sum(annual_incomes) / len(annual_incomes)
        income_variance = self._calculate_variance(annual_incomes)
        income_consistency = max(0, 1 - (income_variance / (avg_annual * avg_annual)))
        
        result.verification_details.income.update({
            "annual": round(avg_annual),
            "monthly": round(avg_annual / 12),
            "consistency": income_consistency,
            "sources": sources
        })
        
        # Set verification status based on consistency
        if income_consistency > 0.9:
            result.verification_details.income.update({
                "verified": True,
                "confidence": 0.95
            })
        elif income_consistency > 0.8:
            result.verification_details.income.update({
                "verified": True,
                "confidence": 0.8
            })
            result.verification_details.document_consistency["warnings"].append(
                "Minor income inconsistencies detected"
            )
        else:
            result.verification_details.income.update({
                "verified": False,
                "confidence": 0.5
            })
            result.verification_details.document_consistency["issues"].append(
                f"Significant income inconsistencies: {', '.join([f'${int(i):,}' for i in annual_incomes])}"
            )
            
        # Check against expected income
        if expected_income:
            income_difference = abs(avg_annual - expected_income) / expected_income
            if income_difference > 0.1:
                result.verification_details.income["confidence"] *= 0.8
                result.verification_details.document_consistency["warnings"].append(
                    f"Income differs from expected by {income_difference * 100:.1f}%"
                )
                
    async def _verify_employment_details(
        self,
        employment_data: Optional[EmploymentData],
        result: EmploymentVerificationResult
    ) -> None:
        """Verify employment details."""
        
        confidence = 0.0
        verified = False
        
        if employment_data:
            # Job title
            if employment_data.job_title:
                result.verification_details.employment["title"] = employment_data.job_title
                confidence += 0.3
                
            # Start date
            if employment_data.start_date:
                result.verification_details.employment["start_date"] = employment_data.start_date
                confidence += 0.3
            elif employment_data.employment_years:
                # Estimate start date from years of employment
                current_year = datetime.now().year
                estimated_start_year = current_year - employment_data.employment_years
                result.verification_details.employment["start_date"] = f"{estimated_start_year}-01-01"
                confidence += 0.2
                
            # Employment type
            employment_type = employment_data.employment_type or employment_data.employment_status
            if employment_type:
                result.verification_details.employment["employment_type"] = employment_type
                confidence += 0.2
                
            # Overall employment verification
            if confidence > 0.6:
                verified = True
                
        result.verification_details.employment.update({
            "verified": verified,
            "confidence": confidence
        })
        
        if not verified:
            result.verification_details.document_consistency["warnings"].append(
                "Limited employment details available for verification"
            )
            
    async def _check_document_consistency(
        self,
        employment_data: Optional[EmploymentData],
        paystub_data: List[PayStubData],
        tax_data: List[TaxData],
        verification_level: VerificationLevel,
        result: EmploymentVerificationResult
    ) -> None:
        """Check consistency across all documents."""
        
        consistency_score = 1.0
        issues = result.verification_details.document_consistency["issues"]
        warnings = result.verification_details.document_consistency["warnings"]
        
        # Check date consistency in pay stubs
        if len(paystub_data) > 1:
            pay_dates = [ps.pay_period_end for ps in paystub_data if ps.pay_period_end]
            if len(pay_dates) > 1:
                date_gaps = self._analyze_date_gaps(sorted(pay_dates))
                if date_gaps["irregular_gaps"] > 0:
                    consistency_score *= 0.9
                    warnings.append(f"{date_gaps['irregular_gaps']} irregular pay period gaps detected")
                    
        # Check name consistency across documents
        names = self._extract_all_names(paystub_data)
        if len(names) > 1:
            name_consistency = self._check_name_consistency(names)
            if name_consistency < 0.8:
                consistency_score *= 0.8
                issues.append("Inconsistent employee names across documents")
                
        # Enhanced checks for comprehensive verification
        if verification_level == VerificationLevel.COMPREHENSIVE:
            # Check for temporal consistency
            if tax_data and paystub_data:
                temporal_consistency = self._check_temporal_consistency(tax_data, paystub_data)
                consistency_score *= temporal_consistency
                
        # Penalize based on number of issues
        consistency_score *= max(0.3, 1 - (len(issues) * 0.2))
        consistency_score *= max(0.7, 1 - (len(warnings) * 0.1))
        
        result.verification_details.document_consistency["score"] = max(0, min(1, consistency_score))
        
    def _calculate_overall_status(self, result: EmploymentVerificationResult) -> None:
        """Calculate overall employment status and confidence."""
        
        employer_confidence = result.verification_details.employer["confidence"]
        income_confidence = result.verification_details.income["confidence"]
        employment_confidence = result.verification_details.employment["confidence"]
        consistency_score = result.verification_details.document_consistency["score"]
        
        # Calculate weighted confidence
        overall_confidence = (
            employer_confidence * 0.3 +
            income_confidence * 0.4 +
            employment_confidence * 0.2 +
            consistency_score * 0.1
        )
        
        result.confidence = round(overall_confidence, 2)
        
        # Determine employment status
        if overall_confidence >= 0.8:
            result.employment_status = EmploymentStatus.VERIFIED.value
            result.is_employed = True
        elif overall_confidence >= 0.6:
            result.employment_status = EmploymentStatus.VERIFIED.value
            result.is_employed = True
            result.risk_factors.append("Lower confidence verification - additional documentation recommended")
        elif overall_confidence >= 0.4:
            result.employment_status = EmploymentStatus.UNVERIFIED.value
            result.is_employed = False
            result.risk_factors.append("Insufficient verification confidence")
        else:
            result.employment_status = EmploymentStatus.INCONSISTENT.value
            result.is_employed = False
            result.risk_factors.append("Significant inconsistencies detected")
            
        # Add specific risk factors
        if result.verification_details.document_consistency["issues"]:
            result.risk_factors.append("Document consistency issues detected")
        if result.verification_details.income["consistency"] < 0.8:
            result.risk_factors.append("Income inconsistencies across documents")
            
    def _generate_recommendations(
        self,
        result: EmploymentVerificationResult,
        employment_data: Optional[EmploymentData],
        paystub_data: List[PayStubData],
        tax_data: List[TaxData]
    ) -> None:
        """Generate recommendations based on verification results."""
        
        recommendations = result.recommendations
        
        if result.confidence < 0.8:
            recommendations.append("Request additional employment documentation for verification")
            
        if result.verification_details.income["confidence"] < 0.7:
            recommendations.append("Obtain recent pay stubs covering at least 2 pay periods")
            
        if result.verification_details.employer["confidence"] < 0.8:
            recommendations.append("Request direct employer verification or HR contact")
            
        if result.verification_details.document_consistency["score"] < 0.7:
            recommendations.append("Review document inconsistencies and request clarification")
            
        if not tax_data:
            recommendations.append("Request most recent tax returns (W-2 or 1099) for income verification")
            
        if result.employment_status == EmploymentStatus.UNVERIFIED.value:
            recommendations.append("Consider alternative income verification methods or manual review")
            
    # Helper methods
    def _normalize_employer_name(self, name: str) -> str:
        """Normalize employer name for comparison."""
        return re.sub(
            r'\b(inc|llc|corp|corporation|company|co|ltd)\b',
            '',
            re.sub(r'[^\w\s]', '', name.lower())
        ).strip()
        
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Levenshtein distance."""
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
            
        distance = self._levenshtein_distance(longer, shorter)
        return (len(longer) - distance) / len(longer)
        
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
            
        if len(s2) == 0:
            return len(s1)
            
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
        
    def _estimate_annual_from_ytd(self, paystub: PayStubData) -> float:
        """Estimate annual income from YTD gross."""
        if not paystub.ytd_gross or not paystub.pay_period_end:
            return 0.0
            
        try:
            pay_date = datetime.strptime(paystub.pay_period_end, "%Y-%m-%d")
            day_of_year = pay_date.timetuple().tm_yday
            days_in_year = 366 if self._is_leap_year(pay_date.year) else 365
            
            return round((paystub.ytd_gross * days_in_year) / day_of_year)
        except:
            return 0.0
            
    def _calculate_annual_from_pay_period(self, paystub: PayStubData) -> float:
        """Calculate annual income from pay period data."""
        if not paystub.gross_pay or not paystub.pay_frequency:
            return 0.0
            
        frequency_multipliers = {
            'weekly': 52,
            'bi-weekly': 26,
            'biweekly': 26,
            'semi-monthly': 24,
            'monthly': 12,
            'quarterly': 4,
            'annually': 1
        }
        
        frequency = paystub.pay_frequency.lower()
        multiplier = frequency_multipliers.get(frequency, 26)  # Default to bi-weekly
        
        return round(paystub.gross_pay * multiplier)
        
    def _calculate_variance(self, numbers: List[float]) -> float:
        """Calculate variance of a list of numbers."""
        if len(numbers) <= 1:
            return 0.0
            
        mean = sum(numbers) / len(numbers)
        squared_diffs = [(val - mean) ** 2 for val in numbers]
        return sum(squared_diffs) / len(numbers)
        
    def _analyze_date_gaps(self, dates: List[str]) -> Dict[str, int]:
        """Analyze gaps between pay dates."""
        if len(dates) < 2:
            return {"regular_gaps": 0, "irregular_gaps": 0}
            
        gaps = []
        for i in range(1, len(dates)):
            try:
                date1 = datetime.strptime(dates[i-1], "%Y-%m-%d")
                date2 = datetime.strptime(dates[i], "%Y-%m-%d")
                days_diff = abs((date2 - date1).days)
                gaps.append(days_diff)
            except:
                continue
                
        if not gaps:
            return {"regular_gaps": 0, "irregular_gaps": 0}
            
        # Determine expected gap (most common, rounded to nearest week)
        gap_counts = {}
        for gap in gaps:
            rounded_gap = round(gap / 7) * 7
            gap_counts[rounded_gap] = gap_counts.get(rounded_gap, 0) + 1
            
        expected_gap = max(gap_counts.keys(), key=lambda k: gap_counts[k])
        
        regular_gaps = sum(1 for gap in gaps if abs(gap - expected_gap) <= 3)
        irregular_gaps = len(gaps) - regular_gaps
        
        return {"regular_gaps": regular_gaps, "irregular_gaps": irregular_gaps}
        
    def _extract_all_names(self, paystub_data: List[PayStubData]) -> List[str]:
        """Extract all employee names from pay stubs."""
        return [ps.employee_name for ps in paystub_data if ps.employee_name]
        
    def _check_name_consistency(self, names: List[str]) -> float:
        """Check consistency of names across documents."""
        if len(names) <= 1:
            return 1.0
            
        # Normalize names
        normalized_names = [
            re.sub(r'[^\w\s]', '', name.lower()).strip()
            for name in names
        ]
        
        total_similarity = 0.0
        comparisons = 0
        
        for i in range(len(normalized_names)):
            for j in range(i + 1, len(normalized_names)):
                total_similarity += self._calculate_string_similarity(
                    normalized_names[i], normalized_names[j]
                )
                comparisons += 1
                
        return total_similarity / comparisons if comparisons > 0 else 1.0
        
    def _check_temporal_consistency(
        self, tax_data: List[TaxData], paystub_data: List[PayStubData]
    ) -> float:
        """Check temporal consistency between tax and pay stub data."""
        consistency = 1.0
        
        tax_years = [int(td.tax_year) for td in tax_data if td.tax_year and td.tax_year.isdigit()]
        paystub_years = []
        
        for ps in paystub_data:
            if ps.pay_period_end:
                try:
                    year = datetime.strptime(ps.pay_period_end, "%Y-%m-%d").year
                    paystub_years.append(year)
                except:
                    continue
                    
        if tax_years and paystub_years:
            recent_tax_year = max(tax_years)
            has_matching_paystub = any(
                year == recent_tax_year or year == recent_tax_year + 1
                for year in paystub_years
            )
            
            if not has_matching_paystub:
                consistency *= 0.8
                
        return consistency
        
    def _is_leap_year(self, year: int) -> bool:
        """Check if a year is a leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        
    def _get_overall_assessment(self, result: EmploymentVerificationResult) -> str:
        """Get overall assessment summary."""
        if result.confidence >= 0.8:
            return "Strong employment verification with high confidence"
        elif result.confidence >= 0.6:
            return "Good employment verification with acceptable confidence"
        elif result.confidence >= 0.4:
            return "Weak employment verification requiring additional documentation"
        else:
            return "Poor employment verification with significant concerns"
            
    def _get_key_findings(self, result: EmploymentVerificationResult) -> List[str]:
        """Get key findings from verification."""
        findings = []
        
        if result.verification_details.employer["verified"]:
            findings.append(f"Employer verified: {result.verification_details.employer['name']}")
        else:
            findings.append("Employer verification failed or inconsistent")
            
        if result.verification_details.income["verified"]:
            annual = result.verification_details.income["annual"]
            findings.append(f"Income verified: ${annual:,} annually")
        else:
            findings.append("Income verification failed or inconsistent")
            
        if result.verification_details.employment["verified"]:
            findings.append("Employment details verified")
        else:
            findings.append("Limited employment details available")
            
        consistency_score = result.verification_details.document_consistency["score"]
        if consistency_score >= 0.8:
            findings.append("High document consistency")
        elif consistency_score >= 0.6:
            findings.append("Acceptable document consistency")
        else:
            findings.append("Poor document consistency")
            
        return findings
        
    def get_tool_info(self) -> Dict[str, Any]:
        """Get comprehensive tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.metadata.version,
            "verification_levels": [level.value for level in VerificationLevel],
            "employment_statuses": [status.value for status in EmploymentStatus],
            "features": {
                "employer_verification": True,
                "income_verification": True,
                "employment_details_verification": True,
                "document_consistency_checking": True,
                "multi_source_validation": True,
                "confidence_scoring": True,
                "risk_assessment": True,
                "recommendations": True
            },
            "supported_documents": [
                "employment_verification_letters",
                "pay_stubs",
                "tax_documents",
                "w2_forms",
                "1099_forms"
            ],
            "parameters_schema": self.get_parameters_schema()
        }