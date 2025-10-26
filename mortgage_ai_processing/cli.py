"""
Command-line interface for mortgage processing system.

Provides CLI commands for:
- Processing mortgage applications
- Managing workflows
- Interacting with MCP server
- System administration
"""

import asyncio
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import click
import logging

from .workflow_orchestrator import (
    get_orchestrator, process_mortgage_application_simple, WorkflowConfiguration
)
from .mcp.mortgage_server import get_mcp_server
from .models.core import MortgageApplication, BorrowerInfo, PropertyInfo, LoanDetails
from .models.enums import LoanType, ProcessingStatus


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Mortgage AI Processing System CLI."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.group()
def workflow():
    """Workflow management commands."""
    pass


@cli.group()
def mcp():
    """MCP server commands."""
    pass


@cli.group()
def system():
    """System administration commands."""
    pass


@cli.group()
def tools():
    """Individual tool operations."""
    pass


@cli.group()
def agents():
    """Agent management commands."""
    pass

async def _run_workflow_direct(application_file: str, workflow_type: str, output: str):
    """Run workflow directly without subprocess (for testing)."""
    from .workflow_orchestrator import process_mortgage_application_simple
    from .models.core import MortgageApplication
    
    # Load application data
    with open(application_file, 'r') as f:
        app_data = json.load(f)
    
    application = MortgageApplication(**app_data)
    print(f"Processing application {application.application_id}")
    print(f"Workflow type: {workflow_type}")
    
    # Run workflow
    execution, decision = await process_mortgage_application_simple(
        application=application,
        use_parallel_processing=(workflow_type == "parallel")
    )
    
    # Format and display results (simplified)
    print(f"✅ Workflow completed successfully!")
    print(f"Decision: {decision.decision}")
    print(f"Overall Score: {decision.overall_score}")
    print(f"Risk Score: {decision.decision_factors.risk_score}")
    
    # Save results
    result_data = {
        "application_id": application.application_id,
        "decision": decision.decision,
        "overall_score": decision.overall_score,
        "risk_score": decision.decision_factors.risk_score,
        "agent_results": {}
    }
    
    # Add agent results
    for agent_id, agent_result in execution.context.shared_data.items():
        if hasattr(agent_result, 'risk_score'):
            result_data["agent_results"][agent_id] = {
                "risk_score": agent_result.risk_score,
                "risk_level": agent_result.risk_level.value if hasattr(agent_result.risk_level, 'value') else str(agent_result.risk_level),
                "confidence_level": agent_result.confidence_level,
                "errors": agent_result.errors,
                "warnings": agent_result.warnings
            }
    
    with open(output, 'w') as f:
        json.dump(result_data, f, indent=2, default=str)
    
    print(f">> Results saved to {output}")


@workflow.command()
@click.option('--application-file', '-f', type=click.Path(exists=True), 
              help='JSON file containing mortgage application data', required=True)
@click.option('--workflow-type', '-t', 
              type=click.Choice(['standard', 'parallel']), 
              default='parallel',
              help='Type of workflow to use')
@click.option('--output', '-o', type=click.Path(), 
              help='Output file for results', required=True)
@click.option('--direct', is_flag=True, 
              help='Run directly without subprocess (for testing)')
def process(application_file: str, workflow_type: str, output: str, direct: bool):
    """Process a mortgage application through the complete workflow."""
    
    # Store original arguments to prevent contamination
    original_argv = sys.argv.copy()
    
    # Import subprocess and tempfile for both paths
    import subprocess
    import tempfile
    
    try:
        if direct or True:  # Use direct execution by default until subprocess caching is resolved
            # Run workflow directly (for testing)
            result = asyncio.run(_run_workflow_direct(application_file, workflow_type, output))
            return
            
        # Run workflow in subprocess to completely isolate it from CLI
        
        # Create a temporary script to run the workflow with detailed tracing
        script_content = f'''
import asyncio
import json
import sys
import traceback
import importlib
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Force reload modules to pick up any changes
import mortgage_ai_processing.models.core
import mortgage_ai_processing.workflow_orchestrator
import mortgage_ai_processing.agents.risk_assessment
import mortgage_ai_processing.agents.income_verification

# Clear module cache and reload
modules_to_reload = [
    'mortgage_ai_processing.models.core',
    'mortgage_ai_processing.workflow_orchestrator', 
    'mortgage_ai_processing.agents.risk_assessment',
    'mortgage_ai_processing.agents.income_verification'
]

for module_name in modules_to_reload:
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])

from mortgage_ai_processing.workflow_orchestrator import process_mortgage_application_simple
from mortgage_ai_processing.models.core import MortgageApplication

def safe_serialize(obj):
    """Safely serialize objects to JSON-compatible format."""
    if hasattr(obj, 'value'):
        return obj.value
    elif hasattr(obj, '__dict__'):
        return str(obj)
    else:
        return obj

async def run_workflow():
    try:
        # Load application data
        with open("{application_file}", 'r') as f:
            app_data = json.load(f)
            
        # Create MortgageApplication object
        application = MortgageApplication(**app_data)
        
        print(f"Processing application {{application.application_id}}")
        print(f"Workflow type: {workflow_type}")
        print()
        
        # Process the application
        use_parallel = "{workflow_type}" == 'parallel'
        execution, decision = await process_mortgage_application_simple(
            application, use_parallel
        )
        
        print(">> Analyzing workflow execution details...")
        print()
        
        # Extract detailed step information
        step_details = {{}}
        agent_results = {{}}
        
        # Get detailed information from execution context
        if hasattr(execution, 'context') and hasattr(execution.context, 'results'):
            for agent_id, result in execution.context.results.items():
                agent_info = {{
                    "agent_name": result.agent_name if hasattr(result, 'agent_name') else agent_id,
                    "assessment_type": result.assessment_type if hasattr(result, 'assessment_type') else "unknown",
                    "risk_score": result.risk_score if hasattr(result, 'risk_score') else None,
                    "risk_level": safe_serialize(result.risk_level) if hasattr(result, 'risk_level') else None,
                    "confidence_level": result.confidence_level if hasattr(result, 'confidence_level') else None,
                    "processing_time_seconds": result.processing_time_seconds if hasattr(result, 'processing_time_seconds') else None,
                    "errors": result.errors if hasattr(result, 'errors') else [],
                    "warnings": result.warnings if hasattr(result, 'warnings') else [],
                    "recommendations": result.recommendations if hasattr(result, 'recommendations') else [],
                    "conditions": result.conditions if hasattr(result, 'conditions') else [],
                    "red_flags": result.red_flags if hasattr(result, 'red_flags') else [],
                    "tool_results": {{}}
                }}
                
                # Extract tool results
                if hasattr(result, 'tool_results') and result.tool_results:
                    for tool_name, tool_result in result.tool_results.items():
                        tool_info = {{
                            "success": tool_result.success if hasattr(tool_result, 'success') else False,
                            "execution_time": tool_result.execution_time if hasattr(tool_result, 'execution_time') else None,
                            "error_message": tool_result.error_message if hasattr(tool_result, 'error_message') else None,
                            "data_summary": {{}}
                        }}
                        
                        # Summarize tool data (avoid huge data dumps)
                        if hasattr(tool_result, 'data') and tool_result.data:
                            data = tool_result.data
                            if isinstance(data, dict):
                                # Extract key metrics from tool data
                                summary = {{}}
                                for key, value in data.items():
                                    if key in ['confidence_score', 'score', 'risk_score', 'ltv_ratio', 'dti_ratio', 
                                             'credit_score', 'estimated_value', 'decision', 'overall_score']:
                                        summary[key] = value
                                    elif 'score' in key.lower() or 'ratio' in key.lower():
                                        summary[key] = value
                                tool_info["data_summary"] = summary
                        
                        agent_info["tool_results"][tool_name] = tool_info
                
                agent_results[agent_id] = agent_info
                
                # Print agent summary
                status_icon = "[OK]" if not agent_info["errors"] else "[ERR]"
                print(f"{{status_icon}} {{agent_info['agent_name']}} ({{agent_id}})")
                print(f"   Risk Level: {{agent_info['risk_level'] or 'N/A'}}")
                print(f"   Risk Score: {{agent_info['risk_score'] or 'N/A'}}")
                print(f"   Confidence: {{agent_info['confidence_level'] or 'N/A'}}")
                print(f"   Processing Time: {{agent_info['processing_time_seconds'] or 'N/A'}}s")
                
                if agent_info["errors"]:
                    print(f"   [!] Errors: {{len(agent_info['errors'])}}")
                    for error in agent_info["errors"][:3]:  # Show first 3 errors
                        print(f"      - {{error}}")
                
                if agent_info["warnings"]:
                    print(f"   [!] Warnings: {{len(agent_info['warnings'])}}")
                    for warning in agent_info["warnings"][:2]:  # Show first 2 warnings
                        print(f"      - {{warning}}")
                
                if agent_info["tool_results"]:
                    print(f"   [T] Tools: {{len(agent_info['tool_results'])}}")
                    for tool_name, tool_info in agent_info["tool_results"].items():
                        tool_status = "[OK]" if tool_info["success"] else "[ERR]"
                        print(f"      {{tool_status}} {{tool_name}} ({{tool_info['execution_time'] or 'N/A'}}s)")
                        if tool_info["error_message"]:
                            print(f"         Error: {{tool_info['error_message']}}")
                        if tool_info["data_summary"]:
                            for key, value in tool_info["data_summary"].items():
                                print(f"         {{key}}: {{value}}")
                
                print()
        
        # Get workflow step details
        if hasattr(execution, 'workflow_definition') and hasattr(execution.workflow_definition, 'steps'):
            for step in execution.workflow_definition.steps:
                step_status = "[OK]" if step.step_id in execution.completed_steps else "[ERR]"
                step_details[step.step_id] = {{
                    "name": step.name,
                    "agent_id": step.agent_id,
                    "status": "completed" if step.step_id in execution.completed_steps else "failed",
                    "started_at": step.started_at.isoformat() if hasattr(step, 'started_at') and step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if hasattr(step, 'completed_at') and step.completed_at else None,
                    "error_message": step.error_message if hasattr(step, 'error_message') else None,
                    "retry_count": step.retry_count if hasattr(step, 'retry_count') else 0
                }}
                
                print(f"{{step_status}} Step: {{step.name}} ({{step.step_id}})")
                print(f"   Agent: {{step.agent_id}}")
                print(f"   Status: {{step_details[step.step_id]['status']}}")
                if step_details[step.step_id]['error_message']:
                    print(f"   Error: {{step_details[step.step_id]['error_message']}}")
                print()
        
        # Analyze loan decision details
        print(">> Loan Decision Analysis:")
        print(f"   Decision: {{decision.decision}}")
        print(f"   Overall Score: {{decision.overall_score}}")
        print(f"   Risk Score: {{decision.decision_factors.risk_score}}")
        print(f"   Eligibility Score: {{decision.decision_factors.eligibility_score}}")
        print(f"   Compliance Score: {{decision.decision_factors.compliance_score}}")
        print(f"   Policy Score: {{decision.decision_factors.policy_score}}")
        
        if decision.adverse_actions:
            print(f"   Adverse Actions: {{len(decision.adverse_actions)}}")
            for action in decision.adverse_actions:
                print(f"      - [{{action.reason_code}}] {{action.reason_description}} ({{action.category}})")
        
        if decision.conditions:
            print(f"   Conditions: {{len(decision.conditions)}}")
            for condition in decision.conditions:
                print(f"      - {{condition}}")
        
        print(f"   Rationale: {{decision.decision_rationale}}")
        print()
        
        # Format comprehensive results
        results = {{
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "progress": execution.get_progress() if hasattr(execution, 'get_progress') else 100,
            "loan_decision": {{
                "decision": decision.decision.value if hasattr(decision.decision, 'value') else str(decision.decision),
                "overall_score": decision.overall_score,
                "decision_factors": {{
                    "eligibility_score": decision.decision_factors.eligibility_score,
                    "risk_score": decision.decision_factors.risk_score,
                    "compliance_score": decision.decision_factors.compliance_score,
                    "policy_score": decision.decision_factors.policy_score
                }},
                "conditions": decision.conditions,
                "adverse_actions": [
                    {{
                        "reason_code": action.reason_code, 
                        "reason_description": action.reason_description,
                        "category": action.category
                    }} for action in decision.adverse_actions
                ],
                "decision_rationale": decision.decision_rationale,
                "loan_terms": {{
                    "available": decision.loan_terms is not None,
                    "details": str(decision.loan_terms) if decision.loan_terms else None
                }}
            }},
            "processing_time": {{
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "total_duration_seconds": (execution.completed_at - execution.started_at).total_seconds() if execution.started_at and execution.completed_at else None
            }},
            "workflow_details": {{
                "completed_steps": list(execution.completed_steps) if hasattr(execution, 'completed_steps') else [],
                "failed_steps": [step_id for step_id, details in step_details.items() if details['status'] == 'failed'],
                "error_message": execution.error_message if hasattr(execution, 'error_message') and execution.error_message else None,
                "total_steps": len(execution.workflow_definition.steps) if hasattr(execution, 'workflow_definition') else 0,
                "step_details": step_details
            }},
            "agent_results": agent_results,
            "summary": {{
                "total_agents": len(agent_results),
                "agents_with_errors": len([a for a in agent_results.values() if a["errors"]]),
                "agents_with_warnings": len([a for a in agent_results.values() if a["warnings"]]),
                "total_tools_executed": sum(len(a["tool_results"]) for a in agent_results.values()),
                "failed_tools": sum(1 for a in agent_results.values() for t in a["tool_results"].values() if not t["success"])
            }}
        }}
        
        # Save comprehensive results
        with open("{output}", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f">> Comprehensive results saved to {output}")
        return True
        
    except Exception as e:
        print(f"[ERR] Error processing application: {{str(e)}}", file=sys.stderr)
        print(f"Full traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

if __name__ == "__main__":
    success = asyncio.run(run_workflow())
    sys.exit(0 if success else 1)
'''
        
        # Write the script to a temporary file with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(script_content)
            temp_script = temp_file.name
        
        try:
            # Run the workflow in a separate process
            result = subprocess.run([
                sys.executable, temp_script
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            # Display the output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        click.echo(line)
            
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    if line.strip():
                        click.echo(line, err=True)
            
            if result.returncode == 0:
                click.echo("✅ Workflow completed successfully!")
            else:
                click.echo("❌ Workflow failed!", err=True)
                sys.exit(1)
                
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(temp_script)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        click.echo("❌ Workflow timed out after 5 minutes", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        # Restore original arguments
        sys.argv = original_argv


@workflow.command()
def list():
    """List active workflow executions."""
    
    async def _list():
        try:
            orchestrator = get_orchestrator()
            active_workflows = orchestrator.list_active_workflows()
            
            if not active_workflows:
                click.echo("No active workflows")
                return
                
            click.echo(f"Active workflows ({len(active_workflows)}):")
            for execution_id in active_workflows:
                status = await orchestrator.get_workflow_status(execution_id)
                if status:
                    click.echo(f"  {execution_id}: {status['status']} ({status.get('progress_percent', 0):.1f}%)")
                    
        except Exception as e:
            click.echo(f"Error listing workflows: {str(e)}", err=True)
            
    asyncio.run(_list())


@workflow.command()
@click.argument('execution_id')
def status(execution_id: str):
    """Get status of a specific workflow execution."""
    
    async def _status():
        try:
            orchestrator = get_orchestrator()
            status_info = await orchestrator.get_workflow_status(execution_id)
            
            if not status_info:
                click.echo(f"Workflow not found: {execution_id}", err=True)
                return
                
            click.echo(f"Workflow Status: {execution_id}")
            click.echo(json.dumps(status_info, indent=2))
            
        except Exception as e:
            click.echo(f"Error getting workflow status: {str(e)}", err=True)
            
    asyncio.run(_status())


@workflow.command()
@click.argument('execution_id')
def cancel(execution_id: str):
    """Cancel a running workflow execution."""
    
    async def _cancel():
        try:
            orchestrator = get_orchestrator()
            success = await orchestrator.cancel_workflow(execution_id)
            
            if success:
                click.echo(f"Workflow cancelled: {execution_id}")
            else:
                click.echo(f"Failed to cancel workflow: {execution_id}", err=True)
                
        except Exception as e:
            click.echo(f"Error cancelling workflow: {str(e)}", err=True)
            
    asyncio.run(_cancel())


@mcp.command()
@click.option('--port', '-p', default=8000, help='Port to run MCP server on')
@click.option('--host', '-h', default='localhost', help='Host to bind MCP server to')
def serve(port: int, host: str):
    """Start the MCP server."""
    
    async def _serve():
        try:
            server = get_mcp_server()
            click.echo(f"Starting MCP server on {host}:{port}")
            
            # This is a placeholder - actual server implementation would go here
            click.echo("MCP server is ready to handle requests")
            click.echo("Press Ctrl+C to stop")
            
            # Keep server running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                click.echo("\nShutting down MCP server")
                
        except Exception as e:
            click.echo(f"Error starting MCP server: {str(e)}", err=True)
            
    asyncio.run(_serve())


@mcp.command()
@click.argument('method')
@click.option('--params', '-p', help='JSON parameters for the request')
def request(method: str, params: Optional[str]):
    """Send a request to the MCP server."""
    
    async def _request():
        try:
            server = get_mcp_server()
            
            # Parse parameters
            request_params = {}
            if params:
                request_params = json.loads(params)
                
            # Create MCP request
            request_data = {
                "jsonrpc": "2.0",
                "method": method,
                "params": request_params,
                "id": "cli_request"
            }
            
            # Send request
            response_str = await server.handle_request(json.dumps(request_data))
            response = json.loads(response_str)
            
            # Display response
            if "error" in response:
                click.echo(f"Error: {response['error']['message']}", err=True)
                if "data" in response["error"]:
                    click.echo(f"Details: {response['error']['data']}")
            else:
                click.echo("Response:")
                click.echo(json.dumps(response["result"], indent=2))
                
        except Exception as e:
            click.echo(f"Error sending MCP request: {str(e)}", err=True)
            
    asyncio.run(_request())


@system.command()
def health():
    """Check system health status."""
    
    async def _health():
        try:
            server = get_mcp_server()
            health_status = await server._handle_system_health({})
            
            click.echo("System Health Status:")
            click.echo(json.dumps(health_status, indent=2))
            
            if health_status["status"] != "healthy":
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error checking system health: {str(e)}", err=True)
            sys.exit(1)
            
    asyncio.run(_health())


@system.command()
@click.option('--hours', '-h', default=24, help='Remove workflows older than this many hours')
def cleanup(hours: int):
    """Clean up old workflow executions."""
    
    async def _cleanup():
        try:
            orchestrator = get_orchestrator()
            removed_count = await orchestrator.cleanup_completed_workflows(hours)
            
            click.echo(f"Cleaned up {removed_count} old workflow executions")
            
        except Exception as e:
            click.echo(f"Error during cleanup: {str(e)}", err=True)
            
    asyncio.run(_cleanup())


@system.command()
def info():
    """Display system information."""
    
    def _info():
        try:
            orchestrator = get_orchestrator()
            
            # Get system info
            agents = orchestrator.agent_manager.get_all_agents()
            tools = orchestrator.tool_manager.tools
            workflows = orchestrator.workflow_engine.workflows
            
            info = {
                "system": {
                    "name": "Mortgage AI Processing System",
                    "version": "1.0.0"
                },
                "components": {
                    "agents": {
                        "count": len(agents),
                        "names": [agent.name for agent in agents]
                    },
                    "tools": {
                        "count": len(tools),
                        "names": list(tools.keys())
                    },
                    "workflows": {
                        "count": len(workflows),
                        "types": list(workflows.keys())
                    }
                }
            }
            
            click.echo("System Information:")
            click.echo(json.dumps(info, indent=2))
            
        except Exception as e:
            click.echo(f"Error getting system info: {str(e)}", err=True)
            
    _info()


@tools.command()
@click.argument('document_path', type=click.Path(exists=True))
@click.option('--document-id', '-i', help='Custom document ID')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
def ocr(document_path: str, document_id: Optional[str], output: Optional[str]):
    """Extract text and data from documents using OCR."""
    
    async def _ocr():
        try:
            from .tools.document.ocr_extractor import DocumentOCRExtractor
            
            # Generate document ID if not provided
            if not document_id:
                import time
                doc_id = f"cli_doc_{int(time.time())}"
            else:
                doc_id = document_id
            
            click.echo(f"Processing document: {document_path}")
            click.echo(f"Document ID: {doc_id}")
            # Use default features
            analysis_features = ['ocr_read', 'layout', 'key_value_pairs', 'tables']
            
            click.echo(f"Features: {', '.join(analysis_features)}")
            
            # Initialize and execute OCR tool
            ocr_tool = DocumentOCRExtractor()
            result = await ocr_tool.execute(
                document_path=document_path,
                document_id=doc_id,
                analysis_features=analysis_features,
                pages='all'
            )
            
            if result.success:
                click.echo("✅ OCR extraction completed successfully!")
                
                # Format results for display
                data = result.data
                summary = {
                    "document_id": data.get("document_id"),
                    "confidence_score": data.get("confidence_score"),
                    "text_length": len(data.get("extracted_text", "")),
                    "key_value_pairs_found": data.get("key_value_pairs_found", 0),
                    "tables_found": data.get("tables_found", 0),
                    "page_count": data.get("page_count", 0),
                    "extraction_method": data.get("extraction_method"),
                    "extraction_timestamp": data.get("extraction_timestamp")
                }
                
                # Output results
                if output:
                    with open(output, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    click.echo(f"Full results saved to: {output}")
                    
                    # Also save summary
                    summary_file = output.replace('.json', '_summary.json')
                    with open(summary_file, 'w') as f:
                        json.dump(summary, f, indent=2, default=str)
                    click.echo(f"Summary saved to: {summary_file}")
                else:
                    click.echo("\nExtraction Summary:")
                    click.echo(json.dumps(summary, indent=2, default=str))
                    
                    # Show sample of extracted text
                    extracted_text = data.get("extracted_text", "")
                    if extracted_text:
                        click.echo(f"\nSample Text (first 200 chars):")
                        click.echo(f"'{extracted_text[:200]}{'...' if len(extracted_text) > 200 else ''}'")
                    
                    # Show key-value pairs if any
                    kvp = data.get("key_value_pairs", [])
                    if kvp:
                        click.echo(f"\nKey-Value Pairs ({len(kvp)}):")
                        for i, pair in enumerate(kvp[:5]):  # Show first 5
                            click.echo(f"  {pair.get('key', 'N/A')}: {pair.get('value', 'N/A')}")
                        if len(kvp) > 5:
                            click.echo(f"  ... and {len(kvp) - 5} more")
                            
            else:
                click.echo(f"❌ OCR extraction failed: {result.error_message}", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error during OCR processing: {str(e)}", err=True)
            sys.exit(1)
            
    asyncio.run(_ocr())


@tools.command()
def list():
    """List all available tools in the system."""
    
    async def _list():
        try:
            orchestrator = get_orchestrator()
            
            click.echo("Available Tools:")
            click.echo("=" * 50)
            
            for tool_name, tool in orchestrator.tool_manager.tools.items():
                click.echo(f"\n📄 {tool_name}")
                click.echo(f"   Description: {tool.description}")
                click.echo(f"   Domain: {getattr(tool, 'agent_domain', 'unknown')}")
                
                # Show which agent uses this tool
                for agent in orchestrator.agent_manager.get_all_agents():
                    if tool_name in agent.get_tool_names():
                        click.echo(f"   Used by: {agent.name} ({agent.agent_id})")
                        break
                        
            click.echo(f"\nTotal: {len(orchestrator.tool_manager.tools)} tools")
            
        except Exception as e:
            click.echo(f"Error listing tools: {str(e)}", err=True)
            
    asyncio.run(_list())


@tools.command()
@click.argument('tool_name')
def info(tool_name: str):
    """Get detailed information about a specific tool."""
    
    async def _info():
        try:
            orchestrator = get_orchestrator()
            
            tool = orchestrator.tool_manager.tools.get(tool_name)
            if not tool:
                click.echo(f"Tool not found: {tool_name}", err=True)
                return
                
            click.echo(f"Tool Information: {tool_name}")
            click.echo("=" * 50)
            click.echo(f"Name: {tool.name}")
            click.echo(f"Description: {tool.description}")
            click.echo(f"Domain: {getattr(tool, 'agent_domain', 'unknown')}")
            
            # Show parameters schema
            schema = tool.get_parameters_schema()
            click.echo(f"\nParameters Schema:")
            click.echo(json.dumps(schema, indent=2))
            
            # Show which agent uses this tool
            for agent in orchestrator.agent_manager.get_all_agents():
                if tool_name in agent.get_tool_names():
                    click.echo(f"\nUsed by Agent: {agent.name} ({agent.agent_id})")
                    break
                    
        except Exception as e:
            click.echo(f"Error getting tool info: {str(e)}", err=True)
            
    asyncio.run(_info())


@tools.command()
@click.argument('tool_name')
@click.option('--params', '-p', help='JSON parameters for the tool')
@click.option('--params-file', '-f', type=click.Path(exists=True), help='JSON file containing parameters')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--show-schema', '-s', is_flag=True, help='Show parameter schema and exit')
def call(tool_name: str, params: Optional[str], params_file: Optional[str], output: Optional[str], show_schema: bool):
    """Call any available tool with specified parameters."""
    
    async def _call():
        try:
            orchestrator = get_orchestrator()
            
            # Get the tool
            tool = orchestrator.tool_manager.tools.get(tool_name)
            if not tool:
                click.echo(f"Tool not found: {tool_name}", err=True)
                click.echo(f"Available tools: {', '.join(orchestrator.tool_manager.tools.keys())}")
                return
            
            # Show schema if requested
            if show_schema:
                schema = tool.get_parameters_schema()
                click.echo(f"Parameter Schema for {tool_name}:")
                click.echo("=" * 50)
                click.echo(json.dumps(schema, indent=2))
                return
            
            # Validate parameters
            if not params and not params_file:
                click.echo(f"Error: Either --params or --params-file is required for tool execution", err=True)
                click.echo(f"Use --show-schema to see required parameters")
                return
            
            # Parse parameters
            try:
                if params_file:
                    with open(params_file, 'r') as f:
                        tool_params = json.load(f)
                else:
                    tool_params = json.loads(params)
            except json.JSONDecodeError as e:
                click.echo(f"Error parsing JSON parameters: {str(e)}", err=True)
                return
            except FileNotFoundError:
                click.echo(f"Error: Parameters file not found: {params_file}", err=True)
                return
            
            click.echo(f"Calling tool: {tool_name}")
            click.echo(f"Parameters: {json.dumps(tool_params, indent=2)}")
            click.echo()
            
            # Execute the tool
            result = await tool.execute(**tool_params)
            
            if result.success:
                click.echo("✅ Tool execution completed successfully!")
                click.echo()
                
                # Display key results
                data = result.data
                if isinstance(data, dict):
                    # Show summary information
                    summary_keys = [
                        'validation_status', 'validation_score', 'risk_score', 'risk_level',
                        'confidence_score', 'decision', 'status', 'success', 'score',
                        'ltv_ratio', 'dti_ratio', 'credit_score', 'estimated_value',
                        'kyc_compliant', 'compliance_score', 'fraud_risk_level'
                    ]
                    
                    click.echo("Summary Results:")
                    click.echo("-" * 30)
                    for key in summary_keys:
                        if key in data:
                            value = data[key]
                            if isinstance(value, float):
                                value = round(value, 2)
                            click.echo(f"{key.replace('_', ' ').title()}: {value}")
                    
                    # Show execution time if available
                    if hasattr(result, 'execution_time') and result.execution_time:
                        click.echo(f"Execution Time: {result.execution_time:.2f}s")
                
                # Save full results if output specified
                if output:
                    with open(output, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    click.echo(f"\nFull results saved to: {output}")
                else:
                    # Show full results if no output file
                    click.echo(f"\nFull Results:")
                    click.echo("-" * 30)
                    click.echo(json.dumps(data, indent=2, default=str))
                    
            else:
                click.echo(f"❌ Tool execution failed: {result.error_message}", err=True)
                
        except Exception as e:
            click.echo(f"Error during tool execution: {str(e)}", err=True)
            import traceback
            if click.get_current_context().obj and click.get_current_context().obj.get('verbose'):
                traceback.print_exc()
            
    asyncio.run(_call())


@agents.command()
def list():
    """List all available agents in the system."""
    
    async def _list():
        try:
            orchestrator = get_orchestrator()
            
            agents = orchestrator.agent_manager.get_all_agents()
            
            click.echo("Available Agents:")
            click.echo("=" * 50)
            
            for agent in agents:
                click.echo(f"\n🤖 {agent.name}")
                click.echo(f"   ID: {agent.agent_id}")
                click.echo(f"   Tools: {len(agent.get_tool_names())}")
                click.echo(f"   Tool Names: {', '.join(agent.get_tool_names())}")
                
            click.echo(f"\nTotal: {len(agents)} agents")
            
        except Exception as e:
            click.echo(f"Error listing agents: {str(e)}", err=True)
            
    asyncio.run(_list())


@agents.command()
@click.argument('agent_id')
def info(agent_id: str):
    """Get detailed information about a specific agent."""
    
    async def _info():
        try:
            orchestrator = get_orchestrator()
            
            agent = orchestrator.agent_manager.get_agent(agent_id)
            if not agent:
                click.echo(f"Agent not found: {agent_id}", err=True)
                return
                
            click.echo(f"Agent Information: {agent_id}")
            click.echo("=" * 50)
            click.echo(f"Name: {agent.name}")
            click.echo(f"ID: {agent.agent_id}")
            click.echo(f"State: {agent.state}")
            
            # Show tools
            tool_names = agent.get_tool_names()
            click.echo(f"\nTools ({len(tool_names)}):")
            for tool_name in tool_names:
                tool = agent.get_tool(tool_name)
                if tool:
                    click.echo(f"  📄 {tool_name}")
                    click.echo(f"     Description: {tool.description}")
                else:
                    click.echo(f"  ❌ {tool_name} (not found)")
                    
        except Exception as e:
            click.echo(f"Error getting agent info: {str(e)}", err=True)
            
    asyncio.run(_info())


@agents.command()
def status():
    """Show status of all agents."""
    
    async def _status():
        try:
            orchestrator = get_orchestrator()
            
            agents = orchestrator.agent_manager.get_all_agents()
            
            click.echo("Agent Status Summary:")
            click.echo("=" * 50)
            
            for agent in agents:
                tool_count = len(agent.get_tool_names())
                status_icon = "✅" if tool_count > 0 else "⚠️"
                
                click.echo(f"{status_icon} {agent.name} ({agent.agent_id})")
                click.echo(f"   Tools: {tool_count}")
                click.echo(f"   State: {agent.state}")
                
            click.echo(f"\nSummary: {len(agents)} agents total")
            
        except Exception as e:
            click.echo(f"Error getting agent status: {str(e)}", err=True)
            
    asyncio.run(_status())


@agents.command()
@click.argument('agent_id')
@click.option('--application-file', '-f', type=click.Path(exists=True), 
              help='JSON file containing mortgage application data')
@click.option('--application-data', '-d', help='JSON string containing application data')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--show-schema', '-s', is_flag=True, help='Show agent input schema and exit')
def test(agent_id: str, application_file: Optional[str], application_data: Optional[str], 
         output: Optional[str], show_schema: bool):
    """Test an individual agent with mortgage application data."""
    
    async def _test():
        try:
            orchestrator = get_orchestrator()
            
            # Get the agent
            agent = orchestrator.agent_manager.get_agent(agent_id)
            if not agent:
                click.echo(f"Agent not found: {agent_id}", err=True)
                available_agents = [a.agent_id for a in orchestrator.agent_manager.get_all_agents()]
                click.echo(f"Available agents: {', '.join(available_agents)}")
                return
            
            # Show schema if requested
            if show_schema:
                click.echo(f"Agent Input Schema for {agent_id}:")
                click.echo("=" * 50)
                click.echo("Expected input: MortgageApplication object with the following structure:")
                click.echo(json.dumps({
                    "application_id": "string",
                    "borrower_info": {
                        "first_name": "string",
                        "last_name": "string", 
                        "ssn": "string",
                        "date_of_birth": "ISO datetime string",
                        "email": "string",
                        "phone": "string",
                        "current_address": "string",
                        "employment_status": "string",
                        "annual_income": "number"
                    },
                    "property_info": {
                        "address": "string",
                        "property_type": "string",
                        "property_value": "number"
                    },
                    "loan_details": {
                        "loan_amount": "number",
                        "loan_type": "string",
                        "loan_term_years": "number",
                        "down_payment": "number",
                        "purpose": "string"
                    },
                    "documents": "array of document objects",
                    "processing_status": "string"
                }, indent=2))
                return
            
            # Validate input
            if not application_file and not application_data:
                click.echo(f"Error: Either --application-file or --application-data is required", err=True)
                click.echo(f"Use --show-schema to see expected input format")
                return
            
            # Load application data
            try:
                if application_file:
                    with open(application_file, 'r') as f:
                        app_data = json.load(f)
                else:
                    app_data = json.loads(application_data)
            except json.JSONDecodeError as e:
                click.echo(f"Error parsing JSON application data: {str(e)}", err=True)
                return
            except FileNotFoundError:
                click.echo(f"Error: Application file not found: {application_file}", err=True)
                return
            
            # Create MortgageApplication object
            try:
                from .models.core import MortgageApplication
                application = MortgageApplication(**app_data)
            except Exception as e:
                click.echo(f"Error creating MortgageApplication object: {str(e)}", err=True)
                click.echo("Use --show-schema to see the expected format")
                return
            
            click.echo(f"Testing agent: {agent.name} ({agent_id})")
            click.echo(f"Application ID: {application.application_id}")
            click.echo(f"Available tools: {', '.join(agent.get_tool_names())}")
            click.echo()
            
            # Execute the agent
            start_time = datetime.now()
            result = await agent.process(application, {})  # Empty context for individual testing
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            if result:
                click.echo("✅ Agent execution completed successfully!")
                click.echo(f"Execution time: {execution_time:.2f}s")
                click.echo()
                
                # Display key results - AssessmentResult objects don't have .data, use the object directly
                data = result.__dict__ if hasattr(result, '__dict__') else result
                if isinstance(data, dict):
                    # Show summary information
                    summary_keys = [
                        'agent_name', 'assessment_type', 'risk_score', 'risk_level',
                        'confidence_level', 'processing_time_seconds', 'overall_score',
                        'decision', 'status', 'validation_status', 'compliance_score'
                    ]
                    
                    click.echo("Agent Results Summary:")
                    click.echo("-" * 30)
                    for key in summary_keys:
                        if key in data:
                            value = data[key]
                            if isinstance(value, float):
                                value = round(value, 2)
                            click.echo(f"{key.replace('_', ' ').title()}: {value}")
                    
                    # Show errors and warnings
                    if 'errors' in data and data['errors']:
                        click.echo(f"\n⚠️  Errors ({len(data['errors'])}):")
                        for error in data['errors'][:3]:  # Show first 3
                            click.echo(f"   - {error}")
                    
                    if 'warnings' in data and data['warnings']:
                        click.echo(f"\n⚠️  Warnings ({len(data['warnings'])}):")
                        for warning in data['warnings'][:3]:  # Show first 3
                            click.echo(f"   - {warning}")
                    
                    # Show tool results summary
                    if 'tool_results' in data and data['tool_results']:
                        click.echo(f"\n🔧 Tool Results ({len(data['tool_results'])}):")
                        for tool_name, tool_result in data['tool_results'].items():
                            if hasattr(tool_result, 'success'):
                                status = "✅" if tool_result.success else "❌"
                                exec_time = getattr(tool_result, 'execution_time', 'N/A')
                                click.echo(f"   {status} {tool_name} ({exec_time}s)")
                
                # Save full results if output specified
                if output:
                    result_data = {
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                        "application_id": application.application_id,
                        "execution_time_seconds": execution_time,
                        "result": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    with open(output, 'w') as f:
                        json.dump(result_data, f, indent=2, default=str)
                    click.echo(f"\nFull results saved to: {output}")
                else:
                    # Show full results if no output file
                    click.echo(f"\nFull Agent Results:")
                    click.echo("-" * 30)
                    click.echo(json.dumps(data, indent=2, default=str))
                    
            else:
                click.echo(f"❌ Agent execution failed - no result returned", err=True)
        except Exception as e:
            click.echo(f"Error during agent testing: {str(e)}", err=True)
            import traceback
            if click.get_current_context().obj and click.get_current_context().obj.get('verbose'):
                traceback.print_exc()
            
    asyncio.run(_test())


def create_sample_application() -> MortgageApplication:
    """Create a sample mortgage application for testing."""
    return MortgageApplication(
        application_id=f"CLI-SAMPLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        borrower_info=BorrowerInfo(
            first_name="John",
            last_name="Doe",
            ssn="123-45-6789",
            date_of_birth=datetime(1985, 6, 15),
            email="john.doe@example.com",
            phone="555-123-4567",
            current_address="123 Main St, Anytown, ST 12345",
            employment_status="Employed",
            annual_income=Decimal("75000")
        ),
        property_info=PropertyInfo(
            address="456 Oak Ave, Testville, ST 67890",
            property_type="Single Family Home",
            property_value=Decimal("300000")
        ),
        loan_details=LoanDetails(
            loan_amount=Decimal("240000"),
            loan_type=LoanType.CONVENTIONAL,
            loan_term_years=30,
            down_payment=Decimal("60000"),
            purpose="Purchase"
        ),
        documents=[],
        processing_status=ProcessingStatus.PENDING
    )


if __name__ == '__main__':
    try:
        cli()
    except SystemExit as e:
        # Handle normal CLI exits
        sys.exit(e.code)
    except Exception as e:
        # Handle unexpected errors
        click.echo(f"Unexpected CLI error: {str(e)}", err=True)
        sys.exit(1)

