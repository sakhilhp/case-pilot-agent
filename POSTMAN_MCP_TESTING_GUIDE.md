# Postman MCP Testing Guide
## Mortgage AI Processing System - HTTP/JSON-RPC Interface

### Overview
This guide shows you how to use Postman to send MCP (Model Context Protocol) requests to your mortgage processing system via HTTP transport.

## Step 1: Start the MCP HTTP Server

First, start the MCP server with HTTP transport:

```bash
# Start MCP HTTP server on port 8001 (avoiding port conflicts)
python -m mortgage_ai_processing.cli mcp serve --port 8001

# Or start on custom port
python -m mortgage_ai_processing.cli mcp serve --port 8080 --host 0.0.0.0
```

**Expected Output:**
```
🚀 Starting MCP HTTP server on localhost:8001
📋 Server Info: http://localhost:8001/info
❤️  Health Check: http://localhost:8001/health
🔧 MCP Endpoint: http://localhost:8001/mcp

Ready to accept MCP requests via HTTP!
```

## Step 2: Postman Setup

### Basic Configuration:
- **Method**: POST
- **URL**: `http://localhost:8001/mcp`
- **Headers**: 
  - `Content-Type: application/json`
- **Body**: Raw JSON (JSON-RPC 2.0 format)

## Step 3: MCP Request Examples for Postman

### 3.1 Server Information Request

**URL**: `POST http://localhost:8001/mcp`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "server/info",
  "params": {},
  "id": "postman-001"
}
```

**Expected Response**:
```json
{
  "result": {
    "name": "mortgage-processing-server",
    "version": "1.0.0",
    "description": "Mortgage AI Processing MCP Server",
    "author": "Mortgage AI Processing Team"
  },
  "error": null,
  "id": "postman-001",
  "jsonrpc": "2.0"
}
```

### 3.2 List All Tools

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": "postman-002"
}
```

**Expected Response**: List of all 18+ tools with their schemas

### 3.3 List All Agents

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/agents/list",
  "params": {},
  "id": "postman-003"
}
```

**Expected Response**:
```json
{
  "result": {
    "agents": [
      {
        "agent_id": "doc_agent",
        "name": "Document Processing Agent",
        "tools": ["document_ocr_extractor", "document_classifier", ...],
        "tool_count": 5
      },
      ...
    ],
    "total_count": 6
  },
  "error": null,
  "id": "postman-003",
  "jsonrpc": "2.0"
}
```

### 3.4 Execute OCR Tool

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "document_ocr_extractor",
    "arguments": {
      "document_path": "test_documents/sample.pdf",
      "document_id": "postman-ocr-test",
      "analysis_features": ["ocr_read", "layout", "key_value_pairs"]
    }
  },
  "id": "postman-004"
}
```

### 3.5 Process Complete Mortgage Application

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/process",
  "params": {
    "application": {
      "application_id": "POSTMAN-TEST-001",
      "borrower_info": {
        "first_name": "John",
        "last_name": "Doe",
        "ssn": "123-45-6789",
        "date_of_birth": "1985-01-01T00:00:00",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "current_address": "123 Main St, Anytown, ST 12345",
        "employment_status": "Employed",
        "annual_income": "75000"
      },
      "property_info": {
        "address": "456 Oak Avenue, Testville, ST 67890",
        "property_type": "Single Family Home",
        "property_value": "300000"
      },
      "loan_details": {
        "loan_amount": "240000",
        "loan_type": "conventional",
        "loan_term_years": 30,
        "down_payment": "60000",
        "purpose": "Purchase"
      },
      "documents": [],
      "processing_status": "pending"
    },
    "workflow_type": "parallel_mortgage_processing"
  },
  "id": "postman-005"
}
```

### 3.6 Check System Health

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/system/health",
  "params": {},
  "id": "postman-006"
}
```

### 3.7 Get Agent Information

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/agents/info",
  "params": {
    "agent_id": "doc_agent"
  },
  "id": "postman-007"
}
```

### 3.8 Execute Individual Tool via MCP

**Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/tools/execute",
  "params": {
    "tool_name": "enhanced_credit_score_analyzer",
    "arguments": {
      "borrower_name": "John Doe",
      "credit_scores": [
        {
          "bureau": "experian",
          "score_type": "fico_8",
          "score_value": 720,
          "score_date": "2024-10-01",
          "score_factors": ["Payment history", "Credit utilization"]
        }
      ],
      "loan_amount": 800000,
      "loan_purpose": "purchase",
      "property_type": "primary",
      "target_loan_programs": ["conventional"],
      "down_payment_percent": 20,
      "debt_to_income_ratio": 25,
      "first_time_buyer": false
    }
  },
  "id": "postman-008"
}
```

## Step 4: Alternative HTTP Endpoints

### 4.1 Quick Health Check (GET Request)

**URL**: `GET http://localhost:8001/health`

**Expected Response**:
```json
{
  "status": "healthy",
  "server": "mortgage-processing-mcp-server",
  "version": "1.0.0",
  "agents": 6,
  "tools": 18
}
```

### 4.2 Server Info (GET Request)

**URL**: `GET http://localhost:8001/info`

**Expected Response**: Same as MCP server/info request

## Step 5: Postman Collection Setup

### Create a Postman Collection with these requests:

1. **Server Info** - Basic server information
2. **Health Check** - System health status
3. **List Tools** - All available tools
4. **List Agents** - All available agents
5. **OCR Document** - Extract text from documents
6. **Process Application** - Complete mortgage workflow
7. **Agent Info** - Detailed agent information
8. **Tool Execute** - Individual tool execution

### Environment Variables in Postman:
- `base_url`: `http://localhost:8001`
- `mcp_endpoint`: `{{base_url}}/mcp`
- `health_endpoint`: `{{base_url}}/health`

## Step 6: Testing Scenarios

### Scenario A: End-to-End Mortgage Processing
1. **Health Check** - Verify system is ready
2. **Process Application** - Submit complete mortgage application
3. **Check Status** - Monitor processing status (if workflow tracking implemented)

### Scenario B: Individual Tool Testing
1. **List Tools** - See all available tools
2. **OCR Document** - Extract data from document
3. **Credit Analysis** - Analyze credit information
4. **Property Valuation** - Estimate property value

### Scenario C: Agent-Specific Testing
1. **List Agents** - See all agents
2. **Agent Info** - Get detailed agent information
3. **Execute Agent Tools** - Test specific agent capabilities

## Step 7: Error Handling Testing

### Test Invalid Requests:

**Invalid Method**:
```json
{
  "jsonrpc": "2.0",
  "method": "invalid/method",
  "params": {},
  "id": "error-test-001"
}
```

**Invalid JSON-RPC**:
```json
{
  "jsonrpc": "1.0",
  "method": "server/info",
  "id": "error-test-002"
}
```

**Missing Required Parameters**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "document_ocr_extractor"
    // Missing required arguments
  },
  "id": "error-test-003"
}
```

## Step 8: Advanced Testing

### Batch Requests (Multiple MCP calls):
```json
[
  {
    "jsonrpc": "2.0",
    "method": "server/info",
    "id": "batch-001"
  },
  {
    "jsonrpc": "2.0",
    "method": "mortgage/system/health",
    "id": "batch-002"
  },
  {
    "jsonrpc": "2.0",
    "method": "mortgage/agents/list",
    "id": "batch-003"
  }
]
```

### Performance Testing:
- Send multiple concurrent requests
- Measure response times
- Test with large payloads

## Step 9: Workflow Status Tracking

### Start Workflow and Track Progress:

1. **Start Workflow**:
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/process",
  "params": {
    "application": { /* application data */ },
    "workflow_type": "parallel"
  },
  "id": "workflow-start"
}
```

2. **Check Status** (use execution_id from response):
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/workflow/status",
  "params": {
    "execution_id": "exec_20241029_123456"
  },
  "id": "workflow-status"
}
```

3. **List Active Workflows**:
```json
{
  "jsonrpc": "2.0",
  "method": "mortgage/workflow/list",
  "params": {},
  "id": "workflow-list"
}
```

## Step 10: Common Tool Parameter Schemas

### 10.1 Enhanced Credit Score Analyzer

**Required Parameters:**
- `borrower_name` (string): Name of the borrower
- `credit_scores` (array): Array of credit score objects
- `loan_amount` (number): Loan amount requested
- `loan_purpose` (string): "purchase", "refinance", or "cash_out_refinance"
- `property_type` (string): "primary", "secondary", or "investment"
- `target_loan_programs` (array): e.g., ["conventional", "fha", "va"]

**Credit Score Object Structure:**
```json
{
  "bureau": "experian",  // "experian", "equifax", "transunion"
  "score_type": "fico_8",  // "fico_8", "fico_9", "fico_10", etc.
  "score_value": 720,  // 300-850
  "score_date": "2024-10-01",  // ISO date format
  "score_factors": ["Payment history", "Credit utilization"]  // optional
}
```

### 10.2 Document OCR Extractor

**Required Parameters:**
- `document_path` (string): Path to document file
- `document_id` (string): Unique identifier

**Example:**
```json
{
  "document_path": "test_documents/sample.pdf",
  "document_id": "test-doc-001",
  "analysis_features": ["ocr_read", "layout", "key_value_pairs", "tables"],
  "pages": "all"
}
```

### 10.3 Document Classifier

**Required Parameters:**
- `document_id` (string): Unique identifier
- `document_path` OR `document_url` OR `extracted_text`

**Example:**
```json
{
  "document_id": "test-doc-001",
  "document_path": "test_documents/sample.pdf",
  "use_prebuilt_models": true,
  "analysis_features": ["layout", "keyValuePairs", "entities"]
}
```

## Step 11: Troubleshooting

### Common Issues:

1. **Connection Refused**: 
   - Make sure MCP server is running with `python -m mortgage_ai_processing.cli mcp serve`
   - Wait for "🚀 MCP HTTP Server running on http://localhost:8001" message
   - Test with `http://localhost:8001/health` in browser first

2. **Server Starts But HTTP Fails**: 
   - Fixed: There was a duplicate serve command bug - now resolved
   - Ensure you see HTTP server startup logs with endpoint URLs listed

3. **404 Not Found**: Check URL and endpoint path
4. **400 Bad Request**: Validate JSON-RPC format (must have jsonrpc: "2.0", method, id)
5. **Validation Errors**: Check enum values are lowercase:
   - `loan_type`: use "conventional", "fha", "va", "usda", "jumbo" (not uppercase)
   - `processing_status`: use "pending", "in_progress", "completed", etc. (not uppercase)
6. **Workflow Not Found**: Use correct workflow names:
   - `"standard_mortgage_processing"` - Sequential processing
   - `"parallel_mortgage_processing"` - Parallel assessment phase
7. **Parameter Validation Failed**: Check tool parameter schemas:
   - Use `tools/list` to get correct parameter structure
   - See Step 10 for common tool parameter examples
   - Ensure required parameters are provided
   - Check enum values (e.g., bureau names, loan purposes)
8. **500 Internal Error**: Check server logs for details

### Debug Commands:
```bash
# Check if server is running
netstat -an | findstr :8001

# View server logs (if running in separate terminal)
# Server logs will show in the terminal where you started the server
```

## Step 11: Sample Postman Collection JSON

Here's a complete Postman collection you can import:

```json
{
  "info": {
    "name": "Mortgage AI Processing MCP API",
    "description": "Complete MCP API testing for mortgage processing system"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8001"
    }
  ],
  "item": [
    {
      "name": "Server Info",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"jsonrpc\": \"2.0\",\n  \"method\": \"server/info\",\n  \"params\": {},\n  \"id\": \"postman-server-info\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/mcp",
          "host": ["{{base_url}}"],
          "path": ["mcp"]
        }
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "List Tools",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"jsonrpc\": \"2.0\",\n  \"method\": \"tools/list\",\n  \"params\": {},\n  \"id\": \"postman-tools-list\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/mcp",
          "host": ["{{base_url}}"],
          "path": ["mcp"]
        }
      }
    },
    {
      "name": "List Agents",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"jsonrpc\": \"2.0\",\n  \"method\": \"mortgage/agents/list\",\n  \"params\": {},\n  \"id\": \"postman-agents-list\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/mcp",
          "host": ["{{base_url}}"],
          "path": ["mcp"]
        }
      }
    },
    {
      "name": "Process Mortgage Application",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"jsonrpc\": \"2.0\",\n  \"method\": \"mortgage/process\",\n  \"params\": {\n    \"application\": {\n      \"application_id\": \"POSTMAN-TEST-001\",\n      \"borrower_info\": {\n        \"first_name\": \"John\",\n        \"last_name\": \"Doe\",\n        \"ssn\": \"123-45-6789\",\n        \"date_of_birth\": \"1985-01-01T00:00:00\",\n        \"email\": \"john.doe@example.com\",\n        \"phone\": \"555-123-4567\",\n        \"current_address\": \"123 Main St, Anytown, ST 12345\",\n        \"employment_status\": \"Employed\",\n        \"annual_income\": \"75000\"\n      },\n      \"property_info\": {\n        \"address\": \"456 Oak Avenue, Testville, ST 67890\",\n        \"property_type\": \"Single Family Home\",\n        \"property_value\": \"300000\"\n      },\n      \"loan_details\": {\n        \"loan_amount\": \"240000\",\n        \"loan_type\": \"conventional\",\n        \"loan_term_years\": 30,\n        \"down_payment\": \"60000\",\n        \"purpose\": \"Purchase\"\n      },\n      \"documents\": [],\n      \"processing_status\": \"pending\"\n    },\n    \"workflow_type\": \"parallel_mortgage_processing\"\n  },\n  \"id\": \"postman-process\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/mcp",
          "host": ["{{base_url}}"],
          "path": ["mcp"]
        }
      }
    }
  ]
}
```

## Step 12: Quick Testing Commands

### Test Server Availability:
```bash
# Test if server is running
curl http://localhost:8001/health

# Test MCP endpoint
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "server/info", "params": {}, "id": "curl-test"}'
```

## Step 13: Advanced Postman Testing

### Environment Setup:
Create Postman environment variables:
- `mcp_server`: `localhost:8001`
- `application_id`: `POSTMAN-{{$timestamp}}`

### Pre-request Scripts:
```javascript
// Generate unique application ID
pm.environment.set("application_id", "POSTMAN-" + Date.now());

// Set request timestamp
pm.environment.set("request_timestamp", new Date().toISOString());
```

### Test Scripts:
```javascript
// Validate MCP response format
pm.test("Valid JSON-RPC 2.0 response", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('jsonrpc', '2.0');
    pm.expect(jsonData).to.have.property('id');
});

// Check for successful result
pm.test("Request successful", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.error).to.be.null;
    pm.expect(jsonData.result).to.not.be.null;
});

// Store execution ID for workflow tracking
if (pm.response.json().result && pm.response.json().result.execution_id) {
    pm.environment.set("execution_id", pm.response.json().result.execution_id);
}
```

## Step 14: Complete Testing Workflow

### Full End-to-End Test Sequence:

1. **Health Check** → Verify system ready
2. **Server Info** → Get server details
3. **List Agents** → Verify all agents available
4. **List Tools** → Verify all tools available
5. **OCR Document** → Test document processing
6. **Process Application** → Run complete workflow
7. **Check Status** → Monitor workflow progress
8. **System Health** → Verify system stability

### Performance Testing:
- Send multiple concurrent requests
- Measure response times
- Test with different payload sizes
- Monitor server resource usage

## Step 15: Error Response Examples

### Tool Not Found:
```json
{
  "result": null,
  "error": {
    "code": -32601,
    "message": "Method not found: invalid/tool"
  },
  "id": "error-test",
  "jsonrpc": "2.0"
}
```

### Invalid Parameters:
```json
{
  "result": null,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "Missing required parameter: document_path"
    }
  },
  "id": "error-test",
  "jsonrpc": "2.0"
}
```

This guide provides everything you need to test your mortgage AI processing system using Postman with proper HTTP transport. The MCP server will now accept real HTTP requests and respond with JSON-RPC 2.0 formatted responses.