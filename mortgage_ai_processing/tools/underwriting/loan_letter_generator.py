"""
Loan Letter Generator Tool implementation.

This tool generates automated documentation for loan decisions including approval letters,
conditional approval letters, denial letters, and adverse action notices.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from ..base import BaseTool, ToolResult
from ...models.assessment import DecisionType, RiskLevel


class LoanLetterGeneratorTool(BaseTool):
    """
    Tool for automated loan letter and documentation generation.
    
    Generates appropriate letters based on loan decision type:
    - Approval letters with loan terms and closing instructions
    - Conditional approval letters with required conditions
    - Denial letters with adverse action notices
    - Adverse action notices compliant with FCRA requirements
    """
    
    def __init__(self):
        super().__init__(
            name="loan_letter_generator",
            description="Automated loan letter and documentation generator for all decision types",
            agent_domain="underwriting"
        )
        self.logger = logging.getLogger("tool.loan_letter_generator")
        
        # Letter templates
        self.letter_templates = {
            'approval': self._get_approval_template(),
            'conditional_approval': self._get_conditional_approval_template(),
            'denial': self._get_denial_template(),
            'adverse_action': self._get_adverse_action_template()
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute loan letter generation based on decision data.
        
        Args:
            borrower_information: Borrower contact and personal information
            loan_information: Loan application details
            decision_data: Decision results from loan decision engine
            letter_types: List of letter types to generate
            include_adverse_action_notices: Whether to include adverse action notices
            template_customization: Custom template settings
            
        Returns:
            ToolResult containing generated letters and metadata
        """
        try:
            self.logger.info("Starting loan letter generation")
            
            # Extract parameters
            borrower_info = kwargs.get('borrower_information', {})
            loan_info = kwargs.get('loan_information', {})
            decision_data = kwargs.get('decision_data', {})
            letter_types = kwargs.get('letter_types', ['approval', 'conditional_approval', 'denial'])
            include_adverse_action = kwargs.get('include_adverse_action_notices', True)
            template_customization = kwargs.get('template_customization', {})
            
            # Validate required data
            if not borrower_info or not loan_info:
                raise ValueError("Borrower information and loan information are required")
            
            # Determine which letters to generate based on decision
            decision_type = decision_data.get('decision', DecisionType.CONDITIONAL.value)
            letters_to_generate = self._determine_letters_to_generate(
                decision_type, letter_types, include_adverse_action, decision_data
            )
            
            # Generate letters
            generated_letters = {}
            generation_metadata = {}
            
            for letter_type in letters_to_generate:
                letter_content, metadata = self._generate_letter(
                    letter_type, borrower_info, loan_info, decision_data, template_customization
                )
                generated_letters[letter_type] = letter_content
                generation_metadata[letter_type] = metadata
            
            # Calculate generation confidence
            generation_confidence = self._calculate_generation_confidence(
                decision_data, borrower_info, loan_info, generated_letters
            )
            
            result_data = {
                'generated_letters': generated_letters,
                'primary_letter_type': self._get_primary_letter_type(decision_type),
                'letters_generated': list(generated_letters.keys()),
                'generation_confidence': generation_confidence,
                'generation_metadata': generation_metadata,
                'borrower_name': borrower_info.get('name', 'Unknown'),
                'application_id': loan_info.get('application_id', 'Unknown'),
                'generation_timestamp': datetime.now().isoformat(),
                'template_version': '1.0.0',
                'compliance_notes': self._get_compliance_notes(decision_type, decision_data)
            }
            
            self.logger.info(f"Generated {len(generated_letters)} letters for decision: {decision_type}")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            error_msg = f"Loan letter generation failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error_message=error_msg
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "borrower_information": {
                    "type": "object",
                    "description": "Borrower contact and personal information",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"}
                    },
                    "required": ["name"]
                },
                "loan_information": {
                    "type": "object",
                    "description": "Loan application details",
                    "properties": {
                        "application_id": {"type": "string"},
                        "loan_amount": {"type": "number"},
                        "loan_type": {"type": "string"},
                        "property_address": {"type": "string"}
                    },
                    "required": ["application_id"]
                },
                "decision_data": {
                    "type": "object",
                    "description": "Decision results from loan decision engine"
                },
                "letter_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of letter types to generate"
                },
                "include_adverse_action_notices": {
                    "type": "boolean",
                    "description": "Whether to include adverse action notices"
                },
                "template_customization": {
                    "type": "object",
                    "description": "Custom template settings",
                    "properties": {
                        "company_name": {"type": "string"},
                        "include_contact_info": {"type": "boolean"},
                        "include_appeal_process": {"type": "boolean"}
                    }
                }
            },
            "required": ["borrower_information", "loan_information"]
        }
    
    def _determine_letters_to_generate(self, decision_type: str, letter_types: List[str],
                                     include_adverse_action: bool, decision_data: Dict[str, Any]) -> List[str]:
        """Determine which letters to generate based on decision type."""
        letters_to_generate = []
        
        if decision_type == DecisionType.APPROVE.value:
            if 'approval' in letter_types:
                letters_to_generate.append('approval')
        elif decision_type == DecisionType.CONDITIONAL.value:
            if 'conditional_approval' in letter_types:
                letters_to_generate.append('conditional_approval')
        elif decision_type == DecisionType.DENY.value:
            if 'denial' in letter_types:
                letters_to_generate.append('denial')
            
            # Add adverse action notices for denials
            if include_adverse_action and decision_data.get('adverse_actions'):
                letters_to_generate.append('adverse_action')
        
        return letters_to_generate
    
    def _generate_letter(self, letter_type: str, borrower_info: Dict[str, Any],
                        loan_info: Dict[str, Any], decision_data: Dict[str, Any],
                        template_customization: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Generate a specific type of letter."""
        template = self.letter_templates.get(letter_type, "")
        
        if letter_type == 'approval':
            return self._generate_approval_letter(template, borrower_info, loan_info, decision_data, template_customization)
        elif letter_type == 'conditional_approval':
            return self._generate_conditional_approval_letter(template, borrower_info, loan_info, decision_data, template_customization)
        elif letter_type == 'denial':
            return self._generate_denial_letter(template, borrower_info, loan_info, decision_data, template_customization)
        elif letter_type == 'adverse_action':
            return self._generate_adverse_action_notice(template, borrower_info, loan_info, decision_data, template_customization)
        else:
            raise ValueError(f"Unknown letter type: {letter_type}")
    
    def _generate_approval_letter(self, template: str, borrower_info: Dict[str, Any],
                                loan_info: Dict[str, Any], decision_data: Dict[str, Any],
                                template_customization: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Generate approval letter."""
        loan_terms = decision_data.get('loan_terms', {})
        company_name = template_customization.get('company_name', 'Mortgage AI Processing System')
        
        # Format loan terms
        loan_amount = loan_terms.get('loan_amount', 0)
        interest_rate = loan_terms.get('interest_rate', 0)
        monthly_payment = loan_terms.get('monthly_payment', 0)
        loan_term = loan_terms.get('loan_term_years', 30)
        
        letter_content = template.format(
            company_name=company_name,
            borrower_name=borrower_info.get('name', 'Valued Customer'),
            borrower_address=borrower_info.get('address', ''),
            application_id=loan_info.get('application_id', 'N/A'),
            loan_amount=f"${loan_amount:,.2f}" if loan_amount else "N/A",
            interest_rate=f"{interest_rate:.3f}%" if interest_rate else "N/A",
            monthly_payment=f"${monthly_payment:,.2f}" if monthly_payment else "N/A",
            loan_term=f"{loan_term} years",
            property_address=loan_info.get('property_address', 'N/A'),
            date=datetime.now().strftime("%B %d, %Y"),
            expiration_date=(datetime.now() + timedelta(days=30)).strftime("%B %d, %Y"),
            contact_info=self._get_contact_info(template_customization) if template_customization.get('include_contact_info', True) else ""
        )
        
        metadata = {
            'letter_type': 'approval',
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'expiration_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'conditions_count': 0
        }
        
        return letter_content, metadata
    
    def _generate_conditional_approval_letter(self, template: str, borrower_info: Dict[str, Any],
                                            loan_info: Dict[str, Any], decision_data: Dict[str, Any],
                                            template_customization: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Generate conditional approval letter."""
        conditions = decision_data.get('conditions', [])
        loan_terms = decision_data.get('loan_terms', {})
        company_name = template_customization.get('company_name', 'Mortgage AI Processing System')
        
        # Format conditions list
        conditions_text = ""
        if conditions:
            conditions_text = "The following conditions must be satisfied before closing:\n\n"
            for i, condition in enumerate(conditions, 1):
                conditions_text += f"{i}. {condition}\n"
        
        # Format loan terms
        loan_amount = loan_terms.get('loan_amount', 0)
        interest_rate = loan_terms.get('interest_rate', 0)
        
        letter_content = template.format(
            company_name=company_name,
            borrower_name=borrower_info.get('name', 'Valued Customer'),
            borrower_address=borrower_info.get('address', ''),
            application_id=loan_info.get('application_id', 'N/A'),
            loan_amount=f"${loan_amount:,.2f}" if loan_amount else "N/A",
            interest_rate=f"{interest_rate:.3f}%" if interest_rate else "N/A",
            property_address=loan_info.get('property_address', 'N/A'),
            conditions_list=conditions_text,
            conditions_count=len(conditions),
            date=datetime.now().strftime("%B %d, %Y"),
            expiration_date=(datetime.now() + timedelta(days=45)).strftime("%B %d, %Y"),
            contact_info=self._get_contact_info(template_customization) if template_customization.get('include_contact_info', True) else ""
        )
        
        metadata = {
            'letter_type': 'conditional_approval',
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'conditions_count': len(conditions),
            'expiration_date': (datetime.now() + timedelta(days=45)).isoformat()
        }
        
        return letter_content, metadata
    
    def _generate_denial_letter(self, template: str, borrower_info: Dict[str, Any],
                              loan_info: Dict[str, Any], decision_data: Dict[str, Any],
                              template_customization: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Generate denial letter."""
        adverse_actions = decision_data.get('adverse_actions', [])
        company_name = template_customization.get('company_name', 'Mortgage AI Processing System')
        
        # Format denial reasons
        denial_reasons = ""
        if adverse_actions:
            denial_reasons = "The primary reasons for this decision are:\n\n"
            for i, action in enumerate(adverse_actions, 1):
                reason_desc = action.get('reason_description', 'Unspecified reason')
                denial_reasons += f"{i}. {reason_desc}\n"
        
        # Appeal process information
        appeal_info = ""
        if template_customization.get('include_appeal_process', True):
            appeal_info = self._get_appeal_process_info()
        
        letter_content = template.format(
            company_name=company_name,
            borrower_name=borrower_info.get('name', 'Valued Customer'),
            borrower_address=borrower_info.get('address', ''),
            application_id=loan_info.get('application_id', 'N/A'),
            loan_amount=f"${loan_info.get('loan_amount', 0):,.2f}" if loan_info.get('loan_amount') else "N/A",
            property_address=loan_info.get('property_address', 'N/A'),
            denial_reasons=denial_reasons,
            date=datetime.now().strftime("%B %d, %Y"),
            appeal_process=appeal_info,
            contact_info=self._get_contact_info(template_customization) if template_customization.get('include_contact_info', True) else ""
        )
        
        metadata = {
            'letter_type': 'denial',
            'adverse_actions_count': len(adverse_actions),
            'appeal_process_included': template_customization.get('include_appeal_process', True)
        }
        
        return letter_content, metadata
    
    def _generate_adverse_action_notice(self, template: str, borrower_info: Dict[str, Any],
                                      loan_info: Dict[str, Any], decision_data: Dict[str, Any],
                                      template_customization: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Generate adverse action notice (FCRA compliant)."""
        adverse_actions = decision_data.get('adverse_actions', [])
        company_name = template_customization.get('company_name', 'Mortgage AI Processing System')
        
        # Format adverse action reasons with codes
        adverse_reasons = ""
        if adverse_actions:
            adverse_reasons = "Specific reasons for adverse action:\n\n"
            for action in adverse_actions:
                reason_code = action.get('reason_code', 'N/A')
                reason_desc = action.get('reason_description', 'Unspecified reason')
                adverse_reasons += f"• {reason_desc} (Code: {reason_code})\n"
        
        letter_content = template.format(
            company_name=company_name,
            borrower_name=borrower_info.get('name', 'Valued Customer'),
            borrower_address=borrower_info.get('address', ''),
            application_id=loan_info.get('application_id', 'N/A'),
            adverse_reasons=adverse_reasons,
            date=datetime.now().strftime("%B %d, %Y"),
            contact_info=self._get_contact_info(template_customization) if template_customization.get('include_contact_info', True) else ""
        )
        
        metadata = {
            'letter_type': 'adverse_action',
            'adverse_actions_count': len(adverse_actions),
            'fcra_compliant': True
        }
        
        return letter_content, metadata
    
    def _get_primary_letter_type(self, decision_type: str) -> str:
        """Get the primary letter type for a decision."""
        if decision_type == DecisionType.APPROVE.value:
            return 'approval'
        elif decision_type == DecisionType.CONDITIONAL.value:
            return 'conditional_approval'
        elif decision_type == DecisionType.DENY.value:
            return 'denial'
        else:
            return 'unknown'
    
    def _calculate_generation_confidence(self, decision_data: Dict[str, Any],
                                       borrower_info: Dict[str, Any],
                                       loan_info: Dict[str, Any],
                                       generated_letters: Dict[str, str]) -> float:
        """Calculate confidence in letter generation quality."""
        confidence_factors = []
        
        # Data completeness confidence
        required_borrower_fields = ['name', 'address', 'email']
        borrower_completeness = sum(1 for field in required_borrower_fields if borrower_info.get(field)) / len(required_borrower_fields)
        confidence_factors.append(borrower_completeness)
        
        required_loan_fields = ['application_id', 'loan_amount', 'property_address']
        loan_completeness = sum(1 for field in required_loan_fields if loan_info.get(field)) / len(required_loan_fields)
        confidence_factors.append(loan_completeness)
        
        # Decision data quality
        decision_confidence = decision_data.get('confidence_score', 0.5)
        confidence_factors.append(decision_confidence)
        
        # Letter generation success
        generation_success = len(generated_letters) > 0
        confidence_factors.append(1.0 if generation_success else 0.0)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    
    def _get_compliance_notes(self, decision_type: str, decision_data: Dict[str, Any]) -> List[str]:
        """Get compliance notes for the generated letters."""
        notes = []
        
        if decision_type == DecisionType.DENY.value:
            notes.append("Adverse action notices required under FCRA")
            notes.append("Borrower has right to obtain free credit report")
            notes.append("Borrower has right to dispute credit report information")
        
        if decision_data.get('requires_manual_review', False):
            notes.append("Manual review required - automated decision not final")
        
        return notes
    
    def _get_contact_info(self, template_customization: Dict[str, Any]) -> str:
        """Get contact information for letters."""
        return """
For questions about this decision, please contact us at:
Phone: (555) 123-4567
Email: underwriting@mortgageai.com
Hours: Monday-Friday, 8:00 AM - 6:00 PM EST
"""
    
    def _get_appeal_process_info(self) -> str:
        """Get appeal process information for denial letters."""
        return """
If you believe this decision was made in error, you may request a review by:
1. Submitting additional documentation that addresses the concerns noted above
2. Providing a written explanation of any extenuating circumstances
3. Contacting our underwriting department within 30 days of this notice

Please reference your application ID in all correspondence.
"""
    
    # Letter templates
    def _get_approval_template(self) -> str:
        """Get approval letter template."""
        return """
{company_name}
{date}

{borrower_name}
{borrower_address}

RE: Loan Application #{application_id} - APPROVED

Dear {borrower_name},

Congratulations! We are pleased to inform you that your mortgage loan application has been APPROVED.

LOAN DETAILS:
• Loan Amount: {loan_amount}
• Interest Rate: {interest_rate}
• Monthly Payment: {monthly_payment}
• Loan Term: {loan_term}
• Property Address: {property_address}

This approval is valid until {expiration_date}. Please contact us immediately to schedule your closing.

NEXT STEPS:
1. Review and sign the loan documents we will send you
2. Obtain homeowner's insurance and provide proof of coverage
3. Complete final walk-through of the property
4. Attend closing with required funds and identification

We look forward to helping you complete this important milestone.

Sincerely,

Underwriting Department
{company_name}

{contact_info}
"""
    
    def _get_conditional_approval_template(self) -> str:
        """Get conditional approval letter template."""
        return """
{company_name}
{date}

{borrower_name}
{borrower_address}

RE: Loan Application #{application_id} - CONDITIONAL APPROVAL

Dear {borrower_name},

We are pleased to inform you that your mortgage loan application has received CONDITIONAL APPROVAL.

LOAN DETAILS:
• Loan Amount: {loan_amount}
• Interest Rate: {interest_rate}
• Property Address: {property_address}

CONDITIONS REQUIRED FOR FINAL APPROVAL:
{conditions_list}

This conditional approval is valid until {expiration_date}. All conditions must be satisfied before closing can occur.

Please submit the required documentation as soon as possible to avoid any delays in your closing.

Sincerely,

Underwriting Department
{company_name}

{contact_info}
"""
    
    def _get_denial_template(self) -> str:
        """Get denial letter template."""
        return """
{company_name}
{date}

{borrower_name}
{borrower_address}

RE: Loan Application #{application_id} - UNABLE TO APPROVE

Dear {borrower_name},

After careful review of your mortgage loan application for {loan_amount} to purchase the property at {property_address}, we regret to inform you that we are unable to approve your loan at this time.

{denial_reasons}

This decision is based on information in your credit report and/or information you provided in your application. You have the right to a free copy of your credit report from the credit reporting agency we used. You also have the right to dispute the accuracy or completeness of any information in your credit report.

{appeal_process}

We appreciate your interest in our lending services.

Sincerely,

Underwriting Department
{company_name}

{contact_info}
"""
    
    def _get_adverse_action_template(self) -> str:
        """Get adverse action notice template (FCRA compliant)."""
        return """
{company_name}
ADVERSE ACTION NOTICE

{date}

{borrower_name}
{borrower_address}

RE: Application #{application_id} - ADVERSE ACTION NOTICE

Dear {borrower_name},

This notice is to inform you that adverse action has been taken on your credit application.

{adverse_reasons}

IMPORTANT RIGHTS UNDER FEDERAL LAW:

You have the right to obtain a free copy of your credit report from the credit reporting agency listed below within 60 days of receiving this notice:

Experian: 1-888-397-3742, www.experian.com
Equifax: 1-800-685-1111, www.equifax.com
TransUnion: 1-800-916-8800, www.transunion.com

You have the right to dispute the accuracy or completeness of any information in your credit report. The federal Fair Credit Reporting Act (FCRA) gives you specific rights when adverse action is taken based on information in your credit report.

For more information about your rights under the FCRA, visit www.consumerfinance.gov/learnmore or contact the Consumer Financial Protection Bureau at 1-855-411-2372.

Sincerely,

{company_name}

{contact_info}
"""