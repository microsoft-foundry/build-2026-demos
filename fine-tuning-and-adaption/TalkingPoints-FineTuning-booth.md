# Build Fine-Tuning Booth — Demo Walkthrough & Talking Points

> The demos:
> 1. **Distillation & one-click RL from traces** (William's demo session + keynote candidate)
>    - **1.A** Traces → Dataset for Distillation
>    - **1.B** One-click RL from agent traces (keynote candidate)
> 2. **Training API for custom RL recipes** (Tinker-style; advanced/research customers)
> 3. **CLI skills for managing fine-tuning jobs** (William's lightning talk)
> 4. **RT404 mini — RL for a retail agent** (Alicia & Omkar's breakout + lab)
>
> Final videos for demos 1.B, 2, 3, and 4 are being recorded this week; William will drop updates by end of week. Demo 1.A is notebook-only (no video).

---

## Demo 1.A — Traces → Dataset for **Distillation**

**Session: DEM322 — "Smaller, faster, smarter: Distilling agents with fine-tuning"**
- **When:** Tue, Jun 2 · 12:00 PM – 12:25 PM PDT
- **Where:** Gateway Pavilion, Level 2, Theater B
- **Format:** In San Francisco only · **Will be recorded**
- **Abstract:** Large models are powerful, but expensive to run in production. In this lightning talk, we'll show how teams use Foundry for distillation and supervised fine-tuning to train small language models for task-specific accuracy, dramatically reducing latency and cost. We'll cover when distillation makes sense, how it complements fine-tuning and reinforcement learning, and what real production teams have learned when deploying smaller models at scale. Expect fast examples and lots of Q&A.

**What it is**
No video, just the story and the notebook. A pipeline that takes production traces from a deployed agent and converts them into a supervised fine-tuning (SFT) dataset, which is then used to distill a large/expensive "teacher" agent into a smaller, cheaper "student" model that is very good at one specific task.

**Why it matters (the pitch)**
- Once an agent is in production, its traffic becomes a **valuable learning signal** — don't throw it away.
- You don't need an expensive model to handle every narrow task. Use the big agent as a **teacher**, distill into a **smaller student model** for the specific tasks.
- Result: meaningful performance gains on the target task at much lower inference cost.

**How the demo flows**
1. Start from a deployed agent receiving production traffic.
2. Pull traces from the teacher agent.
3. Filter traces down to the successful / satisfactory ones (per the customer's criteria).
4. Convert filtered traces into an SFT dataset.
5. Fine-tune a smaller student model on that dataset.
6. Run evaluations — show the student matches/beats the teacher on the targeted task.

**Surface shown**
- A **notebook** (currently the detailed internal version with full harness — the public-facing version is still being polished; up-leveled for the actual session).

**Talking points at the booth**
- Lead with the cost story: "Stop paying frontier-model prices for narrow tasks."
- Emphasize the **closed loop**: production traffic → dataset → fine-tune → evaluate → redeploy.
- Two customer personas to listen for:
  - **Already doing fine-tuning** → take them straight to the notebook.
  - **Curious about fine-tuning, unsure if it fits** → walk them through the UI/demo to show the use case.
- Public notebook link is shareable; enterprise version requires Alicia to add their GitHub handle.

---

## Demo 1.B — **Reinforcement Learning** using MAI-Thinking -1 (Keynote candidate)

**What it is**
This is the derivation of the first demo topic. An end-to-end Foundry experience with M365: deploy a new MAI model, bring your production data that speaks to the enterprise, and kick off an RL experiment from Foundry. Then, use this model to build better agents with the power of M365 copilot. 

**Talking points at the booth**
- The headline is you can bring your data to perform RL so that your agent is uniquely for your business context
- **"one click from agent → RL run."** No glue code, no manual data pipeline.
- Connect it to Demo 1: same trace asset, different downstream use (SFT vs. RL).
- "Make the model better for *your* business" — personalization story, not just enterprise.

---

## Demo 2 — **Training API for Custom RL Recipes**

**What it is**
A new **training API** that lets advanced teams build their **own RL recipe** instead of using the prepackaged RL framework in the Foundry UI. 

**Why it exists (the nuance to communicate)**
The Foundry UI's one-click RL (Demo 1.B) is great for most customers — it ships a prebuilt framework so you can just "click reinforcement learning" and go. But advanced teams hit a ceiling and need lower-level control. This API is for them.

Two reasons a team would drop down to the API:
1. **Different infrastructure.** Your VMs / GPUs / environment are set up differently from the prepackaged path. The API lets you change how the job runs on *your* infrastructure (GPU type, environment layout, etc.).
2. **Fine-grained science control.** You still want Microsoft to manage the infrastructure (no low-level GPU code), but you want fine-grained control over **how RL itself happens** inside the job — your own recipe, your own algorithm.

**The grader vs. reward function mental model (use this at the booth)**
Reinforcement learning at its core is one **training loop**: a model tries different things on a set of tasks → each attempt gets a score → the model uses that score to self-correct and update weights. This API lets you customize that loop.

- **Grader** = *how the score is calculated.* Like an exam — it checks a bunch of things and outputs a score. You can swap graders in the UI.
- **Reward function** = *the rubric the model uses to interpret that score when updating its weights.* Same B- grade, but one student shrugs it off, another rewrites their whole study plan — the reward function decides how the score actually moves the model.
- **In the UI:** you can change the grader.
- **In the training API (Loom):** you can also bring your own **reward function** and your own **RL algorithm**. This is the part you can't do from the UI.

**Who it's for**
- **Research teams** building novel RL recipes.
- **Advanced customers** who need a very particular training approach for their problem.
- Teams with non-standard infrastructure who need to control how the job is run.

**Surfaces shown**
- Code / API.
- Once a training job is kicked off via the API, it **shows up in the Foundry UI** for monitoring — so there's a UI touchpoint even though authoring is code-first.

**Talking points at the booth**
- Use the **exam analogy**: grader = the exam, reward function = how the student internalizes the grade. Customers grasp this fast.
- Position vs. Demo 1.B: *"If one-click RL doesn't give you enough control, drop down to API."* Same trace assets, same Foundry surface, deeper knobs.
- Honest about the audience: this is **not** the demo for casual fine-tuning curiosity — qualify the visitor first. If they say "research," "custom recipe," "we have our own GPU setup".

---

## Demo 3 — **CLI Skills for Fine-Tuning Job Management** (Lightning talk)

**Session: Lightning Talk — "Smarter training patterns for better AI models" (300 / Advanced · Working with models)**
- **When:** Tue, Jun 2 · 4:30 PM – 4:45 PM PDT
- **Where:** Gateway Pavilion, Level 2, Theater 3
- **Format:** In San Francisco only · **Will NOT be recorded** — push visitors to attend live.

**What it is**
A set of **Copilot CLI / VS Code skills** (markdown-defined) that let a developer manage fine-tuning jobs in natural language — start a run, check status, cancel a run — without memorizing CLI flags.

**Why it matters (the pitch)**
- Fine-tuning jobs have a lot of lifecycle ceremony (start, monitor, cancel, list, inspect). Skills hide that behind plain English.
- Works wherever Copilot lives — **CLI or VS Code** — so it fits both terminal-first and IDE-first devs.
- Conceptually simple compared to demos 1, 2, and 4, so it's a great "quick win" demo to grab walk-ups with.

**How the demo flows**
1. Open Copilot in the CLI or in VS Code.
2. Say something like *"start a new fine-tuning job"* or *"cancel this run."*
3. The skill (a markdown file) routes the agent to the right command and parameters.
4. The job kicks off / is cancelled / status is returned — no manual CLI.

**Talking points at the booth**
- This is William's **lightning talk** topic — point interested customers there.
- Frame it as **"fine-tuning ops, but conversational"** — perfect for teams who don't want to train their devs on a new CLI surface.
- Pairs naturally with Demo 1.A: "Use Demo 1.A to build the dataset, use this to run/manage the job."
- Skills are **markdown** — customers can read, modify, or author their own. Good hook for advanced devs.

---

## Demo 4 — **RT404 mini: RL for a Retail Agent** (Alicia & Omkar — Breakout + Lab)

**Session: BRK231 — "Deploy. Observe. Learn. Reinforcement learning for production agents"**
- **When:** Tue, Jun 2 · 5:00 PM – 5:45 PM PDT
- **Where:** Festival Pavilion, Breakout 2
- **Format:** In San Francisco **+ Online** · **Will be recorded**
- **Abstract:** Agents don't fail in demos — they fail in production. In this breakout, see how teams use fine-tuning and reinforcement learning on Microsoft Foundry to improve production agents using real usage signals. We cover when fine-tuning reduces cost and latency, when RL delivers deeper gains, and how Foundry makes it easy to train, evaluate, and redeploy safely. **Johnson & Johnson shares their journey from RL experiments to production.**

**Session: LAB521 — "Improving agent behavior using reinforcement learning from traces"**
- **When:** Tue, Jun 2 · 12:30 PM – 1:45 PM PDT
- **Where:** Gateway Pavilion, Level 1, Lab 1
- **Format:** In San Francisco only · **Will NOT be recorded** — push visitors to attend live.
- **Abstract:** AI agents often work, but their behavior can be inconsistent or hard to control with prompts alone. In this hands-on lab, you will start with a working agent, inspect execution traces, define "good behavior" using evaluation graders, and apply reinforcement learning to reinforce better decisions. By the end, you'll have a practical workflow for improving agent behavior using feedback from agent runs, without redesigning your agent from scratch.


**What it is**
An in-depth reinforcement-learning session showing **why** agents need RL (not just better prompts and tools) and **how** to do it end-to-end on a realistic **retail agent** scenario. This is **Alicia's breakout room** plus the attached **lab**.

**Why it matters (the pitch)**
- Prompts/tools/skills add **context**, but the **model itself is the reasoning engine** — it's what decides *which* tool to call and *in what sequence*.
- You can't enumerate every real-world case in a prompt. If you could, you wouldn't need an LLM — just 100 if-else statements.
- Without training, agent performance **plateaus quickly** in real-world success metrics no matter how much context you add.
- RL lets the **weights themselves encapsulate the business logic and policy** (e.g., "don't refund items purchased between these dates on sale"). Context + a trained model > context alone.

**How the demo flows**
1. Start with the retail agent — it has all the tools/skills it needs but plateaus on real-world success.
2. Define an **environment** the agent interacts with.
3. Define a **grader** that scores how well the agent accomplished the task per business policy.
4. Kick off an **RL run** — grader feedback updates model weights.
5. **Swap the trained model in** to replace the agent's original model.
6. Show improved performance — now the agent has both rich context *and* a model whose weights have internalized the policy.

**Talking points at the booth**
- Use the retail / refund-policy example — it's concrete and resonates with anyone building business agents.
- Direct deep-interest visitors to **Alicia & Omkar's breakout** and the **lab** for hands-on.

---
