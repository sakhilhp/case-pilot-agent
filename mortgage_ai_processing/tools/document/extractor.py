"""
Generic document extraction tool with template-based extraction.

This tool provides structured data extraction capabilities for any document type
using customizable templates and extraction patterns.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio
import re
from pathlib import Path

from ..base import BaseTool, ToolResult
from ...models.enums import DocumentType


class DocumentExtractor(BaseTool):
    """
    Tool for extracting structured data from documents using templates.
    
    This tool provides:
    - Template-based extraction for any document type
    - Customizable extraction patterns and rules
    - Field validation and data type conversion
    - Template management and customization
    - Confidence scoring for extracted data
    """
    
    def __init__(self):
        super().__init__(
            name="document_extractor",
            description="Extract structured data from documents using customizable templates",
            agent_domain="document_processing"
        )
        self.logger = logging.getLogger("tool.document_extractor")
        
        # Template storage
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.template_directory = "templates/extraction"
        
        # Initialize default templates
        self._initialize_default_templates()
        
        # Load custom templates if available
        self._load_custom_templates()
    
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
                    "description": "Type of document to extract data from",
                    "enum": [dt.value for dt in DocumentType]
                },
                "extracted_text": {
                    "type": "string",
                    "description": "Text content extracted from the document"
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
                "tables": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Tables extracted from the document",
                    "default": []
                },
                "template_name": {
                    "type": "string",
                    "description": "Specific template to use for extraction (optional)"
                },
                "custom_fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field_name": {"type": "string"},
                            "extraction_pattern": {"type": "string"},
                            "data_type": {"type": "string"},
                            "required": {"type": "boolean"}
                        }
                    },
                    "description": "Custom fields to extract beyond template defaults",
                    "default": []
                }
            },
            "required": ["document_id", "document_type", "extracted_text"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute document extraction using templates.
        
        Args:
            document_id: Unique identifier for the document
            document_type: Type of document to extract data from
            extracted_text: Text content from the document
            key_value_pairs: Key-value pairs from OCR
            tables: Tables from OCR
            template_name: Specific template to use
            custom_fields: Additional fields to extract
            
        Returns:
            ToolResult containing extracted structured data
        """
        document_id = kwargs.get("document_id")
        document_type = kwargs.get("document_type")
        extracted_text = kwargs.get("extracted_text", "")
        key_value_pairs = kwargs.get("key_value_pairs", [])
        tables = kwargs.get("tables", [])
        template_name = kwargs.get("template_name")
        custom_fields = kwargs.get("custom_fields", [])
        
        try:
            self.logger.info(f"Starting document extraction for document {document_id} of type {document_type}")
            
            # Validate input
            if not extracted_text.strip():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="No text content provided for extraction"
                )
            
            # Get extraction template
            template = self._get_extraction_template(document_type, template_name)
            if not template:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message=f"No template found for document type: {document_type}"
                )
            
            # Perform extraction
            extraction_result = await self._extract_structured_data(
                extracted_text, key_value_pairs, tables, template, custom_fields
            )
            
            # Build result data
            result_data = {
                "document_id": document_id,
                "document_type": document_type,
                "template_used": template.get("name", "default"),
                "extracted_fields": extraction_result["fields"],
                "extraction_confidence": extraction_result["confidence"],
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_method": "template_based",
                "validation_results": extraction_result["validation"],
                "extraction_metadata": {
                    "fields_extracted": len(extraction_result["fields"]),
                    "fields_validated": len([f for f in extraction_result["validation"] if f["is_valid"]]),
                    "overall_confidence": extraction_result["confidence"]
                }
            }
            
            self.logger.info(f"Document extraction completed for {document_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"Document extraction failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    def _initialize_default_templates(self) -> None:
        """Initialize default extraction templates for common document types."""
        
        # Pay stub template
        self.templates["pay_stub"] = {
            "name": "pay_stub",
            "document_types": [DocumentType.PAY_STUB.value, DocumentType.INCOME.value],
            "fields": {
                "employee_name": {
                    "patterns": [r"employee\s*:?\s*([^\n\r]+)", r"name\s*:?\s*([^\n\r]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "employer_name": {
                    "patterns": [r"company\s*:?\s*([^\n\r]+)", r"employer\s*:?\s*([^\n\r]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "pay_period_start": {
                    "patterns": [r"pay\s+period\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", r"from\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"],
                    "data_type": "date",
                    "required": True,
                    "validation": {"format": "date"}
                },
                "pay_period_end": {
                    "patterns": [r"to\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", r"through\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"],
                    "data_type": "date",
                    "required": True,
                    "validation": {"format": "date"}
                },
                "gross_pay": {
                    "patterns": [r"gross\s+pay\s*:?\s*\$?([0-9,]+\.?\d*)", r"total\s+earnings\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": True,
                    "validation": {"min_value": 0}
                },
                "net_pay": {
                    "patterns": [r"net\s+pay\s*:?\s*\$?([0-9,]+\.?\d*)", r"take\s+home\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": True,
                    "validation": {"min_value": 0}
                },
                "ytd_gross": {
                    "patterns": [r"ytd\s+gross\s*:?\s*\$?([0-9,]+\.?\d*)", r"year\s+to\s+date\s+gross\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": False,
                    "validation": {"min_value": 0}
                }
            }
        }
        
        # Bank statement template
        self.templates["bank_statement"] = {
            "name": "bank_statement",
            "document_types": [DocumentType.BANK_STATEMENT.value],
            "fields": {
                "account_holder": {
                    "patterns": [r"account\s+holder\s*:?\s*([^\n\r]+)", r"customer\s*:?\s*([^\n\r]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "account_number": {
                    "patterns": [r"account\s+(?:no|number)\s*:?\s*([0-9\*\-]+)", r"acct\s*:?\s*([0-9\*\-]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 4}
                },
                "statement_period_start": {
                    "patterns": [r"statement\s+period\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", r"from\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"],
                    "data_type": "date",
                    "required": True,
                    "validation": {"format": "date"}
                },
                "statement_period_end": {
                    "patterns": [r"to\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", r"through\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"],
                    "data_type": "date",
                    "required": True,
                    "validation": {"format": "date"}
                },
                "beginning_balance": {
                    "patterns": [r"beginning\s+balance\s*:?\s*\$?([0-9,\-]+\.?\d*)", r"opening\s+balance\s*:?\s*\$?([0-9,\-]+\.?\d*)"],
                    "data_type": "currency",
                    "required": True,
                    "validation": {}
                },
                "ending_balance": {
                    "patterns": [r"ending\s+balance\s*:?\s*\$?([0-9,\-]+\.?\d*)", r"closing\s+balance\s*:?\s*\$?([0-9,\-]+\.?\d*)"],
                    "data_type": "currency",
                    "required": True,
                    "validation": {}
                }
            }
        }
        
        # Employment letter template
        self.templates["employment_letter"] = {
            "name": "employment_letter",
            "document_types": [DocumentType.EMPLOYMENT_LETTER.value, DocumentType.EMPLOYMENT.value],
            "fields": {
                "employee_name": {
                    "patterns": [r"(?:employee|person)\s*:?\s*([^\n\r]+)", r"(?:mr|ms|mrs)\.?\s+([^\n\r,]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "employer_name": {
                    "patterns": [r"company\s*:?\s*([^\n\r]+)", r"employer\s*:?\s*([^\n\r]+)", r"([A-Z][a-z]+\s+(?:Corporation|Company|Inc|LLC))"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "position": {
                    "patterns": [r"position\s*:?\s*([^\n\r]+)", r"title\s*:?\s*([^\n\r]+)", r"employed\s+as\s+(?:a\s+)?([^\n\r]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "annual_salary": {
                    "patterns": [r"annual\s+salary\s*:?\s*\$?([0-9,]+\.?\d*)", r"yearly\s+compensation\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": False,
                    "validation": {"min_value": 0}
                },
                "hourly_rate": {
                    "patterns": [r"hourly\s+rate\s*:?\s*\$?([0-9,]+\.?\d*)", r"per\s+hour\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": False,
                    "validation": {"min_value": 0}
                },
                "start_date": {
                    "patterns": [r"start\s+date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", r"employed\s+since\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"],
                    "data_type": "date",
                    "required": False,
                    "validation": {"format": "date"}
                }
            }
        }
        
        # Tax document template
        self.templates["tax_document"] = {
            "name": "tax_document",
            "document_types": [DocumentType.TAX_DOCUMENT.value],
            "fields": {
                "taxpayer_name": {
                    "patterns": [r"name\s*:?\s*([^\n\r]+)", r"taxpayer\s*:?\s*([^\n\r]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "tax_year": {
                    "patterns": [r"tax\s+year\s*:?\s*(\d{4})", r"for\s+year\s*:?\s*(\d{4})"],
                    "data_type": "integer",
                    "required": True,
                    "validation": {"min_value": 1900, "max_value": 2030}
                },
                "adjusted_gross_income": {
                    "patterns": [r"adjusted\s+gross\s+income\s*:?\s*\$?([0-9,]+\.?\d*)", r"agi\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": False,
                    "validation": {"min_value": 0}
                },
                "total_income": {
                    "patterns": [r"total\s+income\s*:?\s*\$?([0-9,]+\.?\d*)", r"gross\s+income\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": False,
                    "validation": {"min_value": 0}
                }
            }
        }
        
        # Utility bill template
        self.templates["utility_bill"] = {
            "name": "utility_bill",
            "document_types": [DocumentType.UTILITY_BILL.value, DocumentType.ADDRESS_PROOF.value],
            "fields": {
                "customer_name": {
                    "patterns": [r"customer\s*:?\s*([^\n\r]+)", r"account\s+holder\s*:?\s*([^\n\r]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 2}
                },
                "service_address": {
                    "patterns": [r"service\s+address\s*:?\s*([^\n\r]+)", r"property\s+address\s*:?\s*([^\n\r]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 10}
                },
                "account_number": {
                    "patterns": [r"account\s+(?:no|number)\s*:?\s*([0-9\-]+)", r"acct\s*:?\s*([0-9\-]+)"],
                    "data_type": "string",
                    "required": True,
                    "validation": {"min_length": 4}
                },
                "bill_date": {
                    "patterns": [r"bill\s+date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", r"statement\s+date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"],
                    "data_type": "date",
                    "required": True,
                    "validation": {"format": "date"}
                },
                "amount_due": {
                    "patterns": [r"amount\s+due\s*:?\s*\$?([0-9,]+\.?\d*)", r"total\s+due\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": True,
                    "validation": {"min_value": 0}
                }
            }
        }
        
        # Generic template for unknown document types
        self.templates["generic"] = {
            "name": "generic",
            "document_types": ["*"],
            "fields": {
                "name": {
                    "patterns": [r"name\s*:?\s*([^\n\r]+)", r"full\s+name\s*:?\s*([^\n\r]+)"],
                    "data_type": "string",
                    "required": False,
                    "validation": {"min_length": 2}
                },
                "date": {
                    "patterns": [r"date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})"],
                    "data_type": "date",
                    "required": False,
                    "validation": {"format": "date"}
                },
                "amount": {
                    "patterns": [r"amount\s*:?\s*\$?([0-9,]+\.?\d*)", r"total\s*:?\s*\$?([0-9,]+\.?\d*)"],
                    "data_type": "currency",
                    "required": False,
                    "validation": {"min_value": 0}
                }
            }
        }
    
    def _load_custom_templates(self) -> None:
        """Load custom templates from the template directory."""
        try:
            template_path = Path(self.template_directory)
            if template_path.exists():
                for template_file in template_path.glob("*.json"):
                    try:
                        with open(template_file, 'r') as f:
                            template_data = json.load(f)
                            template_name = template_file.stem
                            self.templates[template_name] = template_data
                            self.logger.info(f"Loaded custom template: {template_name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to load template {template_file}: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Failed to load custom templates: {str(e)}")
    
    def _get_extraction_template(self, document_type: str, template_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the appropriate extraction template for a document type."""
        
        # Use specific template if provided
        if template_name and template_name in self.templates:
            return self.templates[template_name]
        
        # Find template by document type
        for template in self.templates.values():
            if document_type in template.get("document_types", []):
                return template
        
        # Use generic template as fallback
        return self.templates.get("generic")
    
    async def _extract_structured_data(self, extracted_text: str, key_value_pairs: List[Dict],
                                     tables: List[Dict], template: Dict[str, Any],
                                     custom_fields: List[Dict]) -> Dict[str, Any]:
        """Extract structured data using the template."""
        
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        extracted_fields = {}
        validation_results = []
        confidence_scores = []
        
        # Extract fields defined in template
        template_fields = template.get("fields", {})
        for field_name, field_config in template_fields.items():
            field_result = self._extract_field(extracted_text, key_value_pairs, field_name, field_config)
            if field_result["value"] is not None:
                extracted_fields[field_name] = field_result["value"]
                confidence_scores.append(field_result["confidence"])
            
            validation_results.append({
                "field_name": field_name,
                "is_valid": field_result["is_valid"],
                "validation_message": field_result["validation_message"],
                "confidence": field_result["confidence"]
            })
        
        # Extract custom fields
        for custom_field in custom_fields:
            field_name = custom_field.get("field_name")
            if not field_name:
                continue
                
            field_config = {
                "patterns": [custom_field.get("extraction_pattern", "")],
                "data_type": custom_field.get("data_type", "string"),
                "required": custom_field.get("required", False),
                "validation": {}
            }
            
            field_result = self._extract_field(extracted_text, key_value_pairs, field_name, field_config)
            if field_result["value"] is not None:
                extracted_fields[field_name] = field_result["value"]
                confidence_scores.append(field_result["confidence"])
            
            validation_results.append({
                "field_name": field_name,
                "is_valid": field_result["is_valid"],
                "validation_message": field_result["validation_message"],
                "confidence": field_result["confidence"]
            })
        
        # Extract data from tables if available
        if tables:
            table_data = self._extract_from_tables(tables, template)
            extracted_fields.update(table_data)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "fields": extracted_fields,
            "confidence": round(overall_confidence, 3),
            "validation": validation_results
        } 
   
    def _extract_field(self, extracted_text: str, key_value_pairs: List[Dict],
                      field_name: str, field_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a single field using the field configuration."""
        
        patterns = field_config.get("patterns", [])
        data_type = field_config.get("data_type", "string")
        required = field_config.get("required", False)
        validation_config = field_config.get("validation", {})
        
        extracted_value = None
        confidence = 0.0
        
        # First try to extract from key-value pairs (higher confidence)
        kvp_value = self._extract_from_key_value_pairs(key_value_pairs, field_name, patterns)
        if kvp_value:
            extracted_value = kvp_value["value"]
            confidence = kvp_value["confidence"] * 0.9  # Slightly lower than OCR confidence
        
        # If not found in KVP, try text patterns
        if extracted_value is None:
            text_value = self._extract_from_text_patterns(extracted_text, patterns)
            if text_value:
                extracted_value = text_value
                confidence = 0.7  # Medium confidence for pattern matching
        
        # Convert data type
        converted_value, conversion_success = self._convert_data_type(extracted_value, data_type)
        if conversion_success:
            extracted_value = converted_value
        else:
            confidence *= 0.5  # Reduce confidence if conversion failed
        
        # Validate the extracted value
        is_valid, validation_message = self._validate_field_value(extracted_value, validation_config, required)
        
        return {
            "value": extracted_value,
            "confidence": round(confidence, 3),
            "is_valid": is_valid,
            "validation_message": validation_message
        }
    
    def _extract_from_key_value_pairs(self, key_value_pairs: List[Dict], 
                                    field_name: str, patterns: List[str]) -> Optional[Dict[str, Any]]:
        """Extract field value from key-value pairs."""
        
        # Create search terms from field name and patterns
        search_terms = [field_name.lower().replace("_", " ")]
        
        # Add pattern-based search terms
        for pattern in patterns:
            # Extract key words from regex patterns
            clean_pattern = re.sub(r'[\\()\[\]{}.*+?^$|]', ' ', pattern)
            words = [w.strip() for w in clean_pattern.split() if len(w.strip()) > 2]
            search_terms.extend([w.lower() for w in words])
        
        # Remove duplicates
        search_terms = list(set(search_terms))
        
        # Search in key-value pairs
        for kvp in key_value_pairs:
            key = kvp.get("key", "").lower()
            value = kvp.get("value", "")
            kvp_confidence = kvp.get("confidence", 0.0)
            
            # Check if any search term matches the key
            for term in search_terms:
                if term in key or any(word in key for word in term.split()):
                    return {
                        "value": value.strip(),
                        "confidence": kvp_confidence
                    }
        
        return None
    
    def _extract_from_text_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract field value using regex patterns."""
        
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if match.groups():
                        # Return the first capturing group
                        value = match.group(1).strip()
                        if value:
                            return value
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern '{pattern}': {str(e)}")
                continue
        
        return None
    
    def _convert_data_type(self, value: Any, data_type: str) -> tuple[Any, bool]:
        """Convert extracted value to the specified data type."""
        
        if value is None:
            return None, True
        
        try:
            if data_type == "string":
                return str(value), True
            
            elif data_type == "integer":
                # Remove commas and convert to int
                clean_value = str(value).replace(",", "")
                return int(float(clean_value)), True
            
            elif data_type == "float":
                # Remove commas and convert to float
                clean_value = str(value).replace(",", "")
                return float(clean_value), True
            
            elif data_type == "currency":
                # Remove currency symbols and commas, convert to float
                clean_value = re.sub(r'[$,]', '', str(value))
                return float(clean_value), True
            
            elif data_type == "date":
                # Try to parse common date formats
                date_value = self._parse_date(str(value))
                return date_value, date_value is not None
            
            elif data_type == "boolean":
                # Convert to boolean
                bool_value = str(value).lower() in ["true", "yes", "1", "y", "on"]
                return bool_value, True
            
            else:
                # Unknown data type, return as string
                return str(value), True
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to convert '{value}' to {data_type}: {str(e)}")
            return value, False
    
    def _parse_date(self, date_string: str) -> Optional[str]:
        """Parse date string into standardized format."""
        
        # Common date patterns
        date_patterns = [
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})',   # MM/DD/YY or MM-DD-YY
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',   # YYYY/MM/DD or YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_string)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Determine format and convert to YYYY-MM-DD
                        if len(groups[0]) == 4:  # YYYY-MM-DD format
                            year, month, day = groups
                        else:  # MM/DD/YYYY format
                            month, day, year = groups
                            if len(year) == 2:
                                # Convert 2-digit year to 4-digit
                                year = "20" + year if int(year) < 50 else "19" + year
                        
                        # Validate date components
                        year_int = int(year)
                        month_int = int(month)
                        day_int = int(day)
                        
                        if 1900 <= year_int <= 2100 and 1 <= month_int <= 12 and 1 <= day_int <= 31:
                            return f"{year_int:04d}-{month_int:02d}-{day_int:02d}"
                            
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _validate_field_value(self, value: Any, validation_config: Dict[str, Any], 
                            required: bool) -> tuple[bool, str]:
        """Validate extracted field value against validation rules."""
        
        # Check if required field is missing
        if required and (value is None or str(value).strip() == ""):
            return False, "Required field is missing"
        
        # If value is None and not required, it's valid
        if value is None:
            return True, "Optional field not found"
        
        # String validations
        if isinstance(value, str):
            min_length = validation_config.get("min_length")
            max_length = validation_config.get("max_length")
            
            if min_length and len(value) < min_length:
                return False, f"Value too short (minimum {min_length} characters)"
            
            if max_length and len(value) > max_length:
                return False, f"Value too long (maximum {max_length} characters)"
        
        # Numeric validations
        if isinstance(value, (int, float)):
            min_value = validation_config.get("min_value")
            max_value = validation_config.get("max_value")
            
            if min_value is not None and value < min_value:
                return False, f"Value too small (minimum {min_value})"
            
            if max_value is not None and value > max_value:
                return False, f"Value too large (maximum {max_value})"
        
        # Date format validation
        if validation_config.get("format") == "date":
            if not isinstance(value, str) or not re.match(r'\d{4}-\d{2}-\d{2}', value):
                return False, "Invalid date format (expected YYYY-MM-DD)"
        
        # Custom pattern validation
        pattern = validation_config.get("pattern")
        if pattern and isinstance(value, str):
            if not re.match(pattern, value):
                return False, f"Value does not match required pattern"
        
        return True, "Valid"
    
    def _extract_from_tables(self, tables: List[Dict], template: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from tables when available."""
        
        extracted_data = {}
        
        for table in tables:
            # Handle different table formats
            if "cells" in table:
                # Azure Document Intelligence format
                table_data = self._process_azure_table(table)
            elif "data" in table:
                # Simple array format
                table_data = table["data"]
            else:
                continue
            
            # Extract key-value pairs from table
            kvp_data = self._extract_kvp_from_table(table_data)
            
            # Try to match table data to template fields
            template_fields = template.get("fields", {})
            for field_name, field_config in template_fields.items():
                if field_name not in extracted_data:
                    # Look for field in table data
                    field_value = self._find_field_in_table_data(field_name, field_config, kvp_data)
                    if field_value:
                        extracted_data[field_name] = field_value
        
        return extracted_data
    
    def _process_azure_table(self, table: Dict[str, Any]) -> List[List[str]]:
        """Process Azure Document Intelligence table format."""
        
        row_count = table.get("row_count", 0)
        column_count = table.get("column_count", 0)
        cells = table.get("cells", [])
        
        # Initialize table grid
        table_grid = [["" for _ in range(column_count)] for _ in range(row_count)]
        
        # Fill table grid with cell data
        for cell in cells:
            row_index = cell.get("row_index", 0)
            column_index = cell.get("column_index", 0)
            content = cell.get("content", "")
            
            if 0 <= row_index < row_count and 0 <= column_index < column_count:
                table_grid[row_index][column_index] = content
        
        return table_grid
    
    def _extract_kvp_from_table(self, table_data: List[List[str]]) -> List[Dict[str, str]]:
        """Extract key-value pairs from table data."""
        
        kvp_data = []
        
        # Assume first row might be headers
        if len(table_data) < 2:
            return kvp_data
        
        # Try different table layouts
        
        # Layout 1: Two-column key-value table
        if len(table_data[0]) == 2:
            for row in table_data[1:]:  # Skip header row
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    kvp_data.append({
                        "key": row[0].strip(),
                        "value": row[1].strip()
                    })
        
        # Layout 2: Multi-column table with alternating key-value pairs
        elif len(table_data[0]) > 2:
            for row in table_data[1:]:  # Skip header row
                for i in range(0, len(row) - 1, 2):
                    if i + 1 < len(row) and row[i].strip() and row[i + 1].strip():
                        kvp_data.append({
                            "key": row[i].strip(),
                            "value": row[i + 1].strip()
                        })
        
        return kvp_data
    
    def _find_field_in_table_data(self, field_name: str, field_config: Dict[str, Any],
                                 table_kvp_data: List[Dict[str, str]]) -> Optional[str]:
        """Find field value in table key-value data."""
        
        # Create search terms from field name
        search_terms = [field_name.lower().replace("_", " ")]
        
        # Add terms from patterns
        patterns = field_config.get("patterns", [])
        for pattern in patterns:
            clean_pattern = re.sub(r'[\\()\[\]{}.*+?^$|]', ' ', pattern)
            words = [w.strip() for w in clean_pattern.split() if len(w.strip()) > 2]
            search_terms.extend([w.lower() for w in words])
        
        # Remove duplicates
        search_terms = list(set(search_terms))
        
        # Search in table key-value pairs
        for kvp in table_kvp_data:
            key = kvp.get("key", "").lower()
            value = kvp.get("value", "")
            
            # Check if any search term matches the key
            for term in search_terms:
                if term in key or any(word in key for word in term.split()):
                    return value.strip()
        
        return None
    
    def add_custom_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """Add a custom extraction template."""
        
        try:
            # Validate template structure
            if not self._validate_template_structure(template_data):
                self.logger.error(f"Invalid template structure for {template_name}")
                return False
            
            # Add template to memory
            self.templates[template_name] = template_data
            
            # Save to file if template directory exists
            try:
                template_path = Path(self.template_directory)
                template_path.mkdir(parents=True, exist_ok=True)
                
                template_file = template_path / f"{template_name}.json"
                with open(template_file, 'w') as f:
                    json.dump(template_data, f, indent=2)
                
                self.logger.info(f"Custom template '{template_name}' added and saved")
                return True
                
            except Exception as e:
                self.logger.warning(f"Template added to memory but failed to save to file: {str(e)}")
                return True  # Still successful since it's in memory
                
        except Exception as e:
            self.logger.error(f"Failed to add custom template '{template_name}': {str(e)}")
            return False
    
    def _validate_template_structure(self, template_data: Dict[str, Any]) -> bool:
        """Validate template data structure."""
        
        required_keys = ["name", "document_types", "fields"]
        
        # Check required top-level keys
        for key in required_keys:
            if key not in template_data:
                return False
        
        # Validate fields structure
        fields = template_data.get("fields", {})
        if not isinstance(fields, dict):
            return False
        
        for field_name, field_config in fields.items():
            if not isinstance(field_config, dict):
                return False
            
            # Check required field configuration keys
            if "patterns" not in field_config or "data_type" not in field_config:
                return False
            
            # Validate patterns
            patterns = field_config.get("patterns", [])
            if not isinstance(patterns, list) or not patterns:
                return False
        
        return True
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific template."""
        template = self.templates.get(template_name)
        if not template:
            return None
        
        return {
            "name": template.get("name"),
            "document_types": template.get("document_types", []),
            "field_count": len(template.get("fields", {})),
            "fields": list(template.get("fields", {}).keys())
        }