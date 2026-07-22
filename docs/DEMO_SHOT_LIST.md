# DEMO_SHOT_LIST.md

## Screenshots to capture for the deck

1. **Dashboard** — full view showing ingestion stats, top risky assets (P-101, B-12 visible),
   recent alerts, and quick demo-query links.
2. **Copilot — question input** — the seeded quick-prompt list visible, cursor about to click
   "Why is Pump P-101 repeatedly failing?"
3. **Copilot — answer card** — full answer with confidence meter (0.87), citations (IR-07,
   WO-1042, SOP-CENT-PUMP-01, IR-11), recommended actions.
4. **Copilot — "Why this answer" panel expanded** — showing retrieved evidence/reasoning trace.
5. **Asset 360 — P-101** — full page: summary, maintenance timeline (WO-1041→1052→1067→IR-03→
   IR-07→WO-1089), recurring issues, similar incidents, recommended actions.
6. **Graph Explorer — centered on P-101** — showing the asset node with linked documents,
   work orders, and incidents visibly connected.
7. **Graph Explorer — node inspector open** — clicked on the IR-07 incident node, showing its
   linked SOP/regulation.
8. **Compliance Board — B-12 gap** — the relief-valve certificate gap, severity "high",
   corrective action text visible.
9. **Lessons Learned feed** — the IR-07/IR-03 similarity warning card.
10. **Evaluation page** — stat cards for retrieval hit rate, citation coverage, entity linkage
    coverage, average latency, plus the benchmark question list.
11. **Architecture diagram** — rendered from `ARCHITECTURE_DIAGRAM.mmd`.

## Exact app pages/order to record for the demo video

Matches `DEMO_VIDEO_SCRIPT.md` exactly:

1. `/dashboard`
2. `/copilot` → ask "Why is Pump P-101 repeatedly failing?" → expand "Why this answer"
3. `/assets/{P-101 asset id}` (Asset 360)
4. `/graph` centered on P-101 → click the IR-07 node
5. `/compliance` → scroll to / highlight the B-12 gap
6. `/lessons`
7. `/evaluation`
8. back to `/dashboard` for the closing shot

Pre-seed the corpus (`POST /api/ingestion/seed`) before recording — do not record the seed action
itself.
