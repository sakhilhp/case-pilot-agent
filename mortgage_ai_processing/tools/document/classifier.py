"""
Document classification tool with Microsoft Form Recognizer (Azure Document Intelligence).

This tool provides intelligent document classification capabilities for mortgage-related documents,
using Azure Document Intelligence to identify document types and extract relevant details.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
import re

from ..base import BaseTool, ToolResult
from ...models.enums import DocumentType

# Azure Document Intelligence imports
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_AVAILABLE = True
except ImportError as e1:
    try:
        # Fallback to older SDK version
        from azure.ai.formrecognizer import DocumentAnalysisClient as DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        AZURE_AVAILABLE = True
    except ImportError as e2:
        # Log the import errors for debugging
        import logging
        logger = logging.getLogger("tool.document_classifier")
        logger.warning(f"Azure Document Intelligence SDK not available: {e1}")
        logger.warning(f"Azure Form Recognizer SDK also not available: {e2}")
        logger.warning("Document classifier will use fallback pattern-based classification only")
        AZURE_AVAILABLE = False
        
        # Create dummy classes to prevent import errors
        class DocumentIntelligenceClient:
            pass
        class AzureKeyCredential:
            pass


class DocumentClassifier(BaseTool):
    """
    Tool for classifying documents using Microsoft Form Recognizer (Azure Document Intelligence).
    
    This tool uses Azure Document Intelligence to analyze document content and classify documents into
    appropriate types for mortgage processing workflows. It provides:
    - Intelligent document type detection using Azure AI
    - Document layout analysis and structure recognition
    - Key-value pair extraction and field identification
    - Confidence scoring based on Azure AI analysis
    - Support for various document formats (PDF, images, etc.)
    """
    
    def __init__(self):
        from ..base import ToolCategory
        super().__init__(
            name="document_classifier",
            description="Classify documents using Microsoft Form Recognizer with intelligent AI analysis",
            category=ToolCategory.DOCUMENT_PROCESSING,
            agent_domain="document_processing"
        )
        self.logger = logging.getLogger("tool.document_classifier")
        
        # DEBUG: Log initialization
        self.logger.info("🚀 DocumentClassifier initializing with Azure Document Intelligence support")
        
        # Initialize Azure Document Intelligence client
        self.client = None
        self._initialize_azure_client()
        
        # Document type mapping from Azure models to our enum
        self.azure_model_mapping = self._initialize_azure_model_mapping()
        

        
        # Confidence thresholds
        self.high_confidence_threshold = 0.8
        self.medium_confidence_threshold = 0.5
        
        self.logger.info("✅ DocumentClassifier initialization completed")
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema for the tool (required by BaseTool abstract class)."""
        return self.get_parameters_schema()
    
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
                    "description": "Path to the document file for Azure Document Intelligence analysis"
                },
                "document_url": {
                    "type": "string",
                    "description": "URL to the document for Azure Document Intelligence analysis (alternative to document_path)"
                },
                "extracted_text": {
                    "type": "string",
                    "description": "Pre-extracted text content (used as fallback if Azure analysis fails)",
                    "default": ""
                },
                "use_prebuilt_models": {
                    "type": "boolean",
                    "description": "Whether to use Azure prebuilt models for classification",
                    "default": True
                },
                "analysis_features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Azure Document Intelligence features to use (layout, keyValuePairs, entities, etc.)",
                    "default": ["layout", "keyValuePairs", "entities"]
                },
                "mortgage_application": {
                    "type": "object",
                    "description": "Complete mortgage application JSON with documents array - will process all documents automatically",
                    "properties": {
                        "application_id": {"type": "string"},
                        "documents": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "document_id": {"type": "string"},
                                    "file_path": {"type": "string"},
                                    "document_type": {"type": "string"},
                                    "original_filename": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "process_all_documents": {
                    "type": "boolean",
                    "description": "When true, processes all documents in mortgage_application.documents array",
                    "default": False
                }
            },
            "anyOf": [
                {"required": ["document_id", "document_path"]},
                {"required": ["document_id", "document_url"]},
                {"required": ["document_id", "extracted_text"]},
                {"required": ["mortgage_application"], "properties": {"process_all_documents": {"const": True}}}
            ]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute document classification using Azure Document Intelligence.
        
        Automatically detects input type:
        1. Mortgage application JSON (has application_id + documents array)
        2. Single document classification (document_id + document_path/url/text)
        
        Args:
            document_id: Unique identifier for single document
            document_path: Path to single document file
            document_url: URL to single document
            extracted_text: Pre-extracted text for single document
            mortgage_application: Complete mortgage application JSON with documents array
            process_all_documents: Process all documents in mortgage_application.documents
            use_prebuilt_models: Whether to use Azure prebuilt models
            analysis_features: Features to extract (layout, keyValuePairs, entities)
            
        Returns:
            ToolResult containing classification results for single or multiple documents
        """
        
        # DEBUG: Log the input parameters
        self.logger.info(f"🔍 DocumentClassifier.execute() called with parameters: {list(kwargs.keys())}")
        
        # SMART DETECTION: Check if the input looks like a mortgage application
        if self._is_mortgage_application_input(kwargs):
            self.logger.info("✅ Detected mortgage application input - switching to batch processing mode")
            return await self._process_mortgage_application_from_kwargs(kwargs)
        else:
            self.logger.info("ℹ️ No mortgage application detected - using single document mode")
        
        # Check explicit batch processing mode
        mortgage_application = kwargs.get("mortgage_application")
        process_all_documents = kwargs.get("process_all_documents", False)
        
        if mortgage_application and process_all_documents:
            return await self._process_mortgage_application_documents(mortgage_application, kwargs)
        
        # Single document processing mode
        document_id = kwargs.get("document_id")
        document_path = kwargs.get("document_path")
        document_url = kwargs.get("document_url")
        extracted_text = kwargs.get("extracted_text", "")
        use_prebuilt_models = kwargs.get("use_prebuilt_models", True)
        analysis_features = kwargs.get("analysis_features", ["layout", "keyValuePairs", "entities"])
        
        try:
            self.logger.info(f"Starting Azure Document Intelligence classification for document {document_id}")
            
            # Validate input for single document
            if not document_path and not document_url and not extracted_text.strip():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="Must provide document_path, document_url, or extracted_text"
                )
            
            # Process single document
            result_data = await self._process_single_document(
                document_id, document_path, document_url, extracted_text, 
                use_prebuilt_models, analysis_features
            )
            
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
    
    def _is_mortgage_application_input(self, kwargs: Dict[str, Any]) -> bool:
        """
        Smart detection: Check if the input looks like a mortgage application.
        
        Detects if the kwargs contain mortgage application structure:
        - Has application_id
        - Has documents array
        - Has borrower_info or loan_details
        """
        # Check if it has the typical mortgage application structure
        has_application_id = "application_id" in kwargs
        has_documents = "documents" in kwargs and isinstance(kwargs.get("documents"), list)
        has_borrower_info = "borrower_info" in kwargs
        has_loan_details = "loan_details" in kwargs
        has_property_info = "property_info" in kwargs
        
        # If it has application_id and documents, it's likely a mortgage application
        if has_application_id and has_documents:
            self.logger.info("Detected mortgage application: has application_id and documents array")
            return True
        
        # If it has multiple mortgage-specific fields, it's likely a mortgage application
        mortgage_fields = sum([has_borrower_info, has_loan_details, has_property_info])
        if mortgage_fields >= 2 and has_documents:
            self.logger.info("Detected mortgage application: has multiple mortgage fields and documents")
            return True
        
        return False
    
    async def _process_mortgage_application_from_kwargs(self, kwargs: Dict[str, Any]) -> ToolResult:
        """Process mortgage application when it's passed directly in kwargs (smart detection)."""
        # Extract mortgage application data from kwargs
        mortgage_application = {
            "application_id": kwargs.get("application_id", "detected_application"),
            "documents": kwargs.get("documents", []),
            "borrower_info": kwargs.get("borrower_info", {}),
            "loan_details": kwargs.get("loan_details", {}),
            "property_info": kwargs.get("property_info", {}),
            "processing_status": kwargs.get("processing_status", "pending")
        }
        
        self.logger.info(f"Smart detection: Processing mortgage application {mortgage_application['application_id']} with {len(mortgage_application['documents'])} documents")
        
        # Use the existing batch processing method
        return await self._process_mortgage_application_documents(mortgage_application, kwargs)
    
    async def _process_mortgage_application_documents(self, mortgage_application: Dict[str, Any], 
                                                   kwargs: Dict[str, Any]) -> ToolResult:
        """Process all documents in a mortgage application."""
        try:
            application_id = mortgage_application.get("application_id", "unknown")
            documents = mortgage_application.get("documents", [])
            
            self.logger.info(f"Processing {len(documents)} documents from mortgage application {application_id}")
            
            if not documents:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={},
                    error_message="No documents found in mortgage application"
                )
            
            use_prebuilt_models = kwargs.get("use_prebuilt_models", True)
            analysis_features = kwargs.get("analysis_features", ["layout", "keyValuePairs", "entities"])
            
            # Process each document
            all_results = []
            successful_classifications = 0
            failed_classifications = 0
            
            for i, document in enumerate(documents):
                doc_id = document.get("document_id", f"doc_{i}")
                file_path = document.get("file_path", "")
                original_filename = document.get("original_filename", "")
                
                self.logger.info(f"Processing document {i+1}/{len(documents)}: {doc_id}")
                
                try:
                    # Use file_path if available, otherwise try to construct path
                    document_path = file_path
                    if not document_path and original_filename:
                        # Try common document directories
                        for base_dir in ["test_documents", "documents", "uploads"]:
                            potential_path = os.path.join(base_dir, original_filename)
                            if os.path.exists(potential_path):
                                document_path = potential_path
                                break
                    
                    if not document_path:
                        self.logger.warning(f"No valid file path found for document {doc_id}")
                        all_results.append({
                            "document_id": doc_id,
                            "status": "failed",
                            "error": "No valid file path found",
                            "original_document_info": document
                        })
                        failed_classifications += 1
                        continue
                    
                    # Process the document
                    result_data = await self._process_single_document(
                        doc_id, document_path, None, "", 
                        use_prebuilt_models, analysis_features
                    )
                    
                    # Add original document metadata
                    result_data["original_document_info"] = document
                    result_data["status"] = "success"
                    
                    all_results.append(result_data)
                    successful_classifications += 1
                    
                    self.logger.info(f"Successfully classified document {doc_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to classify document {doc_id}: {str(e)}")
                    all_results.append({
                        "document_id": doc_id,
                        "status": "failed",
                        "error": str(e),
                        "original_document_info": document
                    })
                    failed_classifications += 1
            
            # Build comprehensive batch result
            batch_result = {
                "application_id": application_id,
                "batch_processing": True,
                "total_documents": len(documents),
                "successful_classifications": successful_classifications,
                "failed_classifications": failed_classifications,
                "processing_timestamp": datetime.now().isoformat(),
                "document_results": all_results,
                "summary": {
                    "success_rate": successful_classifications / len(documents) if documents else 0,
                    "primary_document_types": self._get_primary_document_types(all_results),
                    "classification_methods_used": self._get_classification_methods_used(all_results)
                }
            }
            
            self.logger.info(f"Batch processing completed: {successful_classifications}/{len(documents)} successful")
            
            return ToolResult(
                tool_name=self.name,
                success=successful_classifications > 0,  # Success if at least one document was classified
                data=batch_result
            )
            
        except Exception as e:
            error_msg = f"Batch document processing failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    async def _process_single_document(self, document_id: str, document_path: Optional[str], 
                                     document_url: Optional[str], extracted_text: str,
                                     use_prebuilt_models: bool, analysis_features: List[str]) -> Dict[str, Any]:
        """Process a single document and return classification results."""
        # Try Azure Document Intelligence first
        classification_results = None
        azure_analysis = None
        classification_method = "fallback_analysis"
        
        if self.client and (document_path or document_url):
            try:
                azure_analysis = await self._analyze_with_azure(
                    document_path, document_url, use_prebuilt_models, analysis_features
                )
                classification_results = await self._classify_from_azure_analysis(azure_analysis)
                classification_method = "azure_document_intelligence"
                self.logger.info(f"Successfully classified document using Azure Document Intelligence")
            except Exception as e:
                self.logger.warning(f"Azure analysis failed, falling back to pattern matching: {str(e)}")
        
        # Require Azure Document Intelligence - no fallback to mock data
        if not classification_results:
            if not self.client:
                raise Exception("Azure Document Intelligence not configured. Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_API_KEY environment variables.")
            else:
                raise Exception("Azure Document Intelligence analysis failed and no alternative processing method available.")
        
        # Build result data
        result_data = {
            "document_id": document_id,
            "classification_results": classification_results,
            "classification_timestamp": datetime.now().isoformat(),
            "primary_classification": classification_results[0] if classification_results else None,
            "classification_method": classification_method,
            "azure_analysis_available": azure_analysis is not None,
            "extracted_details": self._extract_document_details(azure_analysis) if azure_analysis else {},
            "confidence_summary": self._generate_confidence_summary(classification_results),
            "document_path": document_path,
            "document_url": document_url
        }
        
        return result_data
    
    def _get_primary_document_types(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary of primary document types from batch results."""
        type_counts = {}
        for result in results:
            if result.get("status") == "success" and result.get("primary_classification"):
                doc_type = result["primary_classification"].get("document_type", "unknown")
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        return type_counts
    
    def _get_classification_methods_used(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary of classification methods used in batch processing."""
        method_counts = {}
        for result in results:
            if result.get("status") == "success":
                method = result.get("classification_method", "unknown")
                method_counts[method] = method_counts.get(method, 0) + 1
        return method_counts
    
    def _initialize_azure_client(self):
        """Initialize Azure Document Intelligence client."""
        try:
            endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
            api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
            
            self.logger.info(f"🔍 Azure Configuration Check:")
            self.logger.info(f"   Azure SDK available: {AZURE_AVAILABLE}")
            self.logger.info(f"   Endpoint configured: {bool(endpoint)}")
            self.logger.info(f"   API key configured: {bool(api_key)}")
            
            if endpoint:
                self.logger.info(f"   Endpoint: {endpoint}")
            if api_key:
                self.logger.info(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
            
            if endpoint and api_key and AZURE_AVAILABLE:
                self.client = DocumentIntelligenceClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(api_key)
                )
                self.logger.info(f"✅ Azure Document Intelligence client initialized successfully!")
                self.logger.info(f"   Will use REAL Azure API calls for document analysis")
            else:
                missing_items = []
                if not endpoint:
                    missing_items.append("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
                if not api_key:
                    missing_items.append("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
                if not AZURE_AVAILABLE:
                    missing_items.append("Azure SDK not installed")
                
                self.logger.error(f"❌ Azure Document Intelligence not configured - missing: {', '.join(missing_items)}")
                self.logger.error(f"   Document classification will fail without proper Azure configuration")
                self.client = None
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Azure client: {str(e)}")
            import traceback
            self.logger.error(f"Full error: {traceback.format_exc()}")
            self.client = None
    
    def _initialize_azure_model_mapping(self) -> Dict[str, DocumentType]:
        """Map Azure prebuilt model types to our document types."""
        return {
            # Azure prebuilt models
            "prebuilt-idDocument": DocumentType.PASSPORT,  # Can be passport, driver's license, etc.
            "prebuilt-invoice": DocumentType.INVOICE,
            "prebuilt-receipt": DocumentType.RECEIPT,
            "prebuilt-contract": DocumentType.CONTRACT,
            "prebuilt-businessCard": DocumentType.IDENTITY,  # Use IDENTITY as fallback
            "prebuilt-layout": DocumentType.IDENTITY,  # Use IDENTITY as fallback
            
            # Document type detection based on content
            "identity_document": DocumentType.PASSPORT,
            "financial_document": DocumentType.BANK_STATEMENT,
            "employment_document": DocumentType.EMPLOYMENT_LETTER,
            "tax_document": DocumentType.TAX_DOCUMENT,
            "utility_document": DocumentType.UTILITY_BILL,
            "pay_document": DocumentType.PAY_STUB
        }
    
    async def _analyze_with_azure(self, document_path: Optional[str], document_url: Optional[str],
                                use_prebuilt_models: bool, analysis_features: List[str]) -> Dict[str, Any]:
        """Analyze document using Azure Document Intelligence."""
        if not self.client:
            raise Exception("Azure Document Intelligence client not available")
        
        try:
            self.logger.info(f"Starting Azure Document Intelligence analysis for document: {document_path or document_url}")
            
            # Determine which model to use
            model_id = "prebuilt-layout"  # Default to layout analysis
            
            if use_prebuilt_models:
                # Try to determine the best prebuilt model based on document characteristics
                if document_path:
                    filename = os.path.basename(document_path).lower()
                    if any(term in filename for term in ["invoice", "bill"]):
                        model_id = "prebuilt-invoice"
                        self.logger.info(f"Using prebuilt-invoice model based on filename: {filename}")
                    elif any(term in filename for term in ["receipt", "transaction"]):
                        model_id = "prebuilt-receipt"
                        self.logger.info(f"Using prebuilt-receipt model based on filename: {filename}")
                    elif any(term in filename for term in ["id", "passport", "license"]):
                        model_id = "prebuilt-idDocument"
                        self.logger.info(f"Using prebuilt-idDocument model based on filename: {filename}")
                    elif any(term in filename for term in ["contract", "agreement"]):
                        model_id = "prebuilt-contract"
                        self.logger.info(f"Using prebuilt-contract model based on filename: {filename}")
            
            self.logger.info(f"Using Azure model: {model_id}")
            
            # Make the actual Azure API call
            if document_url:
                # For URL-based analysis
                self.logger.info(f"Analyzing document from URL: {document_url}")
                poller = self.client.begin_analyze_document(
                    model_id=model_id,
                    analyze_request={"url_source": document_url},
                    features=analysis_features if analysis_features else None
                )
            else:
                # For file-based analysis
                self.logger.info(f"Analyzing document from file: {document_path}")
                if not os.path.exists(document_path):
                    raise FileNotFoundError(f"Document file not found: {document_path}")
                
                with open(document_path, "rb") as document_file:
                    document_content = document_file.read()
                
                # Use the correct API format for Azure Document Intelligence
                try:
                    # Try the correct format for azure-ai-documentintelligence
                    poller = self.client.begin_analyze_document(
                        model_id=model_id,
                        body=document_content,
                        content_type="application/octet-stream"
                    )
                except Exception as e:
                    self.logger.warning(f"Document Intelligence format failed, trying Form Recognizer format: {str(e)}")
                    # Fallback to azure-ai-formrecognizer format
                    try:
                        poller = self.client.begin_analyze_document(
                            model_id=model_id,
                            document=document_content
                        )
                    except Exception as e2:
                        self.logger.error(f"Both API formats failed: {str(e2)}")
                        raise
            
            # Wait for the analysis to complete
            self.logger.info("Waiting for Azure Document Intelligence analysis to complete...")
            result = poller.result()
            self.logger.info("Azure Document Intelligence analysis completed successfully")
            
            # Convert Azure result to our format
            azure_response = self._convert_azure_result_to_dict(result, model_id)
            
            return azure_response
            
        except Exception as e:
            self.logger.error(f"Azure Document Intelligence analysis failed: {str(e)}")
            raise
    
    def _convert_azure_result_to_dict(self, azure_result, model_id: str) -> Dict[str, Any]:
        """Convert Azure Document Intelligence result to our dictionary format."""
        try:
            response = {
                "model_id": model_id,
                "api_version": getattr(azure_result, 'api_version', '2024-02-29-preview'),
                "content": getattr(azure_result, 'content', ''),
                "pages": [],
                "key_value_pairs": [],
                "entities": [],
                "document_types": []
            }
            
            # Extract pages information
            if hasattr(azure_result, 'pages') and azure_result.pages:
                for page in azure_result.pages:
                    page_info = {
                        "page_number": getattr(page, 'page_number', 1),
                        "width": getattr(page, 'width', 0),
                        "height": getattr(page, 'height', 0),
                        "unit": getattr(page, 'unit', 'pixel')
                    }
                    response["pages"].append(page_info)
            
            # Extract key-value pairs
            if hasattr(azure_result, 'key_value_pairs') and azure_result.key_value_pairs:
                for kvp in azure_result.key_value_pairs:
                    kvp_info = {
                        "key": {"content": getattr(kvp.key, 'content', '') if kvp.key else ''},
                        "value": {"content": getattr(kvp.value, 'content', '') if kvp.value else ''},
                        "confidence": getattr(kvp, 'confidence', 0.0)
                    }
                    response["key_value_pairs"].append(kvp_info)
            
            # Extract entities
            if hasattr(azure_result, 'entities') and azure_result.entities:
                for entity in azure_result.entities:
                    entity_info = {
                        "category": getattr(entity, 'category', ''),
                        "content": getattr(entity, 'content', ''),
                        "confidence": getattr(entity, 'confidence', 0.0)
                    }
                    response["entities"].append(entity_info)
            
            # Extract document types (if available from prebuilt models)
            if hasattr(azure_result, 'documents') and azure_result.documents:
                for doc in azure_result.documents:
                    doc_type_info = {
                        "type": getattr(doc, 'doc_type', model_id.replace('prebuilt-', '')),
                        "confidence": getattr(doc, 'confidence', 0.8)
                    }
                    response["document_types"].append(doc_type_info)
            
            # If no document types found, infer from model
            if not response["document_types"]:
                inferred_type = model_id.replace('prebuilt-', '')
                response["document_types"].append({
                    "type": inferred_type,
                    "confidence": 0.7  # Medium confidence for inference
                })
            
            self.logger.info(f"Converted Azure result: {len(response['key_value_pairs'])} key-value pairs, "
                           f"{len(response['entities'])} entities, {len(response['document_types'])} document types")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error converting Azure result: {str(e)}")
            # Return minimal response on conversion error
            return {
                "model_id": model_id,
                "content": getattr(azure_result, 'content', ''),
                "pages": [],
                "key_value_pairs": [],
                "entities": [],
                "document_types": [{"type": "unknown", "confidence": 0.3}]
            }
    
    async def _classify_from_azure_analysis(self, azure_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract classification results from Azure Document Intelligence analysis."""
        classification_results = []
        
        # Get document types from Azure analysis
        document_types = azure_analysis.get("document_types", [])
        model_id = azure_analysis.get("model_id", "")
        
        # Process Azure-detected document types
        for doc_type_info in document_types:
            doc_type_name = doc_type_info.get("type", "")
            confidence = doc_type_info.get("confidence", 0.0)
            
            # Map Azure type to our DocumentType enum
            mapped_type = self._map_azure_type_to_document_type(doc_type_name, model_id)
            
            classification_results.append({
                "document_type": mapped_type.value,
                "confidence_score": confidence,
                "confidence_level": self._determine_confidence_level(confidence),
                "classification_factors": [
                    f"Azure Document Intelligence detection: {doc_type_name}",
                    f"Model used: {model_id}",
                    f"Azure confidence: {confidence:.2f}"
                ],
                "azure_model_id": model_id,
                "azure_detected_type": doc_type_name
            })
        
        # If no specific document types detected, infer from model and content
        if not classification_results:
            inferred_type = self._infer_type_from_azure_model(model_id, azure_analysis)
            classification_results.append({
                "document_type": inferred_type.value,
                "confidence_score": 0.7,  # Medium confidence for inference
                "confidence_level": "medium",
                "classification_factors": [
                    f"Inferred from Azure model: {model_id}",
                    "Layout and structure analysis"
                ],
                "azure_model_id": model_id,
                "azure_detected_type": "inferred"
            })
        
        # Sort by confidence
        classification_results.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return classification_results[:3]  # Return top 3
    
    def _map_azure_type_to_document_type(self, azure_type: str, model_id: str) -> DocumentType:
        """Map Azure detected type to our DocumentType enum."""
        # Direct mapping from Azure types
        type_mapping = {
            "invoice": DocumentType.INVOICE,
            "receipt": DocumentType.RECEIPT,
            "contract": DocumentType.CONTRACT,
            "statement": DocumentType.BANK_STATEMENT,
            "tax_form": DocumentType.TAX_DOCUMENT,
            "pay_stub": DocumentType.PAY_STUB,
            "employment_letter": DocumentType.EMPLOYMENT_LETTER,
            "utility_bill": DocumentType.UTILITY_BILL,
            "passport": DocumentType.PASSPORT,
            "driver_license": DocumentType.DRIVERS_LICENSE,
            "national_id": DocumentType.NATIONAL_ID
        }
        
        # Check direct mapping first
        if azure_type.lower() in type_mapping:
            return type_mapping[azure_type.lower()]
        
        # Check model-based mapping
        if model_id in self.azure_model_mapping:
            return self.azure_model_mapping[model_id]
        
        # Default fallback
        return DocumentType.IDENTITY
    
    def _infer_type_from_azure_model(self, model_id: str, azure_analysis: Dict[str, Any]) -> DocumentType:
        """Infer document type from Azure model and analysis results."""
        # Check key-value pairs for type hints
        key_value_pairs = azure_analysis.get("key_value_pairs", [])
        entities = azure_analysis.get("entities", [])
        
        # Look for specific patterns in extracted data
        kvp_keys = [kvp.get("key", {}).get("content", "").lower() for kvp in key_value_pairs]
        entity_categories = [entity.get("category", "").lower() for entity in entities]
        
        # Financial document indicators
        if any(key in kvp_keys for key in ["account", "balance", "statement", "bank"]):
            return DocumentType.BANK_STATEMENT
        
        # Employment document indicators
        if any(key in kvp_keys for key in ["salary", "employer", "position", "employment"]):
            return DocumentType.EMPLOYMENT_LETTER
        
        # Tax document indicators
        if any(key in kvp_keys for key in ["tax", "irs", "w-2", "1099", "income"]):
            return DocumentType.TAX_DOCUMENT
        
        # Utility bill indicators
        if any(key in kvp_keys for key in ["service", "utility", "electric", "gas", "water"]):
            return DocumentType.UTILITY_BILL
        
        # Identity document indicators
        if any(key in kvp_keys for key in ["passport", "license", "id", "nationality"]):
            if "passport" in kvp_keys:
                return DocumentType.PASSPORT
            elif "license" in kvp_keys:
                return DocumentType.DRIVERS_LICENSE
            else:
                return DocumentType.NATIONAL_ID
        
        # Default based on model
        return self.azure_model_mapping.get(model_id, DocumentType.IDENTITY)
    
    def _extract_document_details(self, azure_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed information from Azure analysis."""
        if not azure_analysis:
            return {}
        
        details = {
            "extracted_text": azure_analysis.get("content", ""),
            "page_count": len(azure_analysis.get("pages", [])),
            "key_value_pairs": [],
            "entities": [],
            "confidence_scores": {}
        }
        
        # Process key-value pairs
        for kvp in azure_analysis.get("key_value_pairs", []):
            key_content = kvp.get("key", {}).get("content", "")
            value_content = kvp.get("value", {}).get("content", "")
            confidence = kvp.get("confidence", 0.0)
            
            details["key_value_pairs"].append({
                "key": key_content,
                "value": value_content,
                "confidence": confidence
            })
        
        # Process entities
        for entity in azure_analysis.get("entities", []):
            details["entities"].append({
                "category": entity.get("category", ""),
                "content": entity.get("content", ""),
                "confidence": entity.get("confidence", 0.0)
            })
        
        # Calculate average confidence scores
        if details["key_value_pairs"]:
            avg_kvp_confidence = sum(kvp["confidence"] for kvp in details["key_value_pairs"]) / len(details["key_value_pairs"])
            details["confidence_scores"]["key_value_pairs"] = avg_kvp_confidence
        
        if details["entities"]:
            avg_entity_confidence = sum(entity["confidence"] for entity in details["entities"]) / len(details["entities"])
            details["confidence_scores"]["entities"] = avg_entity_confidence
        
        return details
    
    def _generate_confidence_summary(self, classification_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of classification confidence."""
        if not classification_results:
            return {"overall_confidence": "low", "primary_confidence": 0.0, "alternatives_count": 0}
        
        primary_result = classification_results[0]
        primary_confidence = primary_result.get("confidence_score", 0.0)
        
        return {
            "overall_confidence": primary_result.get("confidence_level", "low"),
            "primary_confidence": primary_confidence,
            "primary_type": primary_result.get("document_type", "unknown"),
            "alternatives_count": len(classification_results) - 1,
            "classification_method": "azure_document_intelligence" if "azure_model_id" in primary_result else "pattern_based"
        }
    

    
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
            # Weighted combination of scores (adjust weights if structure_scores is empty)
            if structure_scores:
                filename_weight = 0.2
                content_weight = 0.6
                structure_weight = 0.2
                
                combined_score = (
                    filename_scores.get(doc_type, 0.0) * filename_weight +
                    content_scores.get(doc_type, 0.0) * content_weight +
                    structure_scores.get(doc_type, 0.0) * structure_weight
                )
            else:
                # No structure analysis available
                filename_weight = 0.3
                content_weight = 0.7
                
                combined_score = (
                    filename_scores.get(doc_type, 0.0) * filename_weight +
                    content_scores.get(doc_type, 0.0) * content_weight
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