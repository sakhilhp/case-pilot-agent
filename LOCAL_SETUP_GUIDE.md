# Mortgage AI Processing System - Local Setup Guide

This guide provides step-by-step instructions to set up the Mortgage AI Processing System on your local machine.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: At least 2GB free space
- **Internet**: Required for Azure Document Intelligence API calls

### Required Accounts & Services
- **Azure Account**: For Document Intelligence services
- **Azure Document Intelligence Resource**: Set up in Azure portal

## Step 1: Environment Setup

### 1.1 Install Python Dependencies

```bash
# Clone or download the project
cd mortgage_ai_processing

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 1.2 Required Python Packages

The system requires these key packages:
```
azure-ai-documentintelligence>=1.0.2
pydantic>=2.0.0
click>=8.0.0
aiohttp>=3.8.0
python-dotenv>=1.0.0
asyncio
logging
```

## Step 2: Azure Document Intelligence Setup

### 2.1 Create Azure Resource

1. **Log into Azure Portal**: https://portal.azure.com
2. **Create Resource**: Search for "Document Intelligence"
3. **Configure Resource**:
   - Resource name: `your-document-intelligence`
   - Subscription: Select your subscription
   - Resource group: Create new or use existing
   - Region: Choose closest region
   - Pricing tier: F0 (Free) or S0 (Standard)
4. **Deploy**: Wait for deployment to complete
5. **Get Credentials**: Go to resource → Keys and Endpoint

### 2.2 Configure Environment Variables

Create a `.env` file in the project root:

```env
# Azure Document Intelligence Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-api-key-here
```

**Important**: Replace `your-resource-name` and `your-api-key-here` with your actual values.

## Step 3: Project Structure Setup

### 3.1 Verify Directory Structure

Ensure your project has this structure:
```
mortgage_ai_processing/
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
├── mortgage_ai_processing/       # Main package
│   ├── __init__.py
│   ├── cli.py                   # Command-line interface
│   ├── workflow_orchestrator.py # Main orchestrator
│   ├── agents/                  # Processing agents
│   ├── tools/                   # Processing tools
│   ├── models/                  # Data models
│   └── mcp/                     # MCP server components
├── test_documents/              # Test documents
└── docs/                        # Documentation
```

### 3.2 Create Test Documents Directory

```bash
mkdir test_documents
# Add sample PDF files for testing
```

## Step 4: Installation Verification

### 4.1 Test Basic Installation

```bash
# Test CLI installation
python -m mortgage_ai_processing.cli --help

# Expected output: CLI help menu with available commands
```

### 4.2 Test Azure Configuration

```bash
# Test document processing
python -m mortgage_ai_processing.cli tools test document_ocr_extractor --document-path "test_documents/sample.pdf"

# Expected: Successful OCR extraction with Azure API calls
```

## Step 5: System Components Testing

### 5.1 Test CLI Commands

```bash
# List available tools
python -m mortgage_ai_processing.cli tools list

# Test individual tool
python -m mortgage_ai_processing.cli tools test enhanced_credit_score_analyzer

# Process sample application
python -m mortgage_ai_processing.cli process --application-file sample_application.json
```

### 5.2 Test MCP Server

```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8001

# Expected output:
# 🚀 MCP HTTP Server running on http://localhost:8001
# Ready to accept MCP requests via HTTP!
```

### 5.3 Test Health Endpoints

```bash
# Test health check (in another terminal)
curl http://localhost:8001/health

# Expected: {"status": "healthy", "server": "mortgage-processing-mcp-server", ...}
```

## Step 6: Troubleshooting Common Issues

### 6.1 Python Environment Issues

**Problem**: `ModuleNotFoundError` or import errors
**Solution**:
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### 6.2 Azure Configuration Issues

**Problem**: "Azure Document Intelligence credentials not configured"
**Solution**:
1. Verify `.env` file exists in project root
2. Check endpoint URL format (must include `https://` and trailing `/`)
3. Verify API key is correct (32+ character string)
4. Test Azure resource in Azure portal

### 6.3 Port Conflicts

**Problem**: "Address already in use" when starting MCP server
**Solution**:
```bash
# Use different port
python -m mortgage_ai_processing.cli mcp serve --port 8002

# Or find and kill process using port
# Windows:
netstat -ano | findstr :8001
taskkill /PID <process_id> /F

# macOS/Linux:
lsof -ti:8001 | xargs kill -9
```

### 6.4 Document Processing Issues

**Problem**: Document processing fails
**Solution**:
1. Ensure document file exists and is readable
2. Check file format (PDF, PNG, JPG supported)
3. Verify file size < 500MB
4. Test with simple PDF first

## Step 7: Development Setup (Optional)

### 7.1 IDE Configuration

**VS Code Extensions**:
- Python
- Pylance
- Python Docstring Generator

**PyCharm Configuration**:
- Set Python interpreter to virtual environment
- Configure run configurations for CLI commands

### 7.2 Debugging Setup

```python
# Add to your IDE debug configuration
{
    "name": "MCP Server Debug",
    "type": "python",
    "request": "launch",
    "module": "mortgage_ai_processing.cli",
    "args": ["mcp", "serve", "--port", "8001"],
    "console": "integratedTerminal"
}
```

## Step 8: Production Considerations

### 8.1 Security

- **Never commit `.env` file** to version control
- **Use Azure Key Vault** for production credentials
- **Implement proper authentication** for MCP endpoints
- **Use HTTPS** in production environments

### 8.2 Performance

- **Monitor Azure API usage** and costs
- **Implement caching** for repeated document processing
- **Use connection pooling** for database connections
- **Configure proper logging levels**

### 8.3 Monitoring

```python
# Add logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Step 9: Validation Checklist

### ✅ Installation Complete When:

- [ ] Python environment activated
- [ ] All dependencies installed successfully
- [ ] `.env` file configured with valid Azure credentials
- [ ] CLI commands respond correctly
- [ ] Azure Document Intelligence API calls work
- [ ] MCP server starts without errors
- [ ] Health endpoints return 200 OK
- [ ] Sample document processing succeeds
- [ ] All test plans can be executed

### ✅ Ready for Testing When:

- [ ] All components start successfully
- [ ] No error messages in logs
- [ ] Sample requests return valid responses
- [ ] Azure API calls complete successfully
- [ ] All 18 tools are registered
- [ ] All 6 agents are initialized
- [ ] Workflow execution completes

## Step 10: Next Steps

After successful setup:

1. **Run CLI Test Plan**: Execute `CLI_COMPREHENSIVE_TEST_PLAN.md`
2. **Run MCP Test Plan**: Execute `MCP_COMPREHENSIVE_TEST_PLAN.md`
3. **Run Postman Tests**: Follow `POSTMAN_MCP_TESTING_GUIDE.md`
4. **Process Sample Applications**: Test end-to-end workflows
5. **Monitor Performance**: Check response times and error rates

## Support & Resources

### Documentation
- `CLI_COMPREHENSIVE_TEST_PLAN.md` - CLI testing procedures
- `MCP_COMPREHENSIVE_TEST_PLAN.md` - MCP server testing
- `POSTMAN_MCP_TESTING_GUIDE.md` - Postman API testing

### Common Commands Reference
```bash
# Start MCP server
python -m mortgage_ai_processing.cli mcp serve --port 8001

# List all tools
python -m mortgage_ai_processing.cli tools list

# Process application
python -m mortgage_ai_processing.cli process --application-file app.json

# Test specific tool
python -m mortgage_ai_processing.cli tools test <tool_name>

# Health check
python -m mortgage_ai_processing.cli system health
```

### Troubleshooting Resources
- Check server logs for detailed error messages
- Verify Azure portal for API usage and limits
- Test individual components before full workflow
- Use health endpoints to verify system status

---

**Setup Complete!** Your Mortgage AI Processing System is ready for testing and development.