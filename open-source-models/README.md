# Open-Source Models on Microsoft Foundry

> **Microsoft Build 2026 — Station 3: Open-Source Models Expert Meet Up**

---
## Related Build 2026 Sessions

| Code | Title | Day | Time (PDT) | Description |
| --- | --- | --- | --- | --- |
| **BRK232** | Train and deploy custom OSS reasoning models with Foundry | Wed, Jun 3 | 2:45 PM – 3:30 PM | Open-source reasoning models work out of the box, but production requires domain-specific training. In this session, ML engineers will learn how to use Microsoft Foundry to train and tune open-source reasoning models in a code-first workflow using curated RL environments and modern frameworks. |
| **DEM321** | Train and deploy custom reasoning models using reinforcement learning | Tue, Jun 2 | 2:10 PM – 2:35 PM | Go beyond prompt engineering to build custom reasoning models using reinforcement learning in Microsoft Foundry. We'll walk through how to train and fine-tune a model to improve reasoning quality, deploy it into Foundry, and integrate it into an agent workflow. |
| **DEM320** | Hugging Face open-source models to production on Microsoft Foundry | Wed, Jun 3 | 10:30 AM – 10:55 AM | Open-source models fuel modern AI but running them in production is hard. In this lightning talk, Microsoft and Hugging Face demonstrate how to deploy and scale Hugging Face models using Foundry Managed Compute inside Microsoft Foundry. |
| **LGT419** | Turn ideas into AI applications with Microsoft Foundry Labs | Tue, Jun 2 | 12:20 PM – 12:35 PM | Developers need a fast path from ideas to real AI applications. In this lightning talk, Microsoft introduces Foundry Labs 2.0, a new experience for rapid AI prototyping. Through a live demo, developers will explore domain-specific models and data, experiment in interactive playgrounds, and compose models, data, and agents into a working application. |
---

## Build 2026 Key Announcements

### Private Preview Feature and Capability Launches

- **Foundry Managed Compute** — A dedicated GPU compute platform within Microsoft Foundry, built specifically for hosting open-source models. Extends Foundry's existing hosting tiers (Pay-per-token, PTU) with a new deployment type for OSS models — no VM or cluster management required.
- **Custom / Code-First Model Training with Foundry** — End-to-end training pipelines for ML engineers, with curated RL environments and modern frameworks in a code-first workflow.
- **Bring Your Own Weights** — Import custom model weights into Foundry from local storage or directly from a training job, with automatic base-model lineage matching to compatible GPU and serving configurations.

Additionally: 
- New Hugging Face models on Microsoft Foundry ​
- Microsoft OSS models on Foundry 
---
## What Is Foundry Managed Compute?

Foundry Managed Compute is a **managed GPU compute platform within Microsoft Foundry** designed to run open-source (OSS) models. It lets developers deploy, customize, and scale models on dedicated GPU infrastructure — without managing VMs, clusters, or low-level infrastructure.

It is a **new deployment type** in Foundry, complementing the existing serverless and reserved-throughput options.

> **Real-world example:** A team wants to deploy a custom fine-tuned Llama variant for an internal agent.
>
> - **Without Managed Compute:** stand up GPU VMs, install vLLM, configure scaling, manage patches, and wire up networking.
> - **With Managed Compute:** import the weights, select an H100 footprint, set scale-to-zero, and get a live endpoint behind the same Foundry API.

### Foundry Hosting Tiers

| Tier | What it means |
| --- | --- |
| **Pay-per-token** | Serverless, token-based inference for first-party models |
| **PTU** | Reserved throughput units for consistent performance |
| **Managed Compute** _(new)_ | Dedicated GPUs for OSS and custom models |

### Core Value

Managed Compute simplifies OSS model deployment by providing:

- **No infrastructure management** — no VM or cluster setup required.
- **Fast access to thousands of OSS models** through the Foundry Model Catalog.
- **Seamless integration** with Foundry APIs, SDKs, and authentication.
- **Flexible, GPU-based pricing** with auto-scaling and scale-to-zero cost controls.

### Key Capabilities

#### Model Catalog

- Thousands of models from **Hugging Face, NVIDIA, and Microsoft Research**.
- **Rapid onboarding** of new models — published within hours of release.
- **Enterprise-ready** out of the box:
  - Security and vulnerability scanning
  - Licensing compliance
  - Standardized formats (SafeTensors)
- Includes **domain- and industry-specific** models.

#### Optimized Inference Stack

- High-performance runtimes: **vLLM**, **SGLang**, **NVIDIA NIM**.
- Advanced serving features:
  - Continuous batching
  - Speculative decoding
  - Tensor parallelism
  - Prefix caching
  - Disaggregated prefill/decode
- Supports both **full model weights** and **LoRA adapters**.

#### Managed GPU Infrastructure

- **Deploy by model instance**, not by infrastructure.
- GPU options: **NVIDIA A100, H100, H200, and AMD MI300**.
- Features:
  - Auto-scaling or manual scaling
  - **Scale-to-zero** when idle
  - Microsoft-managed runtime updates and security patching
- Supports **global and region-specific** deployments.

### Deployment Experience

The deployment flow is **model-centric and simplified**:

1. **Select a model** (UI or API).
2. **Choose runtime configuration** (framework, context length, optimization profile).
3. **Select a GPU family** — no VM SKU knowledge required.
4. **Configure scaling** (auto or manual; optional scale-to-zero).
5. **Deploy** and receive a live inference endpoint.

> **Key characteristic:** no VMs, clusters, or infrastructure provisioning to manage.

### Bring Your Own Models (BYOW)

Managed Compute supports custom models. You can:

- Import models from **local storage**, a **training job**, or **Hugging Face**.
- Let Foundry automatically:
  - Map the model to a compatible runtime
  - Select appropriate GPU configurations

This enables **custom weight hosting** and **fine-tuned models** with no infrastructure work.

### Unified Developer Experience

Managed Compute integrates fully into Foundry:

- Same **authentication and networking**.
- Same **standard inference APIs** (e.g., chat completions).
- Same **SDKs and portal experience**.

> **Result:** the same code works across **Pay-per-token**, **PTU**, and **Managed Compute** deployments.


### Technical Architecture

Serving an LLM on Managed Compute consists of three layers:

| Layer | What it is |
| --- | --- |
| **Weights** | Model parameters — publisher- or customer-provided |
| **Runtime** | Managed serving frameworks (vLLM, SGLang, NIM) |
| **Configuration** | Parallelism, context length, batching, and routing |

These are packaged into **deployment templates** that define how models are served and scaled.

---

## Demo Flow

The station demo is centered in the **Microsoft Foundry portal**. Two parallel flows showcase complementary capabilities.

### Demo 1 — Managed Compute Deployment

_Demonstrate how OSS models are deployed and consumed on Foundry Managed Compute, mirroring the 5-step deployment experience._

**What to show:**

1. **Select a model** — open the **Model Catalog** in your Foundry project and pick an OSS model (Hugging Face, NVIDIA, or Microsoft Research). Call out enterprise readiness: vulnerability scanning, licensing compliance, and SafeTensors.
2. **Choose runtime configuration** — pick a serving framework (**vLLM**, **SGLang**, or **NVIDIA NIM**), context length, and optimization profile (e.g., LoRA, speculative decoding, prefix caching).
3. **Select a GPU family** — **NVIDIA A100, H100, H200, or AMD MI300**. No VM SKU knowledge required; Foundry maps the model to a compatible configuration.
4. **Configure scaling** — manual (GPU count = model instances × GPUs per instance), auto-scaling, or **scale-to-zero** with an idle timeout.
5. **Deploy and consume** — receive a live inference endpoint, then run a **Python sample** using `ChatCompletionsClient` from `azure.ai.inference` with standard Foundry credentials.

**Key talking points:**

- **No VMs, no clusters** — Microsoft manages runtimes, updates, and security patching.
- **Same Foundry developer experience** — the same SDK, API keys, private endpoints, and portal work across **Pay-per-token**, **PTU**, and **Managed Compute**.
- **GPU flexibility** — NVIDIA A100/H100/H200 and AMD MI300, with automatic configuration matching.
- **Cost controls** — hourly per-GPU-SKU billing with auto-scaling; quota is managed in Foundry per SKU, per region.

### Demo 2 — Train, Deploy, and Improve Agents

_Demonstrate the end-to-end loop from custom training and Bring Your Own Weights to agent consumption on Managed Compute._

**What to show:**

1. Walk through the **five-step cycle**: Experiment → Train (SFT then RFT with graders and rewards) → Deploy (managed endpoints with LLM-native monitoring) → Consume in agents → Improve.
2. Show **Bring Your Own Weights (BYOW)** — import from **local storage**, a **training job**, or **Hugging Face**. Foundry automatically maps the model to a compatible runtime and selects appropriate GPU configurations.
3. **Deploy on Managed Compute** behind a standard Foundry endpoint, then drop the custom model into a **Foundry agent or tool** — unchanged auth, networking, and SDK.
4. Emphasize the **continuous improvement loop** — _"every cycle makes the agent smarter"_ — by feeding production signals back into the next training round.

**Key talking points:**

- **Training-to-deployment is fully integrated** — no glue code between fine-tuning and inference; lineage-aware GPU + serving config matching.
- **Reinforcement learning** with curated RL environments enables custom reasoning models in a code-first workflow.
- **Custom models inherit** the same enterprise-grade security, compliance, networking, and managed inference stack (vLLM / SGLang / NIM) as first-party models.

---

## Documentation Links


- KBYG — Open-Source Models presentation: <https://microsoft-my.sharepoint.com/:p:/p/gulsimoosimi/cQoP7RSBj_BjSJ1v9zojXLLKEgUCxetN42qK3Px-zqsTUwgaOw>
