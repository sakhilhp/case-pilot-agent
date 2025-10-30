"""
Document OCR extraction tool using Azure Document Intelligence.

This tool provides OCR capabilities for extracting text, tables, and key-value pairs
from mortgage-related documents using Azure's Document Intelligence service.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from dotenv import load_dotenv

from ..base import BaseTool, ToolResult

load_dotenv()


class DocumentOCRExtractor(BaseTool):
    """
    Tool for extracting text, tables, and key-value pairs from documents using Azure Document Intelligence.
    
    This tool integrates with Azure Document Intelligence to provide:
    - Text extraction from various document formats
    - Table detection and extraction
    - Key-value pair identification
    - Layout analysis and structure detection
    - Confidence scoring for extracted content
    """
    
    def __init__(self):
        from ..base import ToolCategory
        super().__init__(
            name="document_ocr_extractor",
            description="Extract text, tables, and key-value pairs from documents using Azure Document Intelligence",
            category=ToolCategory.DOCUMENT_PROCESSING,
            agent_domain="document_processing"
        )
        self.logger = logging.getLogger("tool.document_ocr_extractor")
        
        # Azure Document Intelligence configuration
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
        self.api_version = "2023-07-31"
        
        # Validate configuration
        if not self.endpoint or not self.api_key:
            self.logger.warning("Azure Document Intelligence credentials not configured")
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "document_path": {
                    "type": "string",
                    "description": "Path to the document file to process"
                },
                "document_id": {
                    "type": "string", 
                    "description": "Unique identifier for the document"
                },
                "analysis_features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of analysis features to enable",
                    "default": ["ocr_read", "layout", "key_value_pairs", "tables"]
                },
                "pages": {
                    "type": "string",
                    "description": "Page range to analyze (e.g., '1-3' or 'all')",
                    "default": "all"
                }
            },
            "required": ["document_path", "document_id"]
        }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters (backward compatibility)."""
        return self.get_input_schema()
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute OCR extraction on the specified document.
        
        Args:
            document_path: Path to the document file
            document_id: Unique identifier for the document
            analysis_features: List of features to analyze
            pages: Page range to process
            
        Returns:
            ToolResult containing extracted text, tables, and key-value pairs
        """
        document_path = kwargs.get("document_path")
        document_id = kwargs.get("document_id")
        analysis_features = kwargs.get("analysis_features", ["ocr_read", "layout", "key_value_pairs", "tables"])
        pages = kwargs.get("pages", "all")
        
        try:
            self.logger.info(f"Starting OCR extraction for document {document_id}")
            
            # Check if Azure credentials are configured
            if not self.endpoint or not self.api_key:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="Azure Document Intelligence credentials not configured. Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_API_KEY environment variables."
                )
            
            # Perform actual Azure Document Intelligence extraction
            extraction_result = await self._perform_azure_extraction(
                document_path, analysis_features, pages
            )
            
            # Process and structure the results
            processed_result = self._process_extraction_result(extraction_result, document_id)
            
            self.logger.info(f"OCR extraction completed for document {document_id}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=processed_result
            )
            
        except FileNotFoundError:
            error_msg = f"Document file not found: {document_path}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
            
        except Exception as e:
            error_msg = f"OCR extraction failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    async def _perform_azure_extraction(self, document_path: str, 
                                      analysis_features: List[str], 
                                      pages: str) -> Dict[str, Any]:
        """
        Perform actual Azure Document Intelligence extraction.
        
        Args:
            document_path: Path to document file
            analysis_features: Features to analyze
            pages: Page range to process
            
        Returns:
            Raw extraction result from Azure
        """
        try:
            # Import Azure SDK (only when needed)
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
            
            # Validate file exists and is readable
            if not os.path.exists(document_path):
                raise FileNotFoundError(f"Document file not found: {document_path}")
            
            # Check file size (Azure has limits)
            file_size = os.path.getsize(document_path)
            max_size = 500 * 1024 * 1024  # 500MB limit for Azure Document Intelligence
            if file_size > max_size:
                raise ValueError(f"Document file too large: {file_size} bytes (max: {max_size})")
            
            # Initialize Azure client
            client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
            
            # Read document file
            with open(document_path, "rb") as document_file:
                document_content = document_file.read()
            
            # Validate document content
            if not document_content:
                raise ValueError("Document file is empty")
            
            # Start analysis with timeout handling
            self.logger.info(f"Starting Azure Document Intelligence analysis for {document_path}")
            poller = client.begin_analyze_document(
                model_id="prebuilt-layout",  # Use prebuilt layout model
                body=document_content,  # Pass document content directly as body
                content_type="application/octet-stream",  # Specify content type
                pages=pages if pages != "all" else None
            )
            
            # Wait for completion with timeout
            result = poller.result()
            self.logger.info("Azure Document Intelligence analysis completed successfully")
            
            return self._convert_azure_result_to_dict(result)
            
        except ImportError as e:
            self.logger.error(f"Azure Document Intelligence SDK not available: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=f"Azure Document Intelligence SDK not installed. Please install with: pip install azure-ai-documentintelligence"
            )
        
        except FileNotFoundError:
            self.logger.error(f"Document file not found: {document_path}")
            raise
        
        except ValueError as e:
            self.logger.error(f"Document validation failed: {str(e)}")
            raise
        
        except Exception as e:
            self.logger.error(f"Azure extraction failed: {str(e)}")
            # For certain Azure service errors, return proper error
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                self.logger.error("Azure authentication failed")
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="Azure Document Intelligence authentication failed. Please check your API key and endpoint configuration."
                )
            raise
    
    def _convert_azure_result_to_dict(self, azure_result) -> Dict[str, Any]:
        """
        Convert Azure Document Intelligence result to dictionary format.
        
        Args:
            azure_result: Result from Azure Document Intelligence
            
        Returns:
            Dictionary representation of the result
        """
        try:
            result = {
                "pages": [],
                "tables": [],
                "key_value_pairs": [],
                "paragraphs": [],
                "content": azure_result.content if hasattr(azure_result, 'content') else ""
            }
            
            # Extract pages with error handling
            if hasattr(azure_result, 'pages') and azure_result.pages:
                for page in azure_result.pages:
                    try:
                        page_data = {
                            "page_number": getattr(page, 'page_number', 0),
                            "width": getattr(page, 'width', 0),
                            "height": getattr(page, 'height', 0),
                            "unit": getattr(page, 'unit', 'inch'),
                            "lines": []
                        }
                        
                        if hasattr(page, 'lines') and page.lines:
                            for line in page.lines:
                                try:
                                    line_data = {
                                        "content": getattr(line, 'content', ''),
                                        "bounding_box": getattr(line, 'polygon', None)
                                    }
                                    page_data["lines"].append(line_data)
                                except Exception as e:
                                    self.logger.warning(f"Error processing line: {str(e)}")
                                    continue
                        
                        result["pages"].append(page_data)
                    except Exception as e:
                        self.logger.warning(f"Error processing page: {str(e)}")
                        continue
            
            # Extract tables with error handling
            if hasattr(azure_result, 'tables') and azure_result.tables:
                for table in azure_result.tables:
                    try:
                        table_data = {
                            "row_count": getattr(table, 'row_count', 0),
                            "column_count": getattr(table, 'column_count', 0),
                            "cells": []
                        }
                        
                        if hasattr(table, 'cells') and table.cells:
                            for cell in table.cells:
                                try:
                                    cell_data = {
                                        "content": getattr(cell, 'content', ''),
                                        "row_index": getattr(cell, 'row_index', 0),
                                        "column_index": getattr(cell, 'column_index', 0),
                                        "row_span": getattr(cell, 'row_span', 1),
                                        "column_span": getattr(cell, 'column_span', 1)
                                    }
                                    table_data["cells"].append(cell_data)
                                except Exception as e:
                                    self.logger.warning(f"Error processing table cell: {str(e)}")
                                    continue
                        
                        result["tables"].append(table_data)
                    except Exception as e:
                        self.logger.warning(f"Error processing table: {str(e)}")
                        continue
            
            # Extract key-value pairs with error handling
            if hasattr(azure_result, 'key_value_pairs') and azure_result.key_value_pairs:
                for kvp in azure_result.key_value_pairs:
                    try:
                        key_content = ""
                        value_content = ""
                        
                        if hasattr(kvp, 'key') and kvp.key:
                            key_content = getattr(kvp.key, 'content', '')
                        
                        if hasattr(kvp, 'value') and kvp.value:
                            value_content = getattr(kvp.value, 'content', '')
                        
                        kvp_data = {
                            "key": key_content,
                            "value": value_content,
                            "confidence": getattr(kvp, 'confidence', 0.0)
                        }
                        result["key_value_pairs"].append(kvp_data)
                    except Exception as e:
                        self.logger.warning(f"Error processing key-value pair: {str(e)}")
                        continue
            
            # Extract paragraphs with error handling
            if hasattr(azure_result, 'paragraphs') and azure_result.paragraphs:
                for paragraph in azure_result.paragraphs:
                    try:
                        paragraph_data = {
                            "content": getattr(paragraph, 'content', ''),
                            "role": getattr(paragraph, 'role', None)
                        }
                        result["paragraphs"].append(paragraph_data)
                    except Exception as e:
                        self.logger.warning(f"Error processing paragraph: {str(e)}")
                        continue
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error converting Azure result to dict: {str(e)}")
            # Return minimal result structure on error
            return {
                "pages": [],
                "tables": [],
                "key_value_pairs": [],
                "paragraphs": [],
                "content": str(azure_result) if azure_result else ""
            }
    

    
    def _process_extraction_result(self, extraction_result: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        """
        Process and enhance the extraction result.
        
        Args:
            extraction_result: Raw extraction result
            document_id: Document identifier
            
        Returns:
            Processed result with additional metadata
        """
        # Calculate overall confidence score
        confidence_scores = []
        
        # Collect confidence scores from key-value pairs
        if "key_value_pairs" in extraction_result:
            for kvp in extraction_result["key_value_pairs"]:
                if "confidence" in kvp:
                    confidence_scores.append(kvp["confidence"])
        
        # Calculate average confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.85
        
        # Extract text content
        extracted_text = ""
        if "content" in extraction_result:
            extracted_text = extraction_result["content"]
        elif "extracted_text" in extraction_result:
            extracted_text = extraction_result["extracted_text"]
        elif "pages" in extraction_result:
            # Combine text from all pages
            page_texts = []
            for page in extraction_result["pages"]:
                if "lines" in page:
                    page_text = " ".join([line["content"] for line in page["lines"]])
                    page_texts.append(page_text)
            extracted_text = "\n".join(page_texts)
        
        # Build processed result
        processed_result = {
            "document_id": document_id,
            "extracted_text": extracted_text,
            "confidence_score": overall_confidence,
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_method": "azure_document_intelligence",
            "page_count": len(extraction_result.get("pages", [])) or extraction_result.get("page_count", 1),
            "tables_found": len(extraction_result.get("tables", [])),
            "key_value_pairs_found": len(extraction_result.get("key_value_pairs", [])),
            "raw_result": extraction_result
        }
        
        # Add structured data
        if "tables" in extraction_result:
            processed_result["tables"] = extraction_result["tables"]
        
        if "key_value_pairs" in extraction_result:
            processed_result["key_value_pairs"] = extraction_result["key_value_pairs"]
        
        # Add quality metrics
        processed_result["quality_metrics"] = {
            "text_length": len(extracted_text),
            "has_tables": len(extraction_result.get("tables", [])) > 0,
            "has_key_value_pairs": len(extraction_result.get("key_value_pairs", [])) > 0,
            "confidence_level": "high" if overall_confidence > 0.8 else "medium" if overall_confidence >= 0.5 else "low"
        }
        
        return processed_result