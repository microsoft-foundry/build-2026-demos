# Retail Agent in LangGraph

A multi-turn conversational tool-calling agent built with [LangGraph](https://langchain-ai.github.io/langgraph/) and deployable as a Hosted Agent on Foundry.

## Agent details

- Retail agent that assists customers with orders, returns, shipping, and product inquiries. It has access to tools that read and write order data to a local database.
- Built with LangGraph with an agentic loop to perform tool calls and manage conversation flow.
- Uses AgentServer to expose a responses-style API for multi-turn conversations with server-side state management.
- Calls Foundry Model Deployment backed by Azure OpenAI to generate chat completions and agent actions.
- Saves traces to Application Insights connected to Foundry for observability.

## Architecture

```
+--------------------+                   +----------------------------------+
|                    |                   | Retail Agent                     |                            +----------------------+
| User or client app |   --- POST -->    | LangGraph loop                   | -- Db calls from tools --> | Database             |
|                    |    /responses     | chatbot -> tools -> chatbot      |                            +----------------------+
| JSON body:         |                   |                                  |
| - input            |                   | tools:                           |                            +----------------------+
| - previous_        |                   | - find_user_id_by_email()        | -- /chat/completions -->   | Azure OpenAI LLM     |
|   response_id?     |                   | - list_user_orders()             |                            +----------------------+
|                    |                   | - ...                            |
+--------------------+                   +----------------------------------+
                                                  |
                                                  | traces
                                                  v
                                        +-------------------------+
                                        | Application Insights    |
                                        |                         |
                                        +-------------------------+
```

## Deploy to Foundry

### Prerequisites

- [Install Azure Developer CLI (azd)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux&pivots=os-windows)
- Install the Azure AI Agents extension for `azd`: `azd ext install azure.ai.agents`


### Initial steps for existing Foundry project

Please note:
- Your Foundry project must have a model deployment with `gpt-4.1` name.
- Your Foundry project must be connected to Application Insights for traces.
- Below commands have been tested on PowerShell. Adjust syntax as needed for other shells.

```shell
azd auth login

# Replace placeholders with your project details
$env:FOUNDRY_PROJECT_ID="/subscriptions/<YOUR_SUBSCRIPTION_ID>/resourceGroups/<YOUR_RESOURCE_GROUP>/providers/Microsoft.CognitiveServices/accounts/<YOUR_ACCOUNT_NAME>/projects/<YOUR_PROJECT_NAME>"

# Run from parent directory of retail_agent/
azd ai agent init -m retail_agent/agent.manifest.yaml --project-id $FOUNDRY_PROJECT_ID --model gpt-4.1
azd env set enableHostedAgentVNext true
```


### Initial steps for a new Foundry project

Skip this if you've already followed above steps for an existing project.

```shell
azd auth login
azd ai agent init -m retail_agent/agent.manifest.yaml
azd env set enableHostedAgentVNext=true
pip install keyring artifacts-keyring
azd provision
```


### Deploy Agent steps

```shell
azd deploy

# Grant "Azure AI User" role to the agent's identity so it can use the Foundry project resources
$AgentIdentityClientId = (azd ai agent show -o table | Select-String "Instance Identity Client ID").Line -replace ".*Client ID\s+",""
az role assignment create --assignee $AgentIdentityClientId --role "Azure AI User" --scope $FOUNDRY_PROJECT_ID
```


### Invoke Agent

```shell
azd ai agent invoke "Please share my orders. My email is ava.moore2222@example.com"
```


## Troubleshooting

### Agent init fails with: "create_agent: HTTP request failed: AzureDeveloperCLICredential"

If `azd ai agent init` fails with the following error, then run `azd auth logout` and `azd auth login` to refresh your credentials and try again.

```
create_agent: HTTP request failed: AzureDeveloperCLICredential: please run "azd auth login" from a command prompt to authenticate before using this credential
```
