# Mortgage AI Processing System - Testing Guide

## Overview

This comprehensive testing guide covers all aspects of the Mortgage AI Processing System, including end-to-end workflow testing, individual agent testing, and specific tool testing using the command-line interface (CLI).

## System Architecture

The system consists of:
- **6 Specialized Agents**: Document Processing, Credit Assessment, Income Verification, Property Assessment, Risk Assessment, Underwriting
- **20+ Tools**: Organized across 6 domains (document, credit, income, property, risk, underwriting)
- **Workflow Orchestrator**: Manages parallel and sequential processing
- **MCP Server**: Model Context Protocol server for external integrations

## Prerequisites

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables in .env file
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-api-key
```

### Verify Installation
```bash
# Test CLI accessibility
python -m mortgage_ai_processing.cli --help

# Check system health
python -m mortgage_ai_processing.cli system health
```

## 1. End-to-End Workflow Testing

### Complete Mortgage Processing Pipeline

#### Test 1: Standard Workflow Processing
```bash
# Process with existing sample application
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type standard \
  --output e2e_standard_results.json
```

#### Test 2: Parallel Workflow Processing
```bash
# Process with parallel execution (recommended)
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output e2e_parallel_results.json
```

#### Test 3: Custom Application Processing
Create a custom application file:
```json
{
  "application_id": "CUSTOM-TEST-001",
  "borrower_info": {
    "first_name": "Jane",
    "last_name": "Smith",
    "ssn": "987-65-4321",
    "date_of_birth": "1990-03-15T00:00:00",
    "email": "jane.smith@example.com",
    "phone": "555-987-6543",
    "current_address": "789 Oak Street, Testtown, ST 54321",
    "employment_status": "Employed",
    "annual_income": 85000
  },
  "property_info": {
    "address": "321 Pine Avenue, Newcity, ST 98765",
    "property_type": "Condominium",
    "property_value": 350000
  },
  "loan_details": {
    "loan_amount": 280000,
    "loan_type": "conventional",
    "loan_term_years": 30,
    "down_payment": 70000,
    "purpose": "Purchase"
  },
  "documents": [],
  "processing_status": "pending"
}
```

Save as `custom_application.json` and test:
```bash
python -m mortgage_ai_processing.cli workflow process \
  --application-file custom_application.json \
  --workflow-type parallel \
  --output custom_results.json
```

### Workflow Management Commands
```bash
# List active workflows
python -m mortgage_ai_processing.cli workflow list

# Check specific workflow status
python -m mortgage_ai_processing.cli workflow status EXECUTION-ID

# Cancel running workflow
python -m mortgage_ai_processing.cli workflow cancel EXECUTION-ID
```

## 2. Individual Agent Testing

### List All Agents
```bash
# Get complete agent inventory
python -m mortgage_ai_processing.cli agents list
```

### Test Individual Agents

#### Agent Information and Status
```bash
# List all available agents
python -m mortgage_ai_processing.cli agents list

# Get detailed agent information
python -m mortgage_ai_processing.cli agents info document_agent
python -m mortgage_ai_processing.cli agents info credit_agent
python -m mortgage_ai_processing.cli agents info income_agent
python -m mortgage_ai_processing.cli agents info property_agent
python -m mortgage_ai_processing.cli agents info risk_agent
python -m mortgage_ai_processing.cli agents info underwriting_agent

# Check status of all agents
python -m mortgage_ai_processing.cli agents status
```

#### Agent Testing Commands

##### Step 1: See Agent Input Schema
```bash
# Get the expected input format for any agent
python -m mortgage_ai_processing.cli agents test document_agent --show-schema
python -m mortgage_ai_processing.cli agents test credit_agent --show-schema
python -m mortgage_ai_processing.cli agents test income_agent --show-schema
```

##### Step 2: Test Agents with Application Data

###### Using Application File (Recommended)
```bash
# Test document processing agent
python -m mortgage_ai_processing.cli agents test document_agent \
  --application-file e2e_application.json \
  --output document_agent_results.json

# Test credit assessment agent
python -m mortgage_ai_processing.cli agents test credit_agent \
  --application-file e2e_application.json \
  --output credit_agent_results.json

# Test income verification agent
python -m mortgage_ai_processing.cli agents test income_agent \
  --application-file e2e_application.json \
  --output income_agent_results.json

# Test property assessment agent
python -m mortgage_ai_processing.cli agents test property_agent \
  --application-file e2e_application.json \
  --output property_agent_results.json

# Test risk assessment agent
python -m mortgage_ai_processing.cli agents test risk_agent \
  --application-file e2e_application.json \
  --output risk_agent_results.json

# Test underwriting agent
python -m mortgage_ai_processing.cli agents test underwriting_agent \
  --application-file e2e_application.json \
  --output underwriting_agent_results.json
```

###### Using Inline JSON Data
```bash
# Test with inline application data
python -m mortgage_ai_processing.cli agents test credit_agent \
  --application-data '{
    "application_id": "test-001",
    "borrower_info": {
      "first_name": "John",
      "last_name": "Doe",
      "ssn": "123-45-6789",
      "date_of_birth": "1985-01-01T00:00:00",
      "email": "john.doe@example.com",
      "phone": "555-123-4567",
      "current_address": "123 Main St, Anytown, ST 12345",
      "employment_status": "Employed",
      "annual_income": 75000
    },
    "property_info": {
      "address": "456 Oak Ave, Testville, ST 67890",
      "property_type": "Single Family Home",
      "property_value": 300000
    },
    "loan_details": {
      "loan_amount": 240000,
      "loan_type": "conventional",
      "loan_term_years": 30,
      "down_payment": 60000,
      "purpose": "Purchase"
    },
    "documents": [],
    "processing_status": "pending"
  }'
```

##### Step 3: Analyze Agent Results

Each agent test will show:
- ✅ **Execution Status**: Success/failure
- ⏱️ **Execution Time**: How long the agent took
- 📊 **Summary Results**: Key metrics (risk scores, confidence levels, etc.)
- 🔧 **Tool Results**: Which tools were used and their outcomes
- ⚠️ **Errors/Warnings**: Any issues encountered
- 💾 **Full Results**: Complete output (saved to file if specified)

##### Example Agent Testing Workflow
```bash
# 1. Test all agents with the same application
python -m mortgage_ai_processing.cli agents test document_agent -f e2e_application.json -o doc_results.json
python -m mortgage_ai_processing.cli agents test credit_agent -f e2e_application.json -o credit_results.json
python -m mortgage_ai_processing.cli agents test income_agent -f e2e_application.json -o income_results.json
python -m mortgage_ai_processing.cli agents test property_agent -f e2e_application.json -o property_results.json
python -m mortgage_ai_processing.cli agents test risk_agent -f e2e_application.json -o risk_results.json
python -m mortgage_ai_processing.cli agents test underwriting_agent -f e2e_application.json -o underwriting_results.json

# 2. Compare results across agents
type doc_results.json
type credit_results.json
# ... etc
```

## 2.1. Unified Tool Testing with CLI

### Universal Tool Call Command

I've added a unified `tools call` command that works with ANY tool in the system, similar to the OCR command:

```bash
# Generic syntax
python -m mortgage_ai_processing.cli tools call TOOL_NAME --params 'JSON_PARAMETERS'
```

### Step 1: Discover Available Tools
```bash
# List all available tools
python -m mortgage_ai_processing.cli tools list

# Get parameter schema for any tool
python -m mortgage_ai_processing.cli tools call TOOL_NAME --show-schema
```

### Step 2: Test Any Tool

#### Address Proof Validator
```bash
# Get parameter schema first
python -m mortgage_ai_processing.cli tools call address_proof_validator --show-schema

# Test utility bill validation
python -m mortgage_ai_processing.cli tools call address_proof_validator \
  --params '{
    "document_id": "test-utility-001",
    "document_type": "utility_bill",
    "extracted_text": "Pacific Gas & Electric Company\nService Address: 123 Main Street, San Francisco, CA 94102\nAccount Number: 1234567890\nCustomer Name: John Doe\nBill Date: 10/15/2024\nAmount Due: $125.50",
    "applicant_name": "John Doe",
    "expected_address": "123 Main Street, San Francisco, CA 94102"
  }' \
  --output address_validation_results.json

# Test bank statement validation
python -m mortgage_ai_processing.cli tools call address_proof_validator \
  --params '{
    "document_id": "test-bank-001",
    "document_type": "bank_statement",
    "extracted_text": "Bank of America\nAccount Holder: Jane Smith\nMailing Address: 456 Oak Avenue, Los Angeles, CA 90210\nStatement Date: 10/01/2024",
    "applicant_name": "Jane Smith"
  }'
```

#### Credit Score Analyzer
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call credit_score_analyzer --show-schema

# Test credit analysis
python -m mortgage_ai_processing.cli tools call credit_score_analyzer \
  --params '{
    "applicant_id": "test-001",
    "credit_report_data": {
      "credit_score": 720,
      "payment_history": "good",
      "credit_utilization": 0.25,
      "length_of_credit_history": 8,
      "credit_mix": "good",
      "new_credit_inquiries": 2
    }
  }'
```

#### DTI Calculator
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call dti_calculator --show-schema

# Test DTI calculation
python -m mortgage_ai_processing.cli tools call dti_calculator \
  --params '{
    "applicant_id": "test-001",
    "monthly_income": 8000,
    "monthly_debt_payments": 2200,
    "proposed_mortgage_payment": 1800
  }'
```

#### Property Value Estimator
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call property_value_estimator --show-schema

# Test property valuation
python -m mortgage_ai_processing.cli tools call property_value_estimator \
  --params '{
    "property_id": "test-prop-001",
    "address": "123 Main Street, San Francisco, CA 94102",
    "property_type": "Single Family Home",
    "square_footage": 2000,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 1995
  }'
```

#### LTV Calculator
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call ltv_calculator --show-schema

# Test LTV calculation
python -m mortgage_ai_processing.cli tools call ltv_calculator \
  --params '{
    "loan_amount": 400000,
    "property_value": 500000,
    "property_id": "test-prop-001"
  }'
```

#### Income Calculator
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call income_calculator --show-schema

# Test income calculation
python -m mortgage_ai_processing.cli tools call income_calculator \
  --params '{
    "applicant_id": "test-001",
    "employment_income": 75000,
    "bonus_income": 10000,
    "other_income": 5000,
    "employment_type": "W2"
  }'
```

#### KYC Risk Scorer
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call kyc_risk_scorer --show-schema

# Test KYC risk scoring
python -m mortgage_ai_processing.cli tools call kyc_risk_scorer \
  --params '{
    "applicant_id": "test-001",
    "identity_verification_status": "verified",
    "address_verification_status": "verified",
    "employment_verification_status": "verified",
    "income_verification_status": "verified",
    "credit_check_status": "completed"
  }'
```

#### Fraud Detection Analyzer
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call fraud_detection_analyzer --show-schema

# Test fraud detection
python -m mortgage_ai_processing.cli tools call fraud_detection_analyzer \
  --params '{
    "applicant_id": "test-001",
    "application_data": {
      "income_stated": 75000,
      "employment_duration": 24,
      "previous_addresses": 2,
      "credit_inquiries_recent": 3
    },
    "document_analysis": {
      "document_authenticity_score": 0.95,
      "consistency_score": 0.88
    }
  }'
```

#### Loan Decision Engine
```bash
# Get schema
python -m mortgage_ai_processing.cli tools call loan_decision_engine --show-schema

# Test loan decision
python -m mortgage_ai_processing.cli tools call loan_decision_engine \
  --params '{
    "application_id": "test-001",
    "credit_score": 720,
    "dti_ratio": 0.35,
    "ltv_ratio": 0.80,
    "income_verification": "verified",
    "employment_verification": "verified",
    "asset_verification": "verified"
  }'
```

### Expected Agent Information
Each agent should show:
- Agent name and ID
- Associated tools count
- Tool names and descriptions
- Current state

## 3. Individual Tool Testing

### Document Processing Tools

#### OCR Document Extractor
```bash
# Basic OCR extraction
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "test-doc-001" \
  --output ocr_results.json

# Test with passport document
python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt \
  --document-id "passport-test" \
  --output passport_results.json
```

#### List All Available Tools
```bash
# Get comprehensive tool inventory
python -m mortgage_ai_processing.cli tools list
```

#### Complete Tool Testing Examples

#### Document Tools
```bash
# Document OCR Extractor (existing command)
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf --output ocr_results.json

# Document Classifier (Azure Document Intelligence)
python -m mortgage_ai_processing.cli tools call document_classifier --show-schema

# INTELLIGENT MODE: Process entire mortgage application (processes all documents automatically)
python -m mortgage_ai_processing.cli tools call document_classifier \
  --params-file e2e_application.json \
  --params '{"mortgage_application": $(cat e2e_application.json), "process_all_documents": true}' \
  --output batch_classification_results.json

# SINGLE DOCUMENT MODE: Test with individual document file
python -m mortgage_ai_processing.cli tools call document_classifier \
  --params '{"document_id": "test-001", "document_path": "test_documents/sample.pdf", "use_prebuilt_models": true}'

# Test with document URL
python -m mortgage_ai_processing.cli tools call document_classifier \
  --params '{"document_id": "test-002", "document_url": "https://example.com/document.pdf"}'

# Test with extracted text (fallback mode)
python -m mortgage_ai_processing.cli tools call document_classifier \
  --params '{"document_id": "test-003", "extracted_text": "Bank of America Statement Account Number: 1234567890..."}'

# Identity Validator
python -m mortgage_ai_processing.cli tools call identity_validator --show-schema
python -m mortgage_ai_processing.cli tools call identity_validator \
  --params '{"document_id": "test-001", "document_type": "passport", "extracted_text": "Passport details..."}'
```

#### Credit Tools
```bash
# Credit History Analyzer
python -m mortgage_ai_processing.cli tools call credit_history_analyzer --show-schema
python -m mortgage_ai_processing.cli tools call credit_history_analyzer \
  --params '{"applicant_id": "test-001", "credit_report": {"accounts": [], "inquiries": []}}'
```

#### Income Tools
```bash
# Employment Verification
python -m mortgage_ai_processing.cli tools call employment_verification --show-schema
python -m mortgage_ai_processing.cli tools call employment_verification \
  --params '{"applicant_id": "test-001", "employer_name": "ABC Corp", "employment_duration": 24}'

# Income Consistency Checker
python -m mortgage_ai_processing.cli tools call income_consistency_checker --show-schema
python -m mortgage_ai_processing.cli tools call income_consistency_checker \
  --params '{"applicant_id": "test-001", "stated_income": 75000, "verified_income": 73000}'
```

#### Property Tools
```bash
# Property Risk Analyzer
python -m mortgage_ai_processing.cli tools call property_risk_analyzer --show-schema
python -m mortgage_ai_processing.cli tools call property_risk_analyzer \
  --params '{"property_id": "test-001", "location": "San Francisco, CA", "property_type": "Condo"}'
```

#### Risk Tools
```bash
# PEP Sanctions Checker
python -m mortgage_ai_processing.cli tools call pep_sanctions_checker --show-schema
python -m mortgage_ai_processing.cli tools call pep_sanctions_checker \
  --params '{"applicant_id": "test-001", "full_name": "John Doe", "date_of_birth": "1985-01-01"}'
```

#### Underwriting Tools
```bash
# Loan Terms Calculator
python -m mortgage_ai_processing.cli tools call loan_terms_calculator --show-schema
python -m mortgage_ai_processing.cli tools call loan_terms_calculator \
  --params '{"loan_amount": 400000, "interest_rate": 6.5, "loan_term_years": 30}'

# Loan Letter Generator
python -m mortgage_ai_processing.cli tools call loan_letter_generator --show-schema
python -m mortgage_ai_processing.cli tools call loan_letter_generator \
  --params '{"application_id": "test-001", "decision": "approved", "loan_terms": {}}'
```

## 4. System Administration Testing

### Health Checks
```bash
# Check overall system health
python -m mortgage_ai_processing.cli system health
```

### System Information
```bash
# Get comprehensive system information
python -m mortgage_ai_processing.cli system info
```

### Cleanup Operations
```bash
# Clean up old workflows (default: 24 hours)
python -m mortgage_ai_processing.cli system cleanup

# Clean up workflows older than specific hours
python -m mortgage_ai_processing.cli system cleanup --hours 48
```

## 5. MCP Server Testing

### Start MCP Server
```bash
# Start on default port (8000)
python -m mortgage_ai_processing.cli mcp serve

# Start on custom port
python -m mortgage_ai_processing.cli mcp serve --port 8080 --host 0.0.0.0
```

### Send MCP Requests
```bash
# List available tools via MCP
python -m mortgage_ai_processing.cli mcp request "tools/list"

# Call specific tool via MCP
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "mcp-test"}}'
```

## 6. Comprehensive Testing Scenarios

### Scenario A: Complete Document-to-Decision Pipeline
```bash
# Step 1: Extract document data
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "pipeline-001" \
  --output extracted_data.json

# Step 2: Process complete workflow
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output pipeline_results.json

# Step 3: Verify system health
python -m mortgage_ai_processing.cli system health
```

### Scenario B: Multi-Document Processing
```bash
# Process multiple documents
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "doc-1" --output doc1_results.json

python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt \
  --document-id "doc-2" --output doc2_results.json

# Process application with multiple document references
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output multi_doc_results.json
```

### Scenario C: Performance Testing
```bash
# Time complete workflow processing
echo "Starting performance test..."
$start = Get-Date

python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output perf_results.json

$end = Get-Date
$duration = $end - $start
echo "Processing time: $($duration.TotalSeconds) seconds"
```

### Scenario D: Concurrent Processing
```bash
# Run multiple workflows simultaneously
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output concurrent1_results.json &

python -m mortgage_ai_processing.cli workflow process \
  --application-file custom_application.json \
  --workflow-type parallel \
  --output concurrent2_results.json &

# Wait for completion and check results
wait
python -m mortgage_ai_processing.cli workflow list
```

## 7. Error Testing and Troubleshooting

### Test Error Handling
```bash
# Test with non-existent file
python -m mortgage_ai_processing.cli tools ocr non_existent_file.pdf

# Test with invalid workflow type
python -m mortgage_ai_processing.cli workflow process --workflow-type invalid

# Test with malformed application file
echo '{"invalid": "json"}' > invalid_app.json
python -m mortgage_ai_processing.cli workflow process --application-file invalid_app.json
```

### Enable Verbose Logging
```bash
# Enable detailed logging for debugging
python -m mortgage_ai_processing.cli --verbose tools ocr test_documents/sample.pdf
python -m mortgage_ai_processing.cli --verbose workflow process
python -m mortgage_ai_processing.cli --verbose system health
```

## 8. Expected Results and Validation

### Successful Workflow Processing
Expected output structure:
```json
{
  "execution_id": "exec_[timestamp]",
  "status": "COMPLETED",
  "progress": 100,
  "loan_decision": {
    "decision": "APPROVED|DENIED|CONDITIONAL",
    "overall_score": 0.75,
    "decision_factors": {
      "eligibility_score": 0.8,
      "risk_score": 0.3,
      "compliance_score": 0.9,
      "policy_score": 0.85
    },
    "conditions": [],
    "adverse_actions": [],
    "decision_rationale": "..."
  },
  "agent_results": {
    "document_agent": {...},
    "credit_agent": {...},
    "income_agent": {...},
    "property_agent": {...},
    "risk_agent": {...},
    "underwriting_agent": {...}
  }
}
```

### Validation Checklist

#### ✅ System Health
- [ ] All agents loaded successfully
- [ ] All tools registered and accessible
- [ ] No critical errors in health check
- [ ] System info shows correct component counts

#### ✅ Document Processing
- [ ] OCR extraction completes successfully
- [ ] Confidence scores are reasonable (>0.5 for mock data)
- [ ] Key-value pairs extracted
- [ ] Document metadata properly recorded

#### ✅ Workflow Processing
- [ ] Application processes without errors
- [ ] All workflow steps complete
- [ ] Execution ID generated and trackable
- [ ] Processing timestamps recorded
- [ ] Loan decision generated with valid scores

#### ✅ Agent Integration
- [ ] All 6 agents respond successfully
- [ ] Tools execute without errors
- [ ] Agent results contain expected data structures
- [ ] No agent timeouts or failures

#### ✅ Tool Functionality
- [ ] Individual tools can be called directly
- [ ] Tool parameters schemas are valid
- [ ] Tool results contain expected data
- [ ] Error handling works for invalid inputs

## 9. Performance Benchmarks

### Expected Processing Times
- **Document OCR**: 2-5 seconds per document
- **Individual Tool**: 0.5-2 seconds per tool
- **Complete Workflow**: 10-30 seconds (parallel), 20-60 seconds (standard)
- **System Health Check**: <1 second

### Resource Usage
Monitor during testing:
- Memory usage should remain stable
- CPU usage spikes during processing but returns to baseline
- No memory leaks during repeated operations

## 10. Common Issues and Solutions

### Issue: Azure Credentials Not Configured
**Symptom**: OCR tool falls back to mock extraction
**Solution**: 
```bash
# Verify .env file exists and contains credentials
type .env
# Should contain:
# AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=...
# AZURE_DOCUMENT_INTELLIGENCE_API_KEY=...
```

### Issue: Import Errors
**Symptom**: ModuleNotFoundError when running CLI
**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify Python path
python -c "import sys; print(sys.path)"
```

### Issue: Workflow Processing Fails
**Symptom**: Workflow exits with errors
**Solution**:
```bash
# Enable verbose logging to see detailed error messages
python -m mortgage_ai_processing.cli --verbose workflow process \
  --application-file e2e_application.json

# Check system health for component issues
python -m mortgage_ai_processing.cli system health
```

### Issue: File Permission Errors
**Symptom**: Cannot write output files
**Solution**:
```bash
# Ensure write permissions in current directory
# On Windows, run as administrator if needed
# Check available disk space
```

## 11. Advanced Testing

### Custom Test Scripts
Create custom Python scripts for specific testing scenarios:

```python
# test_custom_workflow.py
import asyncio
import json
from mortgage_ai_processing.workflow_orchestrator import process_mortgage_application_simple
from mortgage_ai_processing.models.core import MortgageApplication

async def test_custom_workflow():
    # Load application
    with open('e2e_application.json', 'r') as f:
        app_data = json.load(f)
    
    application = MortgageApplication(**app_data)
    
    # Process workflow
    execution, decision = await process_mortgage_application_simple(
        application, use_parallel_processing=True
    )
    
    print(f"Decision: {decision.decision}")
    print(f"Overall Score: {decision.overall_score}")
    
    return execution, decision

# Run test
asyncio.run(test_custom_workflow())
```

### Integration Testing
Test integration with external systems:
```bash
# Test MCP server integration
python -m mortgage_ai_processing.cli mcp serve --port 8000 &
sleep 5
python -m mortgage_ai_processing.cli mcp request "tools/list"
```

## 12. Automated Testing Scripts

### Windows Batch Script
Create `run_all_tests.bat`:
```batch
@echo off
echo Starting comprehensive testing...

echo Testing system health...
python -m mortgage_ai_processing.cli system health

echo Testing document OCR...
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf --output test_ocr.json

echo Testing workflow processing...
python -m mortgage_ai_processing.cli workflow process --application-file e2e_application.json --output test_workflow.json

echo Testing agent status...
python -m mortgage_ai_processing.cli agents status

echo Testing tool listing...
python -m mortgage_ai_processing.cli tools list

echo All tests completed!
pause
```

### PowerShell Script
Create `run_all_tests.ps1`:
```powershell
Write-Host "Starting comprehensive testing..." -ForegroundColor Green

Write-Host "Testing system health..." -ForegroundColor Yellow
python -m mortgage_ai_processing.cli system health

Write-Host "Testing document OCR..." -ForegroundColor Yellow
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf --output test_ocr.json

Write-Host "Testing workflow processing..." -ForegroundColor Yellow
python -m mortgage_ai_processing.cli workflow process --application-file e2e_application.json --output test_workflow.json

Write-Host "Testing agent status..." -ForegroundColor Yellow
python -m mortgage_ai_processing.cli agents status

Write-Host "All tests completed successfully!" -ForegroundColor Green
```

## Conclusion

This comprehensive testing guide ensures thorough validation of the Mortgage AI Processing System. Regular execution of these tests helps maintain system reliability and identifies issues early in the development cycle.

For production deployment, consider implementing automated test suites that run these CLI commands and validate outputs programmatically.