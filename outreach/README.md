# Outreach kit — Report Desk

Two things: the email you send, and the prompt that finds who to send it to.

Read the **Before you send** section at the bottom before the first send. It is short
and it keeps you legal.

---

## 1. The email

Cold email averages about a **3.4% reply rate**. The things that move it are: it is
short, it is visibly about *them*, it asks for something small, and it looks like a
person typed it. Everything below is built for that.

**Rules that matter more than the wording**

- **Plain text only.** No logo, no banner, no HTML template, no attachment. Images and
  heavy HTML hurt deliverability and make it read as a campaign.
- **Under 130 words.** It must be readable on a phone without scrolling.
- **One link, one ask.** A second link halves the odds of either being clicked.
- **One researched line.** Not "I loved your website" — a specific, checkable fact. This
  is the whole difference between a 1% and a 10% reply rate.
- **Send from a real human address** (`you@yourdomain.com`), never `info@` or `hello@`.
- **No tracking pixels.** They trip spam filters and tell you less than replies do.

### Email 1 — the opener

> **Subject:** your September client reports
>
> Hi {{first_name}},
>
> {{one specific researched line — see the hook list below}}
>
> Most agencies around your size lose two to three days a month to client reporting:
> pulling the numbers, writing the commentary, checking it before it goes out.
>
> I've built something that does the first draft. It works from the GA4, Google Ads,
> Search Console and Meta exports you already download (no access to your accounts),
> writes each client's report in your agency's voice, and checks every figure in every
> sentence against the data before anyone sees it. Nothing reaches a client until
> someone on your team approves it, and the report goes out under your name.
>
> Ninety seconds of it running a month for twelve clients: {{video_link}}
>
> If it looks useful, I'll run it on three of your clients for one reporting cycle for
> {{price}}, invoiced after you've seen the drafts.
>
> Worth a look?
>
> {{your name}}
> {{phone}} · {{your site}}

### Email 2 — four working days later

> **Subject:** re: your September client reports
>
> Hi {{first_name}},
>
> Probably caught you mid-month.
>
> The part people actually react to is the self-check: it caught its own wrong figure
> and corrected it before anyone saw it. That is the clip, if nothing else:
> {{video_link}}
>
> If reporting isn't a pain for you, say so and I'll stop.
>
> {{your name}}

### Email 3 — seven days after that, then stop

> **Subject:** closing the loop
>
> Hi {{first_name}},
>
> I'll leave it here — I don't want to be another unread follow-up.
>
> If client reporting ever becomes the bottleneck, the offer stands: three of your
> clients for one reporting cycle, {{price}}, invoiced after you've seen the drafts.
>
> All the best,
> {{your name}}

**{{price}}:** £500 for UK agencies, $650 for US agencies. Don't quote the rollout price
(£2,000 setup + £400/month) in cold email; that conversation happens after the pilot.
Never promise refunds, results or savings figures you can't prove.

**Three emails, then stop.** More than that damages your domain and your name.

### The researched line — pick one, never invent

This is the only part that takes real work. One true, checkable sentence:

| Hook | Example line |
|---|---|
| A named client in a reporting-heavy sector | "You've got {{client}} and {{client}} on retainer — that's a lot of monthly reporting for a team of {{n}}." |
| A recent hire | "Saw you're hiring an account manager — reporting load usually sits with that seat." |
| Their own words | "Your site says you report monthly on 'what it means, not just what happened' — that's the part the agent drafts." |
| A service page | "You run SEO and paid for the same clients, so every report is two data pulls before anyone writes a word." |
| A post of theirs | "Your post about month-end being the worst week is exactly what this is for." |

**If you cannot find a true hook for a prospect, drop them from the list.** A generic
opener is worse than no email — it marks you as a bulk sender.

### What never goes in

- "I hope this email finds you well."
- "I'm a third-year engineering student." (Not a lie — just not the opener. Lead with
  the work. If they ask, tell them straight away.)
- "AI-powered", "revolutionary", "game-changing", "leverage", "synergy".
- Anything claiming you already know their numbers when you don't.
- Any figure you cannot evidence. The film's "41 figures checked, 6 corrected" is real
  eval output — keep it that way.

---

## 2. The prompt for your research agent

Paste the block below into your coding/research agent. It is written to make the agent
**refuse to guess**. The hard part of lead research is not finding companies, it is not
inventing data — so most of the prompt is about evidence and disqualification.

Expect it to return far fewer rows than you asked for. **That is the prompt working.**
30 verified agencies beat 300 guesses, because every bad row costs you a bounce, and
bounces wreck your domain reputation.

```text
ROLE
You are a B2B lead researcher. Your output is used for cold email, so a single
fabricated field causes real damage: a bounce, a wasted send, or a legal problem.
Accuracy is the only thing being measured. A short, fully-evidenced list is a success.
A long list with guesses is a failure.

GOAL
Find marketing, SEO, and digital agencies in the UK and the US that are good candidates
for an AI tool that drafts and fact-checks their monthly client reports.

TARGET (all must be true)
1. It is an agency that does marketing, SEO, paid media, or content for OTHER
   businesses as clients on an ongoing basis.
2. Headcount is between 5 and 50 people.
3. It is based in the UK or the US.
4. It has clients on retainer, or otherwise does recurring work (evidence: a "clients"
   or "case studies" page, retainer or monthly language, a client logo wall).
5. English-language site.

DISQUALIFY (any one of these removes them — record them in the rejects file)
- Fewer than 5 or more than 50 people, or headcount you cannot evidence.
- A freelancer or a one-person studio trading as an agency.
- A pure web-design, branding, PR, or video production shop with no reporting on
  performance data.
- An agency that already sells AI reporting or automated client dashboards as its own
  product (they are a competitor, not a buyer).
- No named human you could address. A generic info@ only is a disqualification.
- UK ONLY: the business is a sole trader or an unincorporated partnership rather than a
  limited company or LLP. This matters legally, so verify the entity type on Companies
  House and record the company number. If you cannot confirm it is a Ltd or an LLP,
  disqualify.
- Any site that is parked, dead, or last updated more than 2 years ago.

EVIDENCE RULES — these are absolute
- Every field you output must have a source_url you actually opened, plus a short
  verbatim quote from that page proving the value. No quote, no field.
- NEVER construct an email address from a pattern. Do not output
  first.last@domain because that pattern appears elsewhere. An email is acceptable ONLY
  if it is published on a page you opened, and you quote the text around it.
  If there is no published personal address, set email to null and set
  email_status to "none_found". Leave the row in — I would rather contact them on
  LinkedIn than email a guess.
- NEVER infer headcount from "we're a big team" or from an About page photo. Acceptable
  evidence is: a LinkedIn company page employee count, a Companies House filing, or a
  team page where you counted the named people (say which, and give the number counted).
- If two sources disagree, record both and set confidence to "low".
- If you cannot verify a mandatory field after a genuine attempt, DISQUALIFY the row.
  Do not fill the gap with your best estimate.
- Do not use your training knowledge as a source. If it is not on a page you opened in
  this run, it does not exist.

PERSONALISATION HOOK — mandatory, and the hardest field
For each qualified agency, find ONE specific, checkable fact that could open an email
to them. It must be something true of THEM and not of every agency. Good: a named
client in a reporting-heavy sector; a current job opening; a distinctive line from
their own site about how they report; a recent post about workload or month-end.
Bad: "great website", "impressive portfolio", "I see you do SEO".
Write it as one sentence I could paste into an email, and give the source_url.
If you cannot find a real hook, set hook to null and confidence to "low" — do not
invent one.

OUTPUT
Write two files.

(a) leads.csv — one row per QUALIFIED agency, with these columns:
    agency_name, website, country, city,
    headcount, headcount_evidence, headcount_source_url,
    entity_type, companies_house_number,     # UK only; leave blank for US
    contact_name, contact_role, contact_source_url,
    email, email_status,                     # published | none_found
    linkedin_url,
    client_examples,                          # 2-3 named clients if public
    hook, hook_source_url,
    confidence,                               # high | medium | low
    notes

(b) rejects.csv — every agency you looked at and dropped, with:
    agency_name, website, reason_rejected, source_url
    This file matters as much as the first one. It is how I check your judgement.

METHOD
Work in small batches. Fully verify each agency before moving to the next — do not
collect 100 names and then try to enrich them. After every 10 qualified rows, stop and
print a one-line progress note.

Deduplicate on registered domain (treat example.com and www.example.com as one).

HOW I WILL CHECK YOU
I will pick 5 rows at random and open every source_url. If any quote does not appear on
that page, or any email was pattern-generated, I will discard the entire output. Build
accordingly.

START
Produce 25 qualified agencies. If you can only verify 11, return 11 and tell me what
blocked the rest. Do not pad the list.
```

### After the agent returns — your own check, 10 minutes

1. Open 5 random `source_url`s and confirm the quotes are really there.
2. Run every email through a verifier (ZeroBounce, NeverBounce, Million Verifier — all
   have free credits). **Delete anything not "valid".** Bounces above ~2% damage your
   domain.
3. Read the 5 best hooks aloud. If one could be sent to any agency, rewrite or drop it.
4. UK rows: confirm the Companies House number resolves to a Ltd or LLP.

---

## 3. Before you send

**Warm the domain first.** A brand-new domain sending 50 cold emails on day one goes
straight to spam. Send 5–10 a day for the first two weeks, mostly to people who reply.
Use a separate domain from your main one if you have one (e.g. `getreportdesk.com`),
so a reputation problem never touches your primary address.

**UK recipients.** Under PECR you may email a limited company or an LLP without prior
consent, which is why the prompt verifies entity type. Sole traders and unincorporated
partnerships count as individuals and need consent — the prompt disqualifies them for
this reason. UK GDPR still applies to a named person's work address: you need a
legitimate-interest basis, you must identify yourself, and you must honour an objection
immediately.

**US recipients.** CAN-SPAM permits cold B2B email, but every message must have accurate
headers and a non-deceptive subject, a clear way to opt out that you honour promptly,
and **a valid physical postal address**. Penalties run to tens of thousands of dollars
per email, so the footer is not optional.

**So every email needs a footer like:**

> {{Your name}} · {{your street address, city, postcode, country}}
> Don't want to hear from me again? Reply "no thanks" and I'll remove you.

A reply-based opt-out is acceptable and looks human — but you must actually keep a
suppression list and honour it, immediately and permanently.

*This is a practical summary, not legal advice. If you scale past a few hundred sends,
get it checked.*
