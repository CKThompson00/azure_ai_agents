"""
Test client for Invoice Agent API
"""

import requests
import json
import time

class InvoiceAgentClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self):
        """Check if the API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def create_thread(self):
        """Create a new conversation thread"""
        try:
            response = self.session.post(f"{self.base_url}/api/invoice/new-thread")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, message, thread_id=None):
        """Send a message to the invoice agent"""
        try:
            payload = {"message": message}
            if thread_id:
                payload["thread_id"] = thread_id
            
            response = self.session.post(
                f"{self.base_url}/api/invoice/chat",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_messages(self, thread_id):
        """Get all messages from a thread"""
        try:
            response = self.session.get(f"{self.base_url}/api/invoice/thread/{thread_id}/messages")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def test_local():
    """Test the API running locally"""
    client = InvoiceAgentClient("http://localhost:8000")
    
    print("Testing Invoice Agent API locally...")
    
    # Health check
    print("\nHealth Check:")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    # Create thread
    print("\nCreating new thread:")
    thread_result = client.create_thread()
    print(json.dumps(thread_result, indent=2))
    
    if thread_result.get("success"):
        thread_id = thread_result["thread_id"]
        
        # Send message
        print("\nSending message:")
        chat_result = client.chat("", thread_id)
        # print(json.dumps(chat_result, indent=2))
        
        # Get all messages
        print("\nResults:")
        messages_result = client.get_messages(thread_id)
        # print(json.dumps(messages_result, indent=2))
        # Print only the latest message (robust to a few common response shapes)
        msgs = messages_result.get("messages")[-1].get("content")
        msgs_json = json.loads(msgs)
        for item in msgs_json:
            print(item)

    # print(json.dumps(messages_result, indent=2))
    # Print only the latest message (robust to a few common response shapes)
    msgs = messages_result.get("messages")[-1].get("content")
    msgs_json = json.loads(msgs)
    for item in msgs_json:
        print(item)

def test_azure(app_url):
    """Test the API running on Azure Container Apps"""
    client = InvoiceAgentClient(app_url)
    
    print(f"Testing Invoice Agent API on Azure: {app_url}")
    
    # Health check
    print("\n1. Health Check:")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    # Test chat without creating thread first
    print("\n2. Sending message (auto-create thread):")
    chat_result = client.chat("Hi Invoice Data Extraction Agent")
    print(json.dumps(chat_result, indent=2))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test Azure deployment
        azure_url = sys.argv[1]
        test_azure(azure_url)
    else:
        # Test local
        test_local()