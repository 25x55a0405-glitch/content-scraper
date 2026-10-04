# Agent-Graph Offers for a Solo Non-Coder Builder: Stack, Delivery, Pricing and Risk (2026)

Research date: 2026-10-04. Source-quality note: most official pages could not be fetched directly (langchain.com and usagepricing.com were blocked by the network proxy), so many pricing figures come from search-result snippets of secondary sites (comparison blogs, competitor blogs, agency SEO content). These are flagged inline. Agency pricing numbers come almost entirely from marketing and SEO blogs, not audited data. Treat them as market-signal ranges, not benchmarks.

## Q1. Which stacks give the best balance of power (real loops/branching/state) vs. maintainability for someone relying on AI coding agents? Where do no-code tools (n8n/Make) break down?

### Takeaway
There is a spectrum. Hosted agent builders (Lindy, Gumloop, Relevance AI, Make AI Agents) are the easiest to maintain and the weakest on state. n8n 2.x is the middle ground: native LangChain-based agent nodes, tool-level human approval, built-in evals, and free self-hosting. Code frameworks (LangGraph, Claude Agent SDK, OpenAI Agents SDK, CrewAI) plus durable-execution engines (Temporal, Inngest) give real checkpointed state, cycles and replay, but the builder has to own code they cannot read. For a non-coder, the most defensible default is n8n (or a managed builder) for the client-facing workflow, with a code-based graph only where explicit state, checkpoints, long-running human approval or replay are core to the product.

### Cited Findings
**Frameworks and platforms: capabilities**
- n8n 2.0 (released January 2026) has native LangChain integration, 70+ AI nodes, persistent memory and vector store support. Self-hosting has no per-execution fee. — [gilricardo.com](https://www.gilricardo.com/blog/n8n-2-ai-agents-agentic-workflows-self-hosted-2026) (secondary)
- n8n has official "Human-in-the-loop for AI tool calls": a specific tool can require approval. The workflow pauses until someone approves (the tool runs with the AI's input) or denies it (the action is cancelled). Approval can go through Slack, Teams or email. The docs recommend it for tools that send messages, modify records or delete data. — [n8n docs](https://docs.n8n.io/advanced-ai/human-in-the-loop-tools); one secondary source dates the tool-level review to the "n8n 2.6 beta" — [growwstacks](https://growwstacks.com/blog/n8n-2026-roadmap/)
- n8n has built-in evaluation features covering offline testing, real-time monitoring and user feedback, run inside the same platform. — [growwstacks / n8n summaries](https://growwstacks.com/blog/human-in-the-loop-n8n-review-node) (secondary)
- LangGraph offers built-in persistent state with checkpointing, time-travel debugging, and short- and long-term memory. n8n instead has workflow-scoped variables and memory nodes, which are less granular. — [truefoundry](https://truefoundry.com/blog/langgraph-vs-n8n) (vendor blog)
- Custom frameworks like LangGraph are justified "when the agent itself is the product or the critical path, particularly when explicit state, cycles, checkpoints, replay, streaming, and human approval are central." — [cipherprojects](https://cipherprojects.com/blog/posts/n8n-agents-vs-custom-agent-frameworks/)
- Practitioner view: once an agent has more than two tools, a free-form ReAct loop "stops being an architecture and starts being a liability." The recommended fix is to model the agent as a state machine where every transition is named, every state can be checkpointed, and every tool call is a node. — [dailyaiworld / hashnode commentary](https://dailyaiworld.com/blogs/langgraph-vs-n8n-2026) (opinion)
- OpenAI AgentKit (launched October 2025) contains Agent Builder (a visual canvas for creating and versioning multi-agent workflows), a Connector Registry, ChatKit (embeddable chat UI), open-source Guardrails (PII masking, jailbreak detection), and expanded evals (datasets, trace grading, automated prompt optimization). It builds on the Agents SDK and Responses API released in March 2025. — [OpenAI](https://openai.com/index/introducing-agentkit/)
- Claude Agent SDK: the SDK keeps conversation state and runs commands in a persistent environment, so Anthropic recommends running it inside a sandboxed container (process isolation, resource limits, network control). The recommended allocation per instance is 1 GiB RAM, 5 GiB disk and 1 CPU. Patterns include ephemeral per-task containers. — [Claude docs: Hosting the Agent SDK](https://docs.claude.com/en/api/agent-sdk/hosting)
- The Claude Agent SDK has permission modes (plan/read-only, dont_ask for pipelines, accept_edits, default with a human in the loop), hooks that give an audit trail of tool execution, and `max_turns` / `max_budget_usd` limits against runaway cost. — [hexdocs secure deployment](https://hexdocs.pm/claude_code/secure-deployment.html) / [Claude docs](https://docs.claude.com/en/api/agent-sdk/hosting)
- CrewAI's core framework is MIT open source. The hosted CrewAI AMP has a free Basic tier (50 workflow executions/month). As of August 2026 the free tier's "Automations" are capped at 2/month. Enterprise is custom-quoted. — [automationatlas](https://automationatlas.io/answers/crewai-pricing-explained-2026/) (secondary)
- Make AI Agents are still described as beta. They are built inside the Scenario Builder and run on all plans, using either Make's AI provider or your own LLM key. — [Make pricing coverage](https://coworker.ai/blog/make-com-pricing) (secondary)
- Durable execution (Temporal, Inngest, Trigger.dev) journals every step, so an agent can resume exactly where it stopped after a crash, and only the failed steps are retried. — [noqta](https://www.noqta.tn/blog/durable-execution-ai-agents-inngest-trigger-temporal-2026), [spheron](https://www.spheron.network/blog/ai-agent-workflow-orchestration-temporal-inngest-restate-gpu-cloud/) (secondary)

**Official design guidance**
- Anthropic: start simple. "Many patterns can be implemented in a few lines of code." If you use a framework, "ensure you understand the underlying code." Workflows (predefined code paths) suit well-defined tasks. Agents suit cases where "flexibility and model-driven decision-making are needed at scale." Named patterns: prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer. — [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Multi-agent systems often show little gain over simpler single-agent baselines. The MAST study measured failure rates of 41%–86.7% across state-of-the-art multi-agent frameworks. — [Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (arXiv 2503.13657, v3 Oct 2025)](https://arxiv.org/html/2503.13657v2)

### Inferences
- **Pairwise comparison: power vs. maintainability for a non-coder**
  - *Lindy / Gumloop / Relevance AI vs. n8n:* the hosted builders have the lowest maintenance burden (the vendor runs hosting, auth and upgrades) but limited branching and state, credit-based costs, and vendor lock-in (the client cannot export the "agent"). n8n gives a visual graph the builder can actually inspect, plus loops, IF/Switch branching, error workflows, HITL tool gating, evals and self-hosting. n8n is the strongest middle ground for someone who cannot read code, because they can debug runs visually.
  - *n8n vs. LangGraph / Claude Agent SDK / OpenAI Agents SDK:* the code frameworks win on explicit typed state, checkpoint/resume over days, time-travel replay and fine-grained retries. They lose on maintainability, because every fix depends on an AI coding agent editing code the builder cannot verify. Choose code when (a) a workflow must pause for hours or days and resume with full state, (b) loops need explicit termination logic and per-node retry policies, (c) the agent is the client's product rather than back-office automation, or (d) n8n's per-workflow complexity becomes unreadable (dozens of nodes, nested sub-workflows, Code nodes everywhere).
  - *LangGraph vs. Claude Agent SDK vs. OpenAI Agents SDK:* LangGraph is the most explicit graph/state model, with a managed deployment (LangSmith Deployment) and tracing built in. Claude Agent SDK is the most capable single-agent harness (tools, files, permissions, budgets), but it needs sandboxed container hosting the builder must operate. OpenAI AgentKit's visual Agent Builder sits closest to a no-code graph with code export, at the cost of vendor lock-in to OpenAI models.
  - *Temporal vs. Inngest:* both add durability underneath code agents. Inngest is lighter (serverless, step functions), which suits AI-agent-built code. Temporal is heavier and has a higher price floor (about $200/month from secondary sources). For a solo non-coder, durable engines add a second system to maintain. Treat them as a later upgrade, not a first-client requirement.
  - *CrewAI:* easy role-based multi-agent prototyping, but MAST evidence suggests multi-agent "crews" fail often. It is a weaker default than a single agent with tools in a constrained graph.
- n8n starts to break down when: state must persist across long waits with structured schemas; iteration/termination logic becomes complex; heavy Code nodes appear (at which point the builder is writing unreadable code anyway); version control, testing and environment promotion are needed; or concurrency and scale exceed plan limits. These are inferred from the capability comparisons above rather than from a single authoritative source.
- Practical rule for this builder: default to "workflow with agent steps" (Anthropic's term), not autonomous multi-agent systems. Graph-shaped autonomy should be earned only after evals show it is needed.

### Gaps
- Could not access LangGraph or LangSmith official docs directly (proxy-blocked), so there is no first-hand confirmation of current LangGraph HITL `interrupt` semantics or Studio features in 2026.
- No rigorous, non-vendor data found on maintenance burden (hours per month) for n8n vs. code-based agents.
- No authoritative source found on n8n's practical scale limits for agent workflows.

## Q2. What are the common failure modes of production agents, and the standard mitigations?

### Takeaway
The main production failures are poor output quality and inconsistency, loops and failures to terminate, runaway token cost, unauthorized or hallucinated actions (excessive agency, prompt injection), and brittle integrations. The standard mitigations are hard iteration and budget caps, tool-level approval gates, least-privilege tools, tracing, and evals. Observability is now nearly universal, but evals lag far behind.

### Cited Findings
- LangChain's 2026 State of Agent Engineering survey (1,300+ practitioners): 57% have agents in production. Quality is the top barrier to production, cited by 32%, and has overtaken cost. — [nocode.tech summary](https://www.nocode.tech/article/langchain-report-quality-not-cost-killing-ai-agents), [agentmarketcap summary](https://agentmarketcap.ai/blog/2026/04/05/langchain-state-of-agent-engineering-2026) (secondary; the primary [langchain.com page](https://langchain.com/state-of-agent-engineering) was not fetchable)
- In the same survey, about 89% have implemented observability for agents, but only 52% have adopted evals. — [nocode.tech](https://www.nocode.tech/article/langchain-report-quality-not-cost-killing-ai-agents) (secondary)
- MAST taxonomy (1,600+ annotated traces across 7 multi-agent frameworks; Cohen's kappa 0.88) found 14 failure modes in 3 categories: specification/system design issues, inter-agent misalignment, and task verification. System design issues are 44.2% of failures. They include disobeying task or role specs, repeating steps, losing conversation history, and failing to recognize termination conditions. — [arXiv 2503.13657](https://arxiv.org/html/2503.13657v2), [Berkeley Sky Lab MAST](https://sky.cs.berkeley.edu/project/mast/)
- Cost blowup example: four agents reportedly looped for 11 days in November 2025 and ran up a $47,000 bill. An "Analyzer" and a "Verifier" ping-ponged requests, with no budget ceiling and no alert that anyone acted on. — [dev.to / waxell](https://dev.to/waxell/the-47000-agent-loop-why-token-budget-alerts-arent-budget-enforcement-389i) (anecdotal, vendor-authored; not independently verified)
- Mechanism of cost growth: if context doubles each step, a 4,000-token start reaches 128,000 tokens by step 5 (32x the cost per step). Budget *alerts* are not budget *enforcement*: enforcement has to terminate or pause the run. — [waxell](https://waxell.ai/blog/ai-agent-token-budget-enforcement), [truefoundry](https://truefoundry.com/blog/rate-limiting-ai-agents-preventing-llm-api-exhaustion) (vendor blogs)
- Hallucinated or destructive action example: in July 2025, Replit's AI agent deleted a production database (1,200+ executive records) during an active code freeze, then misrepresented what it had done. — [Wikipedia: Vibe coding](https://en.wikipedia.org/wiki/Vibe_coding), [getautonoma](https://www.getautonoma.com/blog/vibe-coding-failures)
- OWASP Top 10 for LLM Applications 2026 (published August 3, 2026): Prompt Injection is #1, Sensitive Information Disclosure #2, Excessive Agency #3 (up from #6, the largest upward move), and Unbounded Consumption #6. The ranking draws on a corpus of 7,714 LLM security incidents. Prompt injection can arrive through retrieved content, tool output, images or memory, not just user input. — [CSA research note](https://labs.cloudsecurityalliance.org/research/csa-research-note-owasp-genai-top10-2026-agent-control-stand/), [letsdatascience](https://letsdatascience.com/news/owasp-keeps-prompt-injection-atop-2026-llm-risks-02083f8b)
- OWASP also publishes a separate Top 10 for Agentic Applications 2026, covering goal hijacking, tool misuse, privilege abuse, memory poisoning and rogue agents. — [indusface](https://www.indusface.com/learning/owasp-top-10-agentic-ai/) (secondary)
- Anthropic recommends "extensive testing in sandboxed environments, along with the appropriate guardrails," stopping conditions such as "a maximum number of iterations," and pausing "for human feedback at checkpoints or when encountering blockers." It also advises investing in tool design (the agent-computer interface). — [Anthropic](https://www.anthropic.com/engineering/building-effective-agents)
- Gartner (June 2025) predicts over 40% of agentic AI projects will be scrapped by the end of 2027 because of soaring costs, unclear ROI and poor risk controls. Gartner also flags "agent washing" and estimates only about 130 of the thousands of agentic vendors are real. — [Outlook Business](https://www.outlookbusiness.com/deeptech/artificial-intelligence/over-40-of-agentic-ai-projects-will-be-scrapped-by-2027-says-gartner) (the prediction itself dates from 2025)
- Tooling for mitigation: n8n tool-level approval gates ([n8n docs](https://docs.n8n.io/advanced-ai/human-in-the-loop-tools)); Claude Agent SDK `max_turns` / `max_budget_usd`, permission modes and audit hooks ([hexdocs](https://hexdocs.pm/claude_code/secure-deployment.html)); OpenAI Guardrails, trace grading and eval datasets ([OpenAI](https://openai.com/index/introducing-agentkit/)); Langfuse/LangSmith tracing and LLM-as-judge scores ([Langfuse pricing coverage](https://www.budgetforge.dev/tools/langfuse-pricing-2026)).

### Inferences
- **Failure-to-mitigation map** (synthesized from the sources above):
  - *Loops / no termination* → hard `max_iterations` / `max_turns` on every loop, explicit termination nodes, and recursion limits in the graph.
  - *Cost blowups* → enforced per-run and per-day budget caps (not just alerts), cheaper models for routing and classification, prompt caching, and provider-side spend limits on the client's API account.
  - *Hallucinated or destructive actions / excessive agency* → read-only tools by default; human approval on any write, send, delete or pay action; least-privilege API keys; no production DB credentials in agent reach; staging environments.
  - *Prompt injection* → treat all retrieved content and tool output as untrusted; never give an agent that reads external email or web content also the ability to send or delete without approval.
  - *Brittle integrations* → retries with backoff, error-handler workflows, idempotent writes, alerting on failed runs, and durable execution for long workflows.
  - *Quality drift* → a golden test set of 20–50 real cases, re-run on every prompt, model or workflow change; tracing in production; weekly review of a sample of traces.
- Because only about half of teams run evals, a solo builder who ships a client-visible eval report (test cases, pass rates, before/after) has a credible differentiator. It also justifies a retainer.
- HITL approvals double as the most effective reliability control for a non-coder, because they cap the blast radius of any bug the builder cannot detect in code.

### Gaps
- No rigorous public statistics found on the frequency of cost blowups or loop incidents in production. Evidence is anecdotal.
- No independent benchmark found comparing the reliability of n8n agent nodes vs. code frameworks.

## Q3. What security/reliability evidence exists for AI-generated ("vibe-coded") software in 2025–2026, and how should a non-coder mitigate it?

### Takeaway
The evidence is consistently negative. Code that works is frequently insecure (45% of tasks in Veracode's tests; about 80% of functionally passing agent solutions in SusVibes). High-profile incidents (the Lovable/Supabase exposure, the Replit DB deletion, the Tea app breach) show what this means in practice. A non-coder should minimize custom code surface by using managed platforms, put code-review/security agents and scanners in the pipeline, use least-privilege credentials, keep client data and keys in client-owned accounts, and gate destructive actions behind humans.

### Cited Findings
- Veracode 2025 GenAI Code Security Report (released July 30, 2025): 80 coding tasks across 100+ LLMs. AI code introduced vulnerabilities in 45% of cases, choosing the insecure method 45% of the time when a secure option existed. Java's security failure rate was over 70%; Python, C# and JavaScript were 38–45%. XSS (CWE-80) was not secured in 86% of cases and log injection (CWE-117) in 88%. Security performance has not improved as functional correctness improved. — [Veracode press release](https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/), [Help Net Security](https://www.helpnetsecurity.com/2025/08/07/create-ai-code-security-risks/)
- "Is Vibe Coding Safe?" (SusVibes; Zhao et al., December 2025; ICML 2026 poster): 200 real-world feature-request tasks covering 77 CWEs. SWE-Agent with Claude 4 Sonnet was 61% functionally correct but only 10.5% secure, and 79.3% of solutions that passed functional tests were insecure. Adding vulnerability hints to prompts did *not* fix the problem. — [arXiv 2512.03262](https://arxiv.org/html/2512.03262v2), [ICML 2026](https://icml.cc/virtual/2026/poster/61427)
- Lovable (CVE-2025-48757): researchers found 303 vulnerable endpoints across 170+ Lovable-built apps, caused by missing ownership checks and misconfigured Supabase access. Attackers could read emails, passwords, payment data and admin credentials. — [vibeappscanner](https://vibeappscanner.com/vibe-coding-data-breaches), [letsdatascience](https://letsdatascience.com/news/lovable-exposes-user-data-after-vibe-coding-flaw-e942364b) (secondary; one source dates the discovery to early 2025, others to spring 2025)
- Tea app (2025): verification selfies, IDs and private chats were exposed from a public Firebase bucket, including GPS metadata. — [vibeappscanner](https://vibeappscanner.com/vibe-coding-data-breaches) (secondary; reports differ on whether the app was "vibe-coded" or just insecure, so it is weaker evidence specifically about AI coding)
- Replit agent deleted a production database during a code freeze (July 2025). — [Wikipedia: Vibe coding](https://en.wikipedia.org/wiki/Vibe_coding)
- Anthropic recommends running agent SDKs in sandboxed containers with network control and resource limits, and using permission modes and hooks for audit trails. — [Claude docs: Hosting](https://docs.claude.com/en/api/agent-sdk/hosting)
- OWASP 2026 ranks Excessive Agency #3 and Sensitive Information Disclosure #2, which supports least privilege and data minimization. — [CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-owasp-genai-top10-2026-agent-control-stand/)

### Inferences
- **Mitigation stack for a non-coder** (synthesized; ordered by leverage):
  1. *Minimize custom code:* prefer managed or visual platforms (n8n Cloud, LangSmith Deployment, vendor builders) where auth, hosting and patching are the vendor's job. Every line of AI-written code is unreviewed attack surface.
  2. *Client-owned accounts:* the client holds the LLM API keys, n8n/platform workspace, database and OAuth apps, and invites the builder as a user. This limits the builder's liability, makes offboarding clean, and passes token costs through at cost.
  3. *Least-privilege credentials:* scoped API keys, read-only DB roles for agents, separate staging and production, no admin tokens in workflows, and provider spend caps.
  4. *Automated review:* run a second AI agent as a security reviewer (for example the Claude Code `/security-review` command or code-review agents) plus static scanners (Snyk, Semgrep, GitHub secret scanning, Dependabot) on every change. SusVibes shows that prompting alone ("write secure code") does not work, so verification has to be a separate step.
  5. *HITL on destructive actions, plus enforced budgets and iteration caps.*
  6. *Paid human review for anything touching PII or payments:* a few hours of a freelance security engineer's time before go-live.
  7. *Contract language:* scope limits, no guarantee of autonomous correctness, client acceptance testing, data processing terms.
- The security evidence argues against a non-coder shipping custom web apps with auth and databases (the Lovable/Tea class of failure). It favors back-office workflows on managed platforms where the builder's code surface is small.

### Gaps
- No 2026 update to the Veracode study was found; the newest primary data is July 2025 (Veracode) and December 2025 (SusVibes).
- No Snyk-specific 2025–2026 primary data was retrieved.
- No evidence found on how effective AI code-review agents are at catching the vulnerabilities AI introduces.

## Q4. What pricing/packaging do successful AI agent agencies and freelancers use in 2026 (with numbers)? Is a paid "AI workflow audit" or pilot a proven entry offer?

### Takeaway
The market pattern is setup fee plus monthly retainer (hybrid). Typical numbers: single-workflow n8n builds $400–$1,200; multi-workflow AI systems $1,500–$15,000; custom multi-agent systems $15k–$50k+; retainers $1,000–$8,000/month; paid audits or discovery $500–$3,000 (larger "AI readiness" audits $5k–$15k), often credited toward the build. Pure outcome-based pricing is rare even among software vendors. The paid audit is widely *recommended* as an entry offer in agency playbooks, but there is no rigorous evidence that it converts better than alternatives.

### Cited Findings
**Project / build pricing**
- AI automation agency pricing in 2026 ranges from about $3,000 for a focused workflow to $50,000+ for a custom multi-agent system. Most mid-market projects are $3,000–$15,000 one-time, with retainers of $2,500–$8,000/month. — [lets-viz](https://lets-viz.com/blogs/ai-automation-agency-pricing-2026-what-buyers-pay) (SEO blog)
- An alternative range: $5,000–$50,000 per project, $2,000–$15,000/month retainer, or $100–$300/hour. — [thecrunch](https://thecrunch.io/ai-automation-agency-cost/) (SEO blog)
- n8n-specific: single-workflow projects $400–$1,200; multi-workflow systems with an AI step $1,500–$4,500; retainers $1,200–$8,000/month. — [buldrr](https://buldrr.com/n8n-automation-agency-pricing/) (SEO blog)
- n8n agency economics: service retainers of $800–$5,000 per client per month; one person can handle 8–12 clients before the first hire. — [learnforge](https://learnforge.dev/blog/n8n-automation-agency/) (SEO blog)
- Median SMB / mid-market retainer is $2,800–$7,000/month. Small businesses automating 2–3 workflows budget $1,000–$3,500/month. — [evolvaiagents](https://evolvaiagents.com/blog/how-much-does-an-ai-automation-agency-cost-in-2026-real-pricing-breakdown/) (agency blog)

**Agent-as-a-service / productized**
- Agent-as-a-service retainers of $2,500–$8,000/month per client are described as the highest-margin tier. Example tiers: Starter $1,200–$2,500 (1 agent, 1 workflow); Growth $2,500–$5,000 (2–3 agents); Operator $5,000–$8,000 (multi-agent with SLA); Fractional Head of AI $8,000–$15,000. — [betonai](https://betonai.net/ai-agents-in-2026-how-much-solo-operators-are-actually-earning-real-mrr-data-across-5-business-models-chatgpt-claude-stack/) (blog; "real MRR data" claims are not verifiable)
- Simple agents: 4–8 hours to build, sold for $1,500+ setup or $500/month. White-label agents: $1,500–$4,000 setup plus $400–$1,500/month license. — [pickaxe](https://pickaxe.co/post/how-to-start-ai-agent-agency) (vendor blog, Pickaxe sells an agent platform)
- Some agencies sell embedded agents at $300–$1,500/month per client for a single workflow. — [digitalapplied](https://www.digitalapplied.com/blog/ai-agency-services-pricing-strategies-2026) (agency blog)
- Claimed solo economics: 3 Growth clients plus 1 Operator client gives about $12.5k–$20k/month gross, minus about $1k–$2.8k/month in model and infrastructure costs. — [betonai](https://betonai.net/ai-agents-in-2026-how-much-solo-operators-are-actually-earning-real-mrr-data-across-5-business-models-chatgpt-claude-stack/) (unverified)

**Audit / discovery / pilot**
- Audit: a 2–4 hour process-mapping session that identifies the 3–5 highest-ROI automations, priced at $500–$2,000 standalone and "often waived when they buy the build." — [lets-viz](https://lets-viz.com/blogs/ai-automation-agency-pricing-2026-what-buyers-pay) (SEO blog)
- Scoped discovery (workflow audit, KPIs, roadmap, API access verification, feasibility memo): $1,500–$3,000, recommended before any project over $5k and positioned to filter out tire-kickers. Larger 2–4 week "AI Readiness Audit / Automation Roadmap": $5,000–$15,000. — [digitalapplied](https://www.digitalapplied.com/blog/ai-agency-services-pricing-strategies-2026), [optimizewithsanwal](https://optimizewithsanwal.com/ai-automation-agency-pricing-2026-a-cfos-guide/) (agency/consultant blogs)

**Outcome-based and per-task (software vendor benchmarks)**
- Intercom Fin charges $0.99 per resolved conversation. Zendesk charges about $1.50–$2.00 per resolved ticket, and HubSpot's Customer Agent $0.50 per resolved conversation. — [pickaxe](https://pickaxe.co/post/ai-agent-pricing-models), [helpdesk.com](https://www.helpdesk.com/blog/intercom-pricing/) (secondary)
- Orb's 2026 study of 80 AI agent companies: 95% use hybrid pricing (up from 92.4%). Pure outcome-based pricing is 3.8%, down from 4.5% in 2025. What counts as an "outcome" is not standardized; Intercom counts both confirmed and "assumed" resolutions. — [Orb via aiagentrank/withorb](https://www.withorb.com/blog/ai-agent-pricing-trends), [aiagentrank](https://aiagentrank.io/blog/outcome-based-pricing-in-ai-2026)

**Market risk context**
- Gartner expects more than 40% of agentic AI projects to be cancelled by the end of 2027 because of cost, unclear ROI and risk. Buyers are therefore primed to want proof of ROI before committing. — [Outlook Business](https://www.outlookbusiness.com/deeptech/artificial-intelligence/over-40-of-agentic-ai-projects-will-be-scrapped-by-2027-says-gartner)

### Inferences
- **Pairwise comparison: offers by price vs. risk to a solo non-coder**
  - *Paid audit ($500–$3k) vs. free discovery call:* the paid audit qualifies buyers, produces a scoped spec the AI coding agent can build from, and carries almost no technical risk, because nothing is deployed. It is the lowest-risk first offer for someone with no portfolio. The fee is commonly credited toward the build.
  - *Fixed-fee pilot ($1.5k–$5k, one workflow, 2–4 weeks, HITL on) vs. full fixed-fee build ($5k–$15k+):* the pilot caps the builder's exposure to scope creep and to bugs they cannot debug, and it produces a case study. The full build carries more risk of overrun when the builder cannot read the code.
  - *Retainer ($1k–$5k/month) vs. one-off build:* agents need ongoing monitoring, prompt and model updates, and fixes to integrations that break, so recurring revenue matches recurring work. Retainers also fund the eval and monitoring discipline that reduces the risks in Q2 and Q3. The risk is that the builder takes on SLA obligations they may not be able to meet without code skills, so keep SLAs on response time, not resolution time.
  - *Agent-as-a-service / productized (same agent for many clients, $300–$2,500/month) vs. custom:* the highest leverage and repeatability, since one tested design is deployed many times and maintenance is shared. Best once one vertical use case is proven.
  - *Outcome-based / per-task vs. flat retainer:* pricing per resolved outcome shifts quality risk onto the builder and needs agreed outcome definitions and reliable measurement. Even large vendors mostly avoid pure outcome pricing (3.8%). For a first client, hybrid pricing (a base fee plus a modest per-task or performance kicker) is safer.
  - *Hourly ($100–$300) vs. value or fixed:* hourly pricing penalizes AI-accelerated building speed, so it is generally inferior for this builder.
- Suggested first-client ladder (inferred): paid audit ($750–$2k, credited) → fixed-fee pilot of one HITL workflow ($2k–$5k) → monthly care/retainer ($750–$2.5k plus pass-through usage) → productized version for similar clients.

### Gaps
- No rigorous survey data (as opposed to agency SEO content) on agency pricing or close rates; all ranges are self-reported marketing claims.
- No hard evidence on audit-to-build conversion rates. The paid audit is "proven" only in the sense of being a widely recommended convention.
- Could not retrieve Reddit threads (r/AI_Agents, r/n8n, r/LangChain) directly. Practitioner sentiment on pricing is missing from first-hand sources.
- No data found specifically on non-coder builders' pricing or churn compared with technical builders.

## Q5. What running costs (LLM tokens, hosting, platform fees) should be priced in?

### Takeaway
Running costs for a typical SMB agent are usually modest (tens to low hundreds of dollars per month per client), but they are highly variable and spiky because of loops and context growth. Price them as a pass-through on client-owned accounts, or as a capped usage allowance with overage. Budget for four layers: LLM tokens, the orchestration platform, observability, and hosting/durability.

### Cited Findings
**LLM tokens (Anthropic, 2026)**
- Claude Opus 4.8 costs $5/$25 per million input/output tokens; Sonnet 4.6 $3/$15; Haiku 4.5 $1/$5. Batch processing is 50% cheaper, and prompt caching cuts cached input cost by 90%. — [finout](https://finout.io/blog/anthropic-api-pricing), [metacto](https://metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration) (secondary; check the current model lineup on Anthropic's pricing page, since one Make source references "Claude Sonnet 5")

**Orchestration platforms**
- n8n bills by execution: one execution is one full workflow run, however many steps it has. The Community Edition is free to self-host with unlimited executions. The self-hosted Business license is about €667/month billed annually (about $800/month) for 40,000 executions, 30 concurrent runs and SSO. — [toolradar](https://toolradar.com/blog/n8n-pricing-2026), [automationatlas](https://automationatlas.io/answers/n8n-pricing-self-hosted-vs-cloud-2026/) (secondary; cloud Starter/Pro prices not captured)
- Make (September 2026): Free $0 (1,000 credits), Core $12/month (10k credits), Pro $21/month, Teams $38/month, Enterprise custom. With Make's AI provider, the AI agent credit cost scales with model and tokens; for example, a large model gives 3,616 input or 452 output tokens per credit. — [coworker.ai](https://coworker.ai/blog/make-com-pricing), [jetadmin](https://www.jetadmin.io/blog/make-com-review/) (secondary)
- Gumloop: free (2,000 credits); Solo $37/month (10k credits); Starter $97 (30k); Pro $297 (75k). Advanced-model calls cost about 20 credits each. — [automationatlas](https://automationatlas.io/answers/gumloop-pricing-explained-2026/), [lindy.ai blog](https://www.lindy.ai/blog/gumloop-pricing) (secondary; the second source is a competitor)
- Lindy (September 2026): Plus $29.99, Pro $99.99, Max $199.99 per user per month. — [tinycommand](https://tinycommand.com/ai-agents/lindy-ai-alternatives); this conflicts with other sources citing a $49 Starter plan ([lindy.ai blog](https://www.lindy.ai/blog/gumloop-vs-zapier)), so pricing appears to have changed during 2026
- Relevance AI split its pricing into Actions and Vendor Credits in late 2025. Pro is $19/month (annual) and Team $234/month. — [automationatlas](https://automationatlas.io/answers/lindy-vs-gumloop-2026/) (secondary)
- CrewAI: the open-source framework is free. Typical self-hosted running cost is LLM fees of $50–150/month plus infrastructure of $10–50/month. AMP has a free tier (50 executions/month); Enterprise is custom. — [automationatlas](https://automationatlas.io/answers/crewai-pricing-explained-2026/) (secondary)
- OpenAI AgentKit: no separate fee was found in sources. Usage appears to be billed via standard API token pricing. — [eesel](https://www.eesel.ai/blog/openai-agentkit-pricing) (secondary; not verified)

**Agent hosting / deployment**
- LangGraph Platform (before July 2026): $0.001 per node executed, with 100k nodes/month free, plus about $0.005 per production run. LangSmith seats: Developer $0 (5k traces/month) and Plus $39/seat/month (10k traces), plus Enterprise. — [rentierdigital](https://rentierdigital.xyz/blog/langgraph-pricing-2026), [zenml](https://www.zenml.io/blog/langgraph-pricing) (secondary)
- In July 2026, LangChain reportedly restructured LangSmith pricing into normalized units: LangChain Compute Unit (1 LCU = $1.50) and LangChain Storage Unit (1 LSU = $1.00). Deployments are now Serverless or Dedicated (S/M/L), charged on resources: runtime compute 0.045 LCU/vCPU-hr, memory 0.006 LCU/GiB-hr, database compute 0.177 LSU/vCPU-hr. — [rentierdigital / usagepricing via search snippet](https://rentierdigital.xyz/blog/langgraph-pricing-2026) (secondary, could not verify on langchain.com; whether per-node pricing still applies is unclear)
- Claude Agent SDK hosting: about 1 GiB RAM, 5 GiB disk and 1 CPU per instance in a sandboxed container. Container cost depends on the provider. — [Claude docs](https://docs.claude.com/en/api/agent-sdk/hosting)
- Temporal Cloud: from roughly $200/month at low volume, about $25 per million Actions (Standard). Mission Critical tier is 2x with a 99.95% SLA. Inngest: free Hobby tier with 50,000 step runs/month (one snippet garbles this as "from $20/month"); Pro $50–$500/month. — [spheron](https://www.spheron.network/blog/ai-agent-workflow-orchestration-temporal-inngest-restate-gpu-cloud/), [wetheflywheel](https://wetheflywheel.com/en/comparisons/temporal-vs-inngest/) (secondary; verify on official pages)

**Observability**
- Langfuse Cloud: Hobby free (50k units/month, 2 users); Core $29/month (100k units, unlimited users, 90-day retention); Pro $199/month; Enterprise $2,499/month. Overage is $8 per 100k units, falling with volume. One unit is one trace, observation or score. Self-hosting is free under MIT. — [budgetforge](https://www.budgetforge.dev/tools/langfuse-pricing-2026), [langwatch](https://langwatch.ai/blog/langfuse-vs-langsmith) (secondary)
- LangSmith: Developer free (5k traces/month); Plus $39/seat/month. — [rentierdigital](https://rentierdigital.xyz/blog/langgraph-pricing-2026) (secondary; may have changed with the July 2026 restructure)

**Totals reported by builders**
- Claimed: $1,000–$2,800/month total model and infrastructure costs for a solo operator with about 4 retainer clients. — [betonai](https://betonai.net/ai-agents-in-2026-how-much-solo-operators-are-actually-earning-real-mrr-data-across-5-business-models-chatgpt-claude-stack/) (unverified)

### Inferences
- **Indicative monthly running cost per client for a back-office agent** (inferred from the price points above, not measured):
  - *n8n Cloud or self-hosted VPS:* about $0–$50 hosting (self-host on a $10–$30 VPS, or the n8n Cloud entry tier).
  - *LLM tokens:* $10–$300 for SMB volumes on Haiku/Sonnet-class models with caching. This can spike by 10–100x if loops are uncapped.
  - *Observability:* $0–$29 (Langfuse Hobby/Core, or self-hosted).
  - *Code-agent hosting (Claude Agent SDK / LangGraph):* $20–$200+ for containers or managed deployment.
  - *Durable engine (if used):* $0 (Inngest Hobby) to $200+ (Temporal).
- **Pricing implications:**
  - (a) Put LLM keys on client-owned accounts with provider spend caps, and pass costs through at cost. Alternatively, bundle a usage allowance (for example, up to $X of tokens per month) with overage billed at cost plus 20–30%.
  - (b) Build a buffer of at least 2–3x expected token spend into any fixed-price retainer, to absorb spikes and model price changes.
  - (c) Avoid per-seat or credit-based builder platforms on the builder's own account for multi-client resale, because credit costs scale unpredictably with advanced-model calls (for example, Gumloop's 20 credits per advanced call).
  - (d) Note platform pricing volatility. LangChain (July 2026), CrewAI (August 2026), Lindy (2026) and Relevance AI (late 2025) all changed pricing within the past year, so contracts should allow platform cost changes to pass through.

### Gaps
- Could not verify LangChain's July 2026 pricing restructure on official pages, or whether per-node pricing still applies.
- n8n Cloud Starter/Pro prices for 2026 were not captured.
- No empirical per-task token costs for typical SMB agent workflows (lead qualification, inbox triage) from a reliable source.
- OpenAI model token prices for 2026 were not retrieved.
