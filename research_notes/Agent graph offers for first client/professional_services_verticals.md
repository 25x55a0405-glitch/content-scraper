# Professional-services verticals (US/UK) as buyers of custom multi-step AI agent workflows, 2026

Scope: (1) accounting/bookkeeping/tax, (2) small law/legal ops, (3) insurance brokers/agencies, (4) recruiting/staffing, (5) mortgage brokers/financial advisers (RIAs), (6) immigration/visa consultancies. Research date: 2026-10-04.

Method note: about 18 search/fetch calls. Several primary-source pages could not be fetched directly because the network proxy blocked them (financial-cents.com, clio.com, insurancebusinessmag.com). For those, the figures come from search-engine summaries of the pages and are marked "(snippet)". Vendor blogs (agency-pricing guides, SaaS vendors' "best tools" posts) are weaker sources and are marked "(vendor source)". Anything drawn only from background knowledge is put in Gaps or Inferences, never in Cited Findings.

---

## Q1. Which specific multi-step workflows do these firms complain about, and why does an agent graph (not a chatbot) fit?

### Takeaway
The pain that comes up again and again in every vertical is **chasing missing documents or information from clients or candidates, then checking and filing what comes back**. Examples: accounting document collection, legal intake, insurance renewals, recruiting screening, mortgage fact-finds, immigration evidence bundles. Each of these is a loop (request, wait, check completeness, re-request) with branching and a human sign-off, so it is naturally an agent graph rather than a chatbot. Accounting has the clearest survey evidence: chasing documents is firms' #1 choice of task to hand to an autonomous agent.

### Cited Findings
**Accounting/bookkeeping/tax**
- "Nearly 7 in 10 firms picked chasing clients for missing documents as the #1 task they would hand to an autonomous AI agent" (snippet; 2026 State of AI in Accounting & Bookkeeping report) — [Financial Cents](https://financial-cents.com/resources/guides/the-state-of-ai-in-bookkeeping-accounting/)
- Reported AI adoption among accounting firms rose from 9% (2024) to 41% (2025). 88% of firms use AI for client services and 86% for firm operations (snippet; the search returned several 2025–26 survey pages and it was unclear which one is the original source, so treat as indicative) — [CPA.com 2025 AI in Accounting Report](https://www.cpa.com/sites/cpa/files/2025-06/2025_AI_in_Accounting_Report.pdf); [aiopsnav aggregator](https://aiopsnav.ai/ai-accounting-firms)
- Delays often start with "scattered documentation and missing information… buried in email threads" (vendor source) — [Liscio](https://www.liscio.me/blog-posts/how-accounting-firms-can-automate-client-document-collection)
- UK trigger: Making Tax Digital for Income Tax applies from April 2026 to sole traders and landlords earning over £50,000. 42% of accountants were not yet prepared and only 10% were "very prepared". 81.7% called MTD their biggest challenge and 79.1% their biggest opportunity. Practitioners describe themselves as "already overstretched" (vendor survey) — [IRIS MTD readiness survey](https://www.iris.co.uk/news/m-t-d-readiness-survey/); [IRIS blog](https://www.iris.co.uk/blog/accountancy/what-accountancy-professionals-think-about-mtd-ai-outsourcing-and-more/)

**Small law firms**
- In Clio's 2026 US survey, 71% of solos and 75% of small firms report using AI, but only 32% and 31% respectively report a revenue increase from it — [NC Bar Association, May 2026](https://www.ncbar.org/nc-lawyer/2026-05/by-the-numbers-what-surveys-show-about-law-firm-ai-adoption/)
- Clio 2025 Solo & Small report: growing firms invest more in client intake and CRM ("capture leads, automate follow-up… path from initial contact to signed engagement"). Growing solos handle 37% more cases and growing small firms 25% more. The gains come from "eliminating inefficiency in client intake, reducing administrative overhead" (snippet) — [Clio press release](https://www.clio.com/about/press/legal-trends-solo-small-law-firms-2025/); [Clio highlights](https://www.clio.com/blog/solo-small-law-firms-highlights-2025-legal-trends/)

**Insurance agencies (US independent)**
- 2026 Big "I" Tech Trends: two-thirds of agencies plan to increase AI use in the next 12 months. Current use: 33% experimenting, 22% limited areas, 8% embedded in daily workflows, 31% not using AI. Main motivations are operational efficiency (60%) and staff productivity (52%). Agencies mostly use AI for "simple, assistant-level tasks" such as marketing content and meeting summaries, and plan to expand into "workflow automation" — [IndependentAgent.com](https://www.independentagent.com/news/two-thirds-of-independent-agents-plan-to-increase-ai-use-this-year/); [InsuranceNewsNet](https://insurancenewsnet.com/innarticle/two-thirds-of-independent-agencies-plan-to-increase-ai-use-this-year)
- 65% of agents used AI for work in the past year, up from 37% in 2025. Users save about 4 hours/week (snippet) — [Agent for the Future](https://www.agentforthefuture.com/topics/technology/artificial-intelligence-for-insurance-agents/ai-adoption-in-2026/)
- 2026 Agency Universe Study (1,376 respondents): AI adoption "tripled" since 2024 (headline, snippet) — [Insurance Business](https://www.insurancebusinessmag.com/us/news/technology/independent-agency-revenue-rose-at-three-in-four-firms-as-ai-adoption-tripled-big-i-study-finds-590958.aspx); [Insurance Journal, Sep 2026](https://www.insurancejournal.com/news/national/2026/09/24/886639.htm)

**Recruiting/staffing**
- Bullhorn GRID 2025: 61% of staffing firms used AI in 2025 (up from 48%). Search-and-match agents are the top productivity tool. AI could save recruiters 4.5 hrs/week on search plus 3.6 hrs/week on screening and admin. **Only 10% have agentic AI across the full workflow**, held back by data readiness, security and unclear implementation — [Bullhorn press release](https://www.bullhorn.com/news-and-press/press-releases/bullhorn-grid-report-staffing-firms-using-ai-see-stronger-growth-faster-placements/); [GlobeNewswire, Feb 2026](https://www.globenewswire.com/news-release/2026/02/25/3244739/0/en/bullhorn-grid-report-staffing-firms-using-ai-see-stronger-growth-faster-placements.html); [StaffingHub](https://staffinghub.com/technology/ai-adoption-driving-revenue-growth-for-staffing-firms-bullhorn-grid-report/)
- Firms using AI were 2x as likely to have grown revenue and 90% more likely to place within 20 days — [Hunt Scanlon](https://huntscanlon.com/staffing-firms-using-ai-are-twice-as-likely-to-have-increased-revenue-last-year-new-bullhorn-report-reveals/)

**Mortgage brokers / financial advisers**
- UK: the average mortgage adviser completes about 9 mortgages/month but "wastes over 14 hours per week on repetitive admin, duplicated data entry, and manual case handling" (vendor source, unverified) — [AI Workforce UK](https://www.aiworkforce.co.uk/blogs/ai-tools-for-mortgage-brokers)
- AI can draft fact-finds, pull lender criteria and draft suitability letters, but "the broker must verify material information with the customer before relying on it" — [AI Workforce UK](https://www.aiworkforce.co.uk/blogs/ai-tools-for-mortgage-brokers)
- The FCA (Dec 2025) wants brokers to use AI for "better and faster advice while keeping a human touch". It may commission mortgage-specific research in 2026 — [Computer Weekly](https://www.computerweekly.com/news/366636329/Finance-regulator-wants-mortgage-brokers-to-use-artificial-intelligence); [ResultSense](https://www.resultsense.com/news/2025-12-22-fca-mortgage-ai-brokers/)
- US RIAs, Kitces 2025: about 30% of advisers use AI meeting-note tools, roughly half generic (Fathom, Fireflies) and half advisor-specific (Jump, Zocks, Finmate). The biggest driver of tech satisfaction is **integration**, not AI. A typical RIA runs 15–25 tools. "Barely a quarter of advisors want AI to automate tasks"; most want it to speed work up, not replace them — [Digital Alpha on Kitces 2025](https://www.digital-alpha.com/integration-before-ai-what-the-2025-kitces-research-really-says/); [WealthTech Today ep. 300](https://wealthtechtoday.com/2025/08/07/ep-300-what-surprised-us-in-the-2025-kitces-tech-survey-and-what-rias-still-get-wrong-with-michael-kitces/); [Kitces AdvisorTech Apr 2025](https://www.kitces.com/blog/the-latest-in-financial-advisortech-april-2025-news-wealthbox-ai-meeting-note-tool-hubly-advisor360/)

**Immigration**
- Case-management tools focus on smart questionnaires, form filling (USCIS/EOIR/DOL/DOS), client portals for document upload, and deadline tracking. These are the core repetitive workflows the software targets — [Guideflow](https://www.guideflow.com/blog/immigration-law-software); [LegistAI comparison (vendor source)](https://www.legistai.com/best-immigration-software-for-law-firms-complete-comparison-guide/)
- Docketwise's 2025 Immigration Report covers changing processing times and case outcomes amid policy changes and AI adoption — [Silicon UK](https://www.silicon.co.uk/press-release/docketwise-releases-2025-immigration-report-revealing-fluctuations-in-processing-times-case-outcomes-amid-policy-changes-and-ai-adoption)

### Inferences
- **Top 2–3 workflows per vertical**, built from the findings above. The specific step lists are my own synthesis:
  - Accounting: (a) year-end/tax document collection and chasing (request list, portal upload, OCR/classify, completeness check, re-chase loop, preparer review); (b) bank-transaction categorisation and month-end close checklists (categorise, flag low-confidence items for human review, reconcile); (c) UK: MTD quarterly-update data gathering from sole traders and landlords.
  - Small law: (a) lead intake to conflict check to engagement letter to e-sign to matter creation (branches on practice area and conflict outcome, with a lawyer approval gate); (b) client document and evidence collection for a matter; (c) status-update and follow-up chasing.
  - Insurance: (a) renewal preparation (pull expiring policy, re-collect exposure data from the client, re-market to carriers, compare quotes, producer review, proposal); (b) certificate-of-insurance and endorsement requests; (c) submission chasing and new-business data collection (ACORD form filling).
  - Recruiting: (a) inbound CV screening and shortlist (parse, score against the job spec, recruiter review, outreach); (b) candidate compliance and onboarding document collection (right-to-work, references); (c) re-engaging dormant candidates already in the ATS.
  - Mortgage/RIA: (a) fact-find, then document collection (payslips, bank statements), then affordability and criteria check, then suitability letter draft for adviser sign-off; (b) post-meeting workflow (notes to CRM tasks, follow-up email, compliance file); (c) RIA account opening and transfer paperwork, plus annual review prep.
  - Immigration: (a) eligibility questionnaire leading to a personalised evidence checklist and document chase loop; (b) form pre-population and consistency checks across forms and evidence; (c) deadline and status monitoring with client updates.
- An agent graph fits because each workflow has (i) waits on outside parties and retry loops, (ii) branching by case type, (iii) a confidence threshold that sends items to a human, and (iv) writes into several systems of record. A single chatbot turn handles none of these.
- Across verticals, "AI adoption" mostly means chat assistants and meeting notes (Big I: only 8% embedded in daily workflows; Bullhorn: only 10% fully agentic). That leaves real white space for end-to-end workflow builds.

### Gaps
- I could not fetch first-hand practitioner complaints from Reddit (r/Accounting, r/Bookkeeping, r/LawFirm, r/recruiting, r/InsuranceAgent) in the call budget. The workflow lists above come from surveys and vendor material, not forum quotes.
- No UK-specific survey found for recruiting (REC), insurance brokers (BIBA) or law firms (Law Society tech survey).
- No primary data on immigration consultancies' own pain points (UK IAA-registered advisers in particular). Only software-vendor feature lists.

---

## Q2. What do firms currently pay for automation help (consultants, VAs, offshore staff, SaaS), and what is the evidence of willingness to pay for custom builds or retainers?

### Takeaway
The clearest price anchor is offshore labour. A Philippines bookkeeper costs about **$1,800–2,200/month** (or $5–15/hr), so a custom agent workflow has to beat roughly $20–30k/year of human cost per role it replaces or supports. Agency pricing guides put professional-services automation retainers at **$1,500–3,000/month**, with builds from about $1.5k (single n8n workflow with AI) to $5–50k. Those figures come from vendor and agency blogs, not audited data.

### Cited Findings
- Offshore (Philippines) accounting staff: staff bookkeeper about $1,800–2,200/month; CPA-level accountant who owns month-end close $2,500–3,500/month. Hourly: entry $5–7, experienced $8–10, CPA-level $10–15. Through recruitment agencies, $8–14/hr, "up to 80% savings" versus US staff — [Helpware](https://helpware.com/blog/accounting-outsourcing-companies-philippines); [HireTalent.ph](https://hiretalent.ph/hiring-remote-filipino-bookkeeper); [VirtualStaff.ph](https://www.virtualstaff.ph/employer-education/virtual-assistants-accounting-and-bookkeeping)
- Bookkeeping VAs: $600–2,500/month depending on location and skills — [ddiy](https://ddiy.co/virtual-assistant-bookkeeping-accounting-cost/)
- AI automation agencies in 2026: $5k–50k per project, $2k–15k/month retainer, or $100–300/hr (vendor source) — [Lets-Viz](https://lets-viz.com/blogs/ai-automation-agency-pricing-2026-what-buyers-pay); [TheCrunch](https://thecrunch.io/ai-automation-agency-cost/)
- Professional services (law, accounting, insurance) are described as having "the highest retainer values ($1,500–$3K/mo) and longest customer lifetime (18+ months)" (vendor source) — [IdeaProof / MindStudio search results](https://ideaproof.io/guides/ai-automation-agency); [MindStudio case studies](https://www.mindstudio.ai/blog/start-ai-automation-business-case-studies)
- Typical build-and-run structure is $8,000 upfront plus $3,000/month. A rule of thumb sets the retainer at 15–25% of the setup fee per month (vendor source) — [Taskip](https://taskip.net/ai-automation-agency-pricing/); [Layer3Labs](https://www.layer3labs.io/roi/ai-automation-agency-cost)
- n8n agency pricing: single workflow $400–1,200 one-time; multi-workflow system with an AI step $1,500–4,500; retainers $1,200–8,000/month. Self-hosted n8n costs about $20/month (vendor source) — [Buldrr](https://buldrr.com/n8n-automation-agency-pricing/)
- An anecdote (originally from Reddit, reported second-hand) of an individual paid **$35k to set up a locally hosted LLM at a law firm** (unverified, second-hand) — [Nic Conley Substack](https://nicconley.substack.com/p/set-up-llms-for-businesses-and-make)
- What the systems of record cost (the SaaS spend a custom build sits alongside): Karbon $59–89/user/month annual ($79–99 monthly), so a 10-person firm pays about $590–990/month — [Assembly](https://assembly.com/blog/karbon-pricing); Clio $39 (EasyStart) to $79+ (Essentials)/user/month — [Capterra](https://www.capterra.com/p/105428/Clio/pricing); Bullhorn is quote-only, about $99–315/user/month, annual contracts typically $20k+ for small teams (third-party estimate) — [Pin](https://pin.com/blog/bullhorn-pricing); Docketwise from $69/user/month — [Guideflow](https://www.guideflow.com/blog/immigration-law-software)

### Inferences
- **Anchor framing for a pitch:** "This workflow replaces or supports 0.5–1 offshore FTE ($10–25k/yr) or 14 adviser-hours/week." A build of about $3–8k plus about $500–1,500/month is credible for a 5–20 person firm. $2k+/month retainers likely need firms of 20+ staff or a clearly measured hours saved.
- Per-user vertical SaaS costs firms only about $40–300/user/month. A custom retainer priced above the firm's whole SaaS bill will meet resistance unless ROI is shown in hours or revenue.
- Staffing firms already pay $20k+/year for Bullhorn, which suggests a higher tech budget than small law or immigration practices.

### Gaps
- No primary survey of what accounting/law/insurance firms actually spend on outside automation consultants. All agency price ranges are from agencies and SaaS marketing blogs with an incentive to inflate.
- No UK-specific (GBP) consultant or VA price data found.
- Applied Epic pricing was not found (quote-only).
- No reliable per-firm IT/tech budget figures (for example, % of revenue) for any of the six verticals.

---

## Q3. Which verticals already have dominant vertical SaaS doing this, and where are the gaps?

### Takeaway
Every vertical has an entrenched system of record: accounting (Karbon, Canopy, Financial Cents, Liscio, TaxDome), law (Clio), staffing (Bullhorn), insurance (Applied Epic and similar), immigration (Docketwise, LollyLaw, INSZoom), RIAs (CRMs plus AI note-takers Jump, Zocks, Finmate). These vendors are now shipping their own AI. The gap a freelancer can fill is **integration and cross-system orchestration around the firm's specific process**. Kitces finds integration is the #1 satisfaction driver, and Bullhorn finds only 10% of firms run agentic AI end to end.

### Cited Findings
- Accounting practice-management vendors (Karbon, Financial Cents, Liscio, Docyt, Uku) all market document-collection or AI features — [Assembly on Karbon](https://assembly.com/blog/karbon-pricing); [Liscio](https://www.liscio.me/blog-posts/how-accounting-firms-can-automate-client-document-collection); [Docyt](https://docyt.com/article/5-pain-points-ai-is-erasing-for-accounting-firms-in-2025/); [Uku](https://getuku.com/articles/ai-in-accounting-statistics/)
- Applied publicised numbers on its AI platform for independent agencies (snippet, headline only) — [Insurance Business](https://www.insurancebusinessmag.com/us/news/technology/applied-puts-numbers-on-ai-platform-for-independent-agencies-591874.aspx)
- Bullhorn: 78% of firms with 25%+ revenue growth embed AI in their ATS. Search-and-match agents lead. Only 10% are agentic across the full workflow — [Bullhorn press release](https://www.bullhorn.com/news-and-press/press-releases/bullhorn-grid-report-staffing-firms-using-ai-see-stronger-growth-faster-placements/); [StaffingHub](https://staffinghub.com/technology/ai-adoption-driving-revenue-growth-for-staffing-firms-bullhorn-grid-report/). A crowded "best AI tools for recruiting agencies" market exists — [Pin](https://www.pin.com/blog/best-ai-tools-recruiting-agencies-2026/)
- Immigration: LollyLaw (125+ forms, 40+ customisable workflows, client portal); Docketwise (case management, form automation, built-in legal AI, from $69/user/month); newer AI-native challengers such as LegistAI position against them — [Guideflow](https://www.guideflow.com/blog/immigration-law-software); [LegistAI](https://www.legistai.com/best-docketwise-alternative-immigration-software); [eImmigration](https://get.eimmigration.com/blog/best-immigration-software-for-law-firms-the-complete-comparison-guide)
- RIAs run 15–25 tools. Integration matters more than AI for satisfaction. Advisor-specific AI note-takers (Jump, Zocks, Finmate) compete with generic ones — [Digital Alpha](https://www.digital-alpha.com/integration-before-ai-what-the-2025-kitces-research-really-says/); [Kitces AdvisorTech Aug 2026](https://www.kitces.com/blog/the-latest-in-financial-advisortech-august-2026-ycharts-zephyr-hadrius-greenboard-feathery/)
- UK mortgage: adviser-focused AI tools (JammJar, Aveni, "AI for Brokers") are emerging under FCA pressure — [Cherry PLC / JammJar](https://www.cherryplc.co.uk/industry/pressreleases/details/21387); [Aveni](https://aveni.ai/blog/ai-compliance-for-mortgage-lenders-audit-trails-advice-quality-and-regulatory-evidence/); [AI for Brokers](https://aiforbrokers.co.uk/)
- UK law: LEAP and others publish guides to legal AI tools for UK solicitors — [LEAP](https://www.leaplegalsoftware.com/uk/blog/best-legal-ai-tools-for-uk-solicitors-the-complete-guide/)

### Inferences
- Crowdedness ranking, my judgement from vendor density in the search results: **staffing (very crowded)** > **accounting (crowded)** > **RIA (crowded, note-takers)** > **law (crowded at Clio level, thinner for bespoke intake)** > **insurance (incumbent-dominated, Applied/Vertafore, few nimble tools for small agencies)** > **immigration (niche, handful of vendors, UK consultancies especially under-served)**.
- Likely gaps the SaaS does not cover: (i) workflows that span the system of record plus email, portals and spreadsheets (for example insurance renewals across carrier portals); (ii) firm-specific branching, such as a law firm's own conflict and intake rules; (iii) UK-specific processes that US-built tools miss (MTD, UK right-to-work checks, UK visa routes for IAA advisers); (iv) firms too small for Bullhorn or Applied Epic pricing that live in spreadsheets.
- Risk: incumbents adding native AI agents (Bullhorn, Applied, Clio, Karbon) could make a custom build redundant within 12–24 months. Builds should sit on top of the incumbent's API rather than replace it.

### Gaps
- Did not review G2/Capterra complaints to confirm specific feature gaps in Karbon, Canopy, Clio, Bullhorn or Applied Epic.
- No market-share figures for any incumbent.

---

## Q4. Which verticals carry high vs low liability/regulatory risk for a non-coder builder?

### Takeaway
**Highest risk:** immigration (regulated advice in the UK under the IAA; US unauthorised-practice issues), law (solicitor or lawyer remains personally accountable, plus UPL concerns) and regulated financial advice (FCA Consumer Duty, SEC/FINRA). **Medium:** recruiting (AI-hiring laws such as NYC LL144, Colorado, UK GDPR automated decision-making) and insurance (licensed advice, data privacy, the top AI concern being data privacy at 24%). **Lowest:** back-office accounting and bookkeeping workflows, such as document chasing and categorisation with human review, though client financial data still triggers GDPR and data-security expectations.

### Cited Findings
- **Law (US):** ABA Formal Opinion 512 (July 2024) covers competence, confidentiality, client communication, supervision and fees for generative AI. UPL (Rule 5.5) requires vigilance — [National Law Review](https://natlawreview.com/article/american-bar-association-issues-formal-opinion-use-generative-ai-tools); [UNC Law Library](https://library.law.unc.edu/?p=2569). Background: an NCSC white paper on AI and UPL — [NCSC](https://www.ncsc.org/sites/default/files/media/document/AI_UPL_WhitePaper.pdf)
- **Law (UK):** the SRA holds the solicitor, not the tool, accountable. Firms need processes for confidential data entered into unauthorised AI tools, logging of AI use, and verification of AI-generated authorities. The SRA has added AI material to its supervision guidance — [VinciWorks](https://vinciworks.com/blog/is-sras-ai-warning-a-wake-up-call-for-uk-law-firms/); [SRA Lawtech Insight June 2025](https://publications.sra.org.uk/lawtech-insight-june-2025/in-the-news). The SRA has also authorised an AI-enabled law firm — [IBA](https://www.ibanet.org/UK-SRA-takes-unprecedented-approach-in-authorising-AI-enabled-law-firms)
- **Immigration (UK):** non-lawyer immigration advisers must be registered with and follow the Code of Standards of the Immigration Advice Authority (renamed from OISC on 16 Jan 2025). Giving immigration advice without authorisation is an offence — [LexisNexis UK](https://www.lexisnexis.com/en-gb/legal/guidance/giving-immigration-advice-in-the-uk); [DG Legal](https://dglegal.co.uk/services/immigration-advice-authority/)
- **Mortgage/financial advice (UK):** the FCA says Consumer Duty and SM&CR already cover AI-assisted advice. The adviser keeps responsibility for the final decision — [Mortgage Solutions, Dec 2025](https://www.mortgagesolutions.co.uk/mortgage-news/2025/12/15/consumer-duty-and-smcr-already-able-to-manage-ai-advice-risks-says-fca/); [Paradigm](https://www.paradigm.co.uk/blog/The-FCA-AI-vision-opportunity-for-advisers-or-a-threat-to-advice.html). Audit trails and advice-quality evidence are expected (vendor source) — [Aveni](https://aveni.ai/blog/ai-compliance-for-mortgage-lenders-audit-trails-advice-quality-and-regulatory-evidence/)
- **Recruiting:** NYC Local Law 144 (enforced since July 2023) requires annual independent bias audits, public disclosure and candidate notice for automated employment decision tools, and applies to employment agencies. Colorado's AI Act enforcement is on hold by court order but the law still stands. EU AI Act high-risk hiring rules apply from Dec 2, 2027. UK/EU focus on GDPR profiling and automated decision-making. An agency placing in NYC, CA and CO faces "three completely different sets of AI hiring rules" — [Metaview](https://www.metaview.ai/resources/blog/ai-hiring-laws-2026-2027); [Kilpatrick](https://ktslaw.com/insights/alert/2023/8/nyc-tackles-ai-and-automated-decision-making-in-employment-and-recruiting); [WashU Law](https://law.washu.edu/ai-policy-and-regulation-resources/labor-employment/)
- **Insurance:** agencies' top AI concerns are data privacy/compliance risks (24%) and inaccurate outputs (22%) — [IndependentAgent.com](https://www.independentagent.com/news/two-thirds-of-independent-agents-plan-to-increase-ai-use-this-year/)
- **Staffing:** barriers to agentic AI include data readiness and security — [Bullhorn](https://www.bullhorn.com/news-and-press/press-releases/bullhorn-grid-report-staffing-firms-using-ai-see-stronger-growth-faster-placements/)

### Inferences
- For a non-coder freelancer, the safest design rule in every vertical is that the agent **collects, extracts, checks and drafts, and a licensed human approves anything client-facing that counts as advice**. In law, immigration and financial advice this human-in-the-loop gate is effectively required by regulation. In accounting back-office work it is good practice.
- Liability ranking (high to low): immigration ≈ law > financial advice/mortgage > recruiting (screening is the risky part; document collection is low-risk) > insurance > accounting/bookkeeping (lowest).
- Expect regulated firms (law, RIA, insurance carriers' agencies) to ask about data residency, a DPA (UK/EU GDPR), access controls and possibly SOC 2. A solo builder without SOC 2 should use the client's own tenancy and accounts (their n8n/Make, their LLM API keys) to reduce exposure.

### Gaps
- No specific source found on SOC 2 expectations of small firms buying from freelancers.
- Not fetched: SEC Regulation S-P amendments (incident response and vendor oversight, with smaller-firm compliance dates around 2026), FINRA AI guidance, US state bar opinions beyond ABA 512, the AICPA/ICAEW AI ethics guidance, and US insurance-producer licensing (NAIC AI model bulletin). All likely relevant but unverified here.
- No data on professional indemnity or E&O insurance requirements for automation contractors.

---

## Q5. Are there case studies of solo builders or small agencies selling agent workflows to these firms, with prices?

### Takeaway
Reliable, verifiable case studies are scarce. Most "case studies" are from course sellers or agencies marketing themselves (MindStudio, IdeaProof, Gumroad "AI agency" courses). The best concrete data points are a second-hand $35k local-LLM setup for a law firm and generic agency price bands. Treat all of them as marketing.

### Cited Findings
- MindStudio describes AI automation businesses "from $25K to $2.7M ARR" and identifies professional services as a high-retainer niche (vendor source) — [MindStudio](https://www.mindstudio.ai/blog/start-ai-automation-business-case-studies); [MindStudio professional services](https://www.mindstudio.ai/blog/professional-services)
- A second-hand Reddit anecdote of $35k for a locally hosted LLM at a law firm — [Nic Conley Substack](https://nicconley.substack.com/p/set-up-llms-for-businesses-and-make)
- An agency comparison lists 12 AI automation agencies with pricing (vendor source) — [AY Automate](https://www.ayautomate.com/blog/best-ai-automation-agencies)
- Search results for "first client" pricing returned mostly Gumroad course listings, which is a sign of a saturated "AI automation agency" guru market rather than evidence of outcomes — [Gumroad example](https://aiagencybundle.gumroad.com/l/private-offer-price)

### Inferences
- The "AI automation agency" model is heavily promoted, so buyers may be wary of generic AAA pitches. Vertical specificity (for example "renewal-prep agent for Applied Epic agencies" or "MTD document-chase agent for UK practices") is a differentiator.
- The $1.5–3k/month retainer band for professional services matches the offshore-FTE anchor ($1.8–2.2k/month). That suggests firms will frame the purchase as replacing a VA.

### Gaps
- No independently verified case study with firm name, workflow, price and outcome for any of the six verticals.
- No UK case studies found.

---

## Q6. Comparable fields per vertical (for pairwise comparison later) and reachability

### Takeaway
On balance of pain, budget, risk and reachability, **accounting/bookkeeping (especially UK, with the MTD trigger)** and **independent insurance agencies** look like the best first-client verticals for a freelancer. Staffing has budget but is crowded. Law, immigration and financial advice have high pain but high liability.

### Cited Findings (firm size, density, reachability)
- US independent insurance agencies: about 37,000 in 2026 (down from 39,000 in 2024). Average 9.9 staff (up from 8.2). Three in four grew revenue 2024–25 — [Insurance Journal](https://www.insurancejournal.com/news/national/2026/09/24/886639.htm); [Big I Agency Universe Study](https://www.independentagent.com/agency-universe-study/). The Big "I" runs a technology resource hub and the Agents Council for Technology (ACT) — [IndependentAgent.com tech resources](https://www.independentagent.com/agency-management/technology/)
- Small law firms: Clio publishes a dedicated Solo & Small Firm report, showing a large reachable segment. Mid-sized firms are covered separately — [Clio mid-sized report](https://www.clio.com/about/press/clios-2025-legal-trends-for-mid-sized-law-firm-report/)
- Accounting: Intuit's Firm of the Future 2026 Accountant Technology Survey and the CPA.com/AICPA report show active vendor and association channels — [Firm of the Future](https://www.firmofthefuture.com/news/accountant-tech-survey-2026/); [CPA.com](https://www.cpa.com/sites/cpa/files/2025-06/2025_AI_in_Accounting_Report.pdf); [Wolters Kluwer Future Ready Accountant 2025](https://www.wolterskluwer.com/en/news/wolters-kluwer-releases-its-2025-future-ready-accountant-report)
- RIAs: Kitces publishes a monthly AdvisorTech column and an annual tech survey, a concentrated information channel — [Kitces](https://www.kitces.com/)
- UK immigration advisers are a defined registered population under the IAA — [LexisNexis UK](https://www.lexisnexis.com/en-gb/legal/guidance/giving-immigration-advice-in-the-uk)

### Comparison matrix (H/M/L ratings are my inferences based on the findings above)

| Vertical | Pain intensity | Typical firm size | Tech budget / WTP signal | Competition (SaaS crowding) | Liability risk | Reachability for freelancer | Key evidence |
|---|---|---|---|---|---|---|---|
| Accounting/bookkeeping/tax | **High**: about 7 in 10 want an agent for doc-chasing; UK MTD Apr 2026 | Mostly small practices (size data not sourced) | **M**: Karbon $59–99/user; offshore staff $1.8–3.5k/mo is the anchor | **High** (Karbon, Canopy, TaxDome, Financial Cents, Liscio) | **Low–M** (data protection; no advice risk for back-office work) | **High**: dense on LinkedIn, Reddit, associations (AICPA/ICAEW), vendor communities (not quantified) | Financial Cents, IRIS, CPA.com |
| Small law / legal ops | **High**: intake is the growth lever | Solo to about 20 lawyers | **M**: Clio $39–79+/user; 71–75% use AI but only about 31% see revenue gains | **M–High** (Clio plus intake add-ons) | **High** (ABA 512, SRA accountability, UPL, privilege) | **M**: lawyers are reachable but cautious; bar associations | Clio, NC Bar, SRA |
| Insurance agencies | **High**: renewals, COIs, submissions; only 8% have AI embedded | About 10 staff avg; 37k US agencies | **M**: 2/3 plan to increase AI; efficiency is the top motive | **M** (Applied/Vertafore incumbents; few nimble tools for small agencies) | **M** (privacy top concern; licensed advice) | **M–High**: Big I, state associations, ACT, Reddit r/InsuranceAgent | Big I 2026 studies |
| Recruiting/staffing | **High**: screening and admin about 8 hrs/wk | Small to mid agencies | **High**: Bullhorn contracts $20k+/yr; AI users grow 2x | **Very high** (Bullhorn plus many AI tools) | **M–High** for screening (NYC LL144, CO, UK GDPR ADM); low for admin | **High**: recruiters are LinkedIn-native | Bullhorn GRID 2025, Metaview |
| Mortgage brokers / RIAs | **High** (UK brokers about 14 hrs/wk admin, vendor claim) | Small adviser firms; RIAs run 15–25 tools | **M**: note-takers adopted by about 30%; integration valued | **M–High** (Jump, Zocks, Finmate; UK JammJar, Aveni) | **High** (FCA Consumer Duty/SM&CR; SEC) | **M**: Kitces community; UK broker networks (not sourced) | Kitces, FCA via Mortgage Solutions |
| Immigration consultancies | **High** (evidence collection and forms), weakly evidenced | Small practices | **L–M**: Docketwise from $69/user | **L–M** (Docketwise, LollyLaw, INSZoom, LegistAI; UK thinner) | **Very high** (IAA regulated advice; UPL) | **L–M**: niche; IAA register is a defined list | Guideflow, LexisNexis UK |

### Inferences
- **Best first-client candidates:** (1) small accounting/bookkeeping practices, with the document-chase plus categorisation agent; low liability, many firms, obvious offshore-staff anchor; the UK MTD deadline adds urgency. (2) Independent insurance agencies, with a renewal-prep plus COI agent; strong stated intent (2/3 increasing AI), low current embedding (8%), average about 10 staff, a reachable association network. (3) Recruiting, but only for admin and onboarding workflows rather than screening decisions, to avoid AEDT law exposure.
- **Avoid as a first client without legal partnership:** immigration and regulated financial advice. Law is viable only for intake and admin workflows with lawyer sign-off.

### Gaps
- LinkedIn density, membership counts (AICPA, ICAEW, Law Society, REC, BIBA, Big I, IAA register size) and UK firm counts were not gathered. Reachability ratings are judgement-based.
- No sourced typical revenue or tech-spend-as-%-of-revenue per vertical.
- Older data flag: NYC LL144 analysis dates from 2023 and ABA 512 from 2024. Both are still in force as of the sources, but check for 2026 amendments.
