"""Weekly AI Status Report Agent.

Turns rough team notes from AI evaluation, quality audits, and policy workflows
into a clean, executive-ready weekly status report.
"""
import os

import pandas as pd
import streamlit as st

from agent import run, to_markdown
from demo import SECTIONS
from prompts import SYSTEM_PROMPT

st.set_page_config(
    page_title="Weekly AI Status Report Agent",
    page_icon="📊",
    layout="wide",
)


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets first, then from the environment."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default)).strip()


API_KEY = setting("AI_API_KEY")
BASE_URL = setting("AI_BASE_URL", "https://api.openai.com/v1")
MODEL = setting("AI_MODEL", "gpt-4o-mini")

STATUS_COLOUR = {"Green": "#16a34a", "Amber": "#d97706", "Red": "#dc2626"}
SECTION_ICON = {"Highlights": "🌟", "Progress": "✅", "Risks": "⚠️", "Blockers": "⛔", "Next week": "📅"}

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; max-width: 1140px;}
      .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 22px 26px;
        border-radius: 14px;
        margin-bottom: 16px;
      }
      .hero h1 {
        font-size: 1.65rem;
        margin: 0 0 6px 0;
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.02em;
      }
      .hero p {
        margin: 0;
        opacity: 0.9;
        font-size: 0.98rem;
        line-height: 1.45;
      }
      .card {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      }
      .card h4 {
        margin: 0 0 10px 0;
        font-size: 1rem;
        font-weight: 600;
        color: #0f172a;
      }
      .item {
        padding: 8px 0;
        border-top: 1px dashed #e2e8f0;
        font-size: 0.93rem;
        line-height: 1.45;
      }
      .item:first-of-type {border-top: none;}
      .tag {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 2px 8px;
        border-radius: 999px;
        background: #eef2ff;
        color: #3730a3;
        margin-left: 6px;
      }
      .status {
        display: inline-block;
        color: #ffffff;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.95rem;
        letter-spacing: 0.02em;
      }
      .step {
        color: #0f172a;
        padding: 9px 13px;
        border-left: 4px solid #16a34a;
        background: #f8fafc;
        margin-bottom: 8px;
        border-radius: 6px;
        font-size: 0.9rem;
      }
      .step.bad {border-left-color: #d97706;}
      .footer {
        color: #64748b;
        font-size: 0.82rem;
        text-align: center;
        margin-top: 36px;
        padding-top: 16px;
        border-top: 1px solid #e2e8f0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header: Clear title and one-line explainer
st.markdown(
    '<div class="hero">'
    "<h1>📊 Weekly AI Status Report Agent</h1>"
    "<p>Turn rough team notes from AI evaluation, quality audits, and policy workflows into a clean, executive-ready report.</p>"
    "</div>",
    unsafe_allow_html=True,
)

if API_KEY:
    st.caption(f"🤖 Connected to AI Model: **{MODEL}** (self-checking enabled)")
else:
    st.caption("ℹ️ Demo Mode: running with rule-based heuristics. Add API key to switch to full AI model.")

SAMPLES = {
    "AI Quality Pilot Week (Default)": "sample_updates.txt",
    "Sample 6: [GREEN] Flawless Sprint & High Accuracy": "samples/sample6.txt",
    "Sample 9: [GREEN] Phase 1 Milestone Sign-Off": "samples/sample9.txt",
    "Sample 11: [GREEN] Process Optimization & High Velocity": "samples/sample11.txt",
    "Sample 14: [GREEN] Successful Onboarding & Zero Defects": "samples/sample14.txt",
    "Sample 1: [AMBER] Standard AI Quality Pilot": "samples/sample1.txt",
    "Sample 2: [AMBER] Red Teaming & Adversarial Sprint": "samples/sample2.txt",
    "Sample 4: [AMBER] Short 3-Line Summary": "samples/sample4.txt",
    "Sample 5: [AMBER] Missing Owners & Details": "samples/sample5.txt",
    "Sample 12: [AMBER] Complex Math Slips & Ambiguity": "samples/sample12.txt",
    "Sample 15: [AMBER] Vendor API Lag & Staff Shortage": "samples/sample15.txt",
    "Sample 3: [RED] Messy Chat Notes with Outage": "samples/sample3.txt",
    "Sample 7: [RED] Double Outage & Revoked Access": "samples/sample7.txt",
    "Sample 8: [RED] Critical Safety Filter Breach": "samples/sample8.txt",
    "Sample 10: [RED] Platform Crash & 85 Lost Evals": "samples/sample10.txt",
    "Sample 13: [RED] Corrupted Schema & Total Work Stoppage": "samples/sample13.txt",
}


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


if "updates" not in st.session_state:
    st.session_state.updates = ""

left, right = st.columns([1, 1.3], gap="large")

with left:
    st.markdown("#### Input Notes")
    pick = st.selectbox("Select a sample update to test", list(SAMPLES))
    c1, c2 = st.columns([1.2, 1])
    if c1.button("Load sample updates", use_container_width=True):
        st.session_state.updates = read(SAMPLES[pick])

    up = c2.file_uploader("Upload .txt file", type=["txt", "md", "csv"], label_visibility="collapsed")
    if up is not None and st.session_state.get("_uploaded") != up.name:
        st.session_state.updates = up.read().decode("utf-8", errors="ignore")
        st.session_state._uploaded = up.name

    updates = st.text_area(
        "Rough team updates",
        key="updates",
        height=330,
        placeholder="Paste daily stand-up notes, evaluator remarks, Slack updates, or batch progress lines, one per line...",
        label_visibility="collapsed",
    )
    go = st.button("Write my report", type="primary", use_container_width=True)

with right:
    st.markdown("#### Status Report")
    if go:
        if not updates.strip():
            st.warning("Please paste some notes first or click 'Load sample updates'.")
        else:
            # Spinner while the agent works
            with st.spinner("The agent is reading notes, sorting items, and checking its own work..."):
                try:
                    result, steps = run(updates, SYSTEM_PROMPT, API_KEY, BASE_URL, MODEL)
                except Exception as err:
                    st.error(f"The agent could not generate the report: {err}")
                    st.stop()
            st.session_state.result, st.session_state.steps = result, steps

    result = st.session_state.get("result")
    steps = st.session_state.get("steps", [])

    if not result:
        st.markdown(
            """
            <div class="card">
              <h4>How it works</h4>
              <div class="item">1. Click <b>Load sample updates</b> (or paste your own raw team notes).</div>
              <div class="item">2. Click <b>Write my report</b>.</div>
              <div class="item">3. The agent sorts every note into clean sections, runs self-checks, fixes any issues, and highlights missing data.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        items = result.get("items", [])
        count = lambda s: len([i for i in items if i.get("section") == s])
        colour = STATUS_COLOUR.get(result.get("status", ""), "#64748b")

        # 1. Overall Status Pill & Reason
        st.markdown(
            f'<span class="status" style="background:{colour}">Status: {result.get("status", "Not enough information")}</span>'
            f'&nbsp;&nbsp;<span style="color:#475569; font-weight:500;">{result.get("status_reason", "")}</span>',
            unsafe_allow_html=True,
        )
        st.write("")

        # 2. What Matters Most (Headline)
        if result.get("headline"):
            st.markdown(
                f'<div class="card" style="border-left: 6px solid {colour};">'
                f'<h4>What Matters Most This Week</h4>'
                f'<div style="font-size: 1.05rem; line-height: 1.45;">{result["headline"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # 3. Summary
        st.markdown(f"**Executive Summary:** {result.get('summary', 'Not enough information.')}")

        # Metrics overview
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Highlights", count("Highlights"))
        k2.metric("Risks", count("Risks"))
        k3.metric("Blockers", count("Blockers"))
        k4.metric("Questions", len(result.get("questions", [])))

        # 4. Answer in Clearly Separated Sections
        tab_report, tab_register, tab_actions, tab_email, tab_questions, tab_steps = st.tabs(
            [
                "Categorized Report",
                "Risks & Blockers",
                "Actions & Decisions",
                "Sponsor Email",
                "Questions for Team",
                "Agent Steps",
            ]
        )

        with tab_report:
            for s in SECTIONS:
                rows = [i for i in items if i.get("section") == s]
                body = "".join(
                    f'<div class="item">{i.get("text", "")}'
                    + (f'<span class="tag">👤 {i["owner"]}</span>' if i.get("owner") else "")
                    + (f'<span class="tag">📅 {i["due"]}</span>' if i.get("due") else "")
                    + "</div>"
                    for i in rows
                ) or '<div class="item" style="color:#94a3b8;">Nothing to report.</div>'
                st.markdown(f'<div class="card"><h4>{SECTION_ICON[s]} {s}</h4>{body}</div>', unsafe_allow_html=True)

        with tab_register:
            reg = [i for i in items if i.get("section") in ("Risks", "Blockers")]
            if reg:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Type": i["section"][:-1],
                                "Impact": i.get("impact") or "Not known",
                                "Owner": i.get("owner") or "Not known",
                                "Due": i.get("due") or "Not known",
                                "Item": i.get("text", ""),
                            }
                            for i in reg
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No active risks or blockers reported for this week.")

        with tab_actions:
            st.markdown("**Top Priority Actions**")
            for n, a in enumerate(result.get("actions", []) or [], 1):
                st.markdown(
                    f'<div class="step"><b>{n}. {a.get("action", "")}</b><br>'
                    f'<span style="color:#475569;">Owner: {a.get("owner") or "Not known"}  ·  Why: {a.get("why", "")}</span></div>',
                    unsafe_allow_html=True,
                )
            if not result.get("actions"):
                st.write("No immediate actions required.")

            st.markdown("**Decisions Required**")
            for dcs in result.get("decisions", []) or ["No pending decisions this week."]:
                st.markdown(f"- {dcs}")

        with tab_email:
            st.text_area(
                "Executive Email Draft",
                result.get("email", "") or "Not enough information.",
                height=220,
                help="Ready-to-copy summary email for leadership and sponsors.",
            )

        with tab_questions:
            for q in result.get("questions", []) or ["All required information is complete."]:
                st.markdown(f"- {q}")

        with tab_steps:
            for n, s in enumerate(steps, 1):
                st.markdown(
                    f'<div class="step {"" if s["ok"] else "bad"}"><b>{n}. {s["name"]}</b> {"✓" if s["ok"] else "!"}<br>'
                    f'<span style="color:#475569;">{s["detail"]}</span></div>',
                    unsafe_allow_html=True,
                )

        # Reminder banner under the report
        st.markdown(
            '<div style="background:#fffbeb; border:1px solid #fef3c7; border-radius:8px; padding:10px 14px; margin: 14px 0 10px 0; font-size:0.88rem; color:#92400e;">⚠️ <b>Reminder:</b> Please review this report for accuracy, tone, and full context before sharing or using it.</div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            "Download Report (.md)",
            to_markdown(result),
            file_name="ai-quality-weekly-status-report.md",
            use_container_width=True,
        )

# Footer exactly as requested
st.markdown('<div class="footer">Built by Srishti Sonavane at Zero to Live, Future Proof India</div>', unsafe_allow_html=True)
