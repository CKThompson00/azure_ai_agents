#!/bin/bash

# Azure Container Apps Deployment Script for Invoice Agent
# Make sure you have Azure CLI installed and are logged in

set -e

# Configuration - Update these variables
SUBSCRIPTION_ID="your-subscription-id"
RESOURCE_GROUP="invoice-agent-rg"
LOCATION="eastus2"
CONTAINER_APP_ENV="invoice-agent-env"
CONTAINER_APP_NAME="invoice-agent-app"
ACR_NAME="invoiceagentacr"
IMAGE_NAME="invoice-agent"
IMAGE_TAG="latest"

# Azure AI Configuration
AZURE_AI_PROJECT_ENDPOINT=""
AZURE_AI_AGENT_ID=""

echo "Starting deployment of Invoice Agent to Azure Container Apps..."

# Set subscription
echo "Setting Azure subscription..."
az account set --subscription $SUBSCRIPTION_ID

# Create resource group
echo "Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create Azure Container Registry
echo "Creating Azure Container Registry..."
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Build and push image
echo "Building and pushing Docker image..."
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:$IMAGE_TAG \
  --file Dockerfile \
  .

# Create Container Apps environment
echo "Creating Container Apps environment..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create managed identity for the container app
echo "Creating managed identity..."
IDENTITY_ID=$(az identity create \
  --resource-group $RESOURCE_GROUP \
  --name "${CONTAINER_APP_NAME}-identity" \
  --query id --output tsv)

IDENTITY_CLIENT_ID=$(az identity show \
  --ids $IDENTITY_ID \
  --query clientId --output tsv)

# Create the container app
echo "Creating container app..."
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_NAME \
  --registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv) \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --assign-identity $IDENTITY_ID \
  --env-vars \
    AZURE_AI_PROJECT_ENDPOINT=$AZURE_AI_PROJECT_ENDPOINT \
    AZURE_AI_AGENT_ID=$AZURE_AI_AGENT_ID \
    PORT=8000 \
    AZURE_CLIENT_ID=$IDENTITY_CLIENT_ID

# Get the app URL
APP_URL=$(az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

echo "Deployment completed successfully!"
echo "Application URL: https://$APP_URL"
echo "Health check: https://$APP_URL/"
echo "Chat API: https://$APP_URL/api/invoice/chat"

echo ""
echo "To test the API, you can use:"
echo "curl -X POST https://$APP_URL/api/invoice/chat \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": \"Hi Invoice Data Extraction Agent\"}'"