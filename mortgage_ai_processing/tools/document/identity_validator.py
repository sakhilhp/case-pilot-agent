"""
Identity document validation tool for government ID processing.

This tool provides validation and information extraction capabilities for government-issued
identity documents including passports, driver licenses, and national IDs.
"""

import os
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import asyncio

from ..base import BaseTool, ToolResult
from ...models.enums import DocumentType, ValidationStatus


class IdentityDocumentValidator(BaseTool):
    """
    Tool for validating and extracting information from government identity documents.
    
    This tool provides comprehensive validation for:
    - Passports with nationality and travel document verification
    - Driver licenses with class and restriction validation
    - National IDs with citizenship verification
    - Identity information extraction and consistency checking
    """
    
    def __init__(self):
        super().__init__(
            name="identity_document_validator",
            description="Validate government identity documents and extract identity information",
            agent_domain="document_processing"
        )
        self.logger = logging.getLogger("tool.identity_document_validator")
        
        # Validation patterns for different document types
        self.validation_patterns = self._initialize_validation_patterns()
        
        # Country and state codes for validation
        self.country_codes = self._initialize_country_codes()
        self.state_codes = self._initialize_state_codes()
        
        # Document format specifications
        self.document_formats = self._initialize_document_formats()
    
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
                    "enum": ["passport", "drivers_license", "national_id"],
                    "description": "Type of identity document to validate"
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
                "document_metadata": {
                    "type": "object",
                    "properties": {
                        "issuing_country": {"type": "string"},
                        "issuing_state": {"type": "string"},
                        "document_number": {"type": "string"}
                    },
                    "description": "Document metadata for validation",
                    "default": {}
                }
            },
            "required": ["document_id", "document_type", "extracted_text"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute identity document validation and information extraction.
        
        Args:
            document_id: Unique identifier for the document
            document_type: Type of identity document (passport, drivers_license, national_id)
            extracted_text: Text content extracted from the document
            key_value_pairs: Key-value pairs extracted from the document
            document_metadata: Additional document metadata
            
        Returns:
            ToolResult containing validation results and extracted identity information
        """
        document_id = kwargs.get("document_id")
        document_type = kwargs.get("document_type")
        extracted_text = kwargs.get("extracted_text", "")
        key_value_pairs = kwargs.get("key_value_pairs", [])
        document_metadata = kwargs.get("document_metadata", {})
        
        try:
            self.logger.info(f"Starting identity document validation for {document_id} ({document_type})")
            
            # Validate input
            if not extracted_text.strip():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="No text content provided for validation"
                )
            
            if document_type not in ["passport", "drivers_license", "national_id"]:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message=f"Unsupported document type: {document_type}"
                )
            
            # Perform document-specific validation
            validation_results = await self._validate_identity_document(
                document_type, extracted_text, key_value_pairs, document_metadata
            )
            
            # Extract identity information
            identity_info = await self._extract_identity_information(
                document_type, extracted_text, key_value_pairs
            )
            
            # Perform consistency checks
            consistency_results = await self._perform_consistency_checks(
                identity_info, validation_results
            )
            
            # Build result data
            result_data = {
                "document_id": document_id,
                "document_type": document_type,
                "validation_status": validation_results["status"],
                "validation_score": validation_results["score"],
                "validation_details": validation_results["details"],
                "identity_information": identity_info,
                "consistency_checks": consistency_results,
                "validation_timestamp": datetime.now().isoformat(),
                "validation_method": "government_id_processing"
            }
            
            self.logger.info(f"Identity document validation completed for {document_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"Identity document validation failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    async def _validate_identity_document(self, document_type: str, extracted_text: str,
                                        key_value_pairs: List[Dict], 
                                        document_metadata: Dict) -> Dict[str, Any]:
        """
        Perform document-specific validation based on document type.
        
        Args:
            document_type: Type of identity document
            extracted_text: Extracted text content
            key_value_pairs: Key-value pairs from document
            document_metadata: Additional metadata
            
        Returns:
            Dictionary containing validation results
        """
        # Simulate processing delay for validation
        await asyncio.sleep(0.2)
        
        if document_type == "passport":
            return await self._validate_passport(extracted_text, key_value_pairs, document_metadata)
        elif document_type == "drivers_license":
            return await self._validate_drivers_license(extracted_text, key_value_pairs, document_metadata)
        elif document_type == "national_id":
            return await self._validate_national_id(extracted_text, key_value_pairs, document_metadata)
        else:
            return {
                "status": ValidationStatus.INVALID.value,
                "score": 0.0,
                "details": {"error": f"Unsupported document type: {document_type}"}
            }
    
    async def _validate_passport(self, extracted_text: str, key_value_pairs: List[Dict],
                               document_metadata: Dict) -> Dict[str, Any]:
        """Validate passport document."""
        validation_details = {}
        score = 0.0
        max_score = 100.0
        
        text_lower = extracted_text.lower()
        
        # Check for required passport elements
        required_elements = {
            "passport_number": (r"passport\s+no\.?\s*:?\s*([A-Z0-9]{6,12})", 20),
            "nationality": (r"nationality\s*:?\s*([A-Z]{2,3}|[A-Za-z\s]+)", 15),
            "date_of_birth": (r"date\s+of\s+birth\s*:?\s*(\d{1,2}\s+[A-Z]{3}\s+\d{4}|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 15),
            "place_of_birth": (r"place\s+of\s+birth\s*:?\s*([A-Za-z\s,]+)", 10),
            "issuing_authority": (r"issuing\s+authority\s*:?\s*([A-Za-z\s]+)", 10),
            "expiration_date": (r"(?:expir(?:y|ation)|date\s+of\s+expiry)\s*:?\s*(\d{1,2}\s+[A-Z]{3}\s+\d{4}|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 15),
            "given_names": (r"given\s+names?\s*:?\s*([A-Za-z\s]+)", 10),
            "surname": (r"surname\s*:?\s*([A-Za-z\s]+)", 5)
        }
        
        for element, (pattern, points) in required_elements.items():
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                validation_details[element] = {
                    "found": True,
                    "value": match.group(1).strip(),
                    "confidence": 0.9
                }
                score += points
            else:
                validation_details[element] = {
                    "found": False,
                    "value": None,
                    "confidence": 0.0
                }
        
        # Check passport format compliance
        if "passport" in text_lower and "travel document" in text_lower:
            score += 10
            validation_details["document_format"] = {"valid": True, "type": "passport"}
        
        # Validate nationality code
        nationality = validation_details.get("nationality", {}).get("value", "")
        if nationality and self._validate_country_code(nationality):
            score += 5
            validation_details["nationality_valid"] = True
        else:
            validation_details["nationality_valid"] = False
        
        # Determine validation status
        percentage_score = (score / max_score) * 100
        if percentage_score >= 80:
            status = ValidationStatus.VALID.value
        elif percentage_score >= 60:
            status = ValidationStatus.REQUIRES_MANUAL_REVIEW.value
        else:
            status = ValidationStatus.INVALID.value
        
        return {
            "status": status,
            "score": round(percentage_score, 2),
            "details": validation_details
        }
    
    async def _validate_drivers_license(self, extracted_text: str, key_value_pairs: List[Dict],
                                      document_metadata: Dict) -> Dict[str, Any]:
        """Validate driver's license document."""
        validation_details = {}
        score = 0.0
        max_score = 100.0
        
        text_lower = extracted_text.lower()
        
        # Check for required driver's license elements
        required_elements = {
            "license_number": (r"(?:dl|license)\s+no\.?\s*:?\s*([A-Z0-9]{8,15})", 25),
            "class": (r"class\s*:?\s*([A-Z]{1,3})", 15),
            "expiration_date": (r"expir(?:es|ation)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 20),
            "date_of_birth": (r"(?:dob|date\s+of\s+birth)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 15),
            "full_name": (r"(?:name|holder)\s*:?\s*([A-Za-z\s,]+)", 10),
            "address": (r"address\s*:?\s*([A-Za-z0-9\s,\.]+)", 10),
            "restrictions": (r"restrictions?\s*:?\s*([A-Z0-9\s,]+)", 5)
        }
        
        for element, (pattern, points) in required_elements.items():
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                validation_details[element] = {
                    "found": True,
                    "value": match.group(1).strip(),
                    "confidence": 0.85
                }
                score += points
            else:
                validation_details[element] = {
                    "found": False,
                    "value": None,
                    "confidence": 0.0
                }
        
        # Check for driver's license indicators
        dl_indicators = ["driver", "license", "licence", "motor vehicle", "department of motor vehicles"]
        indicator_found = any(indicator in text_lower for indicator in dl_indicators)
        if indicator_found:
            score += 10
            validation_details["document_format"] = {"valid": True, "type": "drivers_license"}
        
        # Validate license class
        license_class = validation_details.get("class", {}).get("value", "")
        if license_class and self._validate_license_class(license_class):
            score += 5
            validation_details["class_valid"] = True
        else:
            validation_details["class_valid"] = False
        
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
    
    async def _validate_national_id(self, extracted_text: str, key_value_pairs: List[Dict],
                                  document_metadata: Dict) -> Dict[str, Any]:
        """Validate national ID document."""
        validation_details = {}
        score = 0.0
        max_score = 100.0
        
        text_lower = extracted_text.lower()
        
        # Check for required national ID elements
        required_elements = {
            "id_number": (r"(?:id|identification)\s+no\.?\s*:?\s*([A-Z0-9]{8,20})", 30),
            "nationality": (r"nationality\s*:?\s*([A-Z]{2,3}|[A-Za-z\s]+)", 20),
            "date_of_birth": (r"(?:dob|date\s+of\s+birth)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 15),
            "full_name": (r"(?:name|holder)\s*:?\s*([A-Za-z\s,]+)", 15),
            "place_of_birth": (r"place\s+of\s+birth\s*:?\s*([A-Za-z\s,]+)", 10),
            "expiration_date": (r"expir(?:y|ation)\s+date\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", 10)
        }
        
        for element, (pattern, points) in required_elements.items():
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                validation_details[element] = {
                    "found": True,
                    "value": match.group(1).strip(),
                    "confidence": 0.8
                }
                score += points
            else:
                validation_details[element] = {
                    "found": False,
                    "value": None,
                    "confidence": 0.0
                }
        
        # Check for national ID indicators
        id_indicators = ["national id", "identity card", "citizen", "identification card"]
        indicator_found = any(indicator in text_lower for indicator in id_indicators)
        if indicator_found:
            score += 10
            validation_details["document_format"] = {"valid": True, "type": "national_id"}
        
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
    
    async def _extract_identity_information(self, document_type: str, extracted_text: str,
                                          key_value_pairs: List[Dict]) -> Dict[str, Any]:
        """Extract standardized identity information from the document."""
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        identity_info = {
            "full_name": None,
            "first_name": None,
            "last_name": None,
            "date_of_birth": None,
            "nationality": None,
            "document_number": None,
            "expiration_date": None,
            "issuing_authority": None,
            "place_of_birth": None,
            "address": None
        }
        
        # Extract information based on document type
        if document_type == "passport":
            identity_info.update(self._extract_passport_info(extracted_text))
        elif document_type == "drivers_license":
            identity_info.update(self._extract_drivers_license_info(extracted_text))
        elif document_type == "national_id":
            identity_info.update(self._extract_national_id_info(extracted_text))
        
        # Enhance with key-value pairs
        identity_info = self._enhance_with_key_value_pairs(identity_info, key_value_pairs)
        
        return identity_info
    
    def _extract_passport_info(self, extracted_text: str) -> Dict[str, Any]:
        """Extract information specific to passport documents."""
        info = {}
        
        # Extract passport number
        passport_match = re.search(r"passport\s+no\.?\s*:?\s*([A-Z0-9]{6,12})", extracted_text, re.IGNORECASE)
        if passport_match:
            info["document_number"] = passport_match.group(1)
        
        # Extract given names and surname
        given_names_match = re.search(r"given\s+names?\s*:?\s*([A-Za-z\s]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        surname_match = re.search(r"surname\s*:?\s*([A-Za-z\s]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        
        if given_names_match and surname_match:
            info["first_name"] = given_names_match.group(1).strip()
            info["last_name"] = surname_match.group(1).strip()
            info["full_name"] = f"{info['first_name']} {info['last_name']}"
        
        # Extract nationality
        nationality_match = re.search(r"nationality\s*:?\s*([A-Z]{2,3}|[A-Za-z\s]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        if nationality_match:
            info["nationality"] = nationality_match.group(1).strip()
        
        # Extract dates
        dob_match = re.search(r"date\s+of\s+birth\s*:?\s*(\d{1,2}\s+[A-Z]{3}\s+\d{4}|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", extracted_text, re.IGNORECASE)
        if dob_match:
            info["date_of_birth"] = dob_match.group(1)
        
        exp_match = re.search(r"(?:expir(?:y|ation)|date\s+of\s+expiry)\s*:?\s*(\d{1,2}\s+[A-Z]{3}\s+\d{4}|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", extracted_text, re.IGNORECASE)
        if exp_match:
            info["expiration_date"] = exp_match.group(1)
        
        # Extract place of birth
        pob_match = re.search(r"place\s+of\s+birth\s*:?\s*([A-Za-z\s,]+)", extracted_text, re.IGNORECASE)
        if pob_match:
            info["place_of_birth"] = pob_match.group(1).strip()
        
        # Extract issuing authority
        authority_match = re.search(r"issuing\s+authority\s*:?\s*([A-Za-z\s\.]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        if authority_match:
            info["issuing_authority"] = authority_match.group(1).strip()
        
        return info
    
    def _extract_drivers_license_info(self, extracted_text: str) -> Dict[str, Any]:
        """Extract information specific to driver's license documents."""
        info = {}
        
        # Extract license number
        license_match = re.search(r"(?:dl|license)\s+no\.?\s*:?\s*([A-Z0-9]{8,15})", extracted_text, re.IGNORECASE)
        if license_match:
            info["document_number"] = license_match.group(1)
        
        # Extract full name
        name_match = re.search(r"(?:name|holder)\s*:?\s*([A-Za-z\s,]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
            info["full_name"] = full_name
            # Try to split into first and last name
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                info["first_name"] = name_parts[0]
                info["last_name"] = " ".join(name_parts[1:])
        
        # Extract dates
        dob_match = re.search(r"(?:dob|date\s+of\s+birth)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", extracted_text, re.IGNORECASE)
        if dob_match:
            info["date_of_birth"] = dob_match.group(1)
        
        exp_match = re.search(r"expir(?:es|ation)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", extracted_text, re.IGNORECASE)
        if exp_match:
            info["expiration_date"] = exp_match.group(1)
        
        # Extract address
        address_match = re.search(r"address\s*:?\s*([A-Za-z0-9\s,\.]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        if address_match:
            info["address"] = address_match.group(1).strip()
        
        return info
    
    def _extract_national_id_info(self, extracted_text: str) -> Dict[str, Any]:
        """Extract information specific to national ID documents."""
        info = {}
        
        # Extract ID number
        id_match = re.search(r"(?:id|identification)\s+no\.?\s*:?\s*([A-Z0-9]{8,20})", extracted_text, re.IGNORECASE)
        if id_match:
            info["document_number"] = id_match.group(1)
        
        # Extract full name
        name_match = re.search(r"(?:name|holder)\s*:?\s*([A-Za-z\s,]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
            info["full_name"] = full_name
            # Try to split into first and last name
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                info["first_name"] = name_parts[0]
                info["last_name"] = " ".join(name_parts[1:])
        
        # Extract nationality
        nationality_match = re.search(r"nationality\s*:?\s*([A-Z]{2,3}|[A-Za-z\s]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        if nationality_match:
            info["nationality"] = nationality_match.group(1).strip()
        
        # Extract dates
        dob_match = re.search(r"(?:dob|date\s+of\s+birth)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", extracted_text, re.IGNORECASE)
        if dob_match:
            info["date_of_birth"] = dob_match.group(1)
        
        exp_match = re.search(r"expir(?:y|ation)\s+date\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", extracted_text, re.IGNORECASE)
        if exp_match:
            info["expiration_date"] = exp_match.group(1)
        
        # Extract place of birth
        pob_match = re.search(r"place\s+of\s+birth\s*:?\s*([A-Za-z\s,]+?)(?:\n|$)", extracted_text, re.IGNORECASE)
        if pob_match:
            info["place_of_birth"] = pob_match.group(1).strip()
        
        return info
    
    def _enhance_with_key_value_pairs(self, identity_info: Dict[str, Any], 
                                    key_value_pairs: List[Dict]) -> Dict[str, Any]:
        """Enhance identity information with key-value pairs."""
        for kvp in key_value_pairs:
            key = kvp.get("key", "").lower()
            value = kvp.get("value", "")
            
            if not value:
                continue
            
            # Map key-value pairs to identity fields
            if "name" in key and not identity_info.get("full_name"):
                identity_info["full_name"] = value
            elif "birth" in key and "date" in key and not identity_info.get("date_of_birth"):
                identity_info["date_of_birth"] = value
            elif "nationality" in key and not identity_info.get("nationality"):
                identity_info["nationality"] = value
            elif ("passport" in key and "no" in key) or ("id" in key and "no" in key) or ("dl" in key and "no" in key):
                if not identity_info.get("document_number"):
                    identity_info["document_number"] = value
            elif "expir" in key and not identity_info.get("expiration_date"):
                identity_info["expiration_date"] = value
            elif "address" in key and not identity_info.get("address"):
                identity_info["address"] = value
        
        return identity_info
    
    async def _perform_consistency_checks(self, identity_info: Dict[str, Any],
                                        validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform consistency checks on extracted identity information."""
        # Simulate processing delay
        await asyncio.sleep(0.05)
        
        consistency_results = {
            "overall_consistency": True,
            "checks_performed": [],
            "inconsistencies": [],
            "warnings": []
        }
        
        # Check date format consistency
        date_fields = ["date_of_birth", "expiration_date"]
        date_formats = []
        
        for field in date_fields:
            if identity_info.get(field):
                date_format = self._detect_date_format(identity_info[field])
                if date_format:
                    date_formats.append(date_format)
                    consistency_results["checks_performed"].append(f"Date format check for {field}")
        
        if len(set(date_formats)) > 1:
            consistency_results["inconsistencies"].append("Inconsistent date formats detected")
            consistency_results["overall_consistency"] = False
        
        # Check name consistency
        if identity_info.get("full_name") and identity_info.get("first_name") and identity_info.get("last_name"):
            expected_full_name = f"{identity_info['first_name']} {identity_info['last_name']}"
            if identity_info["full_name"].lower() != expected_full_name.lower():
                consistency_results["warnings"].append("Name field inconsistency detected")
        
        # Check expiration date validity
        if identity_info.get("expiration_date"):
            if self._is_date_expired(identity_info["expiration_date"]):
                consistency_results["warnings"].append("Document appears to be expired")
            consistency_results["checks_performed"].append("Expiration date validity check")
        
        # Also check validation details for expiration
        validation_details = validation_results.get("details", {})
        for field_name, field_data in validation_details.items():
            if "expir" in field_name and field_data.get("found") and field_data.get("value"):
                if self._is_date_expired(field_data["value"]):
                    consistency_results["warnings"].append("Document appears to be expired")
                    break
        
        # Check validation score consistency
        if validation_results.get("score", 0) < 50:
            consistency_results["warnings"].append("Low validation score indicates potential issues")
        
        return consistency_results
    
    def _initialize_validation_patterns(self) -> Dict[str, Any]:
        """Initialize validation patterns for different document types."""
        return {
            "passport": {
                "required_fields": ["passport_number", "nationality", "date_of_birth", "expiration_date"],
                "optional_fields": ["place_of_birth", "issuing_authority", "given_names", "surname"]
            },
            "drivers_license": {
                "required_fields": ["license_number", "class", "expiration_date", "date_of_birth"],
                "optional_fields": ["full_name", "address", "restrictions"]
            },
            "national_id": {
                "required_fields": ["id_number", "nationality", "date_of_birth"],
                "optional_fields": ["full_name", "place_of_birth", "expiration_date"]
            }
        }
    
    def _initialize_country_codes(self) -> List[str]:
        """Initialize list of valid country codes."""
        return [
            "US", "USA", "CA", "CAN", "GB", "GBR", "DE", "DEU", "FR", "FRA",
            "IT", "ITA", "ES", "ESP", "AU", "AUS", "JP", "JPN", "CN", "CHN",
            "IN", "IND", "BR", "BRA", "MX", "MEX", "RU", "RUS", "ZA", "ZAF"
        ]
    
    def _initialize_state_codes(self) -> List[str]:
        """Initialize list of valid US state codes."""
        return [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
    
    def _initialize_document_formats(self) -> Dict[str, Any]:
        """Initialize document format specifications."""
        return {
            "passport": {
                "number_format": r"^[A-Z0-9]{6,12}$",
                "required_text": ["passport", "travel document"]
            },
            "drivers_license": {
                "number_format": r"^[A-Z0-9]{8,15}$",
                "required_text": ["driver", "license"]
            },
            "national_id": {
                "number_format": r"^[A-Z0-9]{8,20}$",
                "required_text": ["national", "identity", "id"]
            }
        }
    
    def _validate_country_code(self, country_code: str) -> bool:
        """Validate country code against known codes."""
        return country_code.upper() in self.country_codes
    
    def _validate_license_class(self, license_class: str) -> bool:
        """Validate driver's license class."""
        valid_classes = ["A", "B", "C", "D", "M", "CDL-A", "CDL-B", "CDL-C"]
        return license_class.upper() in valid_classes
    
    def _detect_date_format(self, date_string: str) -> Optional[str]:
        """Detect the format of a date string."""
        date_patterns = {
            r"\d{1,2}/\d{1,2}/\d{4}": "MM/DD/YYYY",
            r"\d{1,2}-\d{1,2}-\d{4}": "MM-DD-YYYY",
            r"\d{1,2}\.\d{1,2}\.\d{4}": "MM.DD.YYYY",
            r"\d{4}/\d{1,2}/\d{1,2}": "YYYY/MM/DD",
            r"\d{4}-\d{1,2}-\d{1,2}": "YYYY-MM-DD"
        }
        
        for pattern, format_name in date_patterns.items():
            if re.match(pattern, date_string):
                return format_name
        
        return None
    
    def _is_date_expired(self, date_string: str) -> bool:
        """Check if a date string represents an expired date."""
        try:
            # Try to parse common date formats
            formats = [
                "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
                "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y",
                "%d JAN %Y", "%d FEB %Y", "%d MAR %Y", "%d APR %Y", "%d MAY %Y", "%d JUN %Y",
                "%d JUL %Y", "%d AUG %Y", "%d SEP %Y", "%d OCT %Y", "%d NOV %Y", "%d DEC %Y"
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_string, fmt).date()
                    return parsed_date < date.today()
                except ValueError:
                    continue
        except Exception:
            pass
        
        return False  # If we can't parse the date, assume it's not expired