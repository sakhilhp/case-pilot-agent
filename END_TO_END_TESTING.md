# End-to-End Testing: Document to Loan Decision

This guide walks you through testing the complete mortgage processing pipeline, starting with document extraction and ending with a loan decision.

## Overview

The end-to-end process follows this flow:
1. **Document Processing** - Extract data from mortgage documents using OCR
2. **Data Integration** - Use extracted data to create/enhance mortgage application
3. **Workflow Processing** - Run complete mortgage processing workflow
4. **Decision Generation** - Get final loan decision with risk assessment

## Step-by-Step End-to-End Testing

### Step 1: Document Extraction and Analysis

First, let's extract data from available documents and see what information we can gather:

```bash
# Test OCR extraction on the sample PDF
python -m mortgage_ai_processing.cli tools call document_ocr_extractor \
  --params '{"document_path": "test_documents/sample.pdf", "document_id": "e2e-pdf-001"}' \
  --output "extracted_pdf_data.json"

# Test OCR extraction on the passport document  
python -m mortgage_ai_processing.cli tools call document_ocr_extractor \
  --params '{"document_path": "test_documents/sample_passport.txt", "document_id": "e2e-passport-001"}' \
  --output "extracted_passport_data.json"
```

**Expected Results:**
- Two JSON files with extracted document data
- Confidence scores and extracted text
- Key-value pairs identified from documents
- Document metadata and processing information

### Step 2: Review Extracted Data

Check what data was extracted from your documents:

```bash
# View the extracted data (Windows)
type extracted_pdf_data.json
type extracted_passport_data.json

# Or use PowerShell
Get-Content extracted_pdf_data.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
Get-Content extracted_passport_data.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

Look for key information like:
- Names and personal identifiers
- Addresses
- Income information
- Employment details
- Financial data

### Step 3: Create Enhanced Application with Document Data

Based on the extracted document data, create a comprehensive mortgage application. Here's a template that incorporates typical document-extracted information:

```json
{
  "application_id": "E2E-TEST-001",
  "borrower_info": {
    "first_name": "John",
    "last_name": "Doe",
    "ssn": "123-45-6789",
    "date_of_birth": "1985-01-01T00:00:00",
    "email": "john.doe@example.com",
    "phone": "555-123-4567",
    "current_address": "123 Main St, Anytown, ST 12345",
    "employment_status": "Employed",
    "annual_income": "75000",
    "employer_name": "ABC Corporation",
    "job_title": "Software Engineer",
    "employment_start_date": "2020-01-01T00:00:00"
  },
  "property_info": {
    "address": "456 Oak Avenue, Testville, ST 67890",
    "property_type": "Single Family Home",
    "property_value": "300000",
    "property_use": "Primary Residence",
    "year_built": 2010
  },
  "loan_details": {
    "loan_amount": "240000",
    "loan_type": "conventional",
    "loan_term_years": 30,
    "down_payment": "60000",
    "purpose": "Purchase",
    "interest_rate": 6.5
  },
  "documents": [
    {
      "document_id": "e2e-pdf-001",
      "document_type": "income_verification",
      "file_path": "test_documents/sample.pdf",
      "extraction_status": "completed"
    },
    {
      "document_id": "e2e-passport-001", 
      "document_type": "identity_verification",
      "file_path": "test_documents/sample_passport.txt",
      "extraction_status": "completed"
    }
  ],
  "processing_status": "pending",
  "credit_score": 720,
  "debt_to_income_ratio": 0.28,
  "assets": {
    "checking_account": 25000,
    "savings_account": 45000,
    "retirement_accounts": 85000
  }
}
```

Save this as `e2e_application.json`.

### Step 4: Process Complete Workflow

Now run the complete mortgage processing workflow with your enhanced application:

```bash
# Process the application through the complete workflow
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output "e2e_workflow_results.json"
```

**What This Tests:**
- Document processing integration
- Credit analysis tools
- Income verification tools
- Property valuation tools
- Risk assessment tools
- Underwriting decision engine
- Complete workflow orchestration

### Step 5: Analyze Results

Review the comprehensive results:

```bash
# View the complete workflow results
type e2e_workflow_results.json

# Or for formatted output in PowerShell
Get-Content e2e_workflow_results.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Key Results to Validate:**
- **Execution Status**: Should be "COMPLETED"
- **Loan Decision**: APPROVED/DENIED/CONDITIONAL
- **Risk Scores**: Overall risk assessment
- **Conditions**: Any conditions for approval
- **Processing Time**: Start and completion timestamps
- **Agent Results**: Individual tool outputs

### Step 6: Verify Individual Tool Results

Test specific tools that would have been used in the workflow:

```bash
# List all tools to see what was available
python -m mortgage_ai_processing.cli tools list

# Get information about key tools used
python -m mortgage_ai_processing.cli tools info document_ocr_extractor
python -m mortgage_ai_processing.cli tools info credit_score_analyzer
python -m mortgage_ai_processing.cli tools info dti_calculator
```

### Step 7: Check System Health and Agent Status

Verify the system processed everything correctly:

```bash
# Check overall system health
python -m mortgage_ai_processing.cli system health

# Check agent status
python -m mortgage_ai_processing.cli agents status

# Get system information
python -m mortgage_ai_processing.cli system info
```

## Advanced End-to-End Testing Scenarios

### Scenario A: Multiple Document Types

Test with various document types to simulate a real mortgage application:

```bash
# Create multiple document extractions
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "paystub-001" --output "paystub_data.json"

python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt \
  --document-id "identity-001" --output "identity_data.json"

# Process application with multiple document references
# (Update e2e_application.json to include both documents)
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output "multi_doc_results.json"
```

### Scenario B: Error Handling Testing

Test how the system handles problematic scenarios:

```bash
# Test with missing document
python -m mortgage_ai_processing.cli tools ocr non_existent_file.pdf

# Test with incomplete application data
# (Create incomplete_application.json with missing required fields)
python -m mortgage_ai_processing.cli workflow process \
  --application-file incomplete_application.json \
  --workflow-type parallel
```

### Scenario C: Performance Testing

Test system performance with the complete pipeline:

```bash
# Time the complete end-to-end process
echo "Starting end-to-end performance test..."
$start = Get-Date

# Document processing
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "perf-test-001" --output "perf_doc_data.json"

# Workflow processing  
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output "perf_workflow_results.json"

$end = Get-Date
$duration = $end - $start
echo "Total processing time: $($duration.TotalSeconds) seconds"
```

## Validation Checklist

After running the end-to-end test, verify these outcomes:

### ✅ Document Processing
- [ ] OCR extraction completed successfully
- [ ] Confidence scores are reasonable (>0.5 for mock data)
- [ ] Key-value pairs extracted from documents
- [ ] Document metadata properly recorded

### ✅ Workflow Processing  
- [ ] Application processed without errors
- [ ] All workflow steps completed
- [ ] Execution ID generated and trackable
- [ ] Processing timestamps recorded

### ✅ Decision Engine
- [ ] Loan decision generated (APPROVED/DENIED/CONDITIONAL)
- [ ] Risk scores calculated
- [ ] Decision factors provided
- [ ] Conditions or adverse actions listed if applicable

### ✅ System Integration
- [ ] All agents responded successfully
- [ ] Tools executed without errors
- [ ] System health check passes
- [ ] No critical errors in logs

## Expected End-to-End Results

For a successful end-to-end test with the sample data, you should see:

```json
{
  "execution_id": "exec_[timestamp]",
  "status": "COMPLETED", 
  "progress": 100,
  "loan_decision": {
    "decision": "APPROVED" or "CONDITIONAL",
    "overall_score": 0.75-0.85,
    "risk_score": 0.2-0.4,
    "conditions": [...],
    "adverse_actions": []
  },
  "processing_time": {
    "started_at": "[timestamp]",
    "completed_at": "[timestamp]"
  }
}
```

## Troubleshooting Common Issues

### Issue: OCR Extraction Fails
```bash
# Check if file exists and is readable
dir test_documents\sample.pdf
# Verify Azure credentials in .env file
type .env
```

### Issue: Workflow Processing Errors
```bash
# Enable verbose logging
python -m mortgage_ai_processing.cli --verbose workflow process \
  --application-file e2e_application.json
```

### Issue: Missing Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt
```

## Real-World Testing Tips

1. **Use Realistic Data**: Replace sample data with realistic mortgage application information
2. **Test Edge Cases**: Try applications with high DTI ratios, low credit scores, etc.
3. **Document Variations**: Test with different document formats and quality levels
4. **Concurrent Processing**: Run multiple applications simultaneously
5. **Monitor Performance**: Track processing times and resource usage

This end-to-end testing approach ensures your mortgage processing system works correctly from document intake through final loan decision.