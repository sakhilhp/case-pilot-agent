# CLI Comprehensive Test Plan
## Mortgage AI Processing System

### Overview
This test plan covers comprehensive testing of the mortgage AI processing system through CLI interface, including end-to-end testing, individual agent testing, and individual tool testing scenarios.

## Test Categories

### 1. End-to-End Testing Scenarios

#### E2E-001: Complete Mortgage Processing Pipeline
**Objective**: Test the complete mortgage application processing from document intake to loan decision

**Test Steps**:
```bash
# Step 1: Document extraction
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "e2e-001-pdf" \
  --output "e2e_001_pdf_data.json"

python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt \
  --document-id "e2e-001-passport" \
  --output "e2e_001_passport_data.json"

# Step 2: Process complete workflow with extracted data
python -m mortgage_ai_processing.cli workflow process \
  --application-file e2e_application.json \
  --workflow-type parallel \
  --output "e2e_001_results.json"

# Step 3: Verify system health
python -m mortgage_ai_processing.cli system health
```

**Expected Results**:
- Document extraction completes successfully
- Workflow processes all agents (6 agents)
- Loan decision generated (APPROVED/DENIED/CONDITIONAL)
- Risk scores calculated
- Processing time recorded
- System health shows no errors

#### E2E-002: Sequential vs Parallel Workflow Comparison
**Objective**: Compare performance and results between sequential and parallel processing

**Test Steps**:
```bash
# Test sequential workflow
echo "Testing Sequential Workflow..."
$start = Get-Date
python -m mortgage_ai_processing.cli workflow process \
  --workflow-type standard \
  --output "e2e_002_sequential.json"
$end = Get-Date
$sequential_time = ($end - $start).TotalSeconds

# Test parallel workflow
echo "Testing Parallel Workflow..."
$start = Get-Date
python -m mortgage_ai_processing.cli workflow process \
  --workflow-type parallel \
  --output "e2e_002_parallel.json"
$end = Get-Date
$parallel_time = ($end - $start).TotalSeconds

echo "Sequential time: $sequential_time seconds"
echo "Parallel time: $parallel_time seconds"
```

**Expected Results**:
- Both workflows complete successfully
- Parallel processing should be faster
- Results should be consistent between both approaches
- All agents execute in both scenarios

#### E2E-003: Multi-Document Processing
**Objective**: Test processing with multiple document types

**Test Steps**:
```bash
# Create comprehensive application with multiple documents
# (Use custom JSON with multiple document references)

# Process multiple documents
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "multi-doc-paystub" --output "paystub_data.json"

python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt \
  --document-id "multi-doc-identity" --output "identity_data.json"

# Process workflow with multi-document application
python -m mortgage_ai_processing.cli workflow process \
  --application-file multi_document_application.json \
  --workflow-type parallel \
  --output "e2e_003_results.json"
```

**Expected Results**:
- All documents processed successfully
- Document data integrated into workflow
- Enhanced decision making with multiple data sources

### 2. Individual Agent Testing Scenarios

#### AGENT-001: Document Processing Agent Testing
**Objective**: Test document processing agent capabilities

**Test Steps**:
```bash
# List all agents to verify document agent exists
python -m mortgage_ai_processing.cli agents list

# Get document agent information
python -m mortgage_ai_processing.cli agents info doc_agent

# Test document agent tools individually
python -m mortgage_ai_processing.cli tools info document_ocr_extractor
python -m mortgage_ai_processing.cli tools info document_classifier
python -m mortgage_ai_processing.cli tools info document_validator

# Execute document processing tools
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "agent-test-doc"
```

**Expected Results**:
- Document agent listed with associated tools
- All document tools accessible and functional
- OCR extraction works with confidence scores
- Document classification and validation complete

#### AGENT-002: Income Verification Agent Testing
**Objective**: Test income verification agent and tools

**Test Steps**:
```bash
# Get income agent information
python -m mortgage_ai_processing.cli agents info income_agent

# Test income-related tools
python -m mortgage_ai_processing.cli tools info income_calculator
python -m mortgage_ai_processing.cli tools info employment_verifier
python -m mortgage_ai_processing.cli tools info dti_calculator

# Create income-focused test application
# Process workflow to trigger income agent
python -m mortgage_ai_processing.cli workflow process \
  --application-file income_test_application.json \
  --workflow-type parallel \
  --output "agent_002_results.json"
```

**Expected Results**:
- Income agent tools execute successfully
- DTI calculations accurate
- Employment verification completes
- Income assessment scores generated

#### AGENT-003: Credit Assessment Agent Testing
**Objective**: Test credit assessment agent functionality

**Test Steps**:
```bash
# Get credit agent information
python -m mortgage_ai_processing.cli agents info credit_agent

# Test credit tools
python -m mortgage_ai_processing.cli tools info credit_score_analyzer
python -m mortgage_ai_processing.cli tools info credit_history_evaluator
python -m mortgage_ai_processing.cli tools info debt_analyzer

# Process application with credit focus
python -m mortgage_ai_processing.cli workflow process \
  --application-file credit_test_application.json \
  --workflow-type parallel \
  --output "agent_003_results.json"
```

**Expected Results**:
- Credit tools execute without errors
- Credit scores calculated and analyzed
- Debt analysis completed
- Credit risk assessment generated

#### AGENT-004: Property Assessment Agent Testing
**Objective**: Test property assessment agent capabilities

**Test Steps**:
```bash
# Get property agent information
python -m mortgage_ai_processing.cli agents info property_agent

# Test property tools
python -m mortgage_ai_processing.cli tools info property_value_estimator
python -m mortgage_ai_processing.cli tools info appraisal_analyzer
python -m mortgage_ai_processing.cli tools info market_comparator

# Process property-focused application
python -m mortgage_ai_processing.cli workflow process \
  --application-file property_test_application.json \
  --workflow-type parallel \
  --output "agent_004_results.json"
```

**Expected Results**:
- Property valuation tools execute
- Market comparison analysis completed
- Appraisal data processed
- Property risk factors identified

#### AGENT-005: Risk Assessment Agent Testing
**Objective**: Test risk assessment agent functionality

**Test Steps**:
```bash
# Get risk agent information
python -m mortgage_ai_processing.cli agents info risk_agent

# Test risk tools
python -m mortgage_ai_processing.cli tools info risk_calculator
python -m mortgage_ai_processing.cli tools info fraud_detector
python -m mortgage_ai_processing.cli tools info compliance_checker

# Process high-risk scenario application
python -m mortgage_ai_processing.cli workflow process \
  --application-file high_risk_application.json \
  --workflow-type parallel \
  --output "agent_005_results.json"
```

**Expected Results**:
- Risk calculations completed
- Fraud detection analysis performed
- Compliance checks passed
- Overall risk score generated

#### AGENT-006: Underwriting Agent Testing
**Objective**: Test underwriting agent decision-making

**Test Steps**:
```bash
# Get underwriting agent information
python -m mortgage_ai_processing.cli agents info underwriting_agent

# Test underwriting tools
python -m mortgage_ai_processing.cli tools info underwriting_decision_engine
python -m mortgage_ai_processing.cli tools info condition_generator
python -m mortgage_ai_processing.cli tools info approval_calculator

# Process application for underwriting decision
python -m mortgage_ai_processing.cli workflow process \
  --application-file underwriting_test_application.json \
  --workflow-type parallel \
  --output "agent_006_results.json"
```

**Expected Results**:
- Underwriting decision generated
- Conditions listed if applicable
- Approval probability calculated
- Final loan decision provided

### 3. Individual Tool Testing Scenarios

#### TOOL-001: Document OCR Extractor Testing
**Objective**: Comprehensive testing of OCR extraction tool

**Test Steps**:
```bash
# Get tool information
python -m mortgage_ai_processing.cli tools info document_ocr_extractor

# Test with different document types
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "tool-001-pdf" --output "tool_001_pdf.json"

python -m mortgage_ai_processing.cli tools ocr test_documents/sample_passport.txt \
  --document-id "tool-001-txt" --output "tool_001_txt.json"

# Test error handling with non-existent file
python -m mortgage_ai_processing.cli tools ocr non_existent_file.pdf
```

**Expected Results**:
- Successful extraction from valid files
- Proper error handling for invalid files
- Confidence scores and metadata generated
- JSON output files created

#### TOOL-002: Credit Score Analyzer Testing
**Objective**: Test credit score analysis functionality

**Test Steps**:
```bash
# Get tool information
python -m mortgage_ai_processing.cli tools info credit_score_analyzer

# Test through workflow with different credit scenarios
python -m mortgage_ai_processing.cli workflow process \
  --application-file excellent_credit_application.json \
  --output "tool_002_excellent.json"

python -m mortgage_ai_processing.cli workflow process \
  --application-file poor_credit_application.json \
  --output "tool_002_poor.json"
```

**Expected Results**:
- Credit analysis completed for different scenarios
- Appropriate risk scores generated
- Credit factors identified

#### TOOL-003: DTI Calculator Testing
**Objective**: Test debt-to-income ratio calculations

**Test Steps**:
```bash
# Get tool information
python -m mortgage_ai_processing.cli tools info dti_calculator

# Test with various DTI scenarios
python -m mortgage_ai_processing.cli workflow process \
  --application-file low_dti_application.json \
  --output "tool_003_low_dti.json"

python -m mortgage_ai_processing.cli workflow process \
  --application-file high_dti_application.json \
  --output "tool_003_high_dti.json"
```

**Expected Results**:
- Accurate DTI calculations
- Proper risk assessment based on DTI
- Appropriate loan decisions

#### TOOL-004: Property Value Estimator Testing
**Objective**: Test property valuation functionality

**Test Steps**:
```bash
# Get tool information
python -m mortgage_ai_processing.cli tools info property_value_estimator

# Test with different property types
python -m mortgage_ai_processing.cli workflow process \
  --application-file single_family_application.json \
  --output "tool_004_single_family.json"

python -m mortgage_ai_processing.cli workflow process \
  --application-file condo_application.json \
  --output "tool_004_condo.json"
```

**Expected Results**:
- Property valuations completed
- Market analysis performed
- LTV ratios calculated

### 4. Error Handling and Edge Case Testing

#### ERROR-001: Invalid Input Testing
**Objective**: Test system behavior with invalid inputs

**Test Steps**:
```bash
# Test invalid workflow type
python -m mortgage_ai_processing.cli workflow process --workflow-type invalid

# Test invalid application file
python -m mortgage_ai_processing.cli workflow process \
  --application-file non_existent_file.json

# Test invalid tool name
python -m mortgage_ai_processing.cli tools info invalid_tool_name

# Test invalid agent name
python -m mortgage_ai_processing.cli agents info invalid_agent
```

**Expected Results**:
- Proper error messages displayed
- System remains stable
- No crashes or unexpected behavior

#### ERROR-002: Resource Limitation Testing
**Objective**: Test system behavior under resource constraints

**Test Steps**:
```bash
# Test concurrent workflow processing
python -m mortgage_ai_processing.cli workflow process --workflow-type parallel &
python -m mortgage_ai_processing.cli workflow process --workflow-type parallel &
python -m mortgage_ai_processing.cli workflow process --workflow-type parallel &
wait

# Check system health after concurrent processing
python -m mortgage_ai_processing.cli system health
```

**Expected Results**:
- System handles concurrent requests
- No resource conflicts
- System health remains good

### 5. Performance Testing Scenarios

#### PERF-001: Processing Time Benchmarks
**Objective**: Establish performance baselines

**Test Steps**:
```bash
# Benchmark OCR processing
echo "Benchmarking OCR processing..."
$start = Get-Date
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf
$end = Get-Date
$ocr_time = ($end - $start).TotalSeconds
echo "OCR processing time: $ocr_time seconds"

# Benchmark workflow processing
echo "Benchmarking workflow processing..."
$start = Get-Date
python -m mortgage_ai_processing.cli workflow process --workflow-type parallel
$end = Get-Date
$workflow_time = ($end - $start).TotalSeconds
echo "Workflow processing time: $workflow_time seconds"
```

**Expected Results**:
- Processing times within acceptable limits
- Performance metrics recorded
- No significant performance degradation

#### PERF-002: Memory and Resource Usage
**Objective**: Monitor system resource usage

**Test Steps**:
```bash
# Monitor system resources during processing
# (Use system monitoring tools alongside CLI commands)

# Process large workflow and monitor
python -m mortgage_ai_processing.cli workflow process \
  --workflow-type parallel \
  --output "perf_002_results.json"

# Check system cleanup
python -m mortgage_ai_processing.cli system cleanup
```

**Expected Results**:
- Memory usage within limits
- Proper resource cleanup
- No memory leaks

### 6. Integration Testing Scenarios

#### INT-001: Azure Integration Testing
**Objective**: Test Azure Document Intelligence integration

**Test Steps**:
```bash
# Test with Azure credentials configured
python -m mortgage_ai_processing.cli tools ocr test_documents/sample.pdf \
  --document-id "azure-integration-test"

# Verify Azure API calls in logs
python -m mortgage_ai_processing.cli --verbose tools ocr test_documents/sample.pdf
```

**Expected Results**:
- Azure API integration works
- Real OCR results (not mock data)
- Proper error handling for API failures

#### INT-002: Workflow State Management
**Objective**: Test workflow state persistence and management

**Test Steps**:
```bash
# Start workflow and track execution ID
python -m mortgage_ai_processing.cli workflow process \
  --workflow-type parallel \
  --output "int_002_results.json"

# List active workflows
python -m mortgage_ai_processing.cli workflow list

# Check workflow status using execution ID
python -m mortgage_ai_processing.cli workflow status EXECUTION-ID-HERE

# Test workflow cancellation
python -m mortgage_ai_processing.cli workflow cancel EXECUTION-ID-HERE
```

**Expected Results**:
- Workflow state tracked properly
- Status updates accurate
- Cancellation works correctly

### 7. System Administration Testing

#### ADMIN-001: System Health Monitoring
**Objective**: Test system health and monitoring capabilities

**Test Steps**:
```bash
# Check system health
python -m mortgage_ai_processing.cli system health

# Get system information
python -m mortgage_ai_processing.cli system info

# Check agent status
python -m mortgage_ai_processing.cli agents status

# List all available tools
python -m mortgage_ai_processing.cli tools list
```

**Expected Results**:
- System health reports accurate status
- All agents and tools listed
- No critical errors reported

#### ADMIN-002: System Cleanup and Maintenance
**Objective**: Test system cleanup functionality

**Test Steps**:
```bash
# Run multiple workflows to create cleanup targets
python -m mortgage_ai_processing.cli workflow process &
python -m mortgage_ai_processing.cli workflow process &
wait

# Perform system cleanup
python -m mortgage_ai_processing.cli system cleanup

# Verify cleanup effectiveness
python -m mortgage_ai_processing.cli workflow list
```

**Expected Results**:
- Cleanup removes old workflows
- System performance maintained
- No active workflows affected

## Test Data Requirements

### Application JSON Files Needed:
1. `e2e_application.json` - Standard test application
2. `multi_document_application.json` - Application with multiple documents
3. `income_test_application.json` - Income-focused test case
4. `credit_test_application.json` - Credit-focused test case
5. `property_test_application.json` - Property-focused test case
6. `high_risk_application.json` - High-risk scenario
7. `underwriting_test_application.json` - Underwriting-focused test case
8. `excellent_credit_application.json` - High credit score scenario
9. `poor_credit_application.json` - Low credit score scenario
10. `low_dti_application.json` - Low DTI scenario
11. `high_dti_application.json` - High DTI scenario
12. `single_family_application.json` - Single family home
13. `condo_application.json` - Condominium property

### Document Files Needed:
1. `test_documents/sample.pdf` - Sample PDF document
2. `test_documents/sample_passport.txt` - Sample identity document
3. Additional test documents for various scenarios

## Success Criteria

### End-to-End Testing:
- ✅ Complete workflow processing without errors
- ✅ All agents execute successfully
- ✅ Loan decisions generated with proper scoring
- ✅ Processing times within acceptable limits

### Agent Testing:
- ✅ All 6 agents accessible and functional
- ✅ Agent-specific tools execute correctly
- ✅ Agent results contribute to final decision

### Tool Testing:
- ✅ All 18+ tools accessible via CLI
- ✅ Tool execution completes successfully
- ✅ Proper error handling for invalid inputs

### System Testing:
- ✅ System health checks pass
- ✅ Resource cleanup works properly
- ✅ Performance within acceptable limits
- ✅ Integration with external services functional

## Reporting and Documentation

### Test Results Documentation:
1. Create test execution logs for each scenario
2. Document performance benchmarks
3. Record any failures or issues
4. Generate test coverage reports
5. Create recommendations for improvements

### Automated Test Execution:
Consider creating batch scripts to automate test execution:

```bash
# create_cli_test_suite.bat
@echo off
echo Starting CLI Comprehensive Test Suite...

echo Running End-to-End Tests...
call run_e2e_tests.bat

echo Running Agent Tests...
call run_agent_tests.bat

echo Running Tool Tests...
call run_tool_tests.bat

echo Running Error Handling Tests...
call run_error_tests.bat

echo Running Performance Tests...
call run_performance_tests.bat

echo CLI Test Suite Complete!
```

This comprehensive CLI test plan ensures thorough testing of all system components, from individual tools to complete end-to-end workflows, providing confidence in the system's reliability and functionality.