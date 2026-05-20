# Model Selection and Routing

## model-router-tour.mp4

This video is an ambient walkthrough of a live demo for the model router — an intelligent AI routing system that automatically selects the best AI model for each query based on the task at hand.

The demo guides viewers through a side-by-side comparison of the model router against a fixed benchmark model (GPT-5.2), to illustrate how routing decisions are made. Viewers follow along as the system routes the request through a balanced configuration.

The demo covers four key comparison dimensions:

- **Response Quality** — side-by-side view of the Model Router's response vs. the benchmark, with full JSON metadata
- **Latency** — the Model Router clocks in at ~12,885ms vs. the benchmark's ~21,375ms, showing a 1.7× speed improvement
- **Cost** — a detailed cost breakdown comparing token usage and pricing between routing strategies
- **Accuracy** — an automated evaluation that grades response quality across both approaches

## model-router-demo.mp4

In this video, the model router is tasked with selecting the most cost-efficient and performant language model for a given task, then benchmarks it against a standard model.

In the demo, the user selects the Marketing department and the Campaign Performance Summary scenario, which auto-fills a prompt asking to summarize last month's email campaign performance (Complexity: Medium, Quality Expectation: Moderate accuracy). After submitting, the router picks the optimal model for the task and returns a detailed campaign breakdown.

The video culminates in a Cost Savings Analysis, where the results are striking: the model router cost $0.000538 versus the benchmark's $0.041815 — a 98.7% cost reduction — while also being 3.8x faster (7,284 ms vs. 27,648 ms).

## model-router-zava-chatbot-demo.mp4

This video walks through using the Model router Foundry Models and demonstrates how it intelligently routes queries to the most capable and cost-efficient AI model in real time based on complexity and performance. Using a fictional smart sportswear brand called Zava, the demo shows a customer-facing chatbot powered by the model router dynamically selecting different underlying models depending on whether a query is simple or complex. Watch how the model router achieves 10.5x faster latency at a fraction of the cost with comparable accuracy, all within the Microsoft Foundry.
