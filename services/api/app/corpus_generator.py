"""Synthetic industrial corpus generator.

Generates an internally-consistent demo corpus into `data/sample_corpus/`:
the same asset tags, work order numbers, incident codes, and regulation
codes are cross-referenced across many files, so retrieval + citations in
the demo are grounded in a real, coherent story rather than disconnected
placeholder text.

Central story (per MASTER_SPEC §11 demo flow):
- Pump P-101 suffers *repeated* mechanical seal failures (WO-1041, WO-1052,
  WO-1067) culminating in incident IR-07 (coolant leak), with an earlier
  near-miss IR-03 foreshadowing it, and a preventive fix WO-1089 afterward.
- Boiler B-12 has a real compliance gap: no on-file evidence of the annual
  relief valve (V-045) set-pressure test required by REG-052 / REG-014.

Running `generate_corpus(output_dir)` is idempotent: it clears and rewrites
the target directory so re-running the demo seed script is always safe.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Controlled vocabulary — shared across corpus generation AND used as the
# ground truth people list for entity extraction (see ingestion.py).
# --------------------------------------------------------------------------

PEOPLE = [
    "Raj Patel",       # Mechanical Technician
    "Maria Chen",      # Shift Supervisor
    "Tom Okafor",      # Inspector
    "Priya Nair",      # Safety Officer
    "Sam Reyes",       # Maintenance Lead
    "Amit Sharma",     # Plant Engineer
    "Linda Osei",      # Compliance Auditor
]

ASSETS = [
    dict(tag="P-101", name="Centrifugal Pump P-101", asset_type="pump",
         criticality="high", location="Unit 3 - Cooling Water Loop"),
    dict(tag="P-102", name="Centrifugal Pump P-102 (Standby)", asset_type="pump",
         criticality="medium", location="Unit 3 - Cooling Water Loop"),
    dict(tag="B-12", name="Package Boiler B-12", asset_type="boiler",
         criticality="critical", location="Boiler House"),
    dict(tag="C-201", name="Reciprocating Compressor C-201", asset_type="compressor",
         criticality="high", location="Utility Block"),
    dict(tag="V-045", name="Pressure Relief Valve V-045", asset_type="valve",
         criticality="medium", location="Boiler House"),
    dict(tag="T-300", name="Condensate Storage Tank T-300", asset_type="tank",
         criticality="low", location="Utility Yard"),
]

REGULATIONS = [
    dict(code="REG-014", title="Boiler Pressure Vessel Inspection Code",
         description="Annual inspection and certification requirements for fired pressure vessels."),
    dict(code="REG-022", title="Rotating Equipment Seal Integrity Standard",
         description="Mechanical seal inspection, replacement, and failure-reporting requirements for rotating equipment."),
    dict(code="REG-031", title="PPE Compliance Directive",
         description="Minimum personal protective equipment requirements for maintenance and inspection work."),
    dict(code="OSHA-105", title="Lockout/Tagout Standard",
         description="Control of hazardous energy during maintenance and servicing of equipment."),
    dict(code="REG-045", title="Emergency Shutdown System Testing",
         description="Periodic functional testing requirements for emergency shutdown (ESD) systems."),
    dict(code="REG-052", title="Relief Valve Testing Frequency",
         description="Minimum bench-test frequency and evidence retention for pressure relief valves."),
]

# work orders: (wo_number, asset_tag, failure_mode, status, opened, closed, description)
WORK_ORDERS = [
    dict(wo_number="WO-1041", asset_tag="P-101", failure_mode="mechanical seal failure",
         status="closed", opened_at="2025-02-10", closed_at="2025-02-12",
         description=(
             "Pump P-101 reported excessive leakage at the mechanical seal during routine "
             "rounds. Technician Raj Patel isolated the pump per OSHA-105 lockout/tagout, "
             "removed the seal assembly, and found the seal faces scored and worn well "
             "before expected service life. Root cause suspected: misalignment inducing "
             "shaft runout. Seal replaced with OEM spec part; pump realigned and returned "
             "to service. See REG-022 for seal integrity reporting requirements."
         )),
    dict(wo_number="WO-1052", asset_tag="P-101", failure_mode="mechanical seal failure",
         status="closed", opened_at="2025-05-18", closed_at="2025-05-20",
         description=(
             "Second mechanical seal failure on Pump P-101 in three months. Raj Patel "
             "noted the same wear pattern as WO-1041 (scored seal faces, evidence of "
             "shaft runout). Alignment checked and found within tolerance this time, so "
             "root cause remains open. Seal replaced again. Flagged to Sam Reyes "
             "(Maintenance Lead) as a recurring failure pattern requiring root-cause "
             "investigation, not just repeat repair."
         )),
    dict(wo_number="WO-1067", asset_tag="P-101", failure_mode="mechanical seal failure",
         status="closed", opened_at="2025-08-18", closed_at="2025-08-22",
         description=(
             "Third seal failure on Pump P-101, this time accompanied by bearing wear and "
             "a visible coolant leak at the seal housing (see Incident IR-07 for the "
             "associated incident report). Amit Sharma (Plant Engineer) requested vibration "
             "analysis; results showed elevated vibration consistent with cavitation, "
             "suggesting the pump may be operating away from its best efficiency point. "
             "Seal and bearings replaced. Recommend reviewing suction conditions and duty "
             "cycle per the OEM manual before the next failure."
         )),
    dict(wo_number="WO-1089", asset_tag="P-101", failure_mode="preventive seal upgrade",
         status="closed", opened_at="2025-10-01", closed_at="2025-10-05",
         description=(
             "Preventive action following the repeated seal failures on Pump P-101 "
             "(WO-1041, WO-1052, WO-1067, Incident IR-07). Upgraded to an OEM-recommended "
             "cartridge-style mechanical seal with improved tolerance to minor "
             "misalignment and cavitation-induced vibration. Sam Reyes signed off on the "
             "upgrade as the corrective action closing out the recurring seal failure "
             "pattern on P-101."
         )),
    dict(wo_number="WO-1102", asset_tag="B-12", failure_mode="relief valve inspection followup",
         status="open", opened_at="2025-11-01", closed_at=None,
         description=(
             "Follow-up work order opened after Inspector Tom Okafor could not locate a "
             "current bench-test certificate for Relief Valve V-045 on Boiler B-12 during "
             "the Q4 inspection round (see inspection_b12_relief_valve_2025q4). Required by "
             "REG-052 (Relief Valve Testing Frequency) and REG-014 (Boiler Pressure Vessel "
             "Inspection Code). Awaiting scheduling of bench test with certified vendor."
         )),
    dict(wo_number="WO-1115", asset_tag="C-201", failure_mode="valve plate wear",
         status="closed", opened_at="2025-09-10", closed_at="2025-09-12",
         description=(
             "Compressor C-201 showed reduced discharge pressure and audible knocking. "
             "Raj Patel inspected the valve plates and found wear consistent with normal "
             "service life; plates replaced and unit returned to service. No relation to "
             "the P-101 seal failure pattern."
         )),
    dict(wo_number="WO-1130", asset_tag="V-045", failure_mode="set-pressure drift",
         status="closed", opened_at="2025-06-28", closed_at="2025-06-30",
         description=(
             "Routine check found Relief Valve V-045 (Boiler B-12) set pressure had "
             "drifted slightly outside tolerance. Valve removed, bench tested, reset, and "
             "reinstalled by an outside certified vendor. Certificate filed at the time; "
             "this is the last on-file certificate referenced in the Q4 inspection gap "
             "(WO-1102)."
         )),
    dict(wo_number="WO-1144", asset_tag="P-102", failure_mode=None,
         status="closed", opened_at="2025-11-08", closed_at="2025-11-10",
         description=(
             "Routine scheduled lubrication and bearing check on standby Pump P-102. No "
             "abnormalities found. Pump remains available as backup for P-101."
         )),
]

INCIDENTS = [
    dict(incident_code="IR-03", asset_tag="P-101", severity="low",
         occurred_at="2025-04-02", regulation_codes=["REG-022"],
         title="Near-miss: seal weep observed on Pump P-101",
         summary=(
             "During a routine shift round, Shift Supervisor Maria Chen observed a small "
             "amount of weeping at the P-101 mechanical seal, well before any alarm "
             "threshold. No injury, no environmental release. Logged as a near-miss and "
             "flagged for maintenance follow-up. In hindsight this was an early warning "
             "sign of the seal failure pattern that recurred in WO-1041 and WO-1052, and "
             "culminated in the more serious Incident IR-07 four months later."
         )),
    dict(incident_code="IR-07", asset_tag="P-101", severity="high",
         occurred_at="2025-08-20", regulation_codes=["REG-022"],
         title="Coolant leak from Pump P-101 mechanical seal failure",
         summary=(
             "Pump P-101 experienced a mechanical seal failure resulting in a visible "
             "coolant leak onto the unit floor. Priya Nair (Safety Officer) confirmed no "
             "injuries; the area was cordoned off and cleaned up per spill procedure. This "
             "is the third seal failure on P-101 within seven months, following WO-1041 "
             "and WO-1052, and directly preceded the corrective work order WO-1067. An "
             "earlier near-miss (IR-03) had already flagged seal weeping on this pump. "
             "Root cause investigation pointed to cavitation-induced vibration; see the "
             "P-101 OEM manual guidance on suction conditions. Reported per REG-022 "
             "(Rotating Equipment Seal Integrity Standard)."
         )),
    dict(incident_code="IR-09", asset_tag="B-12", severity="medium",
         occurred_at="2025-10-15", regulation_codes=["REG-045", "REG-052"],
         title="Pressure excursion near-miss on Boiler B-12",
         summary=(
             "Boiler B-12 briefly exceeded normal operating pressure during a load swing "
             "before the control system corrected it; Relief Valve V-045 did not need to "
             "lift. Amit Sharma flagged this as a reason to prioritize closing the "
             "outstanding relief valve test evidence gap (see WO-1102 and the Q4 "
             "inspection report) given REG-045 emergency shutdown testing expectations."
         )),
]

INSPECTIONS = [
    dict(asset_tag="B-12", inspector="Tom Okafor",
         checklist_item="Annual relief valve (V-045) bench-test certificate on file",
         result="not_recorded", inspected_at="2025-11-01",
         filename="inspection_b12_relief_valve_2025q4.txt",
         doc_title="Q4 2025 Inspection Report - Boiler B-12",
         body=(
             "Inspection Report\n"
             "Asset: Boiler B-12 (Package Boiler)\n"
             "Inspector: Tom Okafor\n"
             "Date: 2025-11-01\n\n"
             "Checklist item: Annual relief valve (V-045) bench-test certificate on file.\n"
             "Result: NOT RECORDED. No certificate for calendar year 2025 could be located "
             "in the maintenance file. The most recent certificate on file corresponds to "
             "WO-1130 (2025-06-30), which is a set-pressure drift correction, not the "
             "required annual test. Per REG-052 (Relief Valve Testing Frequency) and "
             "REG-014 (Boiler Pressure Vessel Inspection Code), this is a compliance gap.\n\n"
             "Recommendation: Open a follow-up work order to schedule and document a "
             "current bench test before the next boiler inspection window, and retain the "
             "vendor certificate on file. Follow-up work order WO-1102 opened same day.\n\n"
             "Additional checklist items (pass): pressure gauge calibration current, "
             "burner management system tested, low-water cutoff tested.\n"
         )),
    dict(asset_tag="P-101", inspector="Tom Okafor",
         checklist_item="Seal and vibration condition check",
         result="pass", inspected_at="2025-09-01",
         filename="inspection_p101_seal_vibration_2025q3.txt",
         doc_title="Q3 2025 Inspection Report - Pump P-101",
         body=(
             "Inspection Report\n"
             "Asset: Centrifugal Pump P-101\n"
             "Inspector: Tom Okafor\n"
             "Date: 2025-09-01\n\n"
             "Checklist item: Seal and vibration condition check following seal "
             "replacement under WO-1067.\n"
             "Result: PASS. New seal and bearings installed under WO-1067 show normal "
             "vibration signature (baseline re-established). No visible leakage at time "
             "of inspection. Noted continued monitoring recommended given the recurring "
             "seal failure history (WO-1041, WO-1052, WO-1067, Incident IR-07).\n"
         )),
    dict(asset_tag="C-201", inspector="Tom Okafor",
         checklist_item="General condition and valve plate check",
         result="pass", inspected_at="2025-11-20",
         filename="inspection_c201_2025q4.scan.txt",
         doc_title="Q4 2025 Inspection Report - Compressor C-201 (scanned form)",
         body=(
             "[SIMULATED SCANNED FORM - OCR TRANSCRIPT]\n"
             "FORM: QUARTERLY EQUIPMENT INSPECTION\n"
             "ASSET TAG: C-201\n"
             "INSPECTOR (signature): Tom Okafor\n"
             "DATE: 2025-11-20\n"
             "CHECKLIST ITEM: General condition and valve plate check\n"
             "RESULT: PASS\n"
             "NOTES: Valve plates replaced under WO-1115 in September holding up well. "
             "No abnormal noise or vibration observed. No action required.\n"
         )),
]

HANDOVER_NOTES = [
    dict(filename="handover_2025_11_02.txt",
         doc_title="Shift Handover Note - 2025-11-02 Night Shift",
         from_person="Maria Chen", to_person="Amit Sharma", date="2025-11-02",
         body=(
             "From: Maria Chen (Night Shift Supervisor)\n"
             "To: Amit Sharma (Day Shift Plant Engineer)\n"
             "Date: 2025-11-02\n"
             "Subject: Shift handover - Unit 3 / Boiler House\n\n"
             "Hi Amit,\n\n"
             "Quiet night overall. Two items to track:\n"
             "1) Pump P-101 sounded slightly rougher than usual around 02:00 but vibration "
             "readings were within limits. Given the seal failure history on this pump "
             "(WO-1041, WO-1052, WO-1067, IR-07), Raj Patel will keep an eye on it this "
             "week rather than wait for the next scheduled round.\n"
             "2) Reminder that WO-1102 (Boiler B-12 relief valve V-045 test certificate) "
             "is still open - Tom Okafor flagged it during the Q4 inspection and it "
             "shouldn't slip past the next inspection window.\n\n"
             "- Maria\n"
         )),
    dict(filename="handover_2025_11_15.txt",
         doc_title="Shift Handover Note - 2025-11-15 Day Shift",
         from_person="Amit Sharma", to_person="Maria Chen", date="2025-11-15",
         body=(
             "From: Amit Sharma (Plant Engineer)\n"
             "To: Maria Chen (Shift Supervisor)\n"
             "Date: 2025-11-15\n"
             "Subject: Shift handover - follow-ups\n\n"
             "Maria,\n\n"
             "Sam Reyes confirmed the P-101 cartridge seal upgrade from WO-1089 is holding "
             "up well one month in - no signs of the recurring failure pattern so far. "
             "Please keep logging vibration spot-checks anyway.\n\n"
             "Still no update on the B-12 relief valve V-045 certificate (WO-1102). Priya "
             "Nair asked that we prioritize this given it's a hard compliance item under "
             "REG-052 / REG-014.\n\n"
             "- Amit\n"
         )),
    dict(filename="handover_2025_12_01.txt",
         doc_title="Shift Handover Note - 2025-12-01 Night Shift",
         from_person="Maria Chen", to_person="Amit Sharma", date="2025-12-01",
         body=(
             "From: Maria Chen (Night Shift Supervisor)\n"
             "To: Amit Sharma (Day Shift Plant Engineer)\n"
             "Date: 2025-12-01\n"
             "Subject: Shift handover - month-end notes\n\n"
             "Amit,\n\n"
             "Compressor C-201 running fine since the valve plate replacement (WO-1115). "
             "Tank T-300 levels normal.\n\n"
             "Linda Osei (Compliance Auditor) is doing a walkthrough next week and will "
             "likely ask about the outstanding B-12 relief valve evidence gap (WO-1102) - "
             "worth having Tom Okafor's Q4 inspection report on hand.\n\n"
             "- Maria\n"
         )),
]

COMPLIANCE_GAP = dict(
    asset_tag="B-12",
    checklist_item="Annual relief valve (V-045) bench-test certificate on file",
    regulation_code="REG-052",
    status="gap",
    severity="high",
    missing_evidence=(
        "No calendar-year 2025 bench-test certificate on file for Relief Valve V-045. "
        "Most recent certificate on file is from WO-1130 (2025-06-30, a set-pressure "
        "drift correction, not the required annual test)."
    ),
    corrective_action=(
        "Schedule a certified vendor bench test for Relief Valve V-045 and file the "
        "resulting certificate before the next boiler inspection window (tracked under "
        "WO-1102)."
    ),
)


def _sop_files() -> list[dict]:
    return [
        dict(filename="sop_pump_seal_replacement.md", doc_type="sop",
             title="SOP - Centrifugal Pump Mechanical Seal Replacement",
             body=(
                 "# SOP: Centrifugal Pump Mechanical Seal Replacement\n\n"
                 "Applies to: Centrifugal Pumps (e.g. P-101, P-102).\n\n"
                 "## 1. Safety preparation\n"
                 "Isolate and lock out the pump per OSHA-105 (Lockout/Tagout Standard) "
                 "before beginning work. Priya Nair (Safety Officer) must sign off on "
                 "isolation for any pump with a criticality of high or above.\n\n"
                 "## 2. Procedure\n"
                 "1. Drain and depressurize the casing.\n"
                 "2. Remove coupling guard and disconnect coupling.\n"
                 "3. Withdraw seal assembly; inspect seal faces for scoring, chipping, or "
                 "uneven wear (a common early indicator of misalignment or cavitation - "
                 "see Pump P-101's repeated failure history under WO-1041, WO-1052, and "
                 "WO-1067 for a worked example of what NOT catching this looks like).\n"
                 "4. Check shaft runout and alignment before installing the new seal.\n"
                 "5. Install OEM-spec replacement seal (or approved cartridge-style "
                 "upgrade, see WO-1089).\n"
                 "6. Reassemble, re-align, and perform a controlled startup with vibration "
                 "monitoring.\n\n"
                 "## 3. Reporting\n"
                 "Log the work order under the affected asset tag and report per REG-022 "
                 "(Rotating Equipment Seal Integrity Standard). Repeat failures within 6 "
                 "months on the same asset must be escalated to the Maintenance Lead "
                 "(Sam Reyes) for root-cause investigation rather than closed as routine "
                 "repairs.\n"
             )),
        dict(filename="sop_boiler_startup_shutdown.md", doc_type="sop",
             title="SOP - Package Boiler Startup and Shutdown",
             body=(
                 "# SOP: Package Boiler Startup and Shutdown\n\n"
                 "Applies to: Package Boilers (e.g. B-12).\n\n"
                 "## 1. Pre-startup checks\n"
                 "Confirm low-water cutoff test current, burner management system test "
                 "current, and relief valve (e.g. V-045) bench-test certificate on file "
                 "and within the frequency required by REG-052 (Relief Valve Testing "
                 "Frequency) and REG-014 (Boiler Pressure Vessel Inspection Code). Do not "
                 "start the boiler if the relief valve test evidence is missing or "
                 "expired - escalate to the Compliance Auditor (Linda Osei) instead.\n\n"
                 "## 2. Startup sequence\n"
                 "1. Confirm feedwater supply and chemistry within spec.\n"
                 "2. Purge combustion chamber per burner manufacturer guidance.\n"
                 "3. Light burner at low fire, ramp gradually while monitoring drum "
                 "pressure.\n"
                 "4. Confirm safety interlocks and emergency shutdown (ESD) function per "
                 "REG-045 before ramping to full load.\n\n"
                 "## 3. Shutdown sequence\n"
                 "1. Reduce load gradually.\n"
                 "2. Secure fuel supply and confirm burner off.\n"
                 "3. Allow natural cooldown before isolating for maintenance access.\n"
             )),
        dict(filename="sop_lockout_tagout.md", doc_type="sop",
             title="SOP - Lockout/Tagout for Rotating and Pressurized Equipment",
             body=(
                 "# SOP: Lockout/Tagout (LOTO)\n\n"
                 "Applies to all rotating equipment (pumps, compressors) and pressurized "
                 "equipment (boilers, relief valves) prior to maintenance, per OSHA-105.\n\n"
                 "## Steps\n"
                 "1. Notify affected personnel and the Shift Supervisor (e.g. Maria Chen).\n"
                 "2. Identify all energy sources (electrical, pressure, stored mechanical "
                 "energy) for the asset.\n"
                 "3. Shut down equipment using normal stopping procedure.\n"
                 "4. Isolate energy sources and apply locks/tags.\n"
                 "5. Verify zero energy state before beginning work (e.g. bleed residual "
                 "pressure on pump casings or relief valve piping).\n"
                 "6. On completion, remove locks/tags in reverse order and confirm with "
                 "the Safety Officer (Priya Nair) before returning equipment to service.\n\n"
                 "PPE requirements per REG-031 (PPE Compliance Directive) apply throughout.\n"
             )),
    ]


def _manual_files() -> list[dict]:
    return [
        dict(filename="manual_pump_p101_oem.pdf", doc_type="manual",
             title="OEM Manual Excerpt - Centrifugal Pump P-101",
             lines=[
                 "OEM Manual Excerpt - Centrifugal Pump Model CP-500",
                 "Applicable Asset: P-101, P-102",
                 "",
                 "Section 4: Mechanical Seal Guidance",
                 "The standard mechanical seal is rated for continuous duty within the",
                 "manufacturer's best-efficiency-point (BEP) flow range. Operation away",
                 "from BEP, including low-flow recirculation, increases the risk of",
                 "cavitation, which manifests as elevated vibration and accelerated seal",
                 "face wear. Repeated seal failures on a short interval (see maintenance",
                 "records for asset P-101) should prompt a review of actual duty cycle",
                 "and suction conditions against this section before assuming the seal",
                 "itself is defective.",
                 "",
                 "Section 5: Alignment Tolerance",
                 "Shaft misalignment beyond 0.05 mm TIR at the coupling will materially",
                 "reduce mechanical seal life and is a common root cause of premature",
                 "seal failure alongside cavitation.",
                 "",
                 "Section 7: Recommended Seal Upgrade Path",
                 "For assets experiencing recurring seal failures, the manufacturer",
                 "recommends the cartridge-style mechanical seal (part family CS-9),",
                 "which tolerates minor misalignment and transient cavitation better",
                 "than the standard component seal.",
             ]),
        dict(filename="manual_boiler_b12_oem.pdf", doc_type="manual",
             title="OEM Manual Excerpt - Package Boiler B-12",
             lines=[
                 "OEM Manual Excerpt - Package Boiler Model FB-2200",
                 "Applicable Asset: B-12",
                 "",
                 "Section 3: Relief Valve Maintenance",
                 "The pressure relief valve (site tag V-045) must be bench tested at the",
                 "frequency required by local regulation (see REG-052) and the",
                 "certificate retained on file for the life of the boiler's operating",
                 "permit. Operating the boiler without current relief valve test",
                 "evidence is not permitted under REG-014.",
                 "",
                 "Section 6: Emergency Shutdown (ESD) Testing",
                 "Functional ESD tests should be performed per REG-045 and logged",
                 "alongside the relief valve certificate for audit purposes.",
             ]),
    ]


@dataclass
class CorpusManifestEntry:
    filename: str
    doc_type: str
    title: str


def _write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _write_pdf(path: str, title: str, lines: list[str]) -> None:
    """Write a minimal but genuinely-parseable single/multi-page PDF using
    fpdf2 (pure Python, no system dependencies) so the ingestion pipeline's
    pypdf-based parser has real PDF files to exercise."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    width = pdf.epw
    pdf.set_font("Helvetica", size=14)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(width, 10, title)
    pdf.set_font("Helvetica", size=11)
    pdf.ln(2)
    for line in lines:
        safe = line if line.strip() else " "
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(width, 7, safe)
    pdf.output(path)


def generate_corpus(output_dir: str) -> list[CorpusManifestEntry]:
    """Generate the full synthetic corpus into output_dir. Idempotent."""
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    manifest: list[CorpusManifestEntry] = []

    # --- SOPs (.md) ---
    for sop in _sop_files():
        _write_text(os.path.join(output_dir, sop["filename"]), sop["body"])
        manifest.append(CorpusManifestEntry(sop["filename"], sop["doc_type"], sop["title"]))

    # --- OEM manuals (.pdf) ---
    for man in _manual_files():
        _write_pdf(os.path.join(output_dir, man["filename"]), man["title"], man["lines"])
        manifest.append(CorpusManifestEntry(man["filename"], man["doc_type"], man["title"]))

    # --- Work orders (.json, one .txt) ---
    for wo in WORK_ORDERS:
        fname = f"{wo['wo_number'].lower().replace('-', '_')}.json"
        if wo["wo_number"] == "WO-1144":
            fname = "wo_1144_p102_routine_lube.txt"
            body = (
                f"Work Order {wo['wo_number']}\n"
                f"Asset: {wo['asset_tag']}\n"
                f"Status: {wo['status']}\n"
                f"Opened: {wo['opened_at']}  Closed: {wo['closed_at']}\n\n"
                f"{wo['description']}\n"
            )
            _write_text(os.path.join(output_dir, fname), body)
        else:
            _write_text(os.path.join(output_dir, fname), json.dumps(wo, indent=2))
        title = f"Work Order {wo['wo_number']} - {wo['asset_tag']}"
        manifest.append(CorpusManifestEntry(fname, "work_order", title))

    # --- Inspections (.txt / .scan.txt) ---
    for insp in INSPECTIONS:
        _write_text(os.path.join(output_dir, insp["filename"]), insp["body"])
        manifest.append(CorpusManifestEntry(insp["filename"], "inspection", insp["doc_title"]))

    # --- Incidents (.md) ---
    for inc in INCIDENTS:
        fname = f"incident_{inc['incident_code'].lower().replace('-', '')}_{inc['asset_tag'].lower().replace('-', '')}.md"
        body = (
            f"# Incident Report {inc['incident_code']}\n\n"
            f"**Asset:** {inc['asset_tag']}\n"
            f"**Severity:** {inc['severity']}\n"
            f"**Date:** {inc['occurred_at']}\n"
            f"**Title:** {inc['title']}\n\n"
            f"{inc['summary']}\n"
        )
        _write_text(os.path.join(output_dir, fname), body)
        manifest.append(CorpusManifestEntry(fname, "incident", f"{inc['incident_code']} - {inc['title']}"))

    # --- Asset registry (.csv) ---
    reg_path = os.path.join(output_dir, "asset_registry.csv")
    with open(reg_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["tag", "name", "asset_type", "criticality", "location"])
        writer.writeheader()
        for a in ASSETS:
            writer.writerow(a)
    manifest.append(CorpusManifestEntry("asset_registry.csv", "asset_registry", "Plant Asset Registry"))

    # --- Shift handover notes (.txt, email-style) ---
    for note in HANDOVER_NOTES:
        _write_text(os.path.join(output_dir, note["filename"]), note["body"])
        manifest.append(CorpusManifestEntry(note["filename"], "handover_note", note["doc_title"]))

    # --- Regulatory checklist (.csv, .pdf, .xlsx) ---
    checklist_csv = os.path.join(output_dir, "regulatory_checklist.csv")
    with open(checklist_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["code", "title", "description"])
        writer.writeheader()
        for r in REGULATIONS:
            writer.writerow(r)
    manifest.append(CorpusManifestEntry("regulatory_checklist.csv", "regulation", "Regulatory Checklist (Master)"))

    checklist_lines = [
        "This checklist summarizes the site regulatory codes referenced across",
        "maintenance, inspection, and incident records.",
        "",
    ]
    for r in REGULATIONS:
        checklist_lines.append(f"{r['code']}: {r['title']}")
        checklist_lines.append(f"    {r['description']}")
    _write_pdf(
        os.path.join(output_dir, "regulatory_checklist_boiler.pdf"),
        "Regulatory Checklist - Boiler House Focus",
        checklist_lines,
    )
    manifest.append(CorpusManifestEntry("regulatory_checklist_boiler.pdf", "regulation", "Regulatory Checklist - Boiler House Focus"))

    # compliance audit checklist (.xlsx)
    import pandas as pd

    audit_rows = [
        dict(asset_tag="B-12", checklist_item=COMPLIANCE_GAP["checklist_item"],
             regulation_code=COMPLIANCE_GAP["regulation_code"], status=COMPLIANCE_GAP["status"],
             severity=COMPLIANCE_GAP["severity"], notes=COMPLIANCE_GAP["missing_evidence"]),
        dict(asset_tag="P-101", checklist_item="Seal and vibration condition check",
             regulation_code="REG-022", status="ok", severity="low",
             notes="Passed 2025-Q3 inspection after WO-1067 seal replacement."),
        dict(asset_tag="C-201", checklist_item="General condition and valve plate check",
             regulation_code="REG-031", status="ok", severity="low",
             notes="Passed 2025-Q4 scanned inspection form."),
    ]
    df = pd.DataFrame(audit_rows)
    xlsx_path = os.path.join(output_dir, "compliance_audit_checklist.xlsx")
    df.to_excel(xlsx_path, index=False)
    manifest.append(CorpusManifestEntry("compliance_audit_checklist.xlsx", "regulation", "Compliance Audit Checklist"))

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump([entry.__dict__ for entry in manifest], fh, indent=2)

    return manifest


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    target = os.path.join(base, "data", "sample_corpus")
    entries = generate_corpus(target)
    print(f"Generated {len(entries)} files into {target}")
