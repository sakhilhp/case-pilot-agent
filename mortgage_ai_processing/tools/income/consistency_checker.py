"""
Income Consistency Checker Tool for mortgage processing.

This tool performs cross-validation of income data across multiple documents,
detecting discrepancies and providing verification accuracy scoring for mortgage lending.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import statistics

from ..base import BaseTool, ToolResult


class IncomeConsistencyCheckerTool(BaseTool):
    """
    Tool for cross-validating income data across multiple documents.
    
    This tool analyzes income documents to:
    - Detect discrepancies across multiple income sources
    - Calculate variance percentages between documents
    - Identify suspicious patterns that may indicate fraud
    - Provide verification accuracy scoring
    - Generate recommendations for resolving inconsistencies
    """
    
    def __init__(self):

    
        from ..base import ToolCategory
        super().__init__(
            name="income_consistency_checker",
            description="Cross-document income validation and discrepancy detection for mortgage lending",
            category=ToolCategory.FINANCIAL_ANALYSIS,
            agent_domain="income_verification"
        )
        
        # Variance thresholds for different scenarios
        self.variance_thresholds = {
            "acceptable": 0.05,      # 5% - normal variance
            "moderate": 0.10,        # 10% - moderate concern
            "significant": 0.20,     # 20% - significant discrepancy
            "major": 0.30           # 30% - major red flag
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
                        "stated_income": {"type": "number"}
                    },
                    "required": ["name", "stated_income"]
                },
                "income_documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "document_id": {"type": "string"},
                            "document_type": {"type": "string"},
                            "extracted_data": {"type": "object"},
                            "file_path": {"type": "string"}
                        },
                        "required": ["document_id", "document_type", "extracted_data"]
                    }
                },
                "verification_threshold": {
                    "type": "number",
                    "description": "Variance threshold for flagging discrepancies (default: 0.10)",
                    "minimum": 0.01,
                    "maximum": 1.0
                }
            },
            "required": ["application_id", "borrower_info", "income_documents"]
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
        Execute income consistency checking analysis.
        
        Args:
            application_id: Unique identifier for the mortgage application
            borrower_info: Information about the borrower
            income_documents: List of income-related documents
            verification_threshold: Variance threshold for flagging discrepancies
            
        Returns:
            ToolResult containing consistency analysis
        """
        try:
            application_id = kwargs["application_id"]
            borrower_info = kwargs["borrower_info"]
            income_documents = kwargs["income_documents"]
            verification_threshold = kwargs.get("verification_threshold", 0.10)
            
            self.logger.info(f"Starting income consistency check for application {application_id}")
            
            if len(income_documents) < 2:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data={
                        "has_discrepancies": False,
                        "consistency_status": "insufficient_documents",
                        "max_variance_percentage": 0.0,
                        "confidence_score": 0.5,
                        "consistency_score": 1.0,
                        "document_count": len(income_documents),
                        "recommendations": ["Provide additional income documents for cross-validation"],
                        "discrepant_documents": [],
                        "suspicious_patterns": []
                    }
                )
            
            # Normalize income data across documents
            normalized_incomes = self._normalize_income_data(income_documents)
            
            # Perform cross-document consistency analysis
            consistency_analysis = self._analyze_cross_document_consistency(
                normalized_incomes, borrower_info, verification_threshold
            )
            
            # Detect suspicious patterns
            suspicious_patterns = self._detect_suspicious_patterns(
                normalized_incomes, consistency_analysis
            )
            
            # Calculate overall consistency metrics
            consistency_metrics = self._calculate_consistency_metrics(
                consistency_analysis, suspicious_patterns
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                consistency_analysis, suspicious_patterns, verification_threshold
            )
            
            result_data = {
                "has_discrepancies": consistency_analysis["has_discrepancies"],
                "consistency_status": consistency_analysis["status"],
                "max_variance_percentage": consistency_analysis["max_variance"],
                "confidence_score": consistency_metrics["confidence_score"],
                "consistency_score": consistency_metrics["consistency_score"],
                "document_count": len(income_documents),
                "recommendations": recommendations,
                "discrepant_documents": consistency_analysis["discrepant_documents"],
                "suspicious_patterns": suspicious_patterns,
                "variance_analysis": consistency_analysis["variance_details"],
                "income_comparison": consistency_analysis["income_comparison"],
                "employer_consistency": consistency_analysis["employer_consistency"],
                "temporal_analysis": consistency_analysis["temporal_analysis"]
            }
            
            self.logger.info(f"Income consistency check completed for application {application_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"Income consistency check failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    def _normalize_income_data(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize income data from documents for comparison.
        
        Args:
            documents: List of income documents
            
        Returns:
            List of normalized income data
        """
        normalized_data = []
        
        for doc in documents:
            extracted_data = doc.get("extracted_data", {})
            doc_type = doc.get("document_type", "unknown")
            
            normalized_doc = {
                "document_id": doc.get("document_id"),
                "document_type": doc_type,
                "file_path": doc.get("file_path", ""),
                "employer": None,
                "annual_income": None,
                "monthly_income": None,
                "pay_frequency": None,
                "income_type": None,
                "date_info": None,
                "confidence": 0.5
            }
            
            # Extract employer information
            employer_fields = ["employer", "company", "employer_name", "company_name", "payer"]
            for field in employer_fields:
                if field in extracted_data:
                    normalized_doc["employer"] = str(extracted_data[field]).strip()
                    break
            
            # Extract and normalize income amounts
            income_amount, frequency = self._extract_income_amount_and_frequency(extracted_data, doc_type)
            
            if income_amount and frequency:
                normalized_doc["annual_income"] = self._convert_to_annual(income_amount, frequency)
                normalized_doc["monthly_income"] = normalized_doc["annual_income"] / 12
                normalized_doc["pay_frequency"] = frequency
            
            # Extract income type
            normalized_doc["income_type"] = self._determine_income_type(extracted_data, doc_type)
            
            # Extract date information
            normalized_doc["date_info"] = self._extract_date_information(extracted_data)
            
            # Calculate document confidence
            normalized_doc["confidence"] = self._calculate_document_confidence(normalized_doc, extracted_data)
            
            normalized_data.append(normalized_doc)
        
        return normalized_data
    
    def _extract_income_amount_and_frequency(self, extracted_data: Dict[str, Any], 
                                           doc_type: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract income amount and frequency from document data.
        
        Args:
            extracted_data: Extracted document data
            doc_type: Document type
            
        Returns:
            Tuple of (income_amount, frequency)
        """
        income_amount = None
        frequency = None
        
        # Income amount fields (in order of preference)
        income_fields = [
            "annual_salary", "salary", "annual_income", "yearly_salary",
            "gross_pay", "income", "net_pay", "total_income", "wages",
            "monthly_income", "monthly_salary"
        ]
        
        # Frequency fields
        frequency_fields = ["pay_period", "pay_frequency", "frequency"]
        
        # Extract income amount
        for field in income_fields:
            if field in extracted_data:
                try:
                    income_amount = float(extracted_data[field])
                    
                    # Infer frequency from field name if not explicitly provided
                    if "annual" in field or "yearly" in field:
                        frequency = "annual"
                    elif "monthly" in field:
                        frequency = "monthly"
                    
                    break
                except (ValueError, TypeError):
                    continue
        
        # Extract frequency if not inferred
        if not frequency:
            for field in frequency_fields:
                if field in extracted_data:
                    frequency = str(extracted_data[field]).lower()
                    break
        
        # Default frequency based on document type
        if not frequency:
            if doc_type == "employment":
                frequency = "annual"
            else:
                frequency = "monthly"  # Default assumption
        
        return income_amount, frequency
    
    def _convert_to_annual(self, amount: float, frequency: str) -> float:
        """
        Convert income amount to annual equivalent.
        
        Args:
            amount: Income amount
            frequency: Pay frequency
            
        Returns:
            Annual income amount
        """
        frequency = frequency.lower()
        
        if frequency in ["annual", "yearly", "year"]:
            return amount
        elif frequency in ["monthly", "month"]:
            return amount * 12
        elif frequency in ["biweekly", "bi-weekly", "every two weeks"]:
            return amount * 26
        elif frequency in ["weekly", "week"]:
            return amount * 52
        elif frequency in ["semimonthly", "semi-monthly", "twice monthly"]:
            return amount * 24
        elif frequency in ["quarterly", "quarter"]:
            return amount * 4
        elif frequency in ["hourly", "hour"]:
            # Assume 40 hours per week, 52 weeks per year
            return amount * 40 * 52
        else:
            # Default to annual if frequency is unknown
            return amount
    
    def _determine_income_type(self, extracted_data: Dict[str, Any], doc_type: str) -> str:
        """Determine the type of income from document data."""
        # Check for specific income type indicators
        if any(field in extracted_data for field in ["salary", "annual_salary", "base_salary"]):
            return "salary"
        elif any(field in extracted_data for field in ["wages", "hourly_wage"]):
            return "wages"
        elif any(field in extracted_data for field in ["overtime", "overtime_pay"]):
            return "overtime"
        elif any(field in extracted_data for field in ["bonus", "bonus_pay"]):
            return "bonus"
        elif any(field in extracted_data for field in ["commission", "commission_pay"]):
            return "commission"
        else:
            return "employment_income"  # Default
    
    def _extract_date_information(self, extracted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract date-related information from document data."""
        date_info = {}
        
        # Look for various date fields
        date_fields = {
            "pay_date": "pay_date",
            "pay_period_end": "pay_period_end",
            "pay_period_start": "pay_period_start",
            "issue_date": "issue_date",
            "document_date": "document_date",
            "tax_year": "tax_year"
        }
        
        for field, key in date_fields.items():
            if field in extracted_data:
                date_info[key] = extracted_data[field]
        
        return date_info if date_info else None
    
    def _analyze_cross_document_consistency(self, normalized_incomes: List[Dict[str, Any]],
                                          borrower_info: Dict[str, Any],
                                          threshold: float) -> Dict[str, Any]:
        """
        Analyze consistency across normalized income documents.
        
        Args:
            normalized_incomes: List of normalized income data
            borrower_info: Borrower information
            threshold: Variance threshold for flagging discrepancies
            
        Returns:
            Dictionary containing consistency analysis
        """
        analysis = {
            "has_discrepancies": False,
            "status": "consistent",
            "max_variance": 0.0,
            "discrepant_documents": [],
            "variance_details": [],
            "income_comparison": {},
            "employer_consistency": {},
            "temporal_analysis": {}
        }
        
        # Filter documents with valid income data
        valid_income_docs = [doc for doc in normalized_incomes if doc.get("annual_income")]
        
        if len(valid_income_docs) < 2:
            analysis["status"] = "insufficient_data"
            return analysis
        
        # Analyze income amount consistency
        income_analysis = self._analyze_income_amounts(valid_income_docs, threshold)
        analysis.update(income_analysis)
        
        # Analyze employer consistency
        employer_analysis = self._analyze_employer_consistency(valid_income_docs)
        analysis["employer_consistency"] = employer_analysis
        
        # Analyze temporal consistency
        temporal_analysis = self._analyze_temporal_consistency(valid_income_docs)
        analysis["temporal_analysis"] = temporal_analysis
        
        # Compare with stated income
        stated_income_analysis = self._compare_with_stated_income(
            valid_income_docs, borrower_info.get("stated_income", 0)
        )
        analysis["stated_income_comparison"] = stated_income_analysis
        
        # Determine overall status
        if analysis["max_variance"] > threshold:
            analysis["has_discrepancies"] = True
            if analysis["max_variance"] > self.variance_thresholds["major"]:
                analysis["status"] = "major_discrepancies"
            elif analysis["max_variance"] > self.variance_thresholds["significant"]:
                analysis["status"] = "significant_discrepancies"
            else:
                analysis["status"] = "moderate_discrepancies"
        
        return analysis
    
    def _analyze_income_amounts(self, income_docs: List[Dict[str, Any]], 
                              threshold: float) -> Dict[str, Any]:
        """
        Analyze consistency of income amounts across documents.
        
        Args:
            income_docs: List of documents with valid income data
            threshold: Variance threshold
            
        Returns:
            Dictionary containing income amount analysis
        """
        annual_incomes = [doc["annual_income"] for doc in income_docs]
        
        if not annual_incomes:
            return {
                "max_variance": 0.0,
                "variance_details": [],
                "income_comparison": {}
            }
        
        # Calculate statistics
        mean_income = statistics.mean(annual_incomes)
        median_income = statistics.median(annual_incomes)
        min_income = min(annual_incomes)
        max_income = max(annual_incomes)
        
        # Calculate variances
        variance_details = []
        max_variance = 0.0
        discrepant_documents = []
        
        for i, doc in enumerate(income_docs):
            income = doc["annual_income"]
            variance_from_mean = abs(income - mean_income) / mean_income if mean_income > 0 else 0
            variance_from_median = abs(income - median_income) / median_income if median_income > 0 else 0
            
            # Use the smaller variance (more conservative)
            variance = min(variance_from_mean, variance_from_median)
            
            variance_detail = {
                "document_id": doc["document_id"],
                "document_type": doc["document_type"],
                "annual_income": income,
                "variance_from_mean": variance_from_mean,
                "variance_from_median": variance_from_median,
                "variance_percentage": variance,
                "is_discrepant": variance > threshold
            }
            
            variance_details.append(variance_detail)
            
            if variance > max_variance:
                max_variance = variance
            
            if variance > threshold:
                discrepant_documents.append(doc["document_id"])
        
        income_comparison = {
            "mean_income": mean_income,
            "median_income": median_income,
            "min_income": min_income,
            "max_income": max_income,
            "income_range": max_income - min_income,
            "range_percentage": (max_income - min_income) / mean_income if mean_income > 0 else 0,
            "document_count": len(income_docs)
        }
        
        return {
            "max_variance": max_variance,
            "variance_details": variance_details,
            "income_comparison": income_comparison,
            "discrepant_documents": discrepant_documents
        }
    
    def _analyze_employer_consistency(self, income_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze consistency of employer information across documents.
        
        Args:
            income_docs: List of income documents
            
        Returns:
            Dictionary containing employer consistency analysis
        """
        employers = []
        employer_income_map = {}
        
        for doc in income_docs:
            employer = doc.get("employer")
            if employer:
                employers.append(employer)
                if employer not in employer_income_map:
                    employer_income_map[employer] = []
                employer_income_map[employer].append(doc["annual_income"])
        
        unique_employers = set(employers)
        
        analysis = {
            "total_employers": len(unique_employers),
            "employer_list": list(unique_employers),
            "is_consistent": len(unique_employers) <= 1,
            "employer_income_breakdown": {}
        }
        
        # Analyze income by employer
        for employer, incomes in employer_income_map.items():
            if len(incomes) > 1:
                analysis["employer_income_breakdown"][employer] = {
                    "document_count": len(incomes),
                    "mean_income": statistics.mean(incomes),
                    "income_range": max(incomes) - min(incomes),
                    "variance": statistics.stdev(incomes) if len(incomes) > 1 else 0
                }
        
        return analysis
    
    def _analyze_temporal_consistency(self, income_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze temporal consistency of income documents.
        
        Args:
            income_docs: List of income documents
            
        Returns:
            Dictionary containing temporal analysis
        """
        dated_docs = []
        
        for doc in income_docs:
            date_info = doc.get("date_info")
            if date_info:
                # Try to extract a meaningful date
                doc_date = None
                for date_field in ["pay_date", "pay_period_end", "issue_date", "document_date"]:
                    if date_field in date_info:
                        doc_date = date_info[date_field]
                        break
                
                if doc_date:
                    dated_docs.append({
                        "document_id": doc["document_id"],
                        "date": doc_date,
                        "annual_income": doc["annual_income"]
                    })
        
        analysis = {
            "documents_with_dates": len(dated_docs),
            "total_documents": len(income_docs),
            "temporal_coverage": "unknown"
        }
        
        if len(dated_docs) >= 2:
            # Sort by date and analyze trends
            try:
                # Simple analysis - in a real implementation, would parse dates properly
                analysis["temporal_coverage"] = "multiple_periods"
                analysis["trend_analysis"] = "available"
            except:
                analysis["temporal_coverage"] = "date_parsing_error"
        
        return analysis
    
    def _compare_with_stated_income(self, income_docs: List[Dict[str, Any]], 
                                  stated_income: float) -> Dict[str, Any]:
        """
        Compare verified income with borrower's stated income.
        
        Args:
            income_docs: List of income documents
            stated_income: Borrower's stated annual income
            
        Returns:
            Dictionary containing stated income comparison
        """
        if not income_docs or stated_income <= 0:
            return {
                "comparison_available": False,
                "variance_from_stated": 0.0
            }
        
        annual_incomes = [doc["annual_income"] for doc in income_docs]
        verified_income = statistics.median(annual_incomes)  # Use median as representative
        
        variance = abs(verified_income - stated_income) / stated_income if stated_income > 0 else 1.0
        
        return {
            "comparison_available": True,
            "stated_income": stated_income,
            "verified_income": verified_income,
            "variance_from_stated": variance,
            "variance_percentage": variance,
            "is_significant_variance": variance > 0.10  # 10% threshold
        }
    
    def _detect_suspicious_patterns(self, normalized_incomes: List[Dict[str, Any]],
                                  consistency_analysis: Dict[str, Any]) -> List[str]:
        """
        Detect suspicious patterns that may indicate fraud or errors.
        
        Args:
            normalized_incomes: List of normalized income data
            consistency_analysis: Consistency analysis results
            
        Returns:
            List of suspicious pattern descriptions
        """
        patterns = []
        
        # Pattern 1: Extremely high variance
        max_variance = consistency_analysis.get("max_variance", 0)
        if max_variance > self.variance_thresholds["major"]:
            patterns.append(f"Extremely high income variance ({max_variance:.1%}) suggests potential document manipulation")
        
        # Pattern 2: Round number bias
        annual_incomes = [doc.get("annual_income", 0) for doc in normalized_incomes if doc.get("annual_income")]
        round_numbers = [income for income in annual_incomes if income % 1000 == 0]
        if len(round_numbers) > len(annual_incomes) * 0.7:  # More than 70% are round numbers
            patterns.append("Unusually high frequency of round numbers in income amounts")
        
        # Pattern 3: Inconsistent employer information
        employer_analysis = consistency_analysis.get("employer_consistency", {})
        if employer_analysis.get("total_employers", 0) > 2:
            patterns.append("Multiple different employers across income documents")
        
        # Pattern 4: Income progression anomalies
        if len(annual_incomes) >= 3:
            # Check for unrealistic income jumps
            sorted_incomes = sorted(annual_incomes)
            for i in range(1, len(sorted_incomes)):
                growth_rate = (sorted_incomes[i] - sorted_incomes[i-1]) / sorted_incomes[i-1]
                if growth_rate > 0.50:  # More than 50% increase
                    patterns.append("Unrealistic income growth rate detected between documents")
                    break
        
        # Pattern 5: Document type inconsistencies
        doc_types = [doc.get("document_type") for doc in normalized_incomes]
        if "employment" in doc_types and "income" in doc_types:
            # Check if employment letter income matches pay stub income
            employment_docs = [doc for doc in normalized_incomes if doc.get("document_type") == "employment"]
            income_docs = [doc for doc in normalized_incomes if doc.get("document_type") == "income"]
            
            if employment_docs and income_docs:
                emp_income = employment_docs[0].get("annual_income", 0)
                pay_income = statistics.mean([doc.get("annual_income", 0) for doc in income_docs])
                
                if emp_income > 0 and pay_income > 0:
                    variance = abs(emp_income - pay_income) / emp_income
                    if variance > 0.15:  # 15% variance between employment letter and pay stubs
                        patterns.append("Significant variance between employment letter and pay stub income")
        
        # Pattern 6: Missing critical information
        docs_with_employer = [doc for doc in normalized_incomes if doc.get("employer")]
        if len(docs_with_employer) < len(normalized_incomes) * 0.5:  # Less than 50% have employer info
            patterns.append("Missing employer information in majority of income documents")
        
        return patterns
    
    def _calculate_consistency_metrics(self, consistency_analysis: Dict[str, Any],
                                     suspicious_patterns: List[str]) -> Dict[str, Any]:
        """
        Calculate overall consistency metrics.
        
        Args:
            consistency_analysis: Consistency analysis results
            suspicious_patterns: List of suspicious patterns
            
        Returns:
            Dictionary containing consistency metrics
        """
        base_consistency_score = 1.0
        base_confidence_score = 0.8
        
        # Adjust for variance
        max_variance = consistency_analysis.get("max_variance", 0)
        if max_variance > self.variance_thresholds["acceptable"]:
            variance_penalty = min(max_variance * 2, 0.5)  # Up to 50% penalty
            base_consistency_score -= variance_penalty
            base_confidence_score -= variance_penalty * 0.5
        
        # Adjust for suspicious patterns
        pattern_penalty = len(suspicious_patterns) * 0.1  # 10% per pattern
        base_consistency_score -= pattern_penalty
        base_confidence_score -= pattern_penalty * 0.5
        
        # Adjust for employer consistency
        employer_analysis = consistency_analysis.get("employer_consistency", {})
        if not employer_analysis.get("is_consistent", True):
            base_consistency_score -= 0.2
            base_confidence_score -= 0.1
        
        # Normalize scores
        consistency_score = max(0.0, min(1.0, base_consistency_score))
        confidence_score = max(0.0, min(1.0, base_confidence_score))
        
        return {
            "consistency_score": consistency_score,
            "confidence_score": confidence_score
        }
    
    def _generate_recommendations(self, consistency_analysis: Dict[str, Any],
                                suspicious_patterns: List[str],
                                threshold: float) -> List[str]:
        """
        Generate recommendations based on consistency analysis.
        
        Args:
            consistency_analysis: Consistency analysis results
            suspicious_patterns: List of suspicious patterns
            threshold: Variance threshold used
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Variance-based recommendations
        max_variance = consistency_analysis.get("max_variance", 0)
        if max_variance > threshold:
            recommendations.append("Investigate income discrepancies and obtain borrower explanation")
            
            discrepant_docs = consistency_analysis.get("discrepant_documents", [])
            if discrepant_docs:
                recommendations.append(f"Review specific documents: {', '.join(discrepant_docs)}")
        
        if max_variance > self.variance_thresholds["significant"]:
            recommendations.append("Consider requiring additional income verification documentation")
        
        if max_variance > self.variance_thresholds["major"]:
            recommendations.append("Manual underwriter review required due to major income discrepancies")
        
        # Employer consistency recommendations
        employer_analysis = consistency_analysis.get("employer_consistency", {})
        if employer_analysis.get("total_employers", 0) > 1:
            recommendations.append("Verify employment history and reason for multiple employers")
        
        # Suspicious pattern recommendations
        if suspicious_patterns:
            recommendations.append("Investigate suspicious patterns in income documentation")
            
            if any("fraud" in pattern.lower() or "manipulation" in pattern.lower() for pattern in suspicious_patterns):
                recommendations.append("Consider fraud investigation due to suspicious income patterns")
        
        # Stated income comparison recommendations
        stated_comparison = consistency_analysis.get("stated_income_comparison", {})
        if stated_comparison.get("is_significant_variance", False):
            recommendations.append("Resolve variance between stated and verified income")
        
        # Document quality recommendations
        if consistency_analysis.get("status") == "insufficient_data":
            recommendations.append("Provide additional income documentation for proper verification")
        
        return recommendations
    
    def _calculate_document_confidence(self, normalized_doc: Dict[str, Any], 
                                     extracted_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a normalized document.
        
        Args:
            normalized_doc: Normalized document data
            extracted_data: Original extracted data
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.3  # Base score
        
        # Boost for having key information
        if normalized_doc.get("employer"):
            score += 0.15
        if normalized_doc.get("annual_income"):
            score += 0.20
        if normalized_doc.get("pay_frequency"):
            score += 0.10
        if normalized_doc.get("income_type"):
            score += 0.10
        
        # Boost for reasonable income amounts
        annual_income = normalized_doc.get("annual_income", 0)
        if 20000 <= annual_income <= 500000:  # Reasonable annual income range
            score += 0.10
        
        # Boost for complete extracted data
        if len(extracted_data) > 5:
            score += 0.05
        
        return max(0.0, min(1.0, score))