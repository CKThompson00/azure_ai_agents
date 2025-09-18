"""
Invoice Agent API for Azure Container Apps
A Flask API that wraps the Azure AI Agents invoice processing functionality
"""

from flask import Flask, request, jsonify
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.ai.agents.models import ListSortOrder
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class InvoiceAgentService:
    def __init__(self):
        self.project_client = None
        self.agent_id = None
        self.setup_client()
    
    def setup_client(self):
        """Setup Azure AI Project client with appropriate authentication"""
        try:
            # Get configuration from environment variables
            endpoint = os.getenv('AZURE_AI_PROJECT_ENDPOINT')
            self.agent_id = os.getenv('AZURE_AI_AGENT_ID')
            
            # Try Managed Identity first (for Azure Container Apps), then DefaultAzureCredential
            # try:
            #     credential = ManagedIdentityCredential()
            #     logger.info("Using Managed Identity for authentication")
            # except Exception:
            credential = DefaultAzureCredential()
            logger.info("Using Default Azure Credential for authentication")
            
            self.project_client = AIProjectClient(
                credential=credential,
                endpoint=endpoint
            )
            
            # Test the connection
            agent = self.project_client.agents.get_agent(self.agent_id)
            logger.info(f"Successfully connected to agent: {agent.name if hasattr(agent, 'name') else 'Unknown'}")
            
        except Exception as e:
            logger.error(f"Failed to setup Azure AI Project client: {str(e)}")
            raise
    
    def process_invoice_message(self, user_message, thread_id=None):
        """Process a message using the invoice agent"""
        try:
            # Create a new thread if not provided
            if not thread_id:
                thread = self.project_client.agents.threads.create()
                thread_id = thread.id
                logger.info(f"Created new thread: {thread_id}")
            
            # Create user message
            message = self.project_client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )
            
            # Run the agent
            run = self.project_client.agents.runs.create_and_process(
                thread_id=thread_id,
                agent_id=self.agent_id
            )
            
            if run.status == "failed":
                error_msg = f"Agent run failed: {run.last_error}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "thread_id": thread_id
                }
            
            # Get messages from the thread
            messages = self.project_client.agents.messages.list(
                thread_id=thread_id, 
                order=ListSortOrder.ASCENDING
            )
            
            # Format response
            conversation = []
            for msg in messages:
                if msg.text_messages:
                    conversation.append({
                        "role": msg.role,
                        "content": msg.text_messages[-1].text.value,
                        "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') else datetime.now().isoformat()
                    })
            
            return {
                "success": True,
                "thread_id": thread_id,
                "conversation": conversation,
                "run_status": run.status
            }
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "thread_id": thread_id
            }

# Initialize the service
try:
    invoice_service = InvoiceAgentService()
except Exception as e:
    logger.error(f"Failed to initialize invoice service: {str(e)}")
    invoice_service = None

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Invoice Agent API",
        "timestamp": datetime.now().isoformat(),
        "agent_available": invoice_service is not None
    })

@app.route('/api/invoice/chat', methods=['POST'])
def chat_with_agent():
    """Chat with the invoice agent"""
    if not invoice_service:
        return jsonify({
            "success": False,
            "error": "Invoice service not available"
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'message' in request body"
            }), 400
        
        user_message = data['message']
        thread_id = data.get('thread_id')  # Optional - will create new if not provided
        
        result = invoice_service.process_invoice_message(user_message, thread_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/invoice/new-thread', methods=['POST'])
def create_new_thread():
    """Create a new conversation thread"""
    if not invoice_service:
        return jsonify({
            "success": False,
            "error": "Invoice service not available"
        }), 503
    
    try:
        thread = invoice_service.project_client.agents.threads.create()
        return jsonify({
            "success": True,
            "thread_id": thread.id,
            "created_at": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to create thread: {str(e)}"
        }), 500

@app.route('/api/invoice/thread/<thread_id>/messages', methods=['GET'])
def get_thread_messages(thread_id):
    """Get all messages from a thread"""
    if not invoice_service:
        return jsonify({
            "success": False,
            "error": "Invoice service not available"
        }), 503
    
    try:
        messages = invoice_service.project_client.agents.messages.list(
            thread_id=thread_id,
            order=ListSortOrder.ASCENDING
        )
        
        conversation = []
        for msg in messages:
            if msg.text_messages:
                conversation.append({
                    "role": msg.role,
                    "content": msg.text_messages[-1].text.value,
                    "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') else datetime.now().isoformat()
                })
        
        return jsonify({
            "success": True,
            "thread_id": thread_id,
            "messages": conversation
        })
        
    except Exception as e:
        logger.error(f"Error getting thread messages: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to get messages: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)