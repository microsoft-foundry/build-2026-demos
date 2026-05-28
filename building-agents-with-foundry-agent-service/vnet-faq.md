# vNet / Private Networking – FAQ for Foundry Agent Service

**VNET = virtual network support. The proper term is network isolation.**

## Quick Tip for Booth Experts
  
* Start with: ‘Are you trying to keep all agent traffic private (no public egress), or do you just need private access to specific resources like Key Vault / SQL / AI Search?’
* Then confirm the agent type (prompt vs workflow vs hosted) and required tools, because private networking support and traffic flow can differ by tool.

## Availability & Support

### Do Foundry agents support VNet / private networking today?
  
Yes, absolutely. Foundry Agent Service has a Standard Setup with private networking—basically a BYO VNet approach—that gives you an isolated network environment with private endpoints, private DNS, and deny-by-default rules. Out of the box, there's no public egress, and your private resources are accessible as long as you've set up the right credentials and authorization.

### Is VNet support available for both hosted agents and prompt agents?
  
Yes, VNet support is available for both prompt and hosted agents. They are supported in the same way with the Agent scenario VNet injection. Workflow agents support inbound access (UI, SDK, CLI) but outbound VNet injection is NOT currently supported for workflow agents. Also note: for hosted agents, the VNet injection must be configured when you first create the Foundry account—you can't add it after the fact. And the Azure Container Registry (ACR) for hosted agents must have public network access enabled; private ACR is not yet supported.  

### Is private networking GA or still in preview?
  
BYO VNet and inbound private endpoint support are GA in the Foundry Agent Service feature summaries. Managed Virtual Network is GA as well. But even within GA, some adjacent capabilities—like certain tools running through the VNet—may or may not be supported depending on the specific tool and traffic path.

## Architecture & Traffic Flow

### How does traffic flow when using agents with VNet?
  
Think of it as two networks working together. There's a Microsoft-managed platform network that hosts the Foundry endpoint and platform services, and then there's your customer VNet with a delegated subnet and private endpoints. When a request comes in, it hits the Foundry endpoint first, then tool calls go out through the Agent client that's been injected into your delegated subnet, routing into your VNet to reach your private endpoints.

### Does the agent runtime stay entirely inside my VNet, or does it call out to managed services?
  
No, it doesn't stay entirely inside your VNet. The Foundry endpoint and platform services live on Microsoft-managed infrastructure. What happens is that outbound connectivity to your private resources gets routed into your VNet through VNet injection of the Agent client into your delegated subnet. Some tool traffic may also go over the Microsoft backbone or even public endpoints, depending on which tool you're using.

### What dependencies require outbound access (models, tools, storage, etc.)?
  
With the private networking Standard Setup, the deployment templates provision or connect customer-owned resources like Azure Storage, Cosmos DB, and AI Search—and all of those are reached through private endpoints and private DNS. Tool calls and data access typically route through the injected Agent client to those private endpoints. If you enable specific tools or external APIs that need additional outbound access, you may need to open that up separately.

## Integration with Enterprise Systems

### Can agents access resources inside my VNet (databases, APIs, internal services)?
  
Yes, that's a core part of the design. The private networking setup lets the platform reach resources that are completely private and not discoverable from the internet—as long as you've configured the right credentials and authorization. Tool calls go through the injected Agent client into your VNet to hit those private endpoints and services.

### How do I connect agents to private data sources securely?
  
Set up private endpoints for your Azure dependencies—things like Storage, Cosmos DB, AI Search—and make sure your private DNS zones are linked so names resolve to private IPs. Then use the Standard Setup with private networking (BYO VNet), and agent egress will route through your VNet with deny-by-default rules in place.

### Can agents call services behind private endpoints?
  
Yes, they can. The standard private networking model uses private endpoints to lock down connectivity to key dependent resources, and the data proxy handles routing outbound traffic to those endpoints. If you're calling other private services beyond the defaults, just make sure routing, DNS, and authorization are all configured so the data proxy can actually reach them.

## Private Link vs VNet Injection

### Does Foundry use private endpoints or full VNet injection?
  
It actually uses both, but for different things. Private Link and private endpoints handle isolating PaaS resources and securing inbound access. VNet injection is used for the Agent client and data proxy—those get injected into a delegated subnet so that outbound tool and data traffic stays within your network boundaries.

### What components support Private Link today (agents, models, storage, etc.)?
  
In the Standard Setup with private networking, you get private endpoints for Foundry itself, Azure AI Search, Azure Storage, and Azure Cosmos DB. Private DNS zones are configured for the matching privatelink domains so that both clients and platform components resolve those endpoints to private IP addresses.

### Do I need to configure Private Link manually?
  
Yes, for some of them you do. Private endpoints to Azure AI Search, Azure Storage, and Azure Cosmos DB aren't auto-created when you deploy your Foundry resource—you have to create those separately. You also need to make sure DNS is set up properly, either through Azure Private DNS or your own DNS with conditional forwarders.

## Cross-Service Networking

### How does networking work between Foundry Agents, Azure AI Search, storage, and custom tools?
  
Tool calls go through the single-tenant data proxy into your VNet and reach your resources—Search, Storage, Cosmos—through private endpoints. Now, not every tool follows the same path: some route through your VNet, some use the Microsoft backbone, and some go over public endpoints. It really depends on the specific tool.

### Do all dependent services need to be in the same VNet?
  
They don't all have to be in the same VNet—VNet peering is a common way to connect them. Just make sure your peered VNets don't have overlapping IP ranges. Your Foundry and VNET must be in the same region, but there is no requirement for your CosmosDB, Search and Storage to be in the same region. 

### Can agents securely call services across VNets?
  
Yes, you can do that with VNet peering, but the networks have to use unique, non-overlapping IP ranges or you'll run into routing failures. If you can't avoid IP overlap, the guidance recommends looking at the managed virtual network option instead of BYO VNet.

## Security & Compliance

### How is data protected in transit when using agents in a VNet?
  
The Standard Setup with private networking uses private endpoints and private DNS so traffic to your key data resources stays on private IPs, with deny-by-default rules across the board. That said, some tool traffic can stay on Microsoft's backbone—like Code Interpreter and Function Calling in certain configurations—while other tools might use public endpoints. So the protection level really depends on which tools you're using.

### Does private networking ensure data never leaves my network boundary?
  
Not automatically for every tool—that's an important caveat. Even in a network-isolated environment, some tools communicate over public endpoints. Bing grounding, web search, and SharePoint grounding are examples of that. So if your compliance requirements say all traffic must stay private, you'll need to disable those tools and carefully validate the traffic paths for whatever tools you do keep enabled.

### Which compliance scenarios does VNet support enable?
  
Private networking gives you network isolation and helps meet compliance and data residency requirements by running agents within your virtual network using customer-managed resources. This matters most for regulated workloads where you need strong network boundaries, restricted egress, and private-only access to your data stores.

## Identity & Authentication

### How do agents authenticate when accessing resources inside a VNet?
  
You'll need RBAC role assignments, and for standard setups, you need permissions to assign roles to connected resources like Storage, Cosmos DB, and AI Search. On the tool side, there's support for managed authentication patterns—things like service-managed credentials and On-Behalf-Of (OBO) authentication for the tools that support it.

### Can I use Managed Identity with private resources?
  
Yes, you can. Managed Identity authentication is part of the Foundry Agent Service feature set, and the private networking guidance includes firewall allowlisting steps for managed identity traffic—for example, allowing required FQDNs or the AzureActiveDirectory service tag.

### How is identity propagated across agent tool calls?
  
For tools that support it, Foundry offers managed authentication options including OBO, which lets you do per-user identity propagation. For other tools, calls may use service-managed credentials or the project/agent identity—it depends on how you've configured the tool and your access model.

## Limitations & Trade-offs

### What are the current limitations of VNet support for agents?
  
Tool support varies quite a bit. Some tools work through the VNet, some go over the Microsoft backbone, and some aren't supported yet—or are still under development—in network-isolated setups. On top of that, there are specific callouts like hosted-agent private networking not being available during preview, and workflow-agent outbound injection not being supported in certain configurations.

### Are any features unavailable when private networking is enabled?
  
Yes, and it's not uniform across the board. Some tools are explicitly marked as not supported or under development in network-isolated environments, and certain platform features are called out as not supporting network isolation. Always check the tool-by-tool matrix (in docs) before committing to a fully private design—you don't want surprises later.

### Does VNet impact latency or performance?
  
Scaling itself doesn't introduce latency or performance degradation—that's the good news. The real risk is IP exhaustion in your delegated subnet, which can block scaling and cause failures. So capacity planning for the delegated subnet, and monitoring for data proxy 5xx errors, is part of the operational trade-off when you go with BYO VNet.

## Deployment & Setup

### How do I enable VNet support for agents?
  
For the Standard Setup with private networking, you need to deploy programmatically using Bicep or Terraform—the templates handle provisioning networking resources and connecting your Foundry account and project to customer-owned dependencies. There's also a portal-based flow for setting up private endpoints and VNet injection, but it only shows up after you select BYO resources and disable public network access.

### What Azure resources and configurations are required?
  
You'll typically need a BYO VNet with two subnets—one as the agent delegated subnet and one for private endpoints. Then you set up private endpoints for Foundry and your dependent services, along with private DNS zones for the privatelink domains. On the resource side, you'll connect customer-owned Storage, Cosmos DB, and AI Search to the project.

### Can I deploy this setup using IaC (ARM, Bicep, Terraform)?
  
Yes, absolutely. The private networking guidance points directly to Bicep and Terraform deployment options, and the Azure Skills guidance reinforces using the official Bicep templates for the private network standard agent setup.

## Hybrid & Advanced Scenarios

### Can agents access both public and private resources in the same application?
  
Yes, but you need to be intentional about the traffic path. Some built-in tools work fine in network-isolated environments but still communicate over public endpoints, and external API calls might need firewall rules or NAT for controlled egress. If you need strict no-public-endpoints, disable those tools and lock down your outbound destinations.

### Can agent tools span multiple VNets or regions?
  
You can peer VNets, but the guidance is clear: use non-overlapping IP ranges, and keep all workspace resources in the same region as the VNet for the private networking standard setup. For multi-region designs, validate regional constraints carefully before promising anyone a cross-region fully private architecture.

### How does private networking work in multi-region deployments?
  
The private networking setup requires all Foundry workspace resources to be in the same region as the VNet. So if you have a multi-region requirement, you'll likely need a separate Foundry setup per region to stay within that constraint.

## Comparison Questions

### How does Foundry VNet support compare to Azure OpenAI networking?
  
Azure OpenAI can be secured inside a VNet using private endpoints and private DNS zones, and you can disable public access so only private endpoints work. Foundry's agent private networking goes further—it adds VNet injection with a delegated subnet and a data proxy that routes tool and data traffic into your VNet. It's not just putting the model endpoint behind Private Link; there's a whole agent-specific networking layer on top.

### How does it compare to Copilot Studio networking?
  
Copilot Studio takes a different approach—it uses Power Platform Virtual Network support and integrates over private endpoints for specific outbound scenarios like HTTP calls to Key Vault, telemetry to private-endpoint-enabled Application Insights, and VNet-supported connectors like SQL. The big difference is that the control plane and configuration live in Power Platform managed environments, not in an Azure Foundry project.

### How does it compare to hosting agents in ACA or AKS?
  
With Foundry, hosted agents are deployed as container images and the platform handles scaling, lifecycle, and agent-specific capabilities for you. In a raw ACA or AKS deployment, you'd manage more of the networking surface yourself. The docs in this packet don't give a full ACA/AKS networking comparison, so treat this as a general positioning guideline rather than a detailed feature-by-feature breakdown.

## Troubleshooting & Diagnostics

### How do I troubleshoot networking issues with agents?
  
Start with the basics: make sure your private endpoint connections show as Approved, validate DNS resolution from inside the VNet (do an nslookup and confirm it returns a private IP), and test port 443 connectivity to the private endpoint IP. If you're seeing timeouts, check your NSG outbound rules and whether a firewall is blocking traffic. For 403 errors, those usually point to authentication or RBAC issues, not networking.

### How can I tell if a tool call is failing due to network restrictions?
  
First, figure out which traffic path the tool uses—VNet, Microsoft backbone, or public endpoint—and make sure the required private endpoints and DNS entries exist for VNet paths. If you're running an Azure Firewall, check whether the traffic is actually hitting the firewall and what's getting blocked. Also, the private networking guidance warns against TLS inspection that injects self-signed certs—that can break things.

### What logging or diagnostics are available for networking failures?
  
The Azure portal doesn't show delegated-subnet IP utilization directly, which can be frustrating. Instead, watch for data proxy HTTP 5xx errors and session creation failures—those are your indicators of IP exhaustion. The private networking guide also includes template deployment error patterns and validation steps that help you track down misconfigurations like subnet delegation issues, DNS zone problems, or missing provider registrations.

## High-Impact Customer Questions

### Will my data ever leave my VNet when using agents?
  
The goal with the private networking standard setup is no public egress, and private endpoints cover your key data resources, so core agent-to-data traffic stays private. But here's the catch: some tools—like Bing grounding, web search, and SharePoint grounding—use public endpoints even in network-isolated environments, so enabling those means traffic can leave the private boundary. The safe booth answer is: "It depends on which tools you enable—let's look at your required tool list together."

### Can my agent call internal APIs that are not publicly exposed?
  
Yes, as long as those internal APIs are reachable from your VNet and you've set up routing, DNS, and authorization properly. Tool server calls go through the single-tenant data proxy into your VNet, and the platform can reach private resources when the right credentials and permissions are in place.

### Do I need outbound internet access for agents to function?
  
Not necessarily. The standard private networking setup runs with no public egress by default, but you might choose to allow public endpoint tools or outbound calls to external APIs depending on what you need. If you truly need zero public egress, disable the public endpoint tools and restrict outbound destinations at the firewall.

### If I enable private networking, what functionality changes?
  
Turning on private networking adds setup work—you'll need private endpoints, DNS zones, subnet delegation, and role assignments. It also changes which tools are available and how they route traffic. Some tools aren't supported or are still under development in VNet-isolated setups, and some will still route through public endpoints unless you explicitly disable them.

### Can I run the entire agent stack fully inside my VNet?
  
Not fully, no. Foundry runs the Foundry endpoint and platform services on a Microsoft-managed platform network, and then injects a subnet and data proxy path into your VNet for outbound connectivity to your private resources. The practical goal is no public egress for supported paths—but it's not about moving the entire platform control plane into your VNet.

## Appendix: Reference Links
  
* Microsoft Learn: [How to configure network isolation for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/how-to/configure-private-link)
* Microsoft Learn: [Set up private networking for Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/virtual-networks?tabs=portal)  
* Microsoft Learn: [Deep dive into Foundry Agent Service networking](https://learn.microsoft.com/azure/foundry/agents/concepts/agents-networking-deep-dive)  
* Microsoft Learn: [Use Virtual Network support for agent calls to private endpoints (Copilot Studio)](https://learn.microsoft.com/microsoft-copilot-studio/admin-network-isolation-vnet)  
* Microsoft Learn: [Securing Azure OpenAI inside a virtual network with private endpoints (classic)](https://learn.microsoft.com/azure/foundry-classic/openai/how-to/network)  
* GitHub: [Skill for private network standard agent setup](https://github.com/microsoft/azure-skills/blob/main/skills/microsoft-foundry/resource/private-network/private-network.md)
* Microsoft Learn: [Configure managed virtual network for Microsoft Foundry projects (preview)](https://learn.microsoft.com/en-us/azure/foundry/how-to/managed-virtual-network?view=foundry&tabs=azure-cli)