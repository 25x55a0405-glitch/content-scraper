# Operations-heavy and agency verticals (US/UK) as buyers of custom multi-step AI agent workflows, 2026

Research date: 2026-10-04. Scope: e-commerce/DTC ($1–20M), marketing/SEO/content agencies (incl. white-label), property management ops, freight brokers/3PLs, B2B SaaS internal ops, creators/media.

**About the sources (read first).** Most 2026 pricing and outcome data here comes from vendor or agency marketing blogs (Debales, Haven, Ringly/eesel, betonai, buldrr, adsnipper, nodesure and similar). They sell into these markets and often report results with no named client. Treat their numbers as directional. Higher-quality sources are marked [stronger]: FreightWaves, Truckstop/Bloomberg Intelligence, the Alto UK agency report via the UK property trade press, Shopify's own blog, and published SaaS price lists. The network proxy blocked direct fetches of Upwork, Reddit and many vendor sites, so a lot of the evidence comes from search-result snippets and could not be checked in full context. Reddit sentiment is thin as a result.

---

## Which concrete multi-step workflows are these verticals paying to automate, and why does an agent graph (loops, branching, human-in-the-loop review) fit?

### Takeaway
In every vertical, the workflows that get paid for are inbox- and document-driven processes that touch several systems: carrier and customer emails into the TMS, maintenance requests into work orders and vendor dispatch, ad and analytics data into client reports, supplier files into catalog listings, security questionnaires answered from a knowledge base, and one video into many content pieces. These are a natural fit for agent graphs because each one involves classification and branching, retry or chase loops, and a review step before anything goes out to a client, carrier or tenant. Many of them are now also packaged as vertical SaaS, though.

### Cited Findings

**(1) E-commerce / DTC ($1–20M, Shopify/Amazon)**
- Shopify's own blog lists agentic use cases and case studies, among them AI purchase-order planning: Kuppa Joy uses Prediko, which generates POs automatically from usage, seasonality and lead times. It also cites fraud and chargeback reduction (Cymbiotika on Signifyd: 98% approval rate, 93% fewer chargebacks) [stronger, but these are vendor customer stories] — [Shopify: Agentic AI use cases](https://www.shopify.com/blog/agentic-ai-use-cases)
- Chargeback dispute automation already exists as a Shopify app (Disputifier, "prevent and fight chargebacks on autopilot") — [Disputifier on Shopify App Store](https://apps.shopify.com/disputifier); Shopify also publishes a 2026 chargeback-software guide — [Shopify](https://www.shopify.com/blog/chargeback-management-software)
- A vendor blog claims stores that use AI returns automation see "30–50% fewer return-related disputes" (no source given) — [Shopify agentic AI search snippet / adfinite](https://adfinite.com/blog/ai-agent-returns-refunds-shopify-2)
- Catalog and listing enrichment is a crowded SaaS category. Merchkit (supplier data to enriched listings, syndicated to Amazon/Walmart/Google) starts at $999/mo; PixeePIM from €490/mo; Pimberly $7,500–$15,000 (period not stated); Shopify-native PIMs run $199–$549/mo; enterprise Akeneo/Salsify cost $45k+/yr. "Automated Commerce" (launched Jan 16 2026) turns supplier CSV/PDF/Excel files into listings — [Capterra: Merchkit](https://www.capterra.com/p/10030331/Merchkit/); [Capterra: PixeePIM](https://www.capterra.com/p/10046106/PixeePIM/); [Carro: Best PIM for Shopify](https://getcarro.com/blog/best-pim-for-shopify)
- Amazon FBA reimbursement recovery is run as a contingency service. Most providers (GETIDA, Carbon6, Refunds Manager) charge 25% of recovered funds. The claim window shrank from 18 months to 60 days on Oct 23 2024, and new Inbound Defect Fees ($0.32–$1.74/unit) in Q1 2026 created new claim categories — [Amplisell](https://amplisell.com/blog-posts/best-amazon-reimbursement-services-for-fba-brands); [Titan Network](https://titannetwork.com/amazon-reimbursement-service/)
- Upwork demand signals: job posts include "AI Automation & Agent Specialist (Claude/GPT) for Retail/E-Commerce Brand" and "AI Workflow Developer for Shopify Agency Operating System". Fixed-price gigs bundle Shopify, Sheets/Slack/CRM, AI abandoned-cart emails and a chatbot — [Upwork job](https://www.upwork.com/freelance-jobs/apply/Automation-Agent-Specialist-Claude-GPT-for-Retail-Commerce-Brand_~022080711922231636555/); [Upwork job (Shopify agency OS)](https://www.upwork.com/freelance-jobs/apply/Workflow-Developer-for-Shopify-Agency-Operating-System_~022069781483899170925/); [Upwork service listing](https://www.upwork.com/services/product/development-it-ai-workflow-automation-for-shopify-zapier-chatgpt-email-crm-integration-1950046413520374620)
- Support resolution is already productized. Gorgias AI Agent charges $0.90/resolution on annual plans and $1.00 month-to-month, rising to $1.50 above the bundled allotment. Each resolution also uses up a helpdesk ticket (helpdesk tiers $10/$60/$360/$900 per month) — [Ringly](https://www.ringly.io/blog/gorgias-ai-agent-pricing-per-resolution); [eesel](https://eesel.ai/blog/gorgias-plans-comparison)

**(2) Marketing, SEO and content agencies**
- Client reporting comes up most often. One agency is said to have cut its reporting month from 10 working days to one hour. A 14-person agency moved reporting, research and content prep to agents and saved about 80 hrs/week. A report agent pulling GA, social and ad accounts replaced 3 hrs per client per month. All of these are vendor or agency case-study claims — [Whatagraph: 10 AI workflows from agencies](https://whatagraph.com/blog/articles/ai-marketing-workflows); [Burrak AI case study](https://burrakai.com/blog/marketing-agency-ai-automation-case-study); [GetDevDone](https://getdevdone.com/blog/ai-powered-client-reporting-for-marketing-agency.html)
- The GetDevDone case automated client reporting summaries but kept human review before sending, which is an explicit HITL pattern — [GetDevDone](https://getdevdone.com/blog/ai-powered-client-reporting-for-marketing-agency.html)
- SEO agencies are being sold multi-agent SEO systems covering discovery, AI-visibility checks, SERP research, briefs, schema and reporting. AEO Engine claims "100+ coordinated agents" — [AEO Engine](https://aeoengine.ai/industries/marketing-agency-seo)

**(3) Property management / real-estate operations**
- Maintenance triage (categorize the request, read photos, prioritize, create a work order, dispatch a vendor) and after-hours call coverage are the main automated workflows. AppFolio Realm-X "Flows" automate multi-step leasing, billing and maintenance tasks, and Smart Maintenance creates prioritized work orders from photos — [Second Nature / AppFolio coverage via search](https://www.secondnature.com/blog/ai-property-management-software); [Haven: AppFolio AI glossary](https://www.usehaven.ai/post/appfolio-ai-integration-glossary)
- Collections and rent reminders and leasing response are also automated categories — [Haven: collections AI tools](https://www.usehaven.ai/post/collections-ai-property-management-tools)
- UK: 66% of estate and letting agents expect to rely on compliance/AML automation, and admin pressure is the main driver (Alto 2026 Agency Trends Report, n=250) [stronger] — [Estate Agent Today](https://www.estateagenttoday.co.uk/breaking-news/2026/01/estate-agents-plan-to-adopt-ai-but-there-is-a-size-divide/); [Property Industry Eye](https://propertyindustryeye.com/?p=159266)

**(4) Freight brokers and 3PLs**
- Brokers: agents classify inbound carrier and shipper email (capacity offers, quote requests, check calls, rate confirmations, noise), extract lane, equipment, rate and MC number, pull rate guidance and reply. Vendors claim quote response fell from about 45–47 min to under 1–5 min and win rate rose from 18% to 27% (vendor claims) — [GetTransport blog](https://blog.gettransport.com/trends-in-logistic/ai-agents-freight-brokers-2026-quote-automation/); [Debales guide (search snippet)](https://debales.ai/blog/ai-agents-for-freight-brokers-complete-2026-guide)
- Other broker workflows: check calls and track-and-trace, carrier vetting, rate-con processing, exception handling. Parade CoDriver Voice 2.0 claims 27% more quotes from the same call volume — [Parade](https://www.parade.ai/resources); [Rework: 13 logistics AI tools](https://resources.rework.com/tools/ai-tools/best-ai-tools-for-logistics-2026)
- 3PLs: order intake from email, EDI 940, portals and PDFs, validated against the WMS; WISMO replies (vendor claims 60–75% handled with no human touch); exception detection from WMS/TMS events with drafted outreach; client onboarding that maps requirements to WMS config and EDI mappings — [Debales 3PL page (search snippet)](https://debales.ai/industry/3pl-warehousing); [Productiv: agentic 3PL workflows](https://getproductiv.com/blog/agentic-3pl-workflows); [StackAI 3PL](https://www.stackai.com/solutions/third-party-logistics)
- Industry commentary favors HITL. "Liability and complexity will keep humans in the loop for now". A tool like Levity drafts replies to rate requests for broker review before sending — [FreightCaviar: Let's get real about AI in brokerage](https://freightcaviar.com/stories/lets-get-real-about-ai-in-freight-brokerage); [FreightCaviar: automating broker emails](https://freightcaviar.com/stories/automating-freight-broker-emails)

**(5) B2B SaaS startups (internal ops)**
- Security questionnaire and RFP answering is a mature SaaS category: Conveyor (Business from $9,600/yr, free tier), Loopio Foundations ($20,000/yr), Vanta questionnaire automation (AWS Marketplace listings of $10k/yr for 144 questionnaires and $16k/yr for 288), and Responsive, Whistic, Drata, Inventive AI on custom quotes. Reviewers say Vanta and Conveyor can be prohibitively expensive for early-stage startups — [Wolfia: Conveyor pricing](https://wolfia.com/blog/conveyor-reviews-pricing-alternatives); [Inventive AI comparison](https://www.inventive.ai/blog-posts/best-security-questionnaire-automation-software); [AutoRFP](https://autorfp.ai/blog/best-security-questionnaire-software)
- Support triage and auto-routing are built into helpdesks. Zendesk Suite Professional is $115/agent/mo plus Copilot at $50 (= $165/seat). Supportbench includes AI auto-triage and routing. Helply charges $1/ticket — [Supportbench vs Zendesk](https://www.supportbench.com/the-ultimate-zendesk-alternative/); [Helply](https://helply.com/blog/zendesk-vs-help-scout-vs-helply)
- A search snippet reported that Salesforce agreed to acquire Fin (formerly Intercom) for about $3.6B, announced June 15 2026. I could not check this against a primary source; verify before using — [eesel (snippet)](https://www.eesel.ai/blog/gorgias-automate-pricing-per-resolution-2026)

**(6) Creators / media (YouTube, newsletters)**
- The standard pipeline is one YouTube video → transcript → several platform-specific writers (X, LinkedIn, IG, newsletter, Shorts scripts) → image generation → an Airtable moderation queue for approval → publishing. An open-source example on GitHub claims about 90% less manual content time — [GitHub: content-repurposing-pipeline](https://github.com/TrueSkillMaster/content-repurposing-pipeline); [CreatorSkills guide](https://creatorskills.co/blog/ai-content-repurposing-tools-workflows-2026)
- Newsletter ops are often handed to VAs instead. VA Masters says a Filipino VA costs up to 80% less than a $45k–$60k/yr in-house newsletter coordinator. Productized "newsletter operator" services run beehiiv newsletters using AI with human editing — [VA Masters](https://vamasters.com/beehiiv-newsletter-virtual-assistant/); [Letter Operators](https://letteroperators.carrd.co)
- Sponsorship sales are being absorbed by platforms: beehiiv (about $30M+ ARR, ~110 staff) is doubling its ad sales and ops team in H1 2026 to sell sponsors for creators — [Adweek](https://www.adweek.com/media/beehiiv-ad-sales-newsletter-programmatic/)

### Inferences
- **Why agent graphs fit (common pattern):** (a) a classifier node routes messy inbound items (email, PDF, call transcript) down different branches; (b) tool-calling nodes read and write systems of record (Shopify, TMS, AppFolio/Buildium, GA/ads APIs, WMS); (c) loops handle chasing (supplier PO follow-ups, carrier check calls, missing questionnaire evidence, vendor confirmation); (d) a human-review node before anything goes externally (client report, rate quote, tenant reply, chargeback rebuttal, security answer). The strongest fits have all four. Freight email to quote, maintenance triage to dispatch, and client reporting with review all qualify.
- **Top 2–3 workflows per vertical (synthesis):**
  - E-com: (1) supplier/PO chasing and inbound reconciliation; (2) returns, chargeback and dispute evidence packets; (3) catalog/listing enrichment from supplier files to Shopify/Amazon. Support resolution is real but SaaS-dominated (Gorgias).
  - Agencies: (1) multi-source client reporting with commentary and review; (2) SEO content pipeline (research → brief → draft → optimize → QA); (3) campaign brief and social calendar prep.
  - Property mgmt: (1) maintenance intake → triage → work order → vendor dispatch → tenant updates; (2) after-hours comms; (3) arrears/collections chasing; (UK) compliance and certificate tracking.
  - Freight/3PL: (1) inbound email parsing → quote/tender → TMS entry; (2) check calls and exception handling; (3) 3PL order intake and WISMO.
  - SaaS: (1) security questionnaire/RFP drafting from internal docs with SME review; (2) support ticket triage and draft resolution; (3) churn-signal analysis feeding CS playbooks. Onboarding automation was barely covered in sources (gap).
  - Creators: (1) video → multi-platform repurposing with an approval queue; (2) newsletter assembly; (3) sponsor inbound handling and deliverable tracking (weakly evidenced).

### Gaps
- No primary Reddit threads could be read (fetch was blocked). Pain is inferred from vendor and press sources.
- Supplier/PO chasing for $1–20M DTC brands specifically (as opposed to inventory planning SaaS like Prediko) had no direct case evidence.
- B2B SaaS customer onboarding and churn-analysis agent builds: no concrete case studies or pricing found.
- Creator sponsorship-ops automation: no case studies found.

---

## What do agencies and freelancers charge for these builds and retainers in 2026?

### Takeaway
Most aggregator and agency sources cluster around **$2.5k–$15k per workflow build plus $1.5k–$5k/month retainers** for SMB clients. Simpler e-commerce "AI services" sell for $300–$800/mo, and custom multi-agent systems go to $50k+. Freelance n8n/Make/agent builders report about **$85–$185/hr** (median roughly $95–$135 for n8n). Offshore white-label labor starts around $15/hr. Almost all of these figures are self-reported by sellers.

### Cited Findings
- AI automation agency pricing: setup roughly $2,500–$15,000 per build plus $1,500–$5,000/mo retainers; $3,000 for focused workflow builds up to $50,000+ for custom multi-agent systems — [AdSnipper](https://adsnipper.com/blog/ai-automation-agency/); [AllAble](https://www.allable.ai/blog/ai-automation-agency/); [Lets-Viz pricing 2026 (snippet)](https://lets-viz.com/blogs/ai-automation-agency-pricing-2026-what-buyers-pay); [Buldrr n8n pricing](https://buldrr.com/n8n-automation-agency-pricing/)
- Voice AI managed retainer: $1,500–$3,000/mo per client plus $3,500–$7,500 setup — [AdSnipper/AllAble search snippet](https://www.allable.ai/blog/ai-automation-agency/)
- E-commerce/DTC builds: $5k–$12k build fees with $2k–$5k/mo retainers. A separate figure puts "e-commerce AI services" at $300–$800/mo per customer — [Medium: profitable AI niches (low-quality source)](https://medium.com/@mrbox27/the-5-most-profitable-ai-niches-for-solo-creators-in-2025-with-real-revenue-data-e4061e782c43); [AlmCorp](https://almcorp.com/blog/make-money-ai-digital-agencies-2026/)
- AAA project range: $5k–$50k per project with $500–$5k/mo retainers — [AlmCorp](https://almcorp.com/blog/make-money-ai-digital-agencies-2026/)
- Freelance hourly: n8n self-hosted median $135/hr (top quartile $185); n8n cloud median $95/hr (TQ $140); Make median $85/hr (TQ $120); broader solo-operator range $95–$235/hr; AI automation project rates $2k–$12k. Source is a content site with unclear methodology — [BetOnAI](https://betonai.net/ai-coding-is-the-highest-paying-freelance-skill-in-2026-heres-exactly-what-to-charge-real-rate-data/)
- Demand signal: Claude Code specialist searches rose 938% and n8n AI automation searches 125% between Nov 2025 and Apr 2026. This appears to be marketplace search data (likely Fiverr's index) relayed by an aggregator, so check the original — [9am.works](https://www.9am.works/freelancer-academy/blog/ai-premium-or-ai-discount-two-track-freelance-market); [BetOnAI](https://betonai.net/ai-coding-is-the-highest-paying-freelance-skill-in-2026-heres-exactly-what-to-charge-real-rate-data/)
- LangChain/LangGraph is described as the most requested framework in AI agent job posts, and LangGraph (stateful multi-agent) as a differentiator — [BetOnAI](https://betonai.net/ai-coding-is-the-highest-paying-freelance-skill-in-2026-heres-exactly-what-to-charge-real-rate-data/)
- Property management voice and triage agents (as a done-for-you or SaaS price anchor): $400–$550/mo under 50 units, $550–$800 for 50–200, $800–$1,200 for 200–500, $1,200–$2,500 for 500+ — [Prestyj](https://prestyj.com/blog/ai-voice-agent-pricing-for-property-management)
- Freight broker AI deployments are said to pay back in 60–120 days (vendor claim) — [Debales (snippet)](https://debales.ai/blog/ai-agents-for-freight-brokers-complete-2026-guide)

### Inferences
- For a first-client agent-graph offer, realistic anchors are: **$3k–$8k fixed build for one workflow with HITL, plus $500–$2k/mo for monitoring and iteration**. Ops-heavy buyers with measurable labor savings (freight, 3PL, mid-size PM) sit at the higher end. Creators and small DTC brands sit at the lower end.
- Retainers have to compete with per-resolution or per-unit SaaS pricing ($0.90–$1.50/resolution, $2.50–$18/unit/mo). That caps what can be charged where the SaaS already covers the workflow.

### Gaps
- No verified marketplace dataset (Upwork/Contra) on agent-build contract values; the Upwork pages could not be fetched.
- No UK-specific day rates for AI automation freelancers were found (expect £ rates broadly in line with US hourly, but this is unverified).

---

## Do agencies outsource AI builds (white-label)? At what rates, and how do they find builders?

### Takeaway
Yes. White-label is already normal in agencies (a widely quoted, poorly sourced figure says 73% use some white-label service), and a market of white-label AI build partners exists. It ranges from embedded offshore specialists at about $15/hr ($1.2k–$2.4k/mo) to embedded-partner retainers from about $1.5k/mo and MVP builds from $3k. Agencies resell AI services to their own clients at $300–$1,500/mo. How agencies find builders is poorly documented; observed channels are Upwork posts, productized partner sites, and platform partner programs (Vendasta etc.).

### Cited Findings
- 73% of agencies use white-label services in some form; 60% of those outsource PPC; agencies outsourcing 40–60% of delivery grow 2.3x faster with 18–22% higher margins. These are aggregator stats without a clear primary survey, so flag them — [AlmCorp: white-label AI marketing services 2026](https://almcorp.com/blog/white-label-ai-marketing-services-agencies-2026-guide/)
- Embedded offshore AI automation specialists: $15/hr, $2,400/mo full-time or $1,200/mo part-time, white-labeled — [search snippet, agency pricing article](https://theaiimplementationmethod.com/2026/05/19/n8n-automation-agency-business/)
- White-label AI build partner pricing: embedded partnership from $1,499/mo; MVP builds from $3,000/project; some partners use wholesale per-project pricing with the agency setting retail — [search snippet: whitelabelai.agency / White Label IQ](https://www.whitelabeliq.com/white-label-ai-services/); [White Label AI Agency](https://whitelabelai.agency/)
- Agencies resell white-label AI receptionists and reputation tools at $300–$1,500/mo per client, with $500–$2,000 setup ($3k–$5k in legal/healthcare). Platform licenses, e.g. Chatbot Builder AI agency plan, start at $595/mo — [Vendasta: white-label AI agents](https://www.vendasta.com/blog/white-label-ai-agents/); [Mediaffy](https://mediaffy.com/white-label-ai-agent-platforms/)
- n8n white-labeling (embedding n8n in an agency-branded platform) reportedly costs about $50k/yr in licensing, versus a $20/mo VPS self-hosted for internal use. Agencies can commission a branded automation platform for $13k–$25k — [TaskJuice: real cost of white-labeling n8n](https://taskjuice.ai/blog/n8n-white-label-cost-agencies)
- An Upwork post from a Shopify agency wants an "AI Workflow Developer for [a] Shopify Agency Operating System", which is direct evidence of agencies hiring outside AI builders on marketplaces — [Upwork job](https://www.upwork.com/freelance-jobs/apply/Workflow-Developer-for-Shopify-Agency-Operating-System_~022069781483899170925/)
- UK agency pressure: 36–38% of UK agencies say clients have taken work in-house because of AI; creative agency employment fell 14.3% in 2025 — [Mode Marketing: State of UK Agency Market 2026](https://modemarketing.ai/uk-agency-market-2026/). ISBA's July 2026 survey: 99% engagement with AI but only 14% report significant business impact — [Whitehat SEO: AI in Marketing 2026](https://whitehat-seo.co.uk/blog/ai-in-marketing-2026-research-report)
- A 250-agency agentic AI adoption survey (2026) exists but could not be fetched — [Digital Applied](https://www.digitalapplied.com/blog/agentic-ai-adoption-survey-2026-250-agencies)

### Inferences
- Agencies are a two-sided opportunity: (a) internal ops buyers (reporting, content pipelines), and (b) channel partners who resell builds to their SMB clients. Channel (b) pushes wholesale prices down: if an agency resells at $300–$1,500/mo, a builder can probably get only about 30–60% of that.
- Margin pressure on UK agencies (clients in-housing, layoffs) gives them a reason to buy efficiency tooling but also tightens budgets.
- Reaching agencies is relatively easy for a remote freelancer: agencies are online-native, post on Upwork, join communities, and understand retainers.

### Gaps
- No primary data on how agencies *discover* white-label AI builders (referral vs marketplace vs communities).
- The 73% white-label stat has no primary survey; the Digital Applied survey content could not be checked.

---

## Where is off-the-shelf SaaS already dominant, and where do custom builds still win?

### Takeaway
SaaS is dominant or fast-consolidating in: e-com support resolution (Gorgias), chargebacks and fraud (Signifyd, Disputifier), Amazon reimbursements (25% contingency services), PIM/catalog enrichment ($490–$999/mo tools), security questionnaires (Conveyor/Vanta/Loopio), helpdesk triage (Zendesk/Supportbench), PM maintenance triage and after-hours voice (AppFolio Realm-X, Property Meld, Conduit, EliseAI), and freight email/quote agents (Debales, Parade and others). Custom builds still win where (a) the stack is idiosyncratic (smaller TMS, a mix of spreadsheets and portals), (b) the buyer is below the SaaS minimum or price point, (c) the workflow spans several tools no single vendor covers (agency reporting plus commentary plus client-specific QA; supplier chasing across email, Sheets and ERP), or (d) the buyer wants ownership and HITL control.

### Cited Findings
- AppFolio Realm-X reportedly has minimums of about $280/mo and a 50-unit floor that locks small landlords out. For small portfolios, third-party AI adds value for after-hours phones, maintenance dispatch, and multi-channel comms — [Haven / search snippet](https://www.usehaven.ai/post/betterbot-alternative-for-property-managers); [AI Pro Playbook: Realm-X](https://aiproplaybook.com/tools/appfolio-realm-x)
- EliseAI is best suited to multifamily operators with 500+ units. SMB portfolios are pointed to Buildium ($62/mo) or DoorLoop ($99/mo) — [Second Nature](https://www.secondnature.com/blog/ai-property-management-software); [MagicDoor](https://magicdoor.com/blog/best-ai-property-management-software)
- PM AI SaaS price points: Conduit from $18/unit/mo; Property Meld about $2.50/unit/mo for triage; Super from $250/mo (500 min) to $415/mo (24/7); Fieldproxy from $649/mo; most PM teams spend $300–$1,000/mo — [Conduit](https://www.conduit.ai/blog/best-ai-customer-support-tools-for-property-management-in-2026); [SF AI Labs](https://sfailabs.com/guides/best-ai-maintenance-triage-tools-small-property-managers); [Fieldproxy](https://www.fieldproxy.ai/resources/blog/best-property-management-software-ai-maintenance-2026)
- Freight: Debales is described as a multi-agent platform covering email, quote, check-call, rate-con and exceptions, bootstrapped to $1M ARR with integrations to six major TMSs (McLeod LoadMaster, Alvys, Tai, Turvo, Rose Rocket, Descartes). Freight Technologies launched Zayren Pro (agentic auto-booking) in Jan 2026; Parade sells CoDriver — [GetTransport blog](https://blog.gettransport.com/trends-in-logistic/ai-agents-freight-brokers-2026-quote-automation/); [Rework](https://resources.rework.com/tools/ai-tools/best-ai-tools-for-logistics-2026)
- Security questionnaires: Conveyor $9.6k+/yr, Loopio $20k/yr, Vanta about $10k–$16k/yr, all seen as expensive for early startups — [Wolfia](https://wolfia.com/blog/conveyor-reviews-pricing-alternatives); [Inventive AI](https://www.inventive.ai/blog-posts/best-security-questionnaire-automation-software)
- Creators: n8n and Make have native YouTube/OpenAI/ElevenLabs nodes and free or low tiers. DIY templates (GitHub) and Claude "skills" make simple repurposing cheap to do yourself — [Assistents.ai](https://assistents.ai/blogs/best-ai-agent-for-youtube-automation); [GitHub](https://github.com/TrueSkillMaster/content-repurposing-pipeline)
- UK lettings: smaller independent firms adopt AI more slowly than large agencies (nearly 9 in 10 large agencies plan AI adoption in 2026), and about a third of agents feel nervous or unsure about AI (Alto) [stronger]. A June 2025 Inventory Base survey found 53% of agencies had no AI/automation plans [older, flag] — [Estate Agent Today](https://www.estateagenttoday.co.uk/breaking-news/2026/01/estate-agents-plan-to-adopt-ai-but-there-is-a-size-divide/); [Property Reporter](https://www.propertyreporter.co.uk/over-half-of-lettings-agents-have-no-plans-to-adopt-ai.html)

### Inferences
- **SaaS-dominant (avoid as a lead offer):** Shopify support bots, chargeback fighting, FBA reimbursements, generic PIM, enterprise PM maintenance triage on AppFolio, security questionnaires for Series A+ (where Vanta is already the compliance stack).
- **Custom still wins (lead-offer candidates):** (a) freight brokers on smaller or legacy TMSs, or 3PLs with custom portals and spreadsheets, where vendor integrations don't exist; (b) agency client reporting with bespoke narrative, client-specific QA and white-label delivery; (c) DTC supplier/PO chasing and inbound reconciliation across email, Sheets and ERP/inventory apps; (d) pre-Series-A SaaS that won't pay $10k+/yr for questionnaire software but faces enterprise security reviews; (e) PM firms under AppFolio's 50-unit floor or using Buildium/DoorLoop/Rent Manager, where native AI is thinner.
- Vertical SaaS is spreading fast (Debales $1M ARR bootstrapped; Realm-X Flows), so custom-build advantages may be temporary. Builders should position as "integration plus HITL tailoring" or as implementation partners for these tools.

### Gaps
- No G2 review mining was possible (fetch blocked). Specific complaints about gaps in Gorgias, Realm-X or Debales are not documented here.
- Debales pricing was not found.

---

## Are there case studies of solo builders or small AI agencies serving these verticals, with revenue figures?

### Takeaway
There are plenty of revenue claims, but almost none are verifiable or tied to a specific vertical. Solo operators of productized automation services are said to make about $50k–$300k ARR, and 2–5-person agencies $300k–$1M. The most concrete vertical datapoint is a vendor, not a solo builder: Debales (freight/3PL multi-agent platform), bootstrapped to $1M ARR.

### Cited Findings
- Solo productized-service operators reportedly land at $50k–$300k ARR; 2–5-person agencies at $300k–$1M ARR within two years (no methodology) — [MindStudio case studies (snippet)](https://www.mindstudio.ai/blog/start-ai-automation-business-case-studies)
- Self-reported: an AAA went from 3 clients at $4,200 MRR to 14 clients at $23,000 MRR in 90 days, pricing $800–$3,500/mo by complexity. Another freelancer says $6,000/mo on $20/mo of tools — [NodeSure success stories](https://www.nodesure.com/ai-automation-agency-success-stories-5-real-client-results-in-2026/); [Medium (low quality)](https://medium.com/@mrbox27/the-5-most-profitable-ai-niches-for-solo-creators-in-2025-with-real-revenue-data-e4061e782c43)
- E-com case: an abandoned-cart AI system "recovered $127,000" with "340% ROI within 90 days" (unnamed client, vendor claim) — [NodeSure](https://www.nodesure.com/ai-automation-agency-success-stories-5-real-client-results-in-2026/)
- n8n agency business guides claim a route to $20k+/mo — [The AI Implementation Method](https://theaiimplementationmethod.com/2026/05/19/n8n-automation-agency-business/)
- Fortune (May 2026) reports solo founders using AI to do the work of whole teams, with limits — [Fortune](https://fortune.com/2026/05/18/solo-founders-ai-automation-entire-teams-entrepreneurs/) [stronger outlet; vertical detail not extracted]
- Debales: freight/3PL multi-agent platform bootstrapped to $1M ARR — [GetTransport blog citing Debales](https://blog.gettransport.com/trends-in-logistic/ai-agents-freight-brokers-2026-quote-automation/)

### Inferences
- Revenue claims in the "AI automation agency" niche are heavily inflated by course and lead-gen marketing. Treat $10k–$20k MRR at about 5–15 clients as an upper-middle benchmark for a solo operator, not a typical outcome.
- Vendors like Debales reaching $1M ARR bootstrapped suggest freight/3PL buyers pay real money for email and exception automation, which also means competition is arriving fast.

### Gaps
- No independently verified solo-builder case studies naming a client in any of the six verticals.
- No case studies for creator/media ops builders with revenue.

---

## How do the six verticals compare on pain, budget, competition, risk and reachability? (comparable fields)

### Takeaway
On the evidence, **marketing/SEO agencies** (reachable, retainer-literate, real reporting and content pain, white-label channel) and **freight brokers/3PLs** (very high email pain, measurable ROI, but heavy SaaS entry and a margin squeeze) are the strongest first-client verticals for custom agent graphs. **E-com $1–20M** is attractive only for non-SaaS workflows (supplier/PO chasing, reconciliation). **Property management** and **B2B SaaS** are increasingly SaaS-covered. **Creators** are easy to reach but low-budget and DIY-prone.

### Cited Findings
- Freight market context: awarded broker margins fell to 16.9% in July 2026, down 4.5 points month-over-month (Truckstop/Bloomberg Intelligence related reporting) [stronger] — [Fleet Equipment Mag: broker/carrier survey](https://www.fleetequipmentmag.com/freight-broker-carrier-survey-2026/); [SDCExec/Tabi](https://www.sdcexec.com/transportation/trucking/news/22970730/tabi-connect-spot-freight-market-shifts-toward-shippers)
- FreightWaves calls 2026 a "perfect storm" with a wave of brokerage failures; roughly 8,000 brokerages shut in 2023; stricter FMCSA financial-security enforcement started Jan 16 2026 [stronger] — [FreightWaves](https://www.freightwaves.com/?p=567368); [Factoring.org](https://magazine.factoring.org/magazine-articles/carrier-amp-broker-failures-in-20242025-and-why-2026-may-bring-one-last-wave)
- FreightWaves: "Freight AI isn't replacing brokers — here's the ROI" — [FreightWaves](https://www.freightwaves.com/?p=581687)
- UK property agents: 52% plan AI adoption in 12 months, larger firms far more than independents (Alto, n=250) [stronger] — [Estate Agent Today](https://www.estateagenttoday.co.uk/breaking-news/2026/01/estate-agents-plan-to-adopt-ai-but-there-is-a-size-divide/)
- UK agencies: 36–38% report clients in-housing due to AI — [Mode Marketing](https://modemarketing.ai/uk-agency-market-2026/)
- Newsletter coordinator in-house cost: $45k–$60k/yr (the alternative being a VA) — [VA Masters](https://vamasters.com/beehiiv-newsletter-virtual-assistant/)
- SaaS questionnaire tools: $9.6k–$20k/yr — [Wolfia](https://wolfia.com/blog/conveyor-reviews-pricing-alternatives)

### Inferences
Comparison matrix. Scores are 1–5 (5 = most favorable to a remote freelancer building custom agent graphs, except Risk, where 5 = highest risk). These are judgment scores based on the findings above.

| Vertical | Top workflows | Pain intensity | Typical size | Budget for custom build (inferred) | WTP evidence | SaaS competition | Risk | Reachability (remote) |
|---|---|---|---|---|---|---|---|---|
| E-com/DTC $1–20M | Supplier/PO chasing; returns/chargeback evidence; catalog enrichment | 3 | 2–30 staff | $3k–$10k build; $500–$2k/mo | Medium: Upwork posts; e-com AAA pricing $5–12k claimed | High (Gorgias, Signifyd, Disputifier, PIMs, 25% FBA recovery) | 2–3 (customer-facing errors, refund money) | 4 (online, Upwork, Shopify communities) |
| Marketing/SEO/content agencies (+white-label) | Client reporting with review; SEO content pipeline; brief and calendar prep | 4 | 5–50 staff | $3k–$8k build; $1k–$3k/mo; white-label wholesale lower | Medium-high: many case studies; partner programs at $1.5k/mo+ | Medium (Whatagraph, AEO Engine, generic tools; no one owns custom narrative and QA) | 2 (internal and client-facing reports, low liability) | 5 (online-native, outsource-literate) |
| Property mgmt ops | Maintenance triage → dispatch; after-hours comms; arrears chasing; UK compliance | 4 | 50–2,000 units, 3–50 staff | $2k–$8k; anchored against $300–$1,000/mo SaaS | Medium: SaaS spend data; UK compliance automation intent (66%) | High and rising (AppFolio Realm-X, EliseAI, Conduit, Property Meld, Super) | 3–4 (habitability, emergencies, tenant law, fair housing) | 2–3 (local, less online; UK independents slow to adopt) |
| Freight brokers / 3PLs | Email parse → quote/tender → TMS; check calls/exceptions; 3PL order intake/WISMO | 5 | 5–100 staff | $5k–$15k build; $1k–$4k/mo | High: quote-speed ROI, 60–120 day payback claims, Debales $1M ARR | High and rising (Debales, Parade, Zayren, others) | 3 (financial and carrier errors; margin squeeze → churn or failure) | 3 (relationship-driven, but r/FreightBrokers, LinkedIn, Upwork) |
| B2B SaaS startups (internal ops) | Security questionnaire/RFP; support triage; churn analysis | 3 | 10–150 staff | $3k–$10k; capped by $10k–$20k/yr SaaS | Medium: questionnaire SaaS pricing shows budget; startups say too pricey | Very high (Conveyor, Vanta, Loopio, Zendesk AI, Fin) and an in-house engineering culture | 2–3 (wrong security answers are a liability) | 4 (online, but often build in-house) |
| Creators/media | Video → repurposing with approval; newsletter assembly; sponsor ops | 2–3 | 1–10 staff | $1k–$4k; $200–$1k/mo | Low-medium: VA substitution ($45–60k coordinator vs VA), DIY templates | Medium (Opus/Make templates, beehiiv in-platform sales, VAs) | 1–2 | 4–5 (very online) but price-sensitive |

- Pairwise headline: agencies beat creators (similar reachability, bigger budgets, retainers); freight beats PM (higher pain and measurable ROI, though both face strong SaaS); e-com beats SaaS startups for custom work only where the workflow sits outside helpdesk and questionnaire tools.
- Compared with professional-services verticals (law, accounting): these verticals have lower regulatory risk on average (PM and freight are the exceptions) and are more reachable online, but buyers are often more price-anchored by cheap vertical SaaS.

### Gaps
- Budget figures in the matrix are inferred from general agency pricing plus SaaS anchors. No vertical-specific survey of custom-build budgets was found.
- No US PM industry data (e.g., NARPM) on AI adoption or ops spend was retrieved.
- No count of active small US freight brokerages (FMCSA authorities) for 2026 was found.
