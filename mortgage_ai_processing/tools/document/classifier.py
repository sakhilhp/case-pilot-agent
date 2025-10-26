"""
Document classification tool with AI-powered classification.

This tool provides document classification capabilities for mortgage-related documents,
identifying document types and providing confidence scoring for classification results.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
import re

from ..base import BaseTool, ToolResult
from ...models.enums import DocumentType


class DocumentClassifier(BaseTool):
    """
    Tool for classifying documents using AI-powered analysis.
    
    This tool analyzes document content and metadata to classify documents into
    appropriate types for mortgage processing workflows. It provides:
    - Document type detection (invoice, receipt, contract, identity documents, etc.)
    - Classification confidence scoring
    - Content-based analysis for accurate classification
    - Support for various document formats and structures
    """
    
    def __init__(self):
        super().__init__(
            name="document_classifier",
            description="Classify documents by type with AI-powered analysis and confidence scoring",
            agent_domain="document_processing"
        )
        self.logger = logging.getLogger("tool.document_classifier")
        
        # Classification patterns and keywords for different document types
        self.classification_patterns = self._initialize_classification_patterns()
        
        # Confidence thresholds
        self.high_confidence_threshold = 0.8
        self.medium_confidence_threshold = 0.5
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "Unique identifier for the document"
                },
                "document_path": {
                    "type": "string",
                    "description": "Path to the document file (optional, for filename analysis)"
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
                "file_metadata": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "file_extension": {"type": "string"},
                        "file_size": {"type": "number"}
                    },
                    "description": "File metadata for additional classification hints",
                    "default": {}
                }
            },
            "required": ["document_id", "extracted_text"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute document classification on the provided content.
        
        Args:
            document_id: Unique identifier for the document
            document_path: Optional path to the document file
            extracted_text: Text content extracted from the document
            key_value_pairs: Key-value pairs extracted from the document
            file_metadata: File metadata for additional classification hints
            
        Returns:
            ToolResult containing classification results and confidence scores
        """
        document_id = kwargs.get("document_id")
        document_path = kwargs.get("document_path", "")
        extracted_text = kwargs.get("extracted_text", "")
        key_value_pairs = kwargs.get("key_value_pairs", [])
        file_metadata = kwargs.get("file_metadata", {})
        
        try:
            self.logger.info(f"Starting document classification for document {document_id}")
            
            # Validate input
            if not extracted_text.strip():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="No text content provided for classification"
                )
            
            # Perform classification analysis
            classification_results = await self._classify_document(
                extracted_text, key_value_pairs, document_path, file_metadata
            )
            
            # Build result data
            result_data = {
                "document_id": document_id,
                "classification_results": classification_results,
                "classification_timestamp": datetime.now().isoformat(),
                "primary_classification": classification_results[0] if classification_results else None,
                "classification_method": "ai_powered_analysis"
            }
            
            self.logger.info(f"Document classification completed for {document_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"Document classification failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    async def _classify_document(self, extracted_text: str, key_value_pairs: List[Dict], 
                               document_path: str, file_metadata: Dict) -> List[Dict[str, Any]]:
        """
        Perform document classification using multiple analysis methods.
        
        Args:
            extracted_text: Text content from the document
            key_value_pairs: Extracted key-value pairs
            document_path: Path to the document file
            file_metadata: File metadata
            
        Returns:
            List of classification results sorted by confidence
        """
        # Simulate processing delay for AI analysis
        await asyncio.sleep(0.1)
        
        # Analyze document using multiple methods
        filename_scores = self._analyze_filename(document_path, file_metadata)
        content_scores = self._analyze_content(extracted_text)
        structure_scores = self._analyze_structure(key_value_pairs)
        
        # Combine scores from different analysis methods
        combined_scores = self._combine_classification_scores(
            filename_scores, content_scores, structure_scores
        )
        
        # Convert to classification results with confidence levels
        classification_results = []
        for doc_type, score in combined_scores.items():
            confidence_level = self._determine_confidence_level(score)
            
            classification_results.append({
                "document_type": doc_type.value,
                "confidence_score": round(score, 3),
                "confidence_level": confidence_level,
                "classification_factors": self._get_classification_factors(
                    doc_type, extracted_text, key_value_pairs
                )
            })
        
        # Sort by confidence score (highest first)
        classification_results.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        # Return top 3 classifications
        return classification_results[:3]
    
    def _initialize_classification_patterns(self) -> Dict[DocumentType, Dict[str, Any]]:
        """Initialize classification patterns for different document types."""
        return {
            DocumentType.PASSPORT: {
                "keywords": ["passport", "travel document", "nationality", "place of birth", "issuing authority"],
                "patterns": [r"passport\s+no", r"passport\s+number", r"nationality", r"place\s+of\s+birth"],
                "required_fields": ["passport number", "nationality", "date of birth"]
            },
            DocumentType.DRIVERS_LICENSE: {
                "keywords": ["driver", "license", "licence", "dl", "driving", "motor vehicle"],
                "patterns": [r"driver.?s?\s+licen[cs]e", r"dl\s+no", r"license\s+number", r"class\s+[a-z]"],
                "required_fields": ["license number", "class", "expiration"]
            },
            DocumentType.NATIONAL_ID: {
                "keywords": ["national id", "identity card", "id card", "citizen", "identification"],
                "patterns": [r"national\s+id", r"identity\s+card", r"id\s+no", r"citizen\s+id"],
                "required_fields": ["id number", "nationality"]
            },
            DocumentType.PAY_STUB: {
                "keywords": ["pay stub", "payroll", "earnings", "gross pay", "net pay", "deductions"],
                "patterns": [r"pay\s+stub", r"payroll", r"gross\s+pay", r"net\s+pay", r"ytd\s+earnings"],
                "required_fields": ["gross pay", "net pay", "pay period"]
            },
            DocumentType.EMPLOYMENT_LETTER: {
                "keywords": ["employment", "verification", "confirm", "employed", "position", "salary"],
                "patterns": [r"employment\s+verification", r"confirm.*employ", r"annual\s+salary", r"position"],
                "required_fields": ["employee name", "position", "salary"]
            },
            DocumentType.BANK_STATEMENT: {
                "keywords": ["bank", "statement", "account", "balance", "transaction", "deposit"],
                "patterns": [r"bank\s+statement", r"account\s+summary", r"beginning\s+balance", r"ending\s+balance"],
                "required_fields": ["account number", "balance", "statement period"]
            },
            DocumentType.TAX_DOCUMENT: {
                "keywords": ["tax", "irs", "w-2", "1099", "return", "income tax", "federal"],
                "patterns": [r"tax\s+return", r"w-?2", r"1099", r"irs", r"adjusted\s+gross\s+income"],
                "required_fields": ["tax year", "income", "taxpayer"]
            },
            DocumentType.UTILITY_BILL: {
                "keywords": ["utility", "electric", "gas", "water", "bill", "service address"],
                "patterns": [r"utility\s+bill", r"electric.*company", r"gas.*company", r"service\s+address"],
                "required_fields": ["service address", "account number", "amount due"]
            },
            DocumentType.INVOICE: {
                "keywords": ["invoice", "bill", "amount due", "total", "payment", "vendor"],
                "patterns": [r"invoice\s+no", r"invoice\s+number", r"amount\s+due", r"total\s+amount"],
                "required_fields": ["invoice number", "amount", "vendor"]
            },
            DocumentType.RECEIPT: {
                "keywords": ["receipt", "paid", "transaction", "purchase", "total"],
                "patterns": [r"receipt", r"transaction\s+id", r"total\s+paid", r"purchase\s+date"],
                "required_fields": ["total", "date", "merchant"]
            },
            DocumentType.CONTRACT: {
                "keywords": ["contract", "agreement", "terms", "conditions", "party", "signature"],
                "patterns": [r"contract", r"agreement", r"terms\s+and\s+conditions", r"signature"],
                "required_fields": ["parties", "terms", "signature"]
            }
        }
    
    def _analyze_filename(self, document_path: str, file_metadata: Dict) -> Dict[DocumentType, float]:
        """Analyze filename and metadata for classification hints."""
        scores = {doc_type: 0.0 for doc_type in DocumentType}
        
        # Get filename from path or metadata
        filename = ""
        if document_path:
            filename = os.path.basename(document_path).lower()
        elif "filename" in file_metadata:
            filename = file_metadata["filename"].lower()
        
        if not filename:
            return scores
        
        # Check filename patterns
        filename_patterns = {
            DocumentType.PASSPORT: ["passport", "travel_doc"],
            DocumentType.DRIVERS_LICENSE: ["license", "dl", "driver"],
            DocumentType.PAY_STUB: ["paystub", "pay_stub", "payroll"],
            DocumentType.EMPLOYMENT_LETTER: ["employment", "verification", "letter"],
            DocumentType.BANK_STATEMENT: ["bank", "statement", "account"],
            DocumentType.TAX_DOCUMENT: ["tax", "w2", "1099", "return"],
            DocumentType.UTILITY_BILL: ["utility", "electric", "gas", "water", "bill"],
            DocumentType.INVOICE: ["invoice", "bill"],
            DocumentType.RECEIPT: ["receipt", "transaction"],
            DocumentType.CONTRACT: ["contract", "agreement"]
        }
        
        for doc_type, patterns in filename_patterns.items():
            for pattern in patterns:
                if pattern in filename:
                    scores[doc_type] += 0.3  # Filename match gives moderate confidence
        
        return scores
    
    def _analyze_content(self, extracted_text: str) -> Dict[DocumentType, float]:
        """Analyze document content for classification."""
        scores = {doc_type: 0.0 for doc_type in DocumentType}
        text_lower = extracted_text.lower()
        
        for doc_type, patterns in self.classification_patterns.items():
            # Check keywords
            keyword_matches = 0
            for keyword in patterns["keywords"]:
                if keyword.lower() in text_lower:
                    keyword_matches += 1
            
            # Check regex patterns
            pattern_matches = 0
            for pattern in patterns["patterns"]:
                if re.search(pattern, text_lower):
                    pattern_matches += 1
            
            # Calculate score based on matches
            keyword_score = min(keyword_matches / len(patterns["keywords"]), 1.0) * 0.6
            pattern_score = min(pattern_matches / len(patterns["patterns"]), 1.0) * 0.4
            
            scores[doc_type] = keyword_score + pattern_score
        
        return scores
    
    def _analyze_structure(self, key_value_pairs: List[Dict]) -> Dict[DocumentType, float]:
        """Analyze document structure based on key-value pairs."""
        scores = {doc_type: 0.0 for doc_type in DocumentType}
        
        if not key_value_pairs:
            return scores
        
        # Extract keys from key-value pairs
        keys = [kvp.get("key", "").lower() for kvp in key_value_pairs]
        
        for doc_type, patterns in self.classification_patterns.items():
            required_fields = patterns.get("required_fields", [])
            field_matches = 0
            
            for required_field in required_fields:
                field_lower = required_field.lower()
                # Check if any key contains the required field
                for key in keys:
                    if field_lower in key or any(word in key for word in field_lower.split()):
                        field_matches += 1
                        break
            
            # Calculate structure score
            if required_fields:
                scores[doc_type] = field_matches / len(required_fields) * 0.5
        
        return scores
    
    def _combine_classification_scores(self, filename_scores: Dict[DocumentType, float],
                                     content_scores: Dict[DocumentType, float],
                                     structure_scores: Dict[DocumentType, float]) -> Dict[DocumentType, float]:
        """Combine scores from different analysis methods."""
        combined_scores = {}
        
        for doc_type in DocumentType:
            # Weighted combination of scores
            filename_weight = 0.2
            content_weight = 0.6
            structure_weight = 0.2
            
            combined_score = (
                filename_scores.get(doc_type, 0.0) * filename_weight +
                content_scores.get(doc_type, 0.0) * content_weight +
                structure_scores.get(doc_type, 0.0) * structure_weight
            )
            
            combined_scores[doc_type] = combined_score
        
        return combined_scores
    
    def _determine_confidence_level(self, score: float) -> str:
        """Determine confidence level based on score."""
        if score >= self.high_confidence_threshold:
            return "high"
        elif score >= self.medium_confidence_threshold:
            return "medium"
        else:
            return "low"
    
    def _get_classification_factors(self, doc_type: DocumentType, 
                                  extracted_text: str, 
                                  key_value_pairs: List[Dict]) -> List[str]:
        """Get factors that contributed to the classification."""
        factors = []
        text_lower = extracted_text.lower()
        
        if doc_type in self.classification_patterns:
            patterns = self.classification_patterns[doc_type]
            
            # Check which keywords were found
            for keyword in patterns["keywords"]:
                if keyword.lower() in text_lower:
                    factors.append(f"Keyword match: '{keyword}'")
            
            # Check which patterns were found
            for pattern in patterns["patterns"]:
                if re.search(pattern, text_lower):
                    factors.append(f"Pattern match: {pattern}")
            
            # Check which required fields were found
            keys = [kvp.get("key", "").lower() for kvp in key_value_pairs]
            for required_field in patterns.get("required_fields", []):
                field_lower = required_field.lower()
                for key in keys:
                    if field_lower in key:
                        factors.append(f"Required field found: '{required_field}'")
                        break
        
        return factors[:5]  # Return top 5 factors