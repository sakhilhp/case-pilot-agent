"""
Core data models for the mortgage processing system.

Contains the primary data structures used throughout the mortgage processing
workflow, including applications, documents, and related metadata.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .enums import DocumentType, ProcessingStatus, ValidationStatus, LoanType


class BorrowerInfo(BaseModel):
    """Information about the mortgage borrower."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    ssn: str = Field(..., pattern=r'^\d{3}-\d{2}-\d{4}$')
    date_of_birth: datetime
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: str = Field(..., pattern=r'^\+?1?-?\d{3}-?\d{3}-?\d{4}$')
    phone_number: Optional[str] = Field(None, description="Phone number (alias for phone field)")
    current_address: str = Field(..., min_length=10, max_length=500)
    employment_status: str = Field(..., min_length=1, max_length=100)
    annual_income: Decimal = Field(..., gt=0)
    
    def model_post_init(self, __context) -> None:
        """Sync phone_number with phone field after initialization."""
        if self.phone_number is None:
            self.phone_number = self.phone
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v):
        """Ensure borrower is at least 18 years old."""
        age = (datetime.now() - v).days / 365.25
        if age < 18:
            raise ValueError('Borrower must be at least 18 years old')
        if age > 120:
            raise ValueError('Invalid date of birth')
        return v


class PropertyInfo(BaseModel):
    """Information about the property being financed."""
    address: str = Field(..., min_length=10, max_length=500)
    property_type: str = Field(..., min_length=1, max_length=100)
    property_value: Decimal = Field(..., gt=0)
    square_footage: Optional[int] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[Decimal] = Field(None, ge=0)
    year_built: Optional[int] = Field(None, ge=1800, le=datetime.now().year + 1)
    lot_size: Optional[Decimal] = Field(None, gt=0)
    property_tax_annual: Optional[Decimal] = Field(None, ge=0)
    hoa_fees_monthly: Optional[Decimal] = Field(None, ge=0)


class LoanDetails(BaseModel):
    """Details about the requested loan."""
    loan_amount: Decimal = Field(..., gt=0)
    loan_type: LoanType
    loan_term_years: int = Field(..., gt=0, le=50)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    down_payment: Decimal = Field(..., ge=0)
    loan_to_value_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    debt_to_income_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    purpose: str = Field(..., min_length=1, max_length=100)  # purchase, refinance, etc.
    
    @field_validator('loan_to_value_ratio')
    @classmethod
    def validate_ltv(cls, v):
        """Validate loan-to-value ratio if property value is available."""
        if v is not None and v > 100:
            raise ValueError('Loan-to-value ratio cannot exceed 100%')
        return v


class ClassificationScore(BaseModel):
    """Detailed classification scoring for document types."""
    document_type: DocumentType
    confidence_score: float = Field(..., ge=0, le=1)
    reasoning: Optional[str] = Field(None, max_length=500)
    features_detected: List[str] = Field(default_factory=list)
    alternative_classifications: List[Dict[str, float]] = Field(default_factory=list)


class ProcessingMetadata(BaseModel):
    """Metadata about document processing operations."""
    processed_at: datetime = Field(default_factory=datetime.now)
    processing_agent: str = Field(..., min_length=1, max_length=100)
    processing_tool: str = Field(..., min_length=1, max_length=100)
    processing_duration_seconds: Optional[float] = Field(None, ge=0)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    extraction_method: Optional[str] = Field(None, max_length=100)
    ocr_engine_version: Optional[str] = Field(None, max_length=50)
    classification_scores: List[ClassificationScore] = Field(default_factory=list)
    error_messages: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DocumentRelationship(BaseModel):
    """Represents a relationship between documents."""
    related_document_id: str = Field(..., min_length=1, max_length=100)
    relationship_type: str = Field(..., min_length=1, max_length=100)  # "supports", "contradicts", "supplements", etc.
    confidence_score: float = Field(..., ge=0, le=1)
    description: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)


class Document(BaseModel):
    """Represents a document in the mortgage processing system."""
    document_id: str = Field(..., min_length=1, max_length=100)
    document_type: DocumentType
    file_path: str = Field(..., min_length=1, max_length=1000)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1, max_length=100)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    classification_confidence: float = Field(..., ge=0, le=1)
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    processing_metadata: ProcessingMetadata
    relationships: List[DocumentRelationship] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        """Ensure file path is not empty and has reasonable format."""
        if not v.strip():
            raise ValueError('File path cannot be empty')
        return v.strip()
    
    @field_validator('classification_confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence score is within valid range."""
        if not 0 <= v <= 1:
            raise ValueError('Classification confidence must be between 0 and 1')
        return v


class MortgageApplication(BaseModel):
    """Complete mortgage application with all associated data."""
    application_id: str = Field(..., min_length=1, max_length=100)
    borrower_info: BorrowerInfo
    property_info: PropertyInfo
    loan_details: LoanDetails
    documents: List[Document] = Field(default_factory=list)
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: List[str] = Field(default_factory=list)
    
    @field_validator('application_id')
    @classmethod
    def validate_application_id(cls, v):
        """Ensure application ID follows expected format."""
        if not v.strip():
            raise ValueError('Application ID cannot be empty')
        # Could add more specific format validation here
        return v.strip()
    
    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        """Ensure document IDs are unique within the application."""
        if v:
            doc_ids = [doc.document_id for doc in v]
            if len(doc_ids) != len(set(doc_ids)):
                raise ValueError('Document IDs must be unique within an application')
        return v
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )