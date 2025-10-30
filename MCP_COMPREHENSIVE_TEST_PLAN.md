# MCP Comprehensive Test Plan
## Mortgage AI Processing System - Model Context Protocol Testing

### Overview
This test plan covers comprehensive testing of the mortgage AI processing system through MCP (Model Context Protocol) interface, including end-to-end testing, individual agent testing, and individual tool testing scenarios via MCP server.

## MCP Test Categories

### 1. MCP Server Setup and Initialization Testing

#### MCP-INIT-001: MCP Server Startup Testing
**Objective**: Test MCP server initialization and basic functionality

**Test Steps**:
```bash
# Start MCP server on default port
python -m mortgage_ai_processing.cli mcp serve

# Start MCP server on custom port
python -m mortgage_ai_processing.cli mcp serve --port 8080 --host 0.0.0.0

# Verify server is running (in separate terminal)
netstat -an | findstr :8000
netstat -an | findstr :8080
```

**Expected Results**:
- MCP server starts without errors
- Server listens on specified ports
- All agents and tools registered successfully
- Server capabilities properly declared

#### MCP-INIT-002: MCP Protocol Compliance Testing
**Objective**: Test MCP protocol compliance and standard methods

**Test Steps**:
```bash
# Test server info endpoint
python -m mortgage_ai_processing.cli mcp request "server/info"

# Test server capabilities
python -m mortgage_ai_processing.cli mcp request "server/capabilities"

# Test tools list endpoint
python -m mortgage_ai_processing.cli mcp request "tools/list"

# Test invalid method handling
python -m mortgage_ai_processing.cli mcp request "invalid/method"
```

**Expected Results**:
- Server info returns proper metadata
- Capabilities declaration includes all features
- Tools list returns all 18+ tools with schemas
- Invalid methods return proper MCP error responses

### 2. MCP End-to-End Testing Scenarios

#### MCP-E2E-001: Complete Mortgage Processing via MCP
**Objective**: Test complete mortgage processing workflow through MCP interface

**Test Steps**:
```bash
# Step 1: Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Step 2: Test document processing via MCP
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "mcp-e2e-001"}}'

# Step 3: Process complete mortgage workflow via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "e2e_application.json", "workflow_type": "parallel"}'

# Step 4: Check workflow status via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/workflow/status" \
  --params '{"execution_id": "EXECUTION-ID-FROM-STEP-3"}'
```

**Expected Results**:
- Document extraction completes via MCP
- Workflow processes all agents through MCP
- Status tracking works via MCP interface
- Final loan decision available through MCP

#### MCP-E2E-002: Multi-Client MCP Testing
**Objective**: Test multiple MCP clients accessing the server simultaneously

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Client 1: Process workflow
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "client1_application.json", "workflow_type": "parallel"}' &

# Client 2: Process different workflow
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "client2_application.json", "workflow_type": "standard"}' &

# Client 3: List active workflows
python -m mortgage_ai_processing.cli mcp request "mortgage/workflow/list"

wait
```

**Expected Results**:
- Multiple clients can connect simultaneously
- Concurrent workflow processing works
- No interference between client requests
- Proper isolation of workflow states

#### MCP-E2E-003: MCP Error Recovery Testing
**Objective**: Test MCP error handling and recovery mechanisms

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Test invalid tool call
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "invalid_tool", "arguments": {}}'

# Test invalid workflow processing
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "non_existent.json"}'

# Test recovery with valid request
python -m mortgage_ai_processing.cli mcp request "tools/list"
```

**Expected Results**:
- Invalid requests return proper MCP error responses
- Server remains stable after errors
- Subsequent valid requests work correctly
- Error details are informative

### 3. MCP Agent Testing Scenarios

#### MCP-AGENT-001: Document Processing Agent via MCP
**Objective**: Test document processing agent through MCP interface

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Get agent information via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/info" \
  --params '{"agent_id": "doc_agent"}'

# Test document agent tools via MCP
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "mcp-agent-001"}}'

python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_classifier", "arguments": {"document_path": "test_documents/sample.pdf"}}'
```

**Expected Results**:
- Agent information retrieved via MCP
- Document tools execute successfully via MCP
- OCR extraction returns proper MCP response format
- Document classification completes

#### MCP-AGENT-002: Income Verification Agent via MCP
**Objective**: Test income verification agent through MCP

**Test Steps**:
```bash
# Get income agent information
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/info" \
  --params '{"agent_id": "income_agent"}'

# Test income tools via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "income_calculator", "application_data": {"annual_income": 75000, "employment_status": "Employed"}}'

python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "dti_calculator", "application_data": {"annual_income": 75000, "monthly_debt": 1500}}'
```

**Expected Results**:
- Income agent accessible via MCP
- Income calculations work through MCP
- DTI calculations return accurate results
- MCP response format maintained

#### MCP-AGENT-003: Credit Assessment Agent via MCP
**Objective**: Test credit assessment agent functionality through MCP

**Test Steps**:
```bash
# Get credit agent information
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/info" \
  --params '{"agent_id": "credit_agent"}'

# Test credit tools via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "credit_score_analyzer", "application_data": {"credit_score": 720, "credit_history_length": 10}}'

python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "debt_analyzer", "application_data": {"total_debt": 25000, "monthly_payments": 800}}'
```

**Expected Results**:
- Credit agent responds via MCP
- Credit analysis tools execute
- Debt analysis completes successfully
- Risk scores calculated and returned

#### MCP-AGENT-004: Property Assessment Agent via MCP
**Objective**: Test property assessment agent through MCP

**Test Steps**:
```bash
# Get property agent information
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/info" \
  --params '{"agent_id": "property_agent"}'

# Test property tools via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "property_value_estimator", "application_data": {"property_address": "123 Main St", "property_type": "Single Family", "property_value": 300000}}'

python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "market_comparator", "application_data": {"property_address": "123 Main St", "property_value": 300000}}'
```

**Expected Results**:
- Property agent accessible via MCP
- Property valuation tools work
- Market comparison analysis completes
- LTV calculations accurate

#### MCP-AGENT-005: Risk Assessment Agent via MCP
**Objective**: Test risk assessment agent through MCP

**Test Steps**:
```bash
# Get risk agent information
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/info" \
  --params '{"agent_id": "risk_agent"}'

# Test risk tools via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "risk_calculator", "application_data": {"credit_score": 720, "dti_ratio": 0.28, "ltv_ratio": 0.8}}'

python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "fraud_detector", "application_data": {"borrower_info": {"ssn": "123-45-6789", "address": "123 Main St"}}}'
```

**Expected Results**:
- Risk agent responds via MCP
- Risk calculations complete
- Fraud detection analysis performed
- Overall risk scores generated

#### MCP-AGENT-006: Underwriting Agent via MCP
**Objective**: Test underwriting agent decision-making through MCP

**Test Steps**:
```bash
# Get underwriting agent information
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/info" \
  --params '{"agent_id": "underwriting_agent"}'

# Test underwriting tools via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "underwriting_decision_engine", "application_data": {"credit_score": 720, "dti_ratio": 0.28, "ltv_ratio": 0.8, "risk_score": 0.25}}'

python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "condition_generator", "application_data": {"loan_decision": "CONDITIONAL", "risk_factors": ["high_dti"]}}'
```

**Expected Results**:
- Underwriting agent accessible via MCP
- Decision engine generates loan decisions
- Conditions generated appropriately
- Final approval calculations work

### 4. MCP Individual Tool Testing Scenarios

#### MCP-TOOL-001: Document OCR Extractor via MCP
**Objective**: Comprehensive testing of OCR tool through MCP

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Get tool metadata via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/metadata" \
  --params '{"tool_name": "document_ocr_extractor"}'

# Test OCR with different document types via MCP
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "mcp-tool-001-pdf"}}'

python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample_passport.txt", "document_id": "mcp-tool-001-txt"}}'

# Test error handling via MCP
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "non_existent.pdf", "document_id": "error-test"}}'
```

**Expected Results**:
- Tool metadata returned via MCP
- OCR extraction works for valid files
- Proper MCP error responses for invalid files
- Confidence scores and metadata in MCP format

#### MCP-TOOL-002: Credit Score Analyzer via MCP
**Objective**: Test credit score analysis through MCP

**Test Steps**:
```bash
# Get tool metadata
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/metadata" \
  --params '{"tool_name": "credit_score_analyzer"}'

# Test credit analysis with different scenarios via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "credit_score_analyzer", "application_data": {"credit_score": 800, "credit_history_length": 15}}'

python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "credit_score_analyzer", "application_data": {"credit_score": 580, "credit_history_length": 2}}'
```

**Expected Results**:
- Tool metadata accessible via MCP
- Credit analysis completes for different scores
- Risk assessments vary appropriately
- MCP response format maintained

#### MCP-TOOL-003: DTI Calculator via MCP
**Objective**: Test DTI calculations through MCP

**Test Steps**:
```bash
# Get tool metadata
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/metadata" \
  --params '{"tool_name": "dti_calculator"}'

# Test DTI calculations via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "dti_calculator", "application_data": {"annual_income": 75000, "monthly_debt": 1200}}'

python -m mortgage_ai_processing.cli mcp request "mortgage/tools/execute" \
  --params '{"tool_name": "dti_calculator", "application_data": {"annual_income": 50000, "monthly_debt": 2000}}'
```

**Expected Results**:
- DTI calculations accurate via MCP
- Different scenarios handled properly
- Risk assessments based on DTI ratios
- Proper MCP response formatting

### 5. MCP Workflow Management Testing

#### MCP-WORKFLOW-001: Workflow Lifecycle Management via MCP
**Objective**: Test complete workflow lifecycle through MCP

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Start workflow via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "e2e_application.json", "workflow_type": "parallel"}'

# List active workflows via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/workflow/list"

# Check workflow status via MCP (use execution ID from start)
python -m mortgage_ai_processing.cli mcp request "mortgage/workflow/status" \
  --params '{"execution_id": "EXECUTION-ID-HERE"}'

# Cancel workflow via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/workflow/cancel" \
  --params '{"execution_id": "EXECUTION-ID-HERE"}'
```

**Expected Results**:
- Workflow starts successfully via MCP
- Status tracking works through MCP
- Workflow listing shows active processes
- Cancellation works via MCP interface

#### MCP-WORKFLOW-002: Parallel vs Sequential Processing via MCP
**Objective**: Compare workflow types through MCP interface

**Test Steps**:
```bash
# Test parallel workflow via MCP
echo "Testing Parallel Workflow via MCP..."
$start = Get-Date
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "e2e_application.json", "workflow_type": "parallel"}'
$end = Get-Date
$parallel_time = ($end - $start).TotalSeconds

# Test sequential workflow via MCP
echo "Testing Sequential Workflow via MCP..."
$start = Get-Date
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "e2e_application.json", "workflow_type": "standard"}'
$end = Get-Date
$sequential_time = ($end - $start).TotalSeconds

echo "MCP Parallel time: $parallel_time seconds"
echo "MCP Sequential time: $sequential_time seconds"
```

**Expected Results**:
- Both workflow types work via MCP
- Performance differences measurable
- Results consistent between types
- MCP response times acceptable

### 6. MCP System Administration Testing

#### MCP-ADMIN-001: System Health via MCP
**Objective**: Test system health monitoring through MCP

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Check system health via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/system/health"

# Get system information via MCP
python -m mortgage_ai_processing.cli mcp request "server/info"

# List all agents via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/list"

# Get comprehensive tool list via MCP
python -m mortgage_ai_processing.cli mcp request "tools/list"
```

**Expected Results**:
- System health accessible via MCP
- All agents listed through MCP
- Tool inventory complete via MCP
- Server information accurate

#### MCP-ADMIN-002: System Cleanup via MCP
**Objective**: Test system maintenance through MCP

**Test Steps**:
```bash
# Start multiple workflows via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "e2e_application.json", "workflow_type": "parallel"}' &

python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "e2e_application.json", "workflow_type": "standard"}' &

wait

# Perform cleanup via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/system/cleanup"

# Verify cleanup via MCP
python -m mortgage_ai_processing.cli mcp request "mortgage/workflow/list"
```

**Expected Results**:
- Cleanup operations work via MCP
- Old workflows removed properly
- Active workflows preserved
- System performance maintained

### 7. MCP Performance and Load Testing

#### MCP-PERF-001: MCP Response Time Testing
**Objective**: Measure MCP response times for different operations

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Benchmark MCP tool calls
echo "Benchmarking MCP tool calls..."
$start = Get-Date
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "perf-test"}}'
$end = Get-Date
$tool_time = ($end - $start).TotalSeconds
echo "MCP tool call time: $tool_time seconds"

# Benchmark MCP workflow processing
echo "Benchmarking MCP workflow processing..."
$start = Get-Date
python -m mortgage_ai_processing.cli mcp request "mortgage/process" \
  --params '{"application_file": "e2e_application.json", "workflow_type": "parallel"}'
$end = Get-Date
$workflow_time = ($end - $start).TotalSeconds
echo "MCP workflow time: $workflow_time seconds"
```

**Expected Results**:
- MCP response times within acceptable limits
- Tool calls complete efficiently via MCP
- Workflow processing times reasonable
- No significant MCP overhead

#### MCP-PERF-002: Concurrent MCP Client Testing
**Objective**: Test MCP server under concurrent load

**Test Steps**:
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Launch multiple concurrent MCP clients
echo "Testing concurrent MCP clients..."
python -m mortgage_ai_processing.cli mcp request "tools/list" &
python -m mortgage_ai_processing.cli mcp request "mortgage/agents/list" &
python -m mortgage_ai_processing.cli mcp request "mortgage/system/health" &
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "concurrent-1"}}' &
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf", "document_id": "concurrent-2"}}' &

wait
echo "Concurrent MCP client testing complete"
```

**Expected Results**:
- MCP server handles concurrent clients
- No request interference or conflicts
- All requests complete successfully
- Server remains stable under load

### 8. MCP Integration and Compatibility Testing

#### MCP-INT-001: MCP Protocol Version Compatibility
**Objective**: Test MCP protocol version compatibility

**Test Steps**:
```bash
# Test MCP protocol compliance
python -m mortgage_ai_processing.cli mcp request "server/info"

# Verify JSON-RPC 2.0 compliance
python -m mortgage_ai_processing.cli mcp request "tools/list" \
  --params '{"jsonrpc": "2.0", "method": "tools/list", "id": "test-001"}'

# Test invalid protocol version handling
python -m mortgage_ai_processing.cli mcp request "tools/list" \
  --params '{"jsonrpc": "1.0", "method": "tools/list", "id": "test-002"}'
```

**Expected Results**:
- MCP protocol version properly declared
- JSON-RPC 2.0 compliance verified
- Invalid protocol versions handled gracefully
- Proper error responses for protocol violations

#### MCP-INT-002: MCP Client Integration Testing
**Objective**: Test integration with different MCP client implementations

**Test Steps**:
```bash
# Test with standard MCP client patterns
python -m mortgage_ai_processing.cli mcp serve --port 8000 &

# Test various MCP request formats
python -m mortgage_ai_processing.cli mcp request "tools/list"
python -m mortgage_ai_processing.cli mcp request "tools/call" \
  --params '{"name": "document_ocr_extractor", "arguments": {"document_path": "test_documents/sample.pdf"}}'

# Test MCP batch requests (if supported)
# Test MCP notification handling (if supported)
```

**Expected Results**:
- Standard MCP client patterns work
- Request/response format compliance
- Proper handling of different client types
- Consistent behavior across client implementations

## MCP Test Data Requirements

### Application JSON Files for MCP Testing:
1. `mcp_e2e_application.json` - Standard MCP test application
2. `mcp_client1_application.json` - Multi-client test case 1
3. `mcp_client2_application.json` - Multi-client test case 2
4. `mcp_performance_application.json` - Performance testing application
5. `mcp_error_test_application.json` - Error handling test case

### MCP Server Configuration:
1. Default port: 8000
2. Alternative ports: 8080, 9000 for multi-server testing
3. Host configurations: localhost, 0.0.0.0 for network testing

## MCP Success Criteria

### MCP Server Functionality:
- ✅ MCP server starts and stops cleanly
- ✅ All standard MCP methods implemented
- ✅ Custom mortgage-specific methods work
- ✅ JSON-RPC 2.0 protocol compliance
- ✅ Proper error handling and responses

### MCP Agent Integration:
- ✅ All 6 agents accessible via MCP
- ✅ Agent information retrievable via MCP
- ✅ Agent tools executable through MCP
- ✅ Agent results properly formatted for MCP

### MCP Tool Integration:
- ✅ All 18+ tools accessible via MCP
- ✅ Tool metadata available through MCP
- ✅ Tool execution works via MCP interface
- ✅ Tool results in proper MCP format

### MCP Workflow Management:
- ✅ Workflow initiation via MCP
- ✅ Workflow status tracking via MCP
- ✅ Workflow cancellation via MCP
- ✅ Workflow listing via MCP

### MCP Performance:
- ✅ Response times within acceptable limits
- ✅ Concurrent client handling
- ✅ Server stability under load
- ✅ Resource usage optimization

## MCP Reporting and Documentation

### MCP Test Results Documentation:
1. MCP protocol compliance verification
2. Performance benchmarks for MCP operations
3. Concurrent client handling results
4. Error handling and recovery testing
5. Integration compatibility results

### MCP Automated Test Execution:
Create MCP-specific test automation:

```bash
# create_mcp_test_suite.bat
@echo off
echo Starting MCP Comprehensive Test Suite...

echo Starting MCP Server...
start /B python -m mortgage_ai_processing.cli mcp serve --port 8000
timeout /t 5

echo Running MCP Initialization Tests...
call run_mcp_init_tests.bat

echo Running MCP End-to-End Tests...
call run_mcp_e2e_tests.bat

echo Running MCP Agent Tests...
call run_mcp_agent_tests.bat

echo Running MCP Tool Tests...
call run_mcp_tool_tests.bat

echo Running MCP Performance Tests...
call run_mcp_performance_tests.bat

echo MCP Test Suite Complete!
```

### MCP Test Validation:
1. Verify MCP protocol compliance
2. Validate JSON-RPC 2.0 format adherence
3. Confirm all MCP methods work correctly
4. Test error handling and recovery
5. Validate performance under load

This comprehensive MCP test plan ensures thorough testing of all system components through the MCP interface, providing confidence in the system's MCP compliance and functionality for integration with MCP-compatible clients and tools.