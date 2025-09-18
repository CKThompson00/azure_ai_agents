# Azure Container Apps Deployment Script for Invoice Agent (PowerShell)
# Make sure you have Azure CLI installed and are logged in

param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [string]$ResourceGroup = "invoice-agent-rg",
    [string]$Location = "eastus2",
    [string]$ContainerAppEnv = "invoice-agent-env",
    [string]$ContainerAppName = "invoice-agent-app",
    [string]$AcrName = "invoiceagentacr",
    [string]$ImageName = "invoice-agent",
    [string]$ImageTag = "latest",
    [string]$AzureAIProjectEndpoint = "",
    [string]$AzureAIAgentId = ""
)

Write-Host "Starting deployment of Invoice Agent to Azure Container Apps..." -ForegroundColor Green

try {
    # Set subscription
    Write-Host "Setting Azure subscription..." -ForegroundColor Yellow
    az account set --subscription $SubscriptionId

    # Create resource group
    Write-Host "Creating resource group..." -ForegroundColor Yellow
    az group create --name $ResourceGroup --location $Location

    # Create Azure Container Registry
    Write-Host "Creating Azure Container Registry..." -ForegroundColor Yellow
    az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true

    # Get ACR login server
    $AcrLoginServer = az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer --output tsv

    # Build and push image
    Write-Host "Building and pushing Docker image..." -ForegroundColor Yellow
    az acr build --registry $AcrName --image "${ImageName}:${ImageTag}" --file Dockerfile .

    # Create Container Apps environment
    Write-Host "Creating Container Apps environment..." -ForegroundColor Yellow
    az containerapp env create --name $ContainerAppEnv --resource-group $ResourceGroup --location $Location

    # Create managed identity for the container app
    Write-Host "Creating managed identity..." -ForegroundColor Yellow
    $IdentityId = az identity create --resource-group $ResourceGroup --name "${ContainerAppName}-identity" --query id --output tsv
    $IdentityClientId = az identity show --ids $IdentityId --query clientId --output tsv

    # Get ACR password
    $AcrPassword = az acr credential show --name $AcrName --query passwords[0].value --output tsv

    # Create the container app
    Write-Host "Creating container app..." -ForegroundColor Yellow
    az containerapp create `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --environment $ContainerAppEnv `
        --image "${AcrLoginServer}/${ImageName}:${ImageTag}" `
        --registry-server $AcrLoginServer `
        --registry-username $AcrName `
        --registry-password $AcrPassword `
        --target-port 8000 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 10 `
        --cpu 0.5 `
        --memory 1.0Gi `
        --assign-identity $IdentityId `
        --env-vars AZURE_AI_PROJECT_ENDPOINT=$AzureAIProjectEndpoint AZURE_AI_AGENT_ID=$AzureAIAgentId PORT=8000 AZURE_CLIENT_ID=$IdentityClientId

    # Get the app URL
    $AppUrl = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Application URL: https://$AppUrl" -ForegroundColor Cyan
    Write-Host "Health check: https://$AppUrl/" -ForegroundColor Cyan
    Write-Host "Chat API: https://$AppUrl/api/invoice/chat" -ForegroundColor Cyan

    Write-Host ""
    Write-Host "To test the API, you can use:" -ForegroundColor Yellow
    Write-Host "Invoke-RestMethod -Uri 'https://$AppUrl/api/invoice/chat' -Method POST -ContentType 'application/json' -Body '{\"message\": \"Hi Invoice Data Extraction Agent\"}'" -ForegroundColor White

} catch {
    Write-Error "Deployment failed: $_"
    exit 1
}