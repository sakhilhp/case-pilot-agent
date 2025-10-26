"""
Validation utilities for mortgage processing data models.

Contains helper functions for validating complex business rules
and cross-field validations that go beyond basic Pydantic validation.
"""

from typing import List, Tuple
from decimal import Decimal
from .core import MortgageApplication, Document
from .assessment import LoanDecision
from .enums import DocumentType, DecisionType, ValidationStatus


def validate_mortgage_application(application: MortgageApplication) -> Tuple[bool, List[str]]:
    """
    Validate a complete mortgage application for business rule compliance.
    
    Args:
        application: The mortgage application to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate loan-to-value ratio
    ltv_ratio = calculate_ltv_ratio(application.loan_details.loan_amount, 
                                   application.property_info.property_value)
    if ltv_ratio > 100:
        errors.append(f"Loan-to-value ratio ({ltv_ratio:.2f}%) exceeds 100%")
    
    # Validate down payment consistency
    expected_down_payment = application.property_info.property_value - application.loan_details.loan_amount
    if abs(expected_down_payment - application.loan_details.down_payment) > Decimal('1000'):
        errors.append("Down payment amount is inconsistent with loan amount and property value")
    
    # Validate required documents are present
    required_docs = get_required_document_types(application.loan_details.loan_type.value)
    present_doc_types = {doc.document_type for doc in application.documents}
    missing_docs = required_docs - present_doc_types
    if missing_docs:
        missing_doc_names = [doc_type.value for doc_type in missing_docs]
        errors.append(f"Missing required documents: {', '.join(missing_doc_names)}")
    
    # Validate document validation status
    invalid_docs = [doc for doc in application.documents 
                   if doc.validation_status == ValidationStatus.INVALID]
    if invalid_docs:
        doc_names = [doc.original_filename for doc in invalid_docs]
        errors.append(f"Invalid documents present: {', '.join(doc_names)}")
    
    return len(errors) == 0, errors


def validate_document(document: Document) -> Tuple[bool, List[str]]:
    """
    Validate a document for completeness and consistency.
    
    Args:
        document: The document to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate file exists and is readable
    if not document.file_path or not document.file_path.strip():
        errors.append("Document file path is empty")
    
    # Validate extracted data is present for processed documents
    if (document.validation_status in [ValidationStatus.VALID, ValidationStatus.INVALID] 
        and not document.extracted_data):
        errors.append("Processed document should have extracted data")
    
    # Validate confidence score is reasonable for classified documents
    if document.classification_confidence < 0.5:
        errors.append(f"Low classification confidence ({document.classification_confidence:.2f})")
    
    # Validate document type specific requirements
    type_errors = validate_document_type_requirements(document)
    errors.extend(type_errors)
    
    return len(errors) == 0, errors


def validate_document_type_requirements(document: Document) -> List[str]:
    """
    Validate document-type specific requirements.
    
    Args:
        document: The document to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    extracted_data = document.extracted_data
    
    if document.document_type == DocumentType.IDENTITY:
        required_fields = ['full_name', 'date_of_birth', 'document_number']
        missing_fields = [field for field in required_fields if field not in extracted_data]
        if missing_fields:
            errors.append(f"Identity document missing required fields: {', '.join(missing_fields)}")
    
    elif document.document_type == DocumentType.INCOME:
        required_fields = ['income_amount', 'pay_period']
        missing_fields = [field for field in required_fields if field not in extracted_data]
        if missing_fields:
            errors.append(f"Income document missing required fields: {', '.join(missing_fields)}")
    
    elif document.document_type == DocumentType.EMPLOYMENT:
        required_fields = ['employer_name', 'employment_status', 'start_date']
        missing_fields = [field for field in required_fields if field not in extracted_data]
        if missing_fields:
            errors.append(f"Employment document missing required fields: {', '.join(missing_fields)}")
    
    elif document.document_type == DocumentType.ADDRESS_PROOF:
        required_fields = ['address', 'date_issued']
        missing_fields = [field for field in required_fields if field not in extracted_data]
        if missing_fields:
            errors.append(f"Address proof document missing required fields: {', '.join(missing_fields)}")
    
    return errors


def get_required_document_types(loan_type: str) -> set:
    """
    Get the set of required document types for a given loan type.
    
    Args:
        loan_type: The type of loan (conventional, fha, va, etc.)
        
    Returns:
        Set of required DocumentType enums
    """
    base_requirements = {
        DocumentType.IDENTITY,
        DocumentType.INCOME,
        DocumentType.EMPLOYMENT,
        DocumentType.CREDIT
    }
    
    # Add loan-type specific requirements
    if loan_type.lower() == 'fha':
        base_requirements.add(DocumentType.ADDRESS_PROOF)
    elif loan_type.lower() == 'va':
        base_requirements.add(DocumentType.ADDRESS_PROOF)
    elif loan_type.lower() == 'jumbo':
        base_requirements.add(DocumentType.PROPERTY)
        base_requirements.add(DocumentType.BANK_STATEMENT)
    
    return base_requirements


def calculate_ltv_ratio(loan_amount: Decimal, property_value: Decimal) -> float:
    """
    Calculate loan-to-value ratio.
    
    Args:
        loan_amount: The requested loan amount
        property_value: The appraised property value
        
    Returns:
        LTV ratio as a percentage
    """
    if property_value <= 0:
        raise ValueError("Property value must be greater than zero")
    
    return float((loan_amount / property_value) * 100)


def calculate_dti_ratio(monthly_debt: Decimal, monthly_income: Decimal) -> float:
    """
    Calculate debt-to-income ratio.
    
    Args:
        monthly_debt: Total monthly debt payments
        monthly_income: Total monthly income
        
    Returns:
        DTI ratio as a percentage
    """
    if monthly_income <= 0:
        raise ValueError("Monthly income must be greater than zero")
    
    return float((monthly_debt / monthly_income) * 100)


def validate_loan_decision(decision: LoanDecision) -> Tuple[bool, List[str]]:
    """
    Validate a loan decision for consistency and completeness.
    
    Args:
        decision: The loan decision to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate decision consistency with score
    if decision.decision == DecisionType.APPROVE.value and decision.overall_score < 60:
        errors.append("Approval decision inconsistent with low overall score")
    elif decision.decision == DecisionType.DENY.value and decision.overall_score > 80:
        errors.append("Denial decision inconsistent with high overall score")
    
    # Validate factor scores sum to reasonable total
    calculated_score = decision.decision_factors.calculate_overall_score()
    if abs(calculated_score - decision.overall_score) > 5:  # Allow 5 point tolerance
        errors.append(f"Overall score ({decision.overall_score}) inconsistent with calculated score ({calculated_score:.2f})")
    
    # Validate conditional approvals have conditions
    if decision.decision == DecisionType.CONDITIONAL.value and not decision.conditions:
        errors.append("Conditional approval must include specific conditions")
    
    return len(errors) == 0, errors