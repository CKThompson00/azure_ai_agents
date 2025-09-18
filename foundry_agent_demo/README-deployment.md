# Invoice Agent API - Azure Container Apps Deployment

This project converts the invoice_agent.py script into a containerized REST API that can be deployed to Azure Container Apps.

## Architecture

- **Flask API**: REST endpoints for invoice processing
- **Azure AI Agents**: Backend invoice processing using Azure AI
- **Managed Identity**: Secure authentication to Azure services
- **Gunicorn**: Production WSGI server
- **Docker**: Containerization for consistent deployment

## API Endpoints

### Health Check
```
GET /
```
Returns API health status and availability.

### Chat with Invoice Agent
```
POST /api/invoice/chat
Content-Type: application/json

{
  "message": "Hi Invoice Data Extraction Agent",
  "thread_id": "optional-existing-thread-id"
}
```

### Create New Thread
```
POST /api/invoice/new-thread
```
Creates a new conversation thread.

### Get Thread Messages
```
GET /api/invoice/thread/{thread_id}/messages
```
Retrieves all messages from a specific thread.

## Prerequisites

1. **Azure CLI** installed and configured
2. **Docker** installed (for local testing)
3. **Azure subscription** with appropriate permissions
4. **Azure AI Project** with invoice agent configured

## Configuration

Update the following variables in the deployment scripts:

- `SUBSCRIPTION_ID`: Your Azure subscription ID
- `RESOURCE_GROUP`: Resource group name
- `AZURE_AI_PROJECT_ENDPOINT`: Your Azure AI project endpoint
- `AZURE_AI_AGENT_ID`: Your invoice agent ID

## Local Development

1. Install dependencies:
```bash
pip install -r requirements-container.txt
```

2. Set environment variables:
```bash
export AZURE_AI_PROJECT_ENDPOINT="your-endpoint"
export AZURE_AI_AGENT_ID="your-agent-id"
```

3. Run locally:
```bash
python invoice_agent_api.py
```

4. Test the API:
```bash
python test_api.py
```

## Docker Testing

1. Build the image:
```bash
docker build -t invoice-agent .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e AZURE_AI_PROJECT_ENDPOINT="your-endpoint" \
  -e AZURE_AI_AGENT_ID="your-agent-id" \
  invoice-agent
```

3. Test:
```bash
curl http://localhost:8000/
```

## Azure Container Apps Deployment

### Option 1: PowerShell (Windows)
```powershell
.\deploy.ps1 -SubscriptionId "your-subscription-id"
```

### Option 2: Bash (Linux/Mac)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Deployment Steps

1. **Create Resource Group**:
```bash
az group create --name invoice-agent-rg --location eastus2
```

2. **Create Container Registry**:
```bash
az acr create --resource-group invoice-agent-rg --name invoiceagentacr --sku Basic --admin-enabled true
```

3. **Build and Push Image**:
```bash
az acr build --registry invoiceagentacr --image invoice-agent:latest --file Dockerfile .
```

4. **Create Container Apps Environment**:
```bash
az containerapp env create --name invoice-agent-env --resource-group invoice-agent-rg --location eastus2
```

5. **Create Managed Identity**:
```bash
az identity create --resource-group invoice-agent-rg --name invoice-agent-identity
```

6. **Deploy Container App**:
```bash
az containerapp create \
  --name invoice-agent-app \
  --resource-group invoice-agent-rg \
  --environment invoice-agent-env \
  --image invoiceagentacr.azurecr.io/invoice-agent:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10
```

## Testing the Deployed API

1. Get the application URL:
```bash
az containerapp show --name invoice-agent-app --resource-group invoice-agent-rg --query properties.configuration.ingress.fqdn --output tsv
```

2. Test with curl:
```bash
curl -X POST https://your-app-url.azurecontainerapps.io/api/invoice/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi Invoice Data Extraction Agent"}'
```

3. Test with Python:
```bash
python test_api.py https://your-app-url.azurecontainerapps.io
```

## Security Features

- **Managed Identity**: No stored credentials
- **Non-root user**: Container runs as non-privileged user
- **HTTPS**: External ingress uses TLS
- **Environment variables**: Sensitive config via env vars
- **Health checks**: Kubernetes-style health monitoring

## Monitoring

- **Application Insights**: Enable for detailed telemetry
- **Container Apps logs**: View via Azure portal
- **Health endpoint**: Monitor service availability
- **Scaling metrics**: Auto-scale based on HTTP requests

## Troubleshooting

1. **Check logs**:
```bash
az containerapp logs show --name invoice-agent-app --resource-group invoice-agent-rg --follow
```

2. **Verify environment variables**:
```bash
az containerapp show --name invoice-agent-app --resource-group invoice-agent-rg
```

3. **Test connectivity**:
```bash
az containerapp exec --name invoice-agent-app --resource-group invoice-agent-rg --command /bin/bash
```

## File Structure

```
├── invoice_agent_api.py          # Main Flask API
├── invoice_agent.py              # Original script
├── Dockerfile                    # Container definition
├── gunicorn.conf.py             # Production server config
├── requirements-container.txt    # Python dependencies
├── containerapp.yaml           # Container Apps template
├── deploy.sh                    # Bash deployment script
├── deploy.ps1                   # PowerShell deployment script
├── test_api.py                  # API test client
├── .dockerignore               # Docker ignore file
└── README.md                   # This file
```

## Cost Optimization

- **Auto-scaling**: Scales to zero when not in use
- **Resource limits**: CPU and memory limits prevent overspend
- **Single replica minimum**: Reduces baseline costs
- **Shared infrastructure**: Container Apps environment shared across apps

## Next Steps

1. **Custom domain**: Configure custom domain and SSL
2. **Authentication**: Add Azure AD authentication
3. **Rate limiting**: Implement API rate limiting
4. **Monitoring**: Set up Application Insights
5. **CI/CD**: Implement GitHub Actions for deployment