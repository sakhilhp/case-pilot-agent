"""
Document Processing Agent implementation.

This agent specializes in document processing tasks including OCR extraction,
classification, validation, and structured data extraction from mortgage-related documents.
"""

from typing import Dict, List, Any
import logging
from datetime import datetime

from .base import BaseAgent
from ..models.core import MortgageApplication, Document, DocumentType
from ..models.assessment import AssessmentResult, RiskLevel
from ..tools.base import ToolResult


class DocumentProcessingAgent(BaseAgent):
    """
    Agent specialized in document processing for mortgage applications.
    
    This agent coordinates document processing workflows including:
    - OCR text extraction from documents
    - Document type classification
    - Identity document validation
    - Generic document data extraction
    - Address proof validation
    
    Tools used:
    - document_ocr_extractor: Azure Document Intelligence integration
    - document_classifier: AI-powered document classification
    - identity_document_validator: Government ID processing
    - document_extractor: Template-based extraction
    - address_proof_validator: KYC compliance validation
    """
    
    def __init__(self, agent_id: str = "document_processing_agent"):
        super().__init__(agent_id, "Document Processing Agent")
        self.logger = logging.getLogger("agent.document_processing")
        
    def get_tool_names(self) -> List[str]:
        """Return list of tool names this agent uses."""
        return [
            "document_ocr_extractor",
            "document_classifier",
            "identity_document_validator", 
            "document_extractor",
            "address_proof_validator"
        ]
        
    async def process(self, application: MortgageApplication, context: Dict[str, Any]) -> AssessmentResult:
        """
        Process mortgage application documents using specialized tools.
        
        Args:
            application: The mortgage application to process
            context: Additional context data from other agents
            
        Returns:
            AssessmentResult containing document processing analysis
        """
        start_time = datetime.now()
        tool_results = {}
        errors = []
        warnings = []
        recommendations = []
        
        try:
            self.logger.info(f"Starting document processing for application {application.application_id}")
            
            # Process each document in the application
            for document in application.documents:
                document_results = await self._process_single_document(document)
                tool_results[document.document_id] = document_results
                
                # Collect any errors or warnings from document processing
                for tool_name, result in document_results.items():
                    if not result.success:
                        errors.append(f"Document {document.document_id} - {tool_name}: {result.error_message}")
                    elif result.data.get('warnings'):
                        warnings.extend(result.data['warnings'])
            
            # Generate overall assessment
            risk_score, risk_level = self._calculate_document_risk_score(tool_results)
            confidence_level = self._calculate_confidence_level(tool_results)
            recommendations = self._generate_recommendations(tool_results, application)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Document processing completed for application {application.application_id}")
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="document_processing",
                tool_results=tool_results,
                risk_score=risk_score,
                risk_level=risk_level,
                confidence_level=confidence_level,
                recommendations=recommendations,
                conditions=[],  # Document processing typically doesn't set conditions
                red_flags=self._identify_red_flags(tool_results),
                processing_time_seconds=processing_time,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Document processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            return AssessmentResult(
                agent_name=self.name,
                assessment_type="document_processing",
                tool_results=tool_results,
                risk_score=100.0,  # High risk due to processing failure
                risk_level=RiskLevel.HIGH,
                confidence_level=0.0,
                recommendations=["Manual document review required due to processing failure"],
                conditions=[],
                red_flags=["Document processing system failure"],
                processing_time_seconds=processing_time,
                errors=[error_msg],
                warnings=warnings
            )
    
    async def _process_single_document(self, document: Document) -> Dict[str, ToolResult]:
        """
        Process a single document using appropriate tools based on document type.
        
        Args:
            document: Document to process
            
        Returns:
            Dictionary of tool results for the document
        """
        results = {}
        
        # Always run OCR extraction first
        ocr_tool = self.get_tool("document_ocr_extractor")
        if ocr_tool:
            results["document_ocr_extractor"] = await ocr_tool.safe_execute(
                document_path=document.file_path,
                document_id=document.document_id
            )
        
        # Run document classification
        classifier_tool = self.get_tool("document_classifier")
        if classifier_tool:
            results["document_classifier"] = await classifier_tool.safe_execute(
                document_path=document.file_path,
                document_id=document.document_id,
                extracted_text=results.get("document_ocr_extractor", {}).data.get("extracted_text", "")
            )
        
        # Run document-type specific processing
        if document.document_type == DocumentType.IDENTITY:
            identity_tool = self.get_tool("identity_document_validator")
            if identity_tool:
                # Determine specific identity document type from classification
                classifier_result = results.get("document_classifier", {})
                document_type = "passport"  # Default
                if classifier_result.success:
                    primary_classification = classifier_result.data.get("primary_classification", {})
                    classified_type = primary_classification.get("document_type", "")
                    if classified_type in ["passport", "drivers_license", "national_id"]:
                        document_type = classified_type
                
                ocr_result = results.get("document_ocr_extractor", {})
                extracted_text = ocr_result.data.get("extracted_text", "") if ocr_result.success else ""
                key_value_pairs = ocr_result.data.get("key_value_pairs", []) if ocr_result.success else []
                
                results["identity_document_validator"] = await identity_tool.safe_execute(
                    document_id=document.document_id,
                    document_type=document_type,
                    extracted_text=extracted_text,
                    key_value_pairs=key_value_pairs,
                    document_metadata={}
                )
        
        elif document.document_type == DocumentType.ADDRESS_PROOF:
            address_tool = self.get_tool("address_proof_validator")
            if address_tool:
                # Determine specific address proof document type from classification
                classifier_result = results.get("document_classifier", {})
                document_type = "utility_bill"  # Default
                if classifier_result.success:
                    primary_classification = classifier_result.data.get("primary_classification", {})
                    classified_type = primary_classification.get("document_type", "")
                    if classified_type in ["utility_bill", "bank_statement"]:
                        document_type = classified_type
                
                ocr_result = results.get("document_ocr_extractor", {})
                extracted_text = ocr_result.data.get("extracted_text", "") if ocr_result.success else ""
                key_value_pairs = ocr_result.data.get("key_value_pairs", []) if ocr_result.success else []
                
                results["address_proof_validator"] = await address_tool.safe_execute(
                    document_id=document.document_id,
                    document_type=document_type,
                    extracted_text=extracted_text,
                    key_value_pairs=key_value_pairs,
                    applicant_name="",  # Could be populated from application context
                    expected_address="",  # Could be populated from application context
                    other_documents=[]  # Could be populated with other processed documents
                )
        
        # Always run generic document extraction for structured data
        extractor_tool = self.get_tool("document_extractor")
        if extractor_tool:
            ocr_result = results.get("document_ocr_extractor", {})
            extracted_text = ocr_result.data.get("extracted_text", "") if ocr_result.success else ""
            key_value_pairs = ocr_result.data.get("key_value_pairs", []) if ocr_result.success else []
            tables = ocr_result.data.get("tables", []) if ocr_result.success else []
            
            results["document_extractor"] = await extractor_tool.safe_execute(
                document_id=document.document_id,
                document_type=document.document_type.value,
                extracted_text=extracted_text,
                key_value_pairs=key_value_pairs,
                tables=tables
            )
        
        return results
    
    def _calculate_document_risk_score(self, tool_results: Dict[str, Dict[str, ToolResult]]) -> tuple[float, RiskLevel]:
        """
        Calculate overall document risk score based on tool results.
        
        Args:
            tool_results: Results from all document processing tools
            
        Returns:
            Tuple of (risk_score, risk_level)
        """
        total_score = 0.0
        document_count = len(tool_results)
        
        if document_count == 0:
            return 100.0, RiskLevel.HIGH
        
        for document_id, results in tool_results.items():
            document_score = 0.0
            tool_count = 0
            
            for tool_name, result in results.items():
                if result.success:
                    # Lower confidence scores indicate higher risk
                    confidence = result.data.get('confidence_score', 0.5)
                    document_score += (1.0 - confidence) * 100
                    tool_count += 1
                else:
                    # Failed tools contribute maximum risk
                    document_score += 100.0
                    tool_count += 1
            
            if tool_count > 0:
                total_score += document_score / tool_count
        
        average_risk_score = total_score / document_count
        
        # Determine risk level
        if average_risk_score >= 70:
            risk_level = RiskLevel.HIGH
        elif average_risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return average_risk_score, risk_level
    
    def _calculate_confidence_level(self, tool_results: Dict[str, Dict[str, ToolResult]]) -> float:
        """
        Calculate overall confidence level in document processing results.
        
        Args:
            tool_results: Results from all document processing tools
            
        Returns:
            Confidence level between 0 and 1
        """
        total_confidence = 0.0
        total_tools = 0
        
        for document_id, results in tool_results.items():
            for tool_name, result in results.items():
                if result.success:
                    confidence = result.data.get('confidence_score', 0.5)
                    total_confidence += confidence
                else:
                    # Failed tools have zero confidence
                    total_confidence += 0.0
                total_tools += 1
        
        if total_tools == 0:
            return 0.0
            
        return total_confidence / total_tools
    
    def _generate_recommendations(self, tool_results: Dict[str, Dict[str, ToolResult]], 
                                application: MortgageApplication) -> List[str]:
        """
        Generate recommendations based on document processing results.
        
        Args:
            tool_results: Results from all document processing tools
            application: The mortgage application being processed
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for missing document types
        required_doc_types = {DocumentType.IDENTITY, DocumentType.INCOME, DocumentType.EMPLOYMENT}
        present_doc_types = {doc.document_type for doc in application.documents}
        missing_types = required_doc_types - present_doc_types
        
        if missing_types:
            missing_names = [doc_type.value for doc_type in missing_types]
            recommendations.append(f"Missing required document types: {', '.join(missing_names)}")
        
        # Check for low confidence scores
        low_confidence_docs = []
        for document_id, results in tool_results.items():
            for tool_name, result in results.items():
                if result.success:
                    confidence = result.data.get('confidence_score', 1.0)
                    if confidence < 0.7:
                        low_confidence_docs.append(document_id)
                        break
        
        if low_confidence_docs:
            recommendations.append(f"Manual review recommended for documents with low confidence: {', '.join(low_confidence_docs)}")
        
        # Check for classification mismatches
        classification_issues = []
        for document_id, results in tool_results.items():
            classifier_result = results.get("document_classifier")
            if classifier_result and classifier_result.success:
                predicted_type = classifier_result.data.get('predicted_type')
                # Find the actual document
                actual_doc = next((doc for doc in application.documents if doc.document_id == document_id), None)
                if actual_doc and predicted_type != actual_doc.document_type.value:
                    classification_issues.append(document_id)
        
        if classification_issues:
            recommendations.append(f"Document type verification needed for: {', '.join(classification_issues)}")
        
        return recommendations
    
    def _identify_red_flags(self, tool_results: Dict[str, Dict[str, ToolResult]]) -> List[str]:
        """
        Identify red flags from document processing results.
        
        Args:
            tool_results: Results from all document processing tools
            
        Returns:
            List of red flag descriptions
        """
        red_flags = []
        
        for document_id, results in tool_results.items():
            # Check for validation failures
            identity_result = results.get("identity_document_validator")
            if identity_result and identity_result.success:
                if not identity_result.data.get('is_valid', True):
                    red_flags.append(f"Invalid identity document detected: {document_id}")
            
            address_result = results.get("address_proof_validator")
            if address_result and address_result.success:
                if not address_result.data.get('is_valid', True):
                    red_flags.append(f"Invalid address proof document detected: {document_id}")
            
            # Check for very low confidence scores (potential fraud)
            for tool_name, result in results.items():
                if result.success:
                    confidence = result.data.get('confidence_score', 1.0)
                    if confidence < 0.3:
                        red_flags.append(f"Very low confidence in document authenticity: {document_id}")
                        break
        
        return red_flags