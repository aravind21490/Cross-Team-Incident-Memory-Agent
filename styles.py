"""
styles.py
Case file design tokens and CSS for Streamlit.
Warm light palette, printed incident ledger aesthetic.
"""

import textwrap

CASE_FILE_CSS = textwrap.dedent("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');

:root {
    --paper: #F5F1E8;
    --raised-paper: #FBF9F3;
    --ink: #1C1B18;
    --muted-ink: #6B675E;
    --hairline: #D8D2C4;
    --rust: #B03A2E;
    --green: #2E6B4E;
    --ochre: #A9781B;
    --font-serif: 'Fraunces', Georgia, serif;
    --font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'IBM Plex Mono', Menlo, Consolas, monospace;
}

/* Global Reset */
html, body, [class*="css"], .stApp {
    background-color: var(--paper) !important;
    color: var(--ink) !important;
    font-family: var(--font-sans) !important;
    font-size: 14.5px !important;
    line-height: 1.5 !important;
}

/* Hide Streamlit header decoration, toolbar, deploy button, footer */
header[data-testid="stHeader"] {
    background: transparent !important;
}
.stDeployButton, footer, #MainMenu {
    display: none !important;
}
div[data-testid="stToolbar"] {
    display: none !important;
}
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1360px !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-serif) !important;
    font-weight: 500 !important;
    color: var(--ink) !important;
    letter-spacing: -0.01em;
}

/* Masthead */
.masthead {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid var(--hairline);
    padding-bottom: 0.75rem;
    margin-bottom: 1.5rem;
}
.masthead-title {
    font-family: var(--font-serif);
    font-size: 1.45rem;
    font-weight: 500;
    color: var(--ink);
    line-height: 1.2;
}
.masthead-sub {
    font-family: var(--font-sans);
    font-size: 0.86rem;
    color: var(--muted-ink);
    margin-top: 0.2rem;
}
.masthead-meta {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--muted-ink);
    display: flex;
    align-items: center;
    gap: 1.25rem;
}
.dot-green {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: var(--green);
    margin-right: 5px;
    vertical-align: middle;
}

/* Section Header Labels */
.section-label {
    font-family: var(--font-sans);
    font-size: 0.74rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted-ink);
    margin-bottom: 0.4rem;
}

/* Severity Stamp */
.sev-stamp {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    padding: 2px 6px;
    border-radius: 2px;
    display: inline-block;
    text-transform: uppercase;
}
.sev-stamp-p1 {
    border: 1px solid var(--rust);
    color: var(--rust);
    background: transparent;
}
.sev-stamp-p2 {
    border: 1px solid var(--ochre);
    color: var(--ochre);
    background: transparent;
}

/* Alert Error Block */
.alert-header-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.4rem;
}
.alert-service {
    font-family: var(--font-serif);
    font-size: 1.18rem;
    font-weight: 600;
    color: var(--ink);
}
.alert-team {
    font-family: var(--font-sans);
    font-size: 0.86rem;
    color: var(--muted-ink);
    margin-left: 0.5rem;
}
.alert-time {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--muted-ink);
}

.error-ledger-block {
    background-color: var(--raised-paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 0.85rem 1rem;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: var(--ink);
    line-height: 1.45;
    margin: 0.5rem 0 0.75rem 0;
}
.error-ledger-block.p1 {
    border-left: 2px solid var(--rust);
}
.error-ledger-block.p2 {
    border-left: 2px solid var(--ochre);
}

/* Buttons */
button[kind="primary"], .stButton > button[kind="primary"] {
    background-color: var(--rust) !important;
    color: var(--paper) !important;
    border: 1px solid var(--rust) !important;
    border-radius: 2px !important;
    font-family: var(--font-sans) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 1.2rem !important;
    box-shadow: none !important;
    transition: opacity 120ms ease !important;
}
button[kind="primary"]:hover {
    opacity: 0.9 !important;
}

button[kind="secondary"], .stButton > button[kind="secondary"], .stButton > button:not([kind="primary"]) {
    background-color: transparent !important;
    color: var(--ink) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 2px !important;
    font-family: var(--font-sans) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 0.95rem !important;
    box-shadow: none !important;
    transition: background-color 120ms ease !important;
}
button[kind="secondary"]:hover, .stButton > button:not([kind="primary"]):hover {
    background-color: var(--hairline) !important;
}

/* Tabs: Underline Style */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem !important;
    border-bottom: 1px solid var(--hairline) !important;
    background-color: transparent !important;
    padding-bottom: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--muted-ink) !important;
    font-family: var(--font-sans) !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 0.1rem !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}
.stTabs [aria-selected="true"] {
    border-bottom-color: var(--rust) !important;
    color: var(--ink) !important;
    font-weight: 600 !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: transparent !important;
    font-family: var(--font-sans) !important;
    font-size: 0.86rem !important;
    color: var(--muted-ink) !important;
    border: none !important;
}
details[data-testid="stExpander"] {
    border: 1px solid var(--hairline) !important;
    border-radius: 2px !important;
    background-color: var(--raised-paper) !important;
    margin-bottom: 1rem !important;
}

/* Input Fields & Textareas */
input, textarea, select, [data-baseweb="select"] {
    background-color: var(--raised-paper) !important;
    color: var(--ink) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: 2px !important;
    font-family: var(--font-sans) !important;
    font-size: 0.9rem !important;
}
input:focus, textarea:focus {
    border-color: var(--ink) !important;
    box-shadow: none !important;
}

/* Citation & Sections in Left Column */
.case-section {
    padding: 0.75rem 0 1rem 0;
    border-bottom: 1px solid var(--hairline);
}
.citation-text {
    font-family: var(--font-mono);
    font-size: 0.92rem;
    color: var(--ink);
    font-weight: 500;
}
.citation-none {
    font-family: var(--font-sans);
    font-size: 0.9rem;
    color: var(--muted-ink);
    font-style: italic;
}
.caution-line {
    border-left: 2px solid var(--ochre);
    padding: 0.25rem 0 0.25rem 0.65rem;
    color: var(--ochre);
    font-size: 0.88rem;
    margin: 0.4rem 0;
    line-height: 1.4;
}

/* Soft Green Specifics Highlight */
.mem-highlight {
    background-color: rgba(46, 107, 78, 0.12);
    color: var(--green);
    padding: 1px 4px;
    border-radius: 2px;
    font-weight: 500;
}

/* Assessment Right Column Rows */
.assessment-box {
    border-left: 1px solid var(--hairline);
    padding-left: 1.25rem;
}
.assessment-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.55rem 0;
    border-bottom: 1px solid var(--hairline);
    font-size: 0.86rem;
}
.assessment-label {
    color: var(--muted-ink);
    font-family: var(--font-sans);
}
.assessment-value {
    color: var(--ink);
    font-family: var(--font-mono);
    font-weight: 500;
    text-align: right;
}

/* Confidence Tick Bar */
.confidence-container {
    margin: 0.35rem 0 0.4rem 0;
}
.confidence-track {
    width: 100%;
    height: 3px;
    background-color: var(--hairline);
    position: relative;
    border-radius: 1px;
}
.confidence-fill {
    height: 3px;
    background-color: var(--green);
    border-radius: 1px;
}
.confidence-fill.low {
    background-color: var(--ochre);
}
.confidence-fill.none {
    background-color: var(--muted-ink);
}
.confidence-ticks {
    display: flex;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    color: var(--muted-ink);
    margin-top: 3px;
}
.confidence-threshold {
    color: var(--ochre);
    font-weight: 600;
}

/* Comparison Redline */
.comparison-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-top: 0.75rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid var(--hairline);
}
.comparison-col-left {
    border-right: 1px solid var(--hairline);
    padding-right: 1.5rem;
}
.comparison-col-right {
    padding-left: 0.25rem;
}
.comparison-text {
    font-size: 0.88rem;
    line-height: 1.45;
    color: var(--ink);
    margin-bottom: 0.5rem;
}

/* What memory was used table */
.memory-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
    margin-top: 0.5rem;
}
.memory-table th {
    text-align: left;
    font-family: var(--font-sans);
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted-ink);
    padding: 0.45rem 0.5rem;
    border-bottom: 1px solid var(--hairline);
}
.memory-table td {
    padding: 0.45rem 0.5rem;
    border-bottom: 1px solid var(--hairline);
    color: var(--ink);
    font-family: var(--font-sans);
}
.memory-table td.mono-cell {
    font-family: var(--font-mono);
}
.memory-table tr.top-match {
    border-left: 2px solid var(--green);
    background-color: rgba(46, 107, 78, 0.04);
}

/* Real Working Product - Enterprise Components */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.85rem;
    margin: 0.85rem 0 1.25rem 0;
}
.kpi-card {
    background-color: var(--raised-paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 0.75rem 0.9rem;
}
.kpi-label {
    font-family: var(--font-sans);
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted-ink);
}
.kpi-value {
    font-family: var(--font-mono);
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--ink);
    margin-top: 0.25rem;
}
.kpi-sub {
    font-family: var(--font-sans);
    font-size: 0.75rem;
    color: var(--muted-ink);
    margin-top: 0.15rem;
}

/* Service Topology Mesh */
.topology-container {
    background: var(--raised-paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 1.1rem;
    margin: 0.75rem 0 1.25rem 0;
}
.topology-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.85rem;
    margin-top: 0.75rem;
}
.service-node {
    background: var(--paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 0.85rem;
    transition: border-color 150ms ease;
}
.service-node.active-alert {
    border: 1px solid var(--rust);
    border-left: 3px solid var(--rust);
}
.service-node.upstream-source {
    border: 1px solid var(--ochre);
    border-left: 3px solid var(--ochre);
}
.service-node.healthy {
    border-left: 3px solid var(--green);
}
.service-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.service-title {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--ink);
}
.service-badge {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    font-weight: 600;
    padding: 0.12rem 0.4rem;
    border-radius: 2px;
    text-transform: uppercase;
}
.badge-ok {
    background: rgba(46, 107, 78, 0.12);
    color: var(--green);
}
.badge-alert {
    background: rgba(176, 58, 46, 0.12);
    color: var(--rust);
}
.badge-warn {
    background: rgba(169, 120, 27, 0.12);
    color: var(--ochre);
}
.service-meta-row {
    font-family: var(--font-sans);
    font-size: 0.78rem;
    color: var(--muted-ink);
    margin-top: 0.2rem;
    display: flex;
    justify-content: space-between;
}

/* Runbook Action Box */
.runbook-box {
    background: var(--raised-paper);
    border: 1px solid var(--hairline);
    border-left: 3px solid var(--green);
    border-radius: 2px;
    padding: 0.85rem 1rem;
    margin: 1rem 0;
}
.runbook-title {
    font-family: var(--font-sans);
    font-size: 0.76rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--green);
    margin-bottom: 0.35rem;
}

/* Architecture Pipeline Cards */
.pipeline-step {
    background: var(--raised-paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.85rem;
    display: grid;
    grid-template-columns: 48px 1fr 220px;
    gap: 1.25rem;
    align-items: center;
}
.pipeline-num {
    font-family: var(--font-mono);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--rust);
}
.pipeline-content h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1.05rem;
}
.pipeline-content p {
    margin: 0;
    font-size: 0.85rem;
    color: var(--muted-ink);
}
.pipeline-meta {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--ink);
    border-left: 1px solid var(--hairline);
    padding-left: 1rem;
}

/* Incident Dossier */
.dossier-card {
    background: var(--raised-paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--raised-paper) !important;
    border-right: 1px solid var(--hairline) !important;
    z-index: 1000 !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* Ensure the collapsed sidebar toggle is prominent, highly visible, and clearly labeled */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
}
[data-testid="collapsedControl"] button {
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.4rem !important;
    background-color: var(--raised-paper) !important;
    color: var(--ink) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 2px !important;
    padding: 0.35rem 0.75rem !important;
    font-family: var(--font-sans) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08) !important;
    transition: background-color 120ms ease !important;
}
[data-testid="collapsedControl"] button:hover {
    background-color: var(--paper) !important;
}
[data-testid="collapsedControl"] button::after {
    content: " Open Sidebar (Scenarios & Controls)";
    font-family: var(--font-sans) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
}
</style>
""").strip()
