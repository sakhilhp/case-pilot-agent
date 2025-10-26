# Mortgage AI Processing System - CLI Testing Guide

## Overview

This guide provides step-by-step instructions for testing all tools and functionality in the Mortgage AI Processing System using the command-line interface (CLI). The system includes workflow orchestration, document processing, risk analysis, and various specialized tools for mortgage application processing.

## Prerequisites

### 1. Environment Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
# Ensure .env file contains:
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-api-key
```

### 2. Verify Installation
```bash
# Check if CLI is accessible
python -m mortgage_ai_processing.cli --help

# Alternative method
python mortgage_ai_processing/cli.py --help
```

## CLI Command Structure

The CLI is organized into the following main command groups:
- `workflow` - Workflow management and processing
- `tools` - Individual tool operations
- `agents` - Agent management and information
- `mcp` - MCP server operations
- `system` - System administration and health checks

## Testing Individual Tools

### 1. Document OCR Extraction Tool

#### Basic OCR Testing
```bash
# Test OCR with sample PDF document
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf

# Test with custom document ID and output file
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "test-doc-001" \
  --output "ocr_results.json"
```

#### Expected Output
- Document ID and processing confirmation
- Extraction summary with confidence scores
- Text length and structure information
- Key-value pairs found
- Tables detected
- Sample extracted text preview

#### Testing Different Document Types
```bash
# Test with passport/ID document (uses mock data if no real passport)
python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt \
  --document-id "passport-test"

# Test with different output formats
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --output "detailed_results.json"
```

### 2. List All Available Tools
```bash
# Get comprehensive list of all tools in the system
python -m mortgage_ai_processing.cli tools list
```

#### Expected Output
- Complete tool inventory with descriptions
- Tool domains (document, credit, income, property, risk, underwriting)
- Associated agents for each tool

### 3. Get Tool Information
```bash
# Get detailed information about specific tools
python -m mortgage_ai_processing.cli tools info document_ocr_extractor
python -m mortgage_ai_processing.cli tools info credit_score_analyzer
python -m mortgage_ai_processing.cli tools info dti_calculator
```

#### Expected Output
- Tool name and description
- Parameters schema
- Associated agent information

## Testing Workflow Processing

### 1. Process Sample Application
```bash
# Process with default sample application (parallel workflow)
python -m mortgage_ai_processing.cli workflow process

# Process with standard workflow
python -m mortgage_ai_processing.cli workflow process --workflow-type standard

# Save results to file
python -m mortgage_ai_processing.cli workflow process \
  --workflow-type parallel \
  --output "workflow_results.json"
```

#### Expected Output
- Application ID and processing confirmation
- Workflow execution details
- Loan decision with scores and conditions
- Processing timestamps
- Risk assessment results

### 2. Create Custom Application File
Create a JSON file with mortgage application data:

```json
{
  "application_id": "TEST-APP-001",
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
    "loan_type": "CONVENTIONAL",
    "loan_term_years": 30,
    "down_payment": 70000,
    "purpose": "Purchase"
  },
  "documents": [],
  "processing_status": "PENDING"
}
```

Save as `custom_application.json` and test:
```bash
python -m mortgage_ai_processing.cli workflow process \
  --application-file custom_application.json \
  --workflow-type parallel \
  --output "custom_results.json"
```

### 3. Workflow Management
```bash
# List active workflows
python -m mortgage_ai_processing.cli workflow list

# Check workflow status (use execution ID from previous commands)
python -m mortgage_ai_processing.cli workflow status EXECUTION-ID-HERE

# Cancel a running workflow
python -m mortgage_ai_processing.cli workflow cancel EXECUTION-ID-HERE
```

## Testing Agent System

### 1. List All Agents
```bash
# Get complete agent inventory
python -m mortgage_ai_processing.cli agents list
```

#### Expected Output
- Agent names and IDs
- Tool counts per agent
- Tool names associated with each agent

### 2. Agent Information and Status
```bash
# Get detailed agent information
python -m mortgage_ai_processing.cli agents info AGENT-ID

# Check status of all agents
python -m mortgage_ai_processing.cli agents status
```

## Testing MCP Server Operations

### 1. Start MCP Server
```bash
# Start MCP server on default port (8000)
python -m mortgage_ai_processing.cli mcp serve

# Start on custom port and host
python -m mortgage_ai_processing.cli mcp serve --port 8080 --host 0.0.0.0
```

### 2. Send MCP Requests
```bash
# Send basic MCP request
python -m mortgage_ai_processing.cli mcp request "tools/list"

# Send request with parameters
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "mcp-test"}}'
```

## System Administration Testing

### 1. Health Checks
```bash
# Check overall system health
python -m mortgage_ai_processing.cli system health
```

#### Expected Output
- System status (healthy/unhealthy)
- Component status
- Error details if any issues

### 2. System Information
```bash
# Get comprehensive system information
python -m mortgage_ai_processing.cli system info
```

#### Expected Output
- System name and version
- Agent count and names
- Tool count and names
- Workflow types available

### 3. Cleanup Operations
```bash
# Clean up workflows older than 24 hours (default)
python -m mortgage_ai_processing.cli system cleanup

# Clean up workflows older than specific hours
python -m mortgage_ai_processing.cli system cleanup --hours 48
```

## Comprehensive Testing Scenarios

### Scenario 1: Complete Document Processing Pipeline
```bash
# Step 1: Extract document data
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "pipeline-test-001" \
  --output "extracted_data.json"

# Step 2: Process application with extracted data
python -m mortgage_ai_processing.cli workflow process \
  --workflow-type parallel \
  --output "pipeline_results.json"

# Step 3: Check system health
python -m mortgage_ai_processing.cli system health
```

### Scenario 2: Tool Discovery and Testing
```bash
# Step 1: List all available tools
python -m mortgage_ai_processing.cli tools list

# Step 2: Get information about specific tools
python -m mortgage_ai_processing.cli tools info document_ocr_extractor

# Step 3: Test OCR tool with different documents
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf
python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt
```

### Scenario 3: Workflow Management Testing
```bash
# Step 1: Start multiple workflows
python -m mortgage_ai_processing.cli workflow process --workflow-type parallel &
python -m mortgage_ai_processing.cli workflow process --workflow-type standard &

# Step 2: List active workflows
python -m mortgage_ai_processing.cli workflow list

# Step 3: Check individual workflow status
python -m mortgage_ai_processing.cli workflow status EXECUTION-ID

# Step 4: Clean up completed workflows
python -m mortgage_ai_processing.cli system cleanup
```

## Error Testing and Troubleshooting

### 1. Test Error Handling
```bash
# Test with non-existent file
python -m mortgage_ai_processing.cli tools ocr non_existent_file.pdf

# Test with invalid workflow type
python -m mortgage_ai_processing.cli workflow process --workflow-type invalid

# Test with invalid execution ID
python -m mortgage_ai_processing.cli workflow status invalid-id
```

### 2. Verbose Logging
```bash
# Enable verbose logging for debugging
python -m mortgage_ai_processing.cli --verbose tools ocr test_documents/sample.pdf
python -m mortgage_ai_processing.cli --verbose workflow process
```

## Performance Testing

### 1. Timing Tests
```bash
# Time OCR processing
time python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf

# Time workflow processing
time python -m mortgage_ai_processing.cli workflow process
```

### 2. Concurrent Processing
```bash
# Run multiple OCR processes simultaneously
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf --document-id "concurrent-1" &
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf --document-id "concurrent-2" &
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf --document-id "concurrent-3" &
wait
```

## Expected Results and Validation

### 1. Successful OCR Processing
- ✅ Document processed successfully
- ✅ Confidence scores > 0.8 for mock data
- ✅ Text extraction with reasonable length
- ✅ Key-value pairs identified
- ✅ JSON output files created when specified

### 2. Successful Workflow Processing
- ✅ Application processed through complete pipeline
- ✅ Loan decision generated with scores
- ✅ Risk assessment completed
- ✅ Processing timestamps recorded
- ✅ Execution ID generated for tracking

### 3. System Health Indicators
- ✅ All agents loaded successfully
- ✅ All tools registered and accessible
- ✅ No critical errors in health check
- ✅ MCP server starts without issues

## Common Issues and Solutions

### Issue 1: Azure Credentials Not Configured
**Symptom**: OCR tool falls back to mock extraction
**Solution**: Verify .env file contains correct Azure credentials

### Issue 2: Import Errors
**Symptom**: ModuleNotFoundError when running CLI
**Solution**: Ensure all dependencies installed via `pip install -r requirements.txt`

### Issue 3: File Not Found Errors
**Symptom**: Document processing fails with file not found
**Solution**: Verify file paths are correct and files exist in test_documents/

### Issue 4: Permission Errors
**Symptom**: Cannot write output files
**Solution**: Ensure write permissions in current directory

## Advanced Testing

### 1. Custom Tool Testing
Create custom test scripts to validate specific tool functionality:

```python
# test_custom_tool.py
import asyncio
from mortgage_ai_processing.tools.document.ocr_extractor import DocumentOCRExtractor

async def test_ocr_tool():
    tool = DocumentOCRExtractor()
    result = await tool.execute(
        document_path="test_documents/sample.pdf",
        document_id="custom-test",
        analysis_features=["ocr_read", "tables"]
    )
    print(f"Success: {result.success}")
    print(f"Data: {result.data}")

asyncio.run(test_ocr_tool())
```

### 2. Integration Testing
Test complete workflows with real-world scenarios and validate end-to-end functionality.

## Conclusion

This testing guide covers comprehensive CLI testing for the Mortgage AI Processing System. Regular execution of these tests ensures system reliability and helps identify issues early in the development cycle. For automated testing, consider creating shell scripts that execute these commands in sequence and validate outputs.