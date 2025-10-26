"""
Address proof validation tool for KYC compliance.

This tool provides validation capabilities for address proof documents including
utility bills and bank statements to ensure KYC compliance in mortgage processing.
"""

import os
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import asyncio

from ..base import BaseTool, ToolResult
from ...models.enums import DocumentType, ValidationStatus


class AddressProofValidator(BaseTool):
    """
    Tool for validating address proof documents for KYC compliance.
    
    This tool provides comprehensive validation for:
    - Utility bills (electricity, gas, water, internet, phone)
    - Bank statements with address verification
    - Address consistency checking across multiple documents
    - KYC compliance validation for mortgage lending
    """
    
    def __init__(self):
        super().__init__(
            name="address_proof_validator",
            description="Validate address proof documents for KYC compliance",
            agent_domain="document_processing"
        )
        self.logger = logging.getLogger("tool.address_proof_validator")
        
        # Validation patterns for different document types
        self.validation_patterns = self._initialize_validation_patterns()
        
        # Utility company patterns and bank patterns
        self.utility_companies = self._initialize_utility_companies()
        self.bank_patterns = self._initialize_bank_patterns()
        
        # Address validation patterns
        self.address_patterns = self._initialize_address_patterns()
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "Unique identifier for the document"
                },
                "document_type": {
                    "type": "string",
                    "enum": ["utility_bill", "bank_statement"],
                    "description": "Type of address proof document to validate"
                },
                "extracted_text": {
                    "type": "string",
                    "description": "Extracted text content from the document"
                },
                "key_value_pairs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    },
                    "description": "Key-value pairs extracted from the document",
                    "default": []
                },
                "applicant_name": {
                    "type": "string",
                    "description": "Name of the mortgage applicant for verification",
                    "default": ""
                },
                "expected_address": {
                    "type": "string",
                    "description": "Expected address for consistency checking",
                    "default": ""
                },
                "other_documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "document_id": {"type": "string"},
                            "extracted_address": {"type": "string"},
                            "document_type": {"type": "string"}
                        }
                    },
                    "description": "Other documents for cross-validation",
                    "default": []
                }
            },
            "required": ["document_id", "document_type", "extracted_text"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute address proof validation for KYC compliance.
        
        Args:
            document_id: Unique identifier for the document
            document_type: Type of address proof document (utility_bill, bank_statement)
            extracted_text: Text content extracted from the document
            key_value_pairs: Key-value pairs extracted from the document
            applicant_name: Name of the mortgage applicant for verification
            expected_address: Expected address for consistency checking
            other_documents: Other documents for cross-validation
            
        Returns:
            ToolResult containing validation results and address information
        """
        document_id = kwargs.get("document_id")
        document_type = kwargs.get("document_type")
        extracted_text = kwargs.get("extracted_text", "")
        key_value_pairs = kwargs.get("key_value_pairs", [])
        applicant_name = kwargs.get("applicant_name", "")
        expected_address = kwargs.get("expected_address", "")
        other_documents = kwargs.get("other_documents", [])
        
        try:
            self.logger.info(f"Starting address proof validation for {document_id} ({document_type})")
            
            # Validate input
            if not extracted_text.strip():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="No text content provided for validation"
                )
            
            if document_type not in ["utility_bill", "bank_statement"]:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message=f"Unsupported document type: {document_type}"
                )
            
            # Perform document-specific validation
            validation_results = await self._validate_address_proof_document(
                document_type, extracted_text, key_value_pairs
            )
            
            # Extract address information
            address_info = await self._extract_address_information(
                document_type, extracted_text, key_value_pairs
            )
            
            # Perform KYC compliance checks
            kyc_compliance = await self._perform_kyc_compliance_checks(
                document_type, validation_results, address_info, applicant_name
            )
            
            # Perform address consistency checks
            consistency_results = await self._perform_address_consistency_checks(
                address_info, expected_address, other_documents
            )
            
            # Build result data
            result_data = {
                "document_id": document_id,
                "document_type": document_type,
                "validation_status": validation_results["status"],
                "validation_score": validation_results["score"],
                "validation_details": validation_results,
                "address_information": address_info,
                "kyc_compliance": kyc_compliance,
                "consistency_checks": consistency_results,
                "validation_timestamp": datetime.now().isoformat(),
                "validation_method": "address_proof_kyc_validation"
            }
            
            self.logger.info(f"Address proof validation completed for {document_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"Address proof validation failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    async def _validate_address_proof_document(self, document_type: str, extracted_text: str,
                                             key_value_pairs: List[Dict]) -> Dict[str, Any]:
        """
        Perform document-specific validation based on document type.
        
        Args:
            document_type: Type of address proof document
            extracted_text: Extracted text content
            key_value_pairs: Key-value pairs from document
            
        Returns:
            Dictionary containing validation results
        """
        # Simulate processing delay for validation
        await asyncio.sleep(0.2)
        
        if document_type == "utility_bill":
            return await self._validate_utility_bill(extracted_text, key_value_pairs)
        elif document_type == "bank_statement":
            return await self._validate_bank_statement(extracted_text, key_value_pairs)
        else:
            return {
                "status": ValidationStatus.INVALID.value,
                "score": 0.0,
                "details": {"error": f"Unsupported document type: {document_type}"}
            }
    
    async def _validate_utility_bill(self, extracted_text: str, 
                                   key_value_pairs: List[Dict]) -> Dict[str, Any]:
        """Validate utility bill document."""
        validation_details = {}
        score = 0.0
        max_score = 100.0
        
        text_lower = extracted_text.lower()
        
        # Check for required utility bill elements
        required_elements = {
            "utility_company": (r"(?:electric|gas|water|internet|phone|cable|telecom|energy|power)", 20),
            "account_number": (r"account\s+(?:no\.?|number)\s*:?\s*([A-Z0-9\-]{6,20})", 15),
            "service_address": (r"service\s+address\s*:?\s*([A-Za-z0-9\s,\.#\-]+)", 25),
            "billing_period": (r"(?:billing\s+period|statement\s+period)\s*:?\s*([A-Za-z0-9\s,\-\/]+)", 10),
            "bill_date": (r"(?:bill\s+date|statement\s+date|date)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 15),
            "amount_due": (r"(?:amount\s+due|total\s+due|balance\s+due)\s*:?\s*\$?([0-9,]+\.?\d{0,2})", 10),
            "customer_name": (r"(?:customer|account\s+holder|name)\s*:?\s*([A-Za-z\s\.]+)", 5)
        }
        
        for element, (pattern, points) in required_elements.items():
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                validation_details[element] = {
                    "found": True,
                    "value": match.group(1).strip() if match.lastindex else match.group(0).strip(),
                    "confidence": 0.85
                }
                score += points
            else:
                validation_details[element] = {
                    "found": False,
                    "value": None,
                    "confidence": 0.0
                }
        
        # Check for utility company recognition
        utility_company_found = False
        for company in self.utility_companies:
            if company.lower() in text_lower:
                validation_details["recognized_utility_company"] = {
                    "found": True,
                    "company": company,
                    "confidence": 0.9
                }
                score += 10
                utility_company_found = True
                break
        
        if not utility_company_found:
            validation_details["recognized_utility_company"] = {
                "found": False,
                "company": None,
                "confidence": 0.0
            }
        
        # Check bill recency (within last 3 months)
        bill_date = validation_details.get("bill_date", {}).get("value")
        if bill_date:
            if self._is_date_recent(bill_date, months=3):
                validation_details["bill_recency"] = {"valid": True, "recent": True}
                score += 5
            else:
                validation_details["bill_recency"] = {"valid": True, "recent": False}
        else:
            validation_details["bill_recency"] = {"valid": False, "recent": False}
        
        # Determine validation status
        percentage_score = (score / max_score) * 100
        if percentage_score >= 75:
            status = ValidationStatus.VALID.value
        elif percentage_score >= 55:
            status = ValidationStatus.REQUIRES_MANUAL_REVIEW.value
        else:
            status = ValidationStatus.INVALID.value
        
        return {
            "status": status,
            "score": round(percentage_score, 2),
            "details": validation_details
        }
    
    async def _validate_bank_statement(self, extracted_text: str,
                                     key_value_pairs: List[Dict]) -> Dict[str, Any]:
        """Validate bank statement document."""
        validation_details = {}
        score = 0.0
        max_score = 100.0
        
        text_lower = extracted_text.lower()
        
        # Check for required bank statement elements
        required_elements = {
            "bank_name": (r"(?:bank|credit\s+union|financial)", 20),
            "account_number": (r"account\s+(?:no\.?|number)\s*:?\s*([A-Z0-9\*\-]{6,20})", 15),
            "statement_period": (r"statement\s+period\s*:?\s*([A-Za-z0-9\s,\-\/]+)", 15),
            "account_holder": (r"(?:account\s+holder|name)\s*:?\s*([A-Za-z\s\.]+)", 10),
            "mailing_address": (r"(?:mailing\s+address|address)\s*:?\s*([A-Za-z0-9\s,\.#\-]+)", 25),
            "statement_date": (r"statement\s+date\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 10),
            "beginning_balance": (r"(?:beginning\s+balance|opening\s+balance)\s*:?\s*\$?([0-9,\-]+\.?\d{0,2})", 5)
        }
        
        for element, (pattern, points) in required_elements.items():
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                validation_details[element] = {
                    "found": True,
                    "value": match.group(1).strip() if match.lastindex else match.group(0).strip(),
                    "confidence": 0.8
                }
                score += points
            else:
                validation_details[element] = {
                    "found": False,
                    "value": None,
                    "confidence": 0.0
                }
        
        # Check for recognized bank
        bank_found = False
        for bank_pattern in self.bank_patterns:
            if re.search(bank_pattern, text_lower):
                validation_details["recognized_bank"] = {
                    "found": True,
                    "pattern_matched": bank_pattern,
                    "confidence": 0.9
                }
                score += 10
                bank_found = True
                break
        
        if not bank_found:
            validation_details["recognized_bank"] = {
                "found": False,
                "pattern_matched": None,
                "confidence": 0.0
            }
        
        # Check statement recency (within last 3 months)
        statement_date = validation_details.get("statement_date", {}).get("value")
        if statement_date:
            if self._is_date_recent(statement_date, months=3):
                validation_details["statement_recency"] = {"valid": True, "recent": True}
                score += 5
            else:
                validation_details["statement_recency"] = {"valid": True, "recent": False}
        else:
            validation_details["statement_recency"] = {"valid": False, "recent": False}
        
        # Determine validation status
        percentage_score = (score / max_score) * 100
        if percentage_score >= 70:
            status = ValidationStatus.VALID.value
        elif percentage_score >= 50:
            status = ValidationStatus.REQUIRES_MANUAL_REVIEW.value
        else:
            status = ValidationStatus.INVALID.value
        
        return {
            "status": status,
            "score": round(percentage_score, 2),
            "details": validation_details
        }
    
    async def _extract_address_information(self, document_type: str, extracted_text: str,
                                         key_value_pairs: List[Dict]) -> Dict[str, Any]:
        """Extract standardized address information from the document."""
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        address_info = {
            "primary_address": None,
            "street_address": None,
            "city": None,
            "state": None,
            "zip_code": None,
            "country": None,
            "account_holder_name": None,
            "document_date": None,
            "service_period": None
        }
        
        # Extract information based on document type
        if document_type == "utility_bill":
            address_info.update(self._extract_utility_address_info(extracted_text))
        elif document_type == "bank_statement":
            address_info.update(self._extract_bank_address_info(extracted_text))
        
        # Enhance with key-value pairs
        address_info = self._enhance_address_with_key_value_pairs(address_info, key_value_pairs)
        
        # Parse and standardize address components
        if address_info.get("primary_address"):
            parsed_address = self._parse_address_components(address_info["primary_address"])
            address_info.update(parsed_address)
        
        return address_info
    
    def _extract_utility_address_info(self, extracted_text: str) -> Dict[str, Any]:
        """Extract address information specific to utility bills."""
        info = {}
        
        # Extract service address
        service_address_match = re.search(
            r"service\s+address\s*:?\s*([A-Za-z0-9\s,\.#\-]+?)(?:\n|$|account|customer)",
            extracted_text, re.IGNORECASE
        )
        if service_address_match:
            info["primary_address"] = service_address_match.group(1).strip()
        
        # Extract customer name
        customer_match = re.search(
            r"(?:customer|account\s+holder|name)\s*:?\s*([A-Za-z\s\.]+?)(?:\n|$|account)",
            extracted_text, re.IGNORECASE
        )
        if customer_match:
            info["account_holder_name"] = customer_match.group(1).strip()
        
        # Extract bill date
        bill_date_match = re.search(
            r"(?:bill\s+date|statement\s+date|date)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            extracted_text, re.IGNORECASE
        )
        if bill_date_match:
            info["document_date"] = bill_date_match.group(1)
        
        # Extract billing period
        period_match = re.search(
            r"(?:billing\s+period|service\s+period)\s*:?\s*([A-Za-z0-9\s,\-\/]+?)(?:\n|$)",
            extracted_text, re.IGNORECASE
        )
        if period_match:
            info["service_period"] = period_match.group(1).strip()
        
        return info
    
    def _extract_bank_address_info(self, extracted_text: str) -> Dict[str, Any]:
        """Extract address information specific to bank statements."""
        info = {}
        
        # Extract mailing address
        mailing_address_match = re.search(
            r"(?:mailing\s+address|address)\s*:?\s*([A-Za-z0-9\s,\.#\-]+?)(?:\n|account|statement)",
            extracted_text, re.IGNORECASE
        )
        if mailing_address_match:
            info["primary_address"] = mailing_address_match.group(1).strip()
        
        # Extract account holder name
        holder_match = re.search(
            r"(?:account\s+holder|name)\s*:?\s*([A-Za-z\s\.]+?)(?:\n|$|account)",
            extracted_text, re.IGNORECASE
        )
        if holder_match:
            info["account_holder_name"] = holder_match.group(1).strip()
        
        # Extract statement date
        statement_date_match = re.search(
            r"statement\s+date\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            extracted_text, re.IGNORECASE
        )
        if statement_date_match:
            info["document_date"] = statement_date_match.group(1)
        
        # Extract statement period
        period_match = re.search(
            r"statement\s+period\s*:?\s*([A-Za-z0-9\s,\-\/]+?)(?:\n|$)",
            extracted_text, re.IGNORECASE
        )
        if period_match:
            info["service_period"] = period_match.group(1).strip()
        
        return info
    
    def _enhance_address_with_key_value_pairs(self, address_info: Dict[str, Any],
                                            key_value_pairs: List[Dict]) -> Dict[str, Any]:
        """Enhance address information with key-value pairs."""
        for kvp in key_value_pairs:
            key = kvp.get("key", "").lower()
            value = kvp.get("value", "")
            
            if not value:
                continue
            
            # Map key-value pairs to address fields
            if "address" in key and not address_info.get("primary_address"):
                address_info["primary_address"] = value
            elif "name" in key and "customer" in key and not address_info.get("account_holder_name"):
                address_info["account_holder_name"] = value
            elif "date" in key and not address_info.get("document_date"):
                address_info["document_date"] = value
            elif "period" in key and not address_info.get("service_period"):
                address_info["service_period"] = value
        
        return address_info
    
    def _parse_address_components(self, address: str) -> Dict[str, Any]:
        """Parse address string into components."""
        components = {
            "street_address": None,
            "city": None,
            "state": None,
            "zip_code": None,
            "country": "USA"  # Default assumption
        }
        
        # Clean up the address
        address = address.strip()
        
        # Extract ZIP code (5 digits or 5+4 format)
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
        if zip_match:
            components["zip_code"] = zip_match.group(1)
            address = address.replace(zip_match.group(0), "").strip()
        
        # Extract state (2-letter abbreviation at the end)
        state_match = re.search(r'\b([A-Z]{2})\s*$', address)
        if state_match:
            components["state"] = state_match.group(1)
            address = address.replace(state_match.group(0), "").strip()
        
        # Split remaining address into street and city
        address_parts = [part.strip() for part in address.split(',')]
        if len(address_parts) >= 2:
            components["street_address"] = address_parts[0]
            components["city"] = address_parts[1] if len(address_parts) >= 2 else address_parts[-1]
        elif len(address_parts) == 1:
            components["street_address"] = address_parts[0]
        
        return components
    
    async def _perform_kyc_compliance_checks(self, document_type: str, validation_results: Dict,
                                           address_info: Dict, applicant_name: str) -> Dict[str, Any]:
        """Perform KYC compliance checks on the address proof document."""
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        compliance_results = {
            "kyc_compliant": True,
            "compliance_score": 0.0,
            "checks_performed": [],
            "compliance_issues": [],
            "recommendations": []
        }
        
        max_score = 100.0
        score = 0.0
        
        # Check document validity
        if validation_results.get("status") == ValidationStatus.VALID.value:
            score += 40
            compliance_results["checks_performed"].append("Document validity check")
        else:
            compliance_results["compliance_issues"].append("Document validation failed")
            compliance_results["kyc_compliant"] = False
        
        # Check document recency (within 3 months)
        document_date = address_info.get("document_date")
        if document_date and self._is_date_recent(document_date, months=3):
            score += 25
            compliance_results["checks_performed"].append("Document recency check")
        else:
            compliance_results["compliance_issues"].append("Document is not recent (older than 3 months)")
            compliance_results["recommendations"].append("Obtain more recent address proof document")
        
        # Check name matching (if applicant name provided)
        if applicant_name and address_info.get("account_holder_name"):
            name_similarity = self._calculate_name_similarity(
                applicant_name, address_info["account_holder_name"]
            )
            if name_similarity >= 0.8:
                score += 20
                compliance_results["checks_performed"].append("Name matching check")
            else:
                compliance_results["compliance_issues"].append("Name mismatch between applicant and document")
                compliance_results["recommendations"].append("Verify name discrepancy or obtain document in applicant's name")
        
        # Check address completeness
        address_completeness = self._check_address_completeness(address_info)
        if address_completeness >= 0.7:
            score += 15
            compliance_results["checks_performed"].append("Address completeness check")
        else:
            compliance_results["compliance_issues"].append("Incomplete address information")
            compliance_results["recommendations"].append("Obtain document with complete address details")
        
        # Calculate final compliance score
        compliance_results["compliance_score"] = round((score / max_score) * 100, 2)
        
        # Determine overall compliance
        if compliance_results["compliance_score"] < 60:
            compliance_results["kyc_compliant"] = False
        
        return compliance_results
    
    async def _perform_address_consistency_checks(self, address_info: Dict, expected_address: str,
                                                other_documents: List[Dict]) -> Dict[str, Any]:
        """Perform address consistency checks across documents."""
        # Simulate processing delay
        await asyncio.sleep(0.05)
        
        consistency_results = {
            "overall_consistency": True,
            "consistency_score": 100.0,
            "checks_performed": [],
            "inconsistencies": [],
            "warnings": []
        }
        
        current_address = address_info.get("primary_address", "")
        
        # Check against expected address
        if expected_address and current_address:
            similarity = self._calculate_address_similarity(current_address, expected_address)
            if similarity >= 0.8:
                consistency_results["checks_performed"].append("Expected address match")
            elif similarity >= 0.6:
                consistency_results["warnings"].append("Partial address match with expected address")
                consistency_results["consistency_score"] -= 10
            else:
                consistency_results["inconsistencies"].append("Address does not match expected address")
                consistency_results["overall_consistency"] = False
                consistency_results["consistency_score"] -= 25
        
        # Check against other documents
        for doc in other_documents:
            doc_address = doc.get("extracted_address", "")
            if doc_address and current_address:
                similarity = self._calculate_address_similarity(current_address, doc_address)
                if similarity >= 0.8:
                    consistency_results["checks_performed"].append(f"Address match with {doc.get('document_type', 'document')}")
                elif similarity >= 0.6:
                    consistency_results["warnings"].append(f"Partial address match with {doc.get('document_type', 'document')}")
                    consistency_results["consistency_score"] -= 5
                else:
                    consistency_results["inconsistencies"].append(f"Address inconsistency with {doc.get('document_type', 'document')}")
                    consistency_results["overall_consistency"] = False
                    consistency_results["consistency_score"] -= 15
        
        # Ensure score doesn't go below 0
        consistency_results["consistency_score"] = max(0, consistency_results["consistency_score"])
        
        return consistency_results
    
    def _initialize_validation_patterns(self) -> Dict[str, Any]:
        """Initialize validation patterns for different document types."""
        return {
            "utility_bill": {
                "required_fields": ["utility_company", "service_address", "account_number", "bill_date"],
                "optional_fields": ["customer_name", "billing_period", "amount_due"]
            },
            "bank_statement": {
                "required_fields": ["bank_name", "account_holder", "mailing_address", "statement_date"],
                "optional_fields": ["account_number", "statement_period", "beginning_balance"]
            }
        }
    
    def _initialize_utility_companies(self) -> List[str]:
        """Initialize list of recognized utility companies."""
        return [
            "Pacific Gas & Electric", "PG&E", "Southern California Edison", "SCE",
            "ConEd", "Consolidated Edison", "National Grid", "Dominion Energy",
            "Duke Energy", "Florida Power & Light", "FPL", "Georgia Power",
            "ComEd", "Commonwealth Edison", "Xcel Energy", "APS", "Arizona Public Service",
            "Verizon", "AT&T", "Comcast", "Spectrum", "Cox Communications",
            "CenturyLink", "Frontier", "Time Warner Cable", "Charter Communications"
        ]
    
    def _initialize_bank_patterns(self) -> List[str]:
        """Initialize list of bank name patterns."""
        return [
            r"bank.*america", r"chase", r"wells.*fargo", r"citibank", r"citi",
            r"u\.?s\.?\s+bank", r"pnc\s+bank", r"capital\s+one", r"td\s+bank",
            r"bank.*west", r"regions\s+bank", r"suntrust", r"bb&t",
            r"fifth\s+third", r"ally\s+bank", r"discover\s+bank", r"american\s+express",
            r"navy\s+federal", r"usaa", r"charles\s+schwab", r"fidelity"
        ]
    
    def _initialize_address_patterns(self) -> Dict[str, str]:
        """Initialize address validation patterns."""
        return {
            "street_number": r"^\d+",
            "street_name": r"[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place)",
            "city": r"[A-Za-z\s]+",
            "state": r"[A-Z]{2}",
            "zip_code": r"\d{5}(?:-\d{4})?"
        }
    
    def _is_date_recent(self, date_str: str, months: int = 3) -> bool:
        """Check if a date is within the specified number of months."""
        try:
            # Try different date formats
            date_formats = ["%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                return False
            
            cutoff_date = date.today() - timedelta(days=months * 30)
            return parsed_date >= cutoff_date
            
        except Exception:
            return False
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        name1_clean = re.sub(r'[^\w\s]', '', name1.lower()).strip()
        name2_clean = re.sub(r'[^\w\s]', '', name2.lower()).strip()
        
        # Simple similarity based on common words
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_address_similarity(self, address1: str, address2: str) -> float:
        """Calculate similarity between two addresses."""
        if not address1 or not address2:
            return 0.0
        
        # Normalize addresses
        addr1_clean = re.sub(r'[^\w\s]', '', address1.lower()).strip()
        addr2_clean = re.sub(r'[^\w\s]', '', address2.lower()).strip()
        
        # Simple similarity based on common words
        words1 = set(addr1_clean.split())
        words2 = set(addr2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _check_address_completeness(self, address_info: Dict[str, Any]) -> float:
        """Check completeness of address information."""
        required_fields = ["primary_address", "street_address", "city", "state", "zip_code"]
        present_fields = sum(1 for field in required_fields if address_info.get(field))
        
        return present_fields / len(required_fields)