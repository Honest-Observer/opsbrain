# DEMO_VIDEO_SCRIPT.md

Target runtime: 3:30–4:00. Screen-record at 1080p+, cursor highlighting on. Voiceover script
below; timestamps are targets, not hard cuts.

---

**[0:00–0:20] Open on Dashboard**
*(On screen: Dashboard, ingestion stats visible, top risky assets P-101 and B-12 visible)*

> "This is OpsBrain — an Asset & Operations Brain built for Problem Statement 8. It's already
> ingested twenty-six real-shaped industrial documents: SOPs, OEM manuals, work orders,
> inspection reports, incident logs, an asset registry, and a regulatory checklist. No fake
> demo — this corpus tells one coherent operational story."

**[0:20–1:20] Copilot**
*(Click seeded prompt: "Why is Pump P-101 repeatedly failing?")*

> "Let's ask it the hard question. Notice this isn't a generic chatbot response — every claim
> here is backed by a citation to a real document. Confidence score, eighty-seven percent.
> Here's the incident report, the work order, the SOP it references. And it doesn't just
> diagnose — it recommends a specific fix: a cartridge seal upgrade and a minimum-flow
> interlock, because every recorded failure happened during low-flow operation."
*(Expand "Why this answer" panel briefly)*
> "And if you want to see exactly what evidence it reasoned over, it's right here."

**[1:20–2:10] Asset 360**
*(Click through to P-101 Asset 360)*

> "Clicking into the asset itself, we get the full picture: the maintenance timeline shows the
> actual failure sequence — three seal-failure work orders, a near-miss, then the incident that
> finally got attention, followed by the preventive fix. Recurring issues, similar past
> incidents, and recommended actions, all in one view."

**[2:10–2:50] Graph Explorer**
*(Open Graph Explorer centered on P-101, click a couple of nodes)*

> "This is the actual knowledge graph behind everything you just saw — not a static diagram, a
> real, clickable graph of assets, documents, work orders, incidents, and regulations. Clicking
> a node shows exactly what it connects to."

**[2:50–3:20] Compliance Board**
*(Open Compliance Board, highlight the B-12 gap)*

> "Switching assets — Boiler B-12 has a real compliance gap. The annual relief-valve
> certification is missing for this year, flagged high severity, with the exact corrective
> action and an exportable evidence pack an auditor could use immediately."

**[3:20–3:45] Lessons Learned + Evaluation**
*(Quick cut: Lessons Learned feed, then Evaluation page)*

> "The system is also proactive — it flagged that this incident resembles an earlier near-miss
> before it repeated. And this isn't a fake UI: retrieval hit rate zero-point-eight-seven-five,
> full citation coverage, full entity linkage coverage, measured against twenty-four benchmark
> questions."

**[3:45–4:00] Close**
*(Back to Dashboard)*

> "One system, one flow, one story: upload plant knowledge, build the graph, answer clearly,
> recommend action, and prove compliance and lessons learned — end to end. This is OpsBrain."

---

## Recording notes
- Pre-seed the corpus before recording so the Dashboard opens with data already populated —
  don't record the seeding action itself, it's not visually interesting.
- Keep both terminal windows (backend/frontend logs) off-screen unless asked; this is a product
  demo, not a dev walkthrough.
- If a take needs a restart, re-seeding is safe — all IDs are deterministic, so the demo state
  is reproducible across takes.
