import os, re, json, hashlib
from datetime import datetime, date

import pandas as pd
try:
    import pycountry
except ImportError:
    pycountry = None
import streamlit as st

from database import init_db, get_conn, seed_reference_data, DOC_DIR
from reference_data import (
    countries, currency_items, currency_choices, currency_code, banks,
    isic_sections, get_divisions, get_groups, get_classes,
)
from fx_engine import (
    seed_fx_rates, ensure_currency_rows, get_rate_info,
    convert_to_usd, save_fx_rate,
)
from rules_engine import validate_application, required_documents, evaluate_rules, rule_catalog
from analytics import get_dashboard_metrics, get_monthly_flows, get_application_status
from reporting import applications_to_excel

st.set_page_config(
    page_title="Digital Exchange Control Management Portal — Prototype",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db(); seed_reference_data(); seed_fx_rates(); ensure_currency_rows(currency_items)

st.markdown("""
<style>
:root{--primary:#163A4A;--secondary:#1F6F8B;--accent:#C08A2E;--danger:#B42318;--ink:#182230;--muted:#64748b;--line:#dbe4ee;}
.block-container{padding-top:1rem;padding-bottom:2.5rem;max-width:1550px;}
.portal-header{background:linear-gradient(105deg,#163A4A 0%,#1F6F8B 70%,#C08A2E 100%);padding:20px 25px;border-radius:14px;color:#fff;margin-bottom:14px;box-shadow:0 5px 20px rgba(22,58,74,.20)}
.portal-header .brand{font-size:12px;font-weight:800;letter-spacing:1.3px;text-transform:uppercase}.portal-header h1{margin:3px 0;font-size:30px}.portal-header p{margin:0;opacity:.92}
.section{font-size:21px;font-weight:800;color:#163A4A;margin:12px 0 8px}.subsection{font-size:16px;font-weight:800;color:#1F6F8B;margin-top:10px}
.about{border-left:5px solid #C08A2E;background:#f8fafc;padding:14px 18px;border-radius:9px;margin:8px 0}.legal{border:1px solid #dbe4ee;background:#fff;padding:14px 16px;border-radius:9px;margin:8px 0}.note{background:#eff6ff;border-left:4px solid #1F6F8B;padding:10px;border-radius:6px}.risk{background:#fff7ed;border-left:4px solid #f59e0b;padding:10px;border-radius:6px}.danger{background:#fef2f2;border-left:4px solid #B42318;padding:10px;border-radius:6px}.ok{background:#f0fdf4;border-left:4px solid #15803d;padding:10px;border-radius:6px}.small{font-size:12px;color:#64748b}

.about-title{font-size:20px;font-weight:900;color:#163A4A;margin:5px 0 8px}
.portal-subtitle{margin:0 0 12px;padding:9px 14px;background:#f7fafc;
border-left:4px solid #C08A2E;border-radius:7px;color:#475569;font-size:12px}
.indicator-panel{background:linear-gradient(135deg,#163A4A,#1F6F8B);
border-radius:12px;padding:10px 12px;color:white;box-shadow:0 4px 15px rgba(22,58,74,.16)}
.indicator-title{font-size:10px;font-weight:800;letter-spacing:.9px;opacity:.9;margin-bottom:6px}
.indicator-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
.indicator-card{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);
border-radius:8px;padding:7px}
.indicator-label{font-size:9px;opacity:.85}
.indicator-value{font-size:18px;font-weight:900;line-height:1.1}
.indicator-date{font-size:8px;opacity:.72;margin-top:2px}

div[data-testid="stMetric"]{border:1px solid #dbe4ee;padding:10px;border-radius:10px;background:white}
.stButton>button[kind="primary"]{background:#1F6F8B;border-color:#1F6F8B}

/* ---------------------------------------------------------
   NEUTRAL PROTOTYPE VISUAL SYSTEM
   --------------------------------------------------------- */
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#062f57 0%,#163A4A 48%,#052945 100%);
    border-right:4px solid #C08A2E;
}
[data-testid="stSidebar"] > div:first-child{padding-top:1.0rem;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:#eef5fb;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.18);}
[data-testid="stSidebar"] .sidebar-brand{
    padding:4px 4px 12px 4px;
}
[data-testid="stSidebar"] .sidebar-kicker{
    color:#C08A2E;font-size:11px;font-weight:900;letter-spacing:1.6px;
}
[data-testid="stSidebar"] .sidebar-title{
    color:#fff;font-size:25px;font-weight:900;line-height:1.08;margin-top:5px;
}
[data-testid="stSidebar"] .sidebar-subtitle{
    color:#c9d8e7;font-size:12px;font-weight:700;margin-top:6px;
}
[data-testid="stSidebar"] .sidebar-section-title{
    color:#C08A2E;font-size:11px;font-weight:900;letter-spacing:1.1px;
    text-transform:uppercase;margin:12px 0 7px;
}
[data-testid="stSidebar"] .resource-link{
    display:block;text-decoration:none!important;color:#f8fbff!important;
    background:rgba(255,255,255,.075);border:1px solid rgba(255,255,255,.10);
    border-radius:9px;padding:8px 10px;margin:5px 0;font-size:11.5px;font-weight:650;
    transition:all .18s ease;
}
[data-testid="stSidebar"] .resource-link:hover{
    background:rgba(212,175,55,.18);border-color:rgba(212,175,55,.65);
    transform:translateX(2px);
}
[data-testid="stSidebar"] .sidebar-feature{
    display:flex;align-items:center;gap:8px;padding:8px 9px;margin:5px 0;
    border-left:3px solid #C08A2E;background:rgba(255,255,255,.055);
    border-radius:6px;color:#e8f0f7;font-size:11px;font-weight:650;
}
[data-testid="stSidebar"] .sidebar-security{
    margin-top:12px;padding:12px;border-radius:10px;
    background:linear-gradient(135deg,rgba(212,175,55,.15),rgba(255,255,255,.06));
    border:1px solid rgba(212,175,55,.35);
}
[data-testid="stSidebar"] .security-title{color:#C08A2E;font-size:10px;font-weight:900;letter-spacing:1px;}
[data-testid="stSidebar"] .security-text{color:#dbe7f2;font-size:10.5px;line-height:1.5;margin-top:5px;}
[data-testid="stSidebar"] .sidebar-footer{
    color:#91abc0;font-size:9px;text-align:center;padding:12px 4px 4px;
    letter-spacing:.3px;
}

.main-title-block{padding:7px 0 2px;}
.institution-kicker{color:#163A4A;font-size:12px;font-weight:900;letter-spacing:1.4px;}
.main-title{color:#10253b;font-size:30px;font-weight:950;line-height:1.1;margin-top:4px;}
.main-subtitle{color:#5a6c7f;font-size:13px;font-weight:700;margin-top:5px;}
.market-strip{
    background:linear-gradient(135deg,#062f57,#1F6F8B);color:#fff;
    border-radius:14px;padding:13px 15px;box-shadow:0 8px 22px rgba(22,58,74,.17);
}
.market-heading{font-size:10px;font-weight:900;letter-spacing:1.2px;color:#C08A2E;margin-bottom:8px;}
.market-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;}
.market-grid>div{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.12);border-radius:9px;padding:8px;}
.market-label{font-size:9px;color:#d8e6f2;font-weight:700;}
.market-value{font-size:17px;color:#fff;font-weight:950;line-height:1.15;margin-top:3px;}
.market-date{font-size:8px;color:#b9ccdc;margin-top:3px;}
.gold-rule{height:4px;background:linear-gradient(90deg,#C08A2E 0%,#C08A2E 28%,#1F6F8B 28%,#1F6F8B 100%);border-radius:4px;margin:9px 0 10px;}
.portal-subtitle{
    margin:0 0 16px;padding:10px 14px;background:#f7fafc;
    border:1px solid #e2eaf2;border-left:4px solid #C08A2E;border-radius:8px;
    color:#516274;font-size:11px;font-weight:650;
}
.about-title{font-size:20px;font-weight:900;color:#163A4A;margin:5px 0 8px;}
.about{border-left:5px solid #C08A2E;background:linear-gradient(90deg,#f7fbff,#fff);
    padding:15px 18px;border-radius:10px;margin:8px 0;box-shadow:0 3px 12px rgba(7,55,99,.05);}
.section{font-size:22px;font-weight:900;color:#163A4A;margin:14px 0 8px;}
.subsection{font-size:16px;font-weight:900;color:#1F6F8B;margin-top:10px;}

/* Streamlit controls */
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input{border:1px solid #cbd8e5;border-radius:8px;}
[data-baseweb="select"] > div{border-color:#cbd8e5;border-radius:8px;}
.stButton>button{border-radius:8px;font-weight:800;}
.stButton>button[kind="primary"]{box-shadow:0 4px 12px rgba(11,79,138,.20);}
[data-testid="stAlert"]{border-radius:9px;}

.signed-in-banner{
    display:inline-block;background:#f4f8fc;border:1px solid #dbe6f0;border-left:4px solid #C08A2E;
    color:#40546a;padding:7px 12px;border-radius:8px;font-size:11px;margin:2px 0 10px;
}
.signed-in-banner span{color:#1F6F8B;font-weight:800;}

.login-intro{
    background:linear-gradient(135deg,#eef6ff 0%,#f9fbfd 70%,#fff8e1 100%);
    border:1px solid #dce8f3;border-top:4px solid #C08A2E;
    border-radius:12px;padding:15px 18px;margin:8px 0 14px;
}
.login-intro-title{font-size:18px;font-weight:900;color:#163A4A;}
.login-intro-text{font-size:11px;color:#526579;margin-top:4px;line-height:1.55;}
.access-pill{display:inline-block;background:#163A4A;color:white;padding:4px 8px;border-radius:999px;
    font-size:9px;font-weight:900;letter-spacing:.5px;margin-top:7px;}

.rule-engine-banner{background:linear-gradient(105deg,#062f57,#1F6F8B);color:#fff;border-radius:14px;padding:18px 20px;margin:8px 0 14px;box-shadow:0 6px 18px rgba(7,55,99,.15);}
.rule-engine-banner .kicker{color:#C08A2E;font-size:10px;font-weight:900;letter-spacing:1.4px;text-transform:uppercase;}
.rule-engine-banner h2{margin:3px 0 4px;font-size:24px;}
.rule-engine-banner p{margin:0;color:#dbe8f4;font-size:11px;line-height:1.5;}
.rule-card{border:1px solid #dbe4ee;border-left:5px solid #1F6F8B;border-radius:9px;background:#fff;padding:10px 12px;margin:6px 0;}
.rule-pass{border-left-color:#15803d;background:#f0fdf4}.rule-review{border-left-color:#d97706;background:#fffbeb}.rule-block{border-left-color:#b91c1c;background:#fef2f2}.rule-escalate{border-left-color:#7c3aed;background:#f5f3ff}.rule-info{border-left-color:#2563eb;background:#eff6ff}.rule-na{border-left-color:#94a3b8;background:#f8fafc}
.rule-id{font-size:10px;font-weight:900;letter-spacing:.6px;color:#64748b}.rule-title{font-size:13px;font-weight:900;color:#17324d}.rule-explanation{font-size:11px;color:#475569;line-height:1.45;margin-top:3px}.rule-source{font-size:10px;color:#64748b;margin-top:5px}
.engine-kpi{border:1px solid #dbe4ee;border-radius:10px;background:#fff;padding:10px 12px;text-align:center}.engine-kpi .v{font-size:22px;font-weight:950;color:#163A4A}.engine-kpi .l{font-size:9px;font-weight:800;color:#64748b;text-transform:uppercase;letter-spacing:.7px}
/* Module 2 — Exchange Control Rules Engine */
.module-switch-title{font-size:9px;font-weight:950;letter-spacing:1.2px;color:#C08A2E;text-transform:uppercase;margin:14px 0 6px;}
.module-card{background:linear-gradient(135deg,#062f57,#1F6F8B);border:1px solid rgba(255,255,255,.16);border-radius:12px;padding:12px;margin:6px 0 12px;box-shadow:0 8px 18px rgba(3,35,64,.22);}
.module-card .code{font-size:9px;color:#C08A2E;font-weight:950;letter-spacing:1.1px;text-transform:uppercase;}
.module-card .name{font-size:16px;color:#fff;font-weight:950;margin-top:2px;}
.rules-shell{background:linear-gradient(135deg,#041f3a 0%,#1F6F8B 62%,#174f76 100%);border-radius:18px;padding:24px 26px;color:#fff;margin:2px 0 18px;box-shadow:0 12px 30px rgba(4,31,58,.22);position:relative;overflow:hidden;}
.rules-shell:after{content:'';position:absolute;right:-70px;top:-90px;width:260px;height:260px;border:2px solid rgba(212,175,55,.24);border-radius:50%;}
.rules-shell .eyebrow{font-size:10px;letter-spacing:1.8px;color:#C08A2E;font-weight:950;text-transform:uppercase;}
.rules-shell h1{font-size:32px;margin:6px 0 5px;font-weight:950;}
.rules-shell p{max-width:850px;color:#d9e7f3;font-size:12px;line-height:1.55;margin:0;}
.rules-badge{display:inline-block;margin-top:13px;padding:6px 10px;border:1px solid rgba(255,255,255,.18);border-radius:999px;background:rgba(255,255,255,.08);font-size:9px;font-weight:850;color:#fff;}
.rule-module-kpi{border:1px solid #d8e3ed;background:#fff;border-radius:13px;padding:14px 15px;min-height:94px;box-shadow:0 4px 14px rgba(7,55,99,.05);}
.rule-module-kpi .num{font-size:25px;font-weight:950;color:#163A4A;}.rule-module-kpi .label{font-size:9px;font-weight:900;color:#66788a;text-transform:uppercase;letter-spacing:.8px;margin-top:2px;}.rule-module-kpi .note{font-size:9px;color:#8795a3;margin-top:5px;}
.flow-card{border:1px solid #dbe5ef;border-top:4px solid #1F6F8B;background:#fff;border-radius:11px;padding:13px;min-height:118px;box-shadow:0 4px 12px rgba(7,55,99,.04);}
.flow-card .step{font-size:9px;color:#C08A2E;font-weight:950;letter-spacing:1px;}.flow-card .title{font-size:14px;color:#17324d;font-weight:950;margin-top:3px;}.flow-card .desc{font-size:10px;color:#657688;line-height:1.45;margin-top:5px;}
.rule-category-card{border:1px solid #dbe5ef;border-left:5px solid #C08A2E;background:#fff;border-radius:10px;padding:11px 13px;margin-bottom:8px;}.rule-category-card .cat{font-size:12px;font-weight:950;color:#163A4A;}.rule-category-card .count{font-size:20px;font-weight:950;color:#1F6F8B;float:right;}.rule-category-card .desc{font-size:9px;color:#68798a;margin-top:4px;}
.engine-note{background:#fff9e6;border:1px solid #ead38b;border-left:4px solid #C08A2E;border-radius:9px;padding:10px 12px;font-size:10px;color:#5e5230;line-height:1.5;}
</style>
""", unsafe_allow_html=True)




def get_all_countries():
    """Return a comprehensive ISO 3166 country list, with Zimbabwe first."""
    countries = []
    if pycountry is not None:
        for c in pycountry.countries:
            countries.append(
                {
                    "name": c.name,
                    "code": getattr(c, "alpha_2", ""),
                }
            )
    else:
        # Fallback: retain the existing database country list if pycountry
        # is unavailable. The package is included in requirements.txt.
        countries = [
            {"name": "Zimbabwe", "code": "ZW"},
            {"name": "South Africa", "code": "ZA"},
            {"name": "Zambia", "code": "ZM"},
            {"name": "Botswana", "code": "BW"},
        ]

    # Remove duplicates and normalize names for a clean selector.
    seen = set()
    clean = []
    for item in countries:
        key = (item["name"], item["code"])
        if key not in seen:
            seen.add(key)
            clean.append(item)

    clean.sort(key=lambda x: x["name"].lower())

    # Put Zimbabwe first because this is a Zimbabwean regulatory portal.
    clean.sort(key=lambda x: 0 if x["code"] == "ZW" else 1)
    return clean


def get_all_currencies():
    """
    Return as many current ISO 4217 currencies as practical using pycountry,
    plus important Zimbabwe-specific / recent currency entries.
    """
    currencies = []

    if pycountry is not None:
        for c in pycountry.currencies:
            currencies.append(
                {
                    "code": c.alpha_3,
                    "name": c.name,
                    "numeric": getattr(c, "numeric", ""),
                }
            )

    # Zimbabwe Gold (ZiG) was introduced as the Zimbabwean local currency code ZWG.
    # It may not exist in every installed pycountry release, so ensure it is present.
    extras = [
        {"code": "ZWG", "name": "Zimbabwe Gold (ZiG)", "numeric": "924"},
    ]

    seen = {x["code"] for x in currencies}
    for item in extras:
        if item["code"] not in seen:
            currencies.append(item)

    # Prefer the Zimbabwe currency at the top, then alphabetical by code/name.
    currencies.sort(key=lambda x: (0 if x["code"] == "ZWG" else 1, x["code"]))
    return currencies


def regulatory_resource_links():
    """Regulatory reference sources used by the portal sidebar."""
    return [
        ("🌐 Regulatory Authority Website", "https://www.rbz.co.zw/"),
        ("🏦 Capital Flows Management", "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management"),
        ("📜 Exchange Control Regulatory Framework", "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management/regulatory-framework"),
        ("📘 Exchange Control Act — Chapter 22:05", "https://www.rbz.co.zw/documents/acts/Exchange_Control_Act-_Updated.pdf"),
        ("📗 Exchange Control Regulations — S.I. 109/1996", "https://www.rbz.co.zw/documents/acts/SIs/exchange-control-regulations%2C-1996-%28statutory-instrument-109-of-1996%29.pdf"),
        ("📕 Exchange Control General Order — S.I. 110/1996", "https://www.rbz.co.zw/documents/acts/SIs/exchange-control-%28general-%29-order%2C-1996-%28statutory-instrument-110-of-1996%29.pdf"),
        ("📙 ADLA Order — S.I. 104/2015", "https://www.rbz.co.zw/documents/acts/SIs/SI%20%202015-104%20-%20Exchange%20Control%28Authorised%20Dealer%20with%20Limited%20Authority%29,%20Order,%20%202015%20Statutory-instrument-104.2015.pdf"),
        ("📑 Directives, Circulars & Orders", "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management/directives-circulars-and-orders"),
        ("💱 FX Transactions Guidelines — FXD5 v2.0", "https://www.rbz.co.zw/documents/Regulations_Acts/2026/Foreign_Exchange_Guidelines_FXD5_version_2._March_2026.pdf"),
        ("📊 Latest — 2026 Mid-Term Monetary Policy Statement", "https://www.rbz.co.zw/index.php/monetary-policy/monetary-policy-statements/1639-2026-mid-term-monetary-policy-statement"),
        ("📚 All Monetary Policy Statements", "https://www.rbz.co.zw/index.php/monetary-policy/monetary-policy-statements"),
        ("📰 Regulatory Notices & Publications", "https://www.rbz.co.zw/index.php/publications-notices/notices/press-release"),
        ("🏛️ Authorised Dealers", "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management/authorised-dealers"),
    ]


def render_sidebar():
    """Neutral prototype navigation and regulatory reference resources."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-kicker">DIGITAL EXCHANGE CONTROL</div>
                <div class="sidebar-title">Management Portal</div>
                <div class="sidebar-subtitle">Prototype Application</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("""
            <div class="module-switch-title">System modules</div>
            <div class="module-card"><div class="code">MODULE 2</div><div class="name">Exchange Control Rules Engine</div></div>
            """, unsafe_allow_html=True)
        module_options=['1 · Application & Case Portal','2 · Exchange Control Rules Engine']
        current_module=st.session_state.get('system_module', module_options[0])
        st.session_state['system_module']=st.radio('Select module',module_options,index=module_options.index(current_module),label_visibility='collapsed')
        st.markdown(
            """
            <div class="sidebar-section-title">Portal capabilities</div>
            <div class="sidebar-feature">✓ KYC / AML & beneficial ownership</div>
            <div class="sidebar-feature">✓ Global countries & currencies</div>
            <div class="sidebar-feature">✓ ISIC Rev.4 transaction classification</div>
            <div class="sidebar-feature">✓ FX conversion & auditable rates</div>
            <div class="sidebar-feature">✓ Compliance risk & workflow routing</div>
            <div class="sidebar-feature">✓ Document management & audit trail</div>
            <div class="sidebar-section-title">Regulatory reference sources</div>
            """,
            unsafe_allow_html=True,
        )

        for label, url in regulatory_resource_links():
            st.markdown(
                f'<a class="resource-link" href="{url}" target="_blank">{label}</a>',
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="sidebar-security">
              <div class="security-title">📚 REGULATORY DOCUMENTS</div>
              <div class="security-text">
                Exchange Control Act, Exchange Control Regulations, FXD5 Guidelines,
                regulatory directives, circulars, orders and policy documents are
                linked above to their regulatory reference sources.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            """
            <div class="sidebar-security">
              <div class="security-title">🔒 CONFIDENTIALITY</div>
              <div class="security-text">
                Information and documents submitted through this portal are handled
                with care and confidentiality, subject to the Exchange Control Act,
                applicable laws, regulations, directives and authorised institutional
                procedures.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sidebar-footer">Prototype · Exchange Control · Analytics</div>',
            unsafe_allow_html=True,
        )


def get_portal_indicators():
    """Return the latest configured portal indicators from the database."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT indicator_key, value, unit, display_date, source, updated_at "
            "FROM portal_indicators WHERE active=1 ORDER BY indicator_key"
        ).fetchall()
    finally:
        conn.close()
    return {r["indicator_key"]: dict(r) for r in rows}


def portal_header():
    indicators = get_portal_indicators()

    def val(key, fallback="—"):
        return indicators.get(key, {}).get("value", fallback)

    left, right = st.columns([5.1, 4.0])

    with left:
        st.markdown(
            """
            <div class="main-title-block">
              <div class="institution-kicker">DIGITAL EXCHANGE CONTROL</div>
              <div class="main-title">Management & Intelligence Portal</div>
              <div class="main-subtitle">
                Prototype application · exchange-control workflows · analytics · compliance support
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f"""
            <div class="market-strip">
              <div class="market-heading">MARKET & POLICY SNAPSHOT</div>
              <div class="market-grid">
                <div>
                  <div class="market-label">ZiG Inflation</div>
                  <div class="market-value">{val("inflation_yoy")}%</div>
                  <div class="market-date">{indicators.get("inflation_yoy",{}).get("display_date","")}</div>
                </div>
                <div>
                  <div class="market-label">Policy Rate</div>
                  <div class="market-value">{val("policy_rate")}%</div>
                  <div class="market-date">{indicators.get("policy_rate",{}).get("display_date","")}</div>
                </div>
                <div>
                  <div class="market-label">USD / ZWG</div>
                  <div class="market-value">{val("usd_zwg")}</div>
                  <div class="market-date">{indicators.get("usd_zwg",{}).get("display_date","")}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="gold-rule"></div>
        <div class="portal-subtitle">
          Digital submission · KYC/AML support · transaction classification ·
          FX conversion · compliance workflow · capital-flow intelligence
        </div>
        """,
        unsafe_allow_html=True,
    )


def about_section():
    """User-facing portal guide and regulatory information."""
    topics = [
        "About the Portal",
        "How to Apply",
        "Regulatory Framework",
        "KYC / AML / CFT Compliance",
        "Data Confidentiality & Privacy",
        "Important User Notice",
    ]

    selected = st.selectbox(
        "ℹ️ About the Portal & Regulatory/Compliance Guide",
        topics,
        index=0,
        key="about_topic",
    )

    if selected == "About the Portal":
        st.info(
            "This portal provides a controlled digital channel for exchange-control "
            "applications, applicant identification, transaction classification, "
            "supporting-document submission, preliminary compliance checks, workflow "
            "and status tracking."
        )

    elif selected == "How to Apply":
        st.markdown(
            """
            **1. Complete applicant/KYC information**  
            Provide the required identification, contact, legal-person, ownership,
            beneficial-owner, source-of-funds and source-of-wealth information.

            **2. Complete the transaction section**  
            Select the direction, transaction type, country, ISIC Rev.4 activity,
            currency, amount, Authorised Dealer/banking institution and transaction date.

            **3. Upload supporting documents**  
            Provide the documents relevant to the transaction and respond to any
            subsequent requests for additional information.

            **4. Review declarations**  
            Confirm that the information is accurate and can be supported by evidence.

            **5. Submit and track**  
            The system generates a unique application reference, performs preliminary
            validation and provides a channel for subsequent queries and responses.
            """
        )

    elif selected == "Regulatory Framework":
        st.markdown(
            """
            The portal is designed to operate within Zimbabwe's applicable
            exchange-control, foreign-exchange and financial-crime-control framework.

            **Principal instruments include:**
            - Exchange Control Act [Chapter 22:05]
            - Exchange Control Regulations, 1996 — S.I. 109 of 1996
            - Exchange Control (General) Order, 1996 — S.I. 110 of 1996
            - Exchange Control (Authorised Dealers with Limited Authority) Order, 2015 — S.I. 104 of 2015
            - Foreign Exchange Transactions Guidelines FXD5 Version 2.0 — March 2026
            - Money Laundering and Proceeds of Crime Act [Chapter 9:24], as amended
            - Applicable applicable regulatory/supervisory directives, notices, sanctions requirements and
              authorised institutional procedures.
            """
        )
        st.markdown("#### Selected legal provisions")
        st.markdown(
            '> **Exchange Control Act, section 8:** "Except for the purposes of this Act '
            'or the compilation of statistics or when ordered to do so by a court, no '
            'person exercising any functions under this Act shall ... disclose any '
            'information relating to any person, firm or business, acquired in the '
            'exercise of such functions."'
        )
        st.markdown(
            '> **Money Laundering and Proceeds of Crime Act:** customer identification '
            'and verification, beneficial-owner identification, purpose/nature of the '
            'business relationship and appropriate transaction records form part of '
            'the compliance framework.'
        )
        st.caption(
            "The excerpts are for orientation only. Current legislation, regulations, "
            "directives and institutional procedures prevail."
        )

    elif selected == "KYC / AML / CFT Compliance":
        st.markdown(
            """
            The portal supports risk-based due diligence through:
            - customer identification and verification;
            - legal-person and ownership information;
            - ultimate beneficial ownership;
            - authorised representatives;
            - intended purpose and nature of the relationship;
            - source of funds and source of wealth;
            - PEP and sanctions declarations;
            - adverse legal/regulatory information;
            - transaction size, country, sector and pattern indicators;
            - supporting-document controls; and
            - enhanced-review and compliance-escalation routing where appropriate.

            Automated flags are decision-support controls and do not replace the legal,
            compliance or supervisory judgment of authorised officers.
            """
        )

    elif selected == "Data Confidentiality & Privacy":
        st.markdown(
            """
            ### 🔒 Information and documents are handled with care and confidentiality

            Information and documents submitted through this portal are intended to be
            handled with the **highest level of care and confidentiality consistent with
            the Exchange Control Act and other applicable laws, regulations, directives
            and authorised institutional procedures**.

            Access should be restricted to authorised personnel with a legitimate
            operational, supervisory, compliance, statistical or legal function.

            Information may nevertheless be disclosed where disclosure is authorised or
            required by applicable law, court order, regulatory/supervisory requirement,
            statistical function or another lawful institutional purpose.

            Applicants should submit only information and documents relevant to the
            application and should ensure that all information supplied is accurate and
            complete.
            """
        )

    elif selected == "Important User Notice":
        st.warning(
            "This application is a prototype for research, analytical and demonstration purposes. It is not an officially authorised institutional system. Any operational deployment would require formal approval, information-security controls, identity and access management, retention rules, document security, disaster recovery, integration controls and documented operating procedures."
        )


def indicator_admin():
    st.markdown("### Portal Market & Policy Indicators")
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT indicator_key, label, value, unit, display_date, source,
               updated_at, active
        FROM portal_indicators
        ORDER BY id
        """,
        conn,
    )
    conn.close()

    st.dataframe(df, use_container_width=True, hide_index=True)

    labels = {
        "inflation_yoy": "ZiG Annual Inflation",
        "policy_rate": "Bank Policy Rate",
        "usd_zwg": "USD / ZWG Exchange Rate",
    }

    key = st.selectbox(
        "Indicator to update",
        list(labels.keys()),
        format_func=lambda x: labels[x],
    )

    current = df[df["indicator_key"] == key]
    current_value = current.iloc[0]["value"] if not current.empty else ""
    current_date = current.iloc[0]["display_date"] if not current.empty else str(date.today())
    current_source = current.iloc[0]["source"] if not current.empty else "Authorised institutional source"

    c1, c2, c3 = st.columns(3)
    value = c1.text_input("Value", value=str(current_value))
    display_date = c2.text_input("Display date / period", value=current_date)
    source = c3.text_input("Source", value=current_source)

    if st.button("Update Portal Indicator", type="primary"):
        conn = get_conn()
        conn.execute(
            """
            UPDATE portal_indicators
            SET value=?, display_date=?, source=?, updated_at=CURRENT_TIMESTAMP
            WHERE indicator_key=?
            """,
            (value.strip(), display_date.strip(), source.strip(), key),
        )
        conn.commit()
        conn.close()

        audit(
            current_user()["username"],
            "UPDATE_PORTAL_INDICATOR",
            details=f"{key}={value}; period={display_date}; source={source}",
        )
        st.success("Portal indicator updated.")
        st.rerun()


def current_user(): return st.session_state.get('user')


def audit(username, action, ref=None, details=''):
    conn=get_conn(); conn.execute('INSERT INTO audit_log(username,action,reference_no,details) VALUES(?,?,?,?)',(username,action,ref,details)); conn.commit(); conn.close()


def login():
    st.markdown(
        """
        <div class="login-intro">
          <div class="login-intro-title">Prototype Portal Access</div>
          <div class="login-intro-text">
            Select a demonstration role to explore the exchange-control application, case-management and
            compliance workflow.
          </div>
          <span class="access-pill">PUBLIC PROTOTYPE · DEMONSTRATION ACCESS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    role=st.selectbox('Demonstration role',['Applicant','Exchange Control Officer','Compliance / AML Officer','Management'])
    defaults={'Applicant':'demo_applicant','Exchange Control Officer':'officer','Compliance / AML Officer':'compliance','Management':'management'}
    username=st.text_input('Username',value=defaults[role])
    if st.button('Enter Prototype',type='primary'):
        username = username.strip() or defaults[role]
        st.session_state.user={'username':username,'role':{'Applicant':'applicant','Exchange Control Officer':'officer','Compliance / AML Officer':'compliance','Management':'management'}[role]}
        audit(username,'LOGIN',details=f'Prototype role={role}')
        st.rerun()
    st.warning('Prototype access: authentication is not enabled in this public demonstration. Do not use this version for confidential or operational submissions.')


def set_kyc(data): st.session_state.kyc=data

def set_txn(data): st.session_state.txn=data


def applicant_portal():
    st.subheader('Applicant Portal')
    tabs=st.tabs(['👤 KYC & Applicant','💱 Transaction & Classification','📎 Documents & Declarations','📋 My Applications','⚖️ Rules Pre-Check'])

    with tabs[0]:
        st.markdown('<div class="section">1. Customer / Applicant Identification</div>',unsafe_allow_html=True)
        applicant_type=st.radio('Applicant type *',['Individual','Company / Legal Person','Partnership / Trust / Other Legal Arrangement'],horizontal=True)
        c1,c2,c3=st.columns(3)
        if applicant_type=='Individual':
            first=c1.text_input('First / Given Name *',value=st.session_state.get('kyc',{}).get('first',''))
            middle=c2.text_input('Middle Name',value=st.session_state.get('kyc',{}).get('middle',''))
            last=c3.text_input('Surname / Family Name *',value=st.session_state.get('kyc',{}).get('last',''))
            full_name=' '.join([x for x in [first,middle,last] if x]).strip()
            company_name=''; registration_no=''
            c1,c2,c3=st.columns(3)
            id_type=c1.selectbox('Identity Document *',['National ID','Passport','Driver’s Licence','Other'])
            id_no=c2.text_input('ID / Passport Number *')
            nationality=c3.selectbox('Nationality *',countries,index=countries.index('Zimbabwe') if 'Zimbabwe' in countries else 0)
            c1,c2,c3=st.columns(3)
            dob=c1.date_input('Date of Birth *',value=date(1990,1,1),min_value=date(1900,1,1),max_value=date.today())
            birth_place=c2.text_input('Place of Birth')
            tax_id=c3.text_input('Tax / ZIMRA Number')
            occupation=st.text_input('Occupation / Position')
        else:
            full_name=''; first=middle=last=''; id_type=id_no=''; nationality=''; dob=None; birth_place=''; occupation=''
            c1,c2=st.columns(2)
            company_name=c1.text_input('Registered Legal Name *')
            registration_no=c2.text_input('Company / Registration Number *')
            c1,c2,c3=st.columns(3)
            incorporation=c1.date_input('Date of Incorporation',value=date(2015,1,1),min_value=date(1900,1,1),max_value=date.today())
            tax_id=c2.text_input('Corporate Tax / ZIMRA Number')
            legal_form=c3.selectbox('Legal Form',['Private Limited Company','Public Company','Partnership','Trust','Other Legal Arrangement'])
            business_description=st.text_area('Nature / Principal Business Activity *')
            registered_address=st.text_area('Registered Address *')
            directors=st.text_area('Directors / Trustees / Controlling Persons *',help='List full names and roles; separate persons with semicolons.')
            full_name=company_name
            id_no=''; nationality=''; dob=None; birth_place=''; occupation=''
        c1,c2=st.columns(2)
        email=c1.text_input('Email Address *')
        phone=c2.text_input('Telephone / Mobile Number *')
        c1,c2=st.columns(2)
        address=c1.text_area('Residential / Contact Address *')
        postal=c2.text_input('Postal Address')
        st.markdown('<div class="subsection">Ultimate Beneficial Owner(s)</div>',unsafe_allow_html=True)
        st.caption('For a company/legal arrangement, provide the natural person(s) who ultimately own or control the customer/arrangement. Multiple rows can be entered.')
        default_ubo=pd.DataFrame([{'Full Name':'','Nationality':'','ID/Passport':'','Ownership %':0.0,'Control / Role':''}])
        ubo_df=st.data_editor(default_ubo,num_rows='dynamic',use_container_width=True,key='ubo_editor')
        beneficial_owner='; '.join([str(x).strip() for x in ubo_df['Full Name'].tolist() if str(x).strip()])
        if applicant_type=='Individual' and not beneficial_owner: beneficial_owner=full_name
        st.markdown('<div class="subsection">Source of Funds / Wealth & Relationship</div>',unsafe_allow_html=True)
        c1,c2=st.columns(2)
        source_funds=c1.text_area('Source of Funds *',help='Explain where the money for this specific transaction originates.')
        source_wealth=c2.text_area('Source of Wealth *',help='Explain the broader origin of the applicant’s wealth/assets.')
        expected_activity=st.text_area('Expected Nature / Purpose of Relationship and Expected Transaction Activity *')
        c1,c2,c3=st.columns(3)
        pep=c1.selectbox('Politically Exposed Person (PEP)? *',['No','Yes'])
        sanctions=c2.selectbox('Any sanctions / restricted-party concern known to applicant? *',['No','Yes'])
        adverse_media=c3.selectbox('Any material adverse legal/regulatory information? *',['No','Yes'])
        c1,c2=st.columns(2)
        representative_name=c1.text_input('Authorised Representative / Agent')
        representative_role=c2.text_input('Representative Capacity / Relationship')
        c1,c2=st.columns(2)
        identity_verified=c1.checkbox('I confirm that the identity information supplied is complete and can be supported by documentary evidence.')
        kyc_saved=st.button('Save Applicant / KYC Information',type='secondary')
        if kyc_saved:
            kyc={'applicant_type':applicant_type,'full_name':full_name,'first':first,'middle':middle,'last':last,'company_name':company_name,
                 'registration_no':registration_no,'id_type':id_type,'id_no':id_no,'nationality':nationality,'dob':str(dob) if dob else '',
                 'birth_place':birth_place,'tax_id':tax_id,'occupation':occupation,'legal_form':locals().get('legal_form',''),'incorporation':str(locals().get('incorporation','')),
                 'business_description':locals().get('business_description',''),'registered_address':locals().get('registered_address',''),
                 'directors':locals().get('directors',''),'email':email,'phone':phone,'address':address,'postal':postal,'beneficial_owner':beneficial_owner,
                 'ubo_rows':ubo_df.to_dict('records'),'source_funds':source_funds,'source_wealth':source_wealth,'expected_activity':expected_activity,
                 'pep':pep,'sanctions':sanctions,'adverse_media':adverse_media,'representative_name':representative_name,'representative_role':representative_role,
                 'identity_verified':identity_verified}
            set_kyc(kyc); st.success('KYC information saved for this application session.')
        if st.session_state.get('kyc'): st.success('KYC section has saved data in the current application session.')

    with tabs[1]:
        st.markdown('<div class="section">2. Transaction, Country, ISIC & Foreign Exchange</div>',unsafe_allow_html=True)
        kyc=st.session_state.get('kyc',{})
        c1,c2,c3=st.columns(3)
        direction=c1.selectbox('Capital-flow direction *',['Inflow','Outflow'])
        tx_type=c2.selectbox('Transaction Type *',['Foreign Direct Investment','Dividend Repatriation','External Borrowing','Loan Repayment','Disinvestment','Portfolio Investment','Intercompany Loan','Offshore Investment','Trade Payment','Royalty / Management Fee','Other Capital Transfer'])
        purpose_category=c3.selectbox('Purpose Category *',['Investment','Dividend / Profit Repatriation','Borrowing','Debt Service','Disinvestment','Portfolio Transaction','Intercompany Financing','Offshore Investment','Trade','Services / Royalties','Other'])
        purpose=st.text_area('Detailed Transaction Purpose / Economic Rationale *')
        country=st.selectbox('Counterparty / Destination Country *',countries,index=countries.index('Zimbabwe') if direction=='Inflow' and 'Zimbabwe' in countries else 0)
        st.markdown('<div class="subsection">Economic Activity — ISIC Rev.4</div>',unsafe_allow_html=True)
        sec_code=st.selectbox('ISIC Section *',list(isic_sections.keys()),format_func=lambda x:f'{x} — {isic_sections[x]}')
        divs=get_divisions(sec_code); div_code=st.selectbox('ISIC Division *',list(divs.keys()),format_func=lambda x:f'{x} — {divs[x]}') if divs else ''
        groups=get_groups(div_code); grp_code=st.selectbox('ISIC Group *',list(groups.keys()),format_func=lambda x:f'{x} — {groups[x]}') if groups else ''
        classes=get_classes(grp_code); class_code=st.selectbox('ISIC Class / Subsector *',list(classes.keys()),format_func=lambda x:f'{x} — {classes[x]}') if classes else ''
        st.markdown('<div class="subsection">Amount & Exchange Rate</div>',unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        currency_label=c1.selectbox('Transaction Currency *',currency_choices())
        cur_code=currency_code(currency_label)
        amount=c2.number_input('Transaction Amount *',min_value=0.0,step=1000.0,format='%.4f')
        fx_date=c3.date_input('FX Effective Date *',value=date.today())
        info=get_rate_info(cur_code,fx_date)
        if info['rate_to_usd'] is None: info=get_rate_info(cur_code)
        if info['rate_to_usd'] is not None:
            usd_amount=convert_to_usd(amount,cur_code,info['effective_date'])
            st.markdown(f'<div class="ok"><b>Automatic US$ conversion:</b> {amount:,.4f} {cur_code} → <b>US$ {usd_amount:,.2f}</b><br><span class="small">Rate to USD: {info["rate_to_usd"]:.10f} · Effective: {info["effective_date"]} · Source: {info["source"]}</span></div>',unsafe_allow_html=True)
        else:
            usd_amount=None
            st.warning(f'No approved FX rate is loaded for {cur_code} for the selected effective date. The application cannot complete the automated USD conversion until an authorised rate is loaded.')
        bank=st.selectbox('Authorised Dealer / Banking Institution *',banks)
        transaction_date=st.date_input('Proposed / Transaction Date *',value=date.today())
        linked=st.selectbox('Are there related/linked transactions? *',['No','Yes'])
        description=st.text_area('Additional Transaction Information')
        if st.button('Save Transaction Information',type='secondary'):
            txn={'direction':direction,'transaction_type':tx_type,'purpose_category':purpose_category,'purpose':purpose,'country':country,
                 'isic_section_code':sec_code,'isic_section_name':isic_sections.get(sec_code,''),'isic_division_code':div_code,'isic_division_name':divs.get(div_code,''),
                 'isic_group_code':grp_code,'isic_group_name':groups.get(grp_code,''),'isic_class_code':class_code,'isic_class_name':classes.get(class_code,''),
                 'currency':cur_code,'amount':amount,'usd_amount':usd_amount,'usd_rate':info['rate_to_usd'],'fx_effective_date':info['effective_date'],'fx_source':info['source'],
                 'bank':bank,'transaction_date':str(transaction_date),'linked_transactions':linked,'description':description}
            set_txn(txn); st.success('Transaction information saved for this application session.')
        if st.session_state.get('txn'): st.success('Transaction section has saved data in the current application session.')

    with tabs[2]:
        st.markdown('<div class="section">3. Supporting Documents & Applicant Declaration</div>',unsafe_allow_html=True)
        kyc=st.session_state.get('kyc',{}); txn=st.session_state.get('txn',{})
        req=required_documents(txn.get('transaction_type',''),kyc.get('applicant_type',''))
        st.markdown('<div class="note"><b>Document control:</b> each required document is associated with this application reference after submission. Actual files are stored in the application document repository in this development build.</div>',unsafe_allow_html=True)
        uploaded={}
        for i,item in enumerate(req):
            uploaded[item]=st.file_uploader(item,key=f'reqdoc_{i}',type=['pdf','doc','docx','xls','xlsx','csv','png','jpg','jpeg'])
        additional=st.file_uploader('Additional Supporting Documents',accept_multiple_files=True,key='additional_docs',type=['pdf','doc','docx','xls','xlsx','csv','png','jpg','jpeg'])
        declaration=st.checkbox('I certify that the information supplied is true, complete and not misleading and understand that further information may be requested.')
        if st.button('Submit Exchange Control Application',type='primary'):
            if not kyc or not txn: st.error('Complete and save the KYC and Transaction sections first.'); return
            missing=[]
            mandatory_individual=['email','phone','address','source_funds','source_wealth','expected_activity','beneficial_owner']
            if kyc.get('applicant_type')=='Individual': mandatory_individual += ['full_name','id_no','nationality']
            else: mandatory_individual += ['company_name','registration_no','registered_address','business_description','directors']
            for x in mandatory_individual:
                if not str(kyc.get(x,'' )).strip(): missing.append(x)
            if not kyc.get('identity_verified'): missing.append('identity confirmation')
            if not txn.get('purpose','').strip(): missing.append('transaction purpose')
            if not txn.get('usd_rate'): missing.append('approved FX rate')
            if not declaration: missing.append('applicant declaration')
            if missing: st.error('Submission blocked. Complete: '+', '.join(missing)); return
            app={**txn,**{k:kyc.get(k) for k in ['registration_no','bank','country','pep','sanctions','adverse_media','source_funds','source_wealth','beneficial_owner','identity_verified']}}
            result=validate_application(app)
            ref='EC-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3]
            record=(ref,kyc.get('full_name') or kyc.get('company_name'),kyc.get('applicant_type'),kyc.get('registration_no'),txn['transaction_type'],txn['direction'],txn['purpose'],txn['country'],
                    txn['isic_section_name'],txn['isic_section_code'],txn['isic_section_name'],txn['isic_division_code'],txn['isic_division_name'],txn['isic_group_code'],txn['isic_group_name'],txn['isic_class_code'],txn['isic_class_name'],
                    txn['currency'],txn['amount'],txn['usd_amount'],txn['usd_rate'],txn['fx_effective_date'],txn['fx_source'],txn['bank'],txn['transaction_date'],str(date.today()),'SUBMITTED',result['risk_score'],result['risk_level'],result['decision'],txn['description'],current_user()['username'],json.dumps(kyc),json.dumps(result))
            try:
                conn=get_conn(); conn.execute('''INSERT INTO applications(reference_no,applicant_name,applicant_type,registration_no,transaction_type,direction,purpose,country,sector,isic_section_code,isic_section_name,isic_division_code,isic_division_name,isic_group_code,isic_group_name,isic_class_code,isic_class_name,currency,amount,usd_amount,usd_rate,fx_effective_date,fx_source,bank,transaction_date,submission_date,status,risk_score,risk_level,compliance_decision,description,created_by,kyc_json,compliance_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',record); conn.commit(); conn.close()
                conn=get_conn(); conn.execute('INSERT INTO application_status_history(reference_no,status,changed_by,comment) VALUES(?,?,?,?)',(ref,'SUBMITTED',current_user()['username'],'Application submitted')); conn.commit(); conn.close()
                # Persist actual documents
                all_docs=[(name,f) for name,f in uploaded.items() if f is not None] + [('Additional',f) for f in (additional or [])]
                for doc_type,f in all_docs:
                    safe=re.sub(r'[^A-Za-z0-9_.-]','_',f.name); app_dir=os.path.join(DOC_DIR,ref); os.makedirs(app_dir,exist_ok=True); path=os.path.join(app_dir,safe)
                    data=f.getvalue(); open(path,'wb').write(data); digest=hashlib.sha256(data).hexdigest()
                    conn=get_conn(); conn.execute('INSERT INTO documents(reference_no,document_type,original_name,stored_path,uploaded_by,sha256,file_size) VALUES(?,?,?,?,?,?,?)',(ref,doc_type,f.name,path,current_user()['username'],digest,len(data))); conn.commit(); conn.close()
                audit(current_user()['username'],'SUBMIT_APPLICATION',ref,f"risk={result['risk_score']} level={result['risk_level']} decision={result['decision']}")
                st.success(f'Application submitted successfully. Reference: **{ref}**')
                if result['blocking']: st.error('Compliance information requiring attention: '+' | '.join(result['blocking']))
                if result['escalation']: st.warning('Enhanced-review indicators: '+' | '.join(result['escalation']))
                if result['flags']: st.info('Review flags: '+' | '.join(result['flags']))
                st.session_state.pop('kyc',None); st.session_state.pop('txn',None)
            except Exception as exc: st.error(f'Could not save the application: {exc}')

    with tabs[3]:
        conn=get_conn(); df=pd.read_sql_query('''SELECT reference_no,transaction_type,direction,amount,currency,usd_amount,status,risk_level,compliance_decision,submission_date FROM applications WHERE created_by=? ORDER BY id DESC''',conn,params=(current_user()['username'],)); conn.close()
        if df.empty: st.info('You have no submitted applications yet.')
        else: st.dataframe(df,use_container_width=True,hide_index=True)

    with tabs[4]:
        exchange_control_rules_portal(role='applicant', precheck=True)


def exchange_control_rules_portal(role='officer', precheck=False):
    """Interactive, explainable Exchange Control Rules Engine workspace."""
    st.markdown(
        '''<div class="rule-engine-banner">
          <div class="kicker">2 · Exchange Control Rules Engine</div>
          <h2>Regulatory Logic & Transaction Pre-Check</h2>
          <p>Evaluate transaction characteristics against configured Exchange Control, FXD5, import/export, KYC and workflow rules. Every result is explained and linked to its source.</p>
        </div>''',
        unsafe_allow_html=True,
    )
    st.warning("Decision-support only: the engine does not constitute legal advice, a formal Exchange Control determination, or an approval/rejection by any regulatory authority.")
    kyc0 = st.session_state.get('kyc', {}) if precheck else {}
    txn0 = st.session_state.get('txn', {}) if precheck else {}
    t1, t2, t3 = st.tabs(['🧪 Rule Tester', '📚 Rule Catalogue', '🔗 Regulatory Sources'])
    with t1:
        st.markdown('<div class="subsection">Transaction profile</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        direction = c1.selectbox('Capital-flow direction', ['Inflow','Outflow'], index=0 if txn0.get('direction','Inflow')=='Inflow' else 1, key=f're_dir_{role}_{precheck}')
        tx_options=['Foreign Direct Investment','Dividend Repatriation','External Borrowing','Loan Repayment','Disinvestment','Portfolio Investment','Intercompany Loan','Offshore Investment','Trade Payment','Royalty / Management Fee','Other Capital Transfer']
        tx_default=txn0.get('transaction_type','Trade Payment')
        tx_index=tx_options.index(tx_default) if tx_default in tx_options else tx_options.index('Trade Payment')
        tx=c2.selectbox('Transaction type', tx_options, index=tx_index, key=f're_tx_{role}_{precheck}')
        amount=c3.number_input('Transaction amount', min_value=0.0, value=float(txn0.get('amount') or 0), step=1000.0, key=f're_amt_{role}_{precheck}')
        c1,c2,c3 = st.columns(3)
        usd_amount=c1.number_input('US$ equivalent', min_value=0.0, value=float(txn0.get('usd_amount') or 0), step=1000.0, key=f're_usd_{role}_{precheck}')
        fx_rate=c2.number_input('FX rate to USD', min_value=0.0, value=float(txn0.get('usd_rate') or 0), format='%.10f', key=f're_fx_{role}_{precheck}')
        days=c3.number_input('Days since import payment', min_value=0, value=0, step=1, key=f're_days_{role}_{precheck}')
        st.markdown('<div class="subsection">Transaction-specific controls</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        importer_registered=c1.selectbox('Importer registered with relevant authority?', ['Unknown','Yes','No'], key=f're_imp_{role}_{precheck}')
        exporter_registered=c2.selectbox('Exporter registered?', ['Unknown','Yes','No'], key=f're_exp_{role}_{precheck}')
        export_declared=c3.selectbox('Export CD1 / CEPECS status', ['Unknown','Yes','No'], key=f're_cd1_{role}_{precheck}')
        c1,c2,c3 = st.columns(3)
        third_party=c1.selectbox('Third-party country payment?', ['Unknown','Yes','No'], key=f're_3p_{role}_{precheck}')
        retention=c2.number_input('Exporter FX retention (%)', min_value=0.0, max_value=100.0, value=70.0, step=1.0, key=f're_ret_{role}_{precheck}')
        linked=c3.selectbox('Linked transactions?', ['No','Yes'], key=f're_linked_{role}_{precheck}')
        st.markdown('<div class="subsection">KYC / AML controls</div>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        identity=c1.checkbox('Identity complete / verified', value=bool(kyc0.get('identity_verified')), key=f're_id_{role}_{precheck}')
        ubo=c2.checkbox('Beneficial ownership present', value=bool(kyc0.get('beneficial_owner')), key=f're_ubo_{role}_{precheck}')
        sof=c3.checkbox('Source of funds present', value=bool(kyc0.get('source_funds')), key=f're_sof_{role}_{precheck}')
        pep=c4.selectbox('PEP', ['No','Yes'], index=1 if kyc0.get('pep')=='Yes' else 0, key=f're_pep_{role}_{precheck}')
        c1,c2 = st.columns(2)
        sanctions=c1.selectbox('Sanctions concern declared', ['No','Yes'], index=1 if kyc0.get('sanctions')=='Yes' else 0, key=f're_san_{role}_{precheck}')
        adverse=c2.selectbox('Material adverse legal/regulatory information', ['No','Yes'], index=1 if kyc0.get('adverse_media')=='Yes' else 0, key=f're_adv_{role}_{precheck}')
        app={
            'direction':direction,'transaction_type':tx,'amount':amount,'usd_amount':usd_amount,'usd_rate':fx_rate,
            'days_since_payment':days if tx=='Trade Payment' and direction=='Outflow' else None,
            'importer_registered':importer_registered,'exporter_registered':exporter_registered,
            'export_declared_cd1':export_declared,'third_party_country_payment':third_party,
            'export_retention_pct':retention if tx=='Trade Payment' and direction=='Inflow' else None,
            'linked_transactions':linked,'identity_verified':identity,'beneficial_owner':ubo,
            'source_funds':sof,'pep':pep,'sanctions':sanctions,'adverse_media':adverse,
        }
        if st.button('Run Exchange Control Rules Engine', type='primary', key=f'run_rules_{role}_{precheck}'):
            result=evaluate_rules(app)
            st.session_state['last_rule_result']=result
            audit(current_user()['username'] if current_user() else 'anonymous','RULE_ENGINE_RUN',details=f"tx={tx};direction={direction};decision={result['decision']};score={result['risk_score']}")
        result=st.session_state.get('last_rule_result')
        if result:
            st.markdown('<div class="subsection">Engine outcome</div>', unsafe_allow_html=True)
            k1,k2,k3,k4,k5=st.columns(5)
            for col,v,l in [(k1,result['risk_score'],'Risk score'),(k2,result['risk_level'],'Risk level'),(k3,len(result['blocking']),'Blocks'),(k4,len(result['escalations']),'Escalations'),(k5,len(result['reviews']),'Reviews')]:
                col.markdown(f'<div class="engine-kpi"><div class="v">{v}</div><div class="l">{l}</div></div>',unsafe_allow_html=True)
            if result['decision']=='BLOCKED_PENDING_INFORMATION': st.error('Engine decision signal: BLOCKED_PENDING_INFORMATION')
            elif result['decision']=='ENHANCED_REVIEW': st.warning('Engine decision signal: ENHANCED_REVIEW')
            else: st.success('Engine decision signal: STANDARD_REVIEW')
            st.caption(result['disclaimer'])
            rows=[{'Rule':x['rule_id'],'Category':x['category'],'Rule title':x['title'],'Status':x['status'],'Severity':x['severity'],'Action':x['action'],'Explanation':x['explanation']} for x in result['results']]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            for x in result['results']:
                cls={'PASS':'rule-pass','REVIEW':'rule-review','BLOCK':'rule-block','ESCALATE':'rule-escalate','INFO':'rule-info','N/A':'rule-na'}.get(x['status'],'rule-na')
                st.markdown(f'''<div class="rule-card {cls}"><div class="rule-id">{x['rule_id']} · {x['category']} · {x['status']}</div><div class="rule-title">{x['title']}</div><div class="rule-explanation">{x['explanation']}</div><div class="rule-source">Source: {x['source_title']} · Effective: {x['effective_date']}</div></div>''',unsafe_allow_html=True)
            st.markdown('<div class="subsection">Transaction document checklist</div>', unsafe_allow_html=True)
            for doc in required_documents(tx, kyc0.get('applicant_type','')): st.markdown(f'- {doc}')
    with t2:
        catalog=rule_catalog()
        df=pd.DataFrame([{k:r[k] for k in ['rule_id','title','category','severity','action','effective_date','active']} for r in catalog])
        c1,c2,c3=st.columns(3)
        cat=c1.selectbox('Category', ['All']+sorted(df.category.unique()), key=f'rule_cat_{role}')
        sev=c2.multiselect('Severity', sorted(df.severity.unique()), default=sorted(df.severity.unique()), key=f'rule_sev_{role}')
        search=c3.text_input('Search rules', key=f'rule_search_{role}')
        view=df.copy()
        if cat!='All': view=view[view.category==cat]
        view=view[view.severity.isin(sev)]
        if search: view=view[view.apply(lambda row: search.lower() in ' '.join(map(str,row.values)).lower(),axis=1)]
        st.dataframe(view,use_container_width=True,hide_index=True)
        st.caption(f'{len(view)} rule(s) displayed · Engine version ECRE-2026.03')
    with t3:
        seen=set()
        for r in rule_catalog():
            if r['source_url'] in seen: continue
            seen.add(r['source_url'])
            st.markdown(f'**{r["source_title"]}**')
            st.markdown(f'<a class="resource-link" href="{r["source_url"]}" target="_blank">Open regulatory reference</a>', unsafe_allow_html=True)


def show_case(ref, role):
    conn=get_conn(); row=pd.read_sql_query('SELECT * FROM applications WHERE reference_no=?',conn,params=(ref,)); hist=pd.read_sql_query('SELECT status,changed_by,comment,changed_at FROM application_status_history WHERE reference_no=? ORDER BY id DESC',conn,params=(ref,)); docs=pd.read_sql_query('SELECT document_type,original_name,file_size,sha256,uploaded_by,uploaded_at FROM documents WHERE reference_no=? ORDER BY id DESC',conn,params=(ref,)); conn.close()
    if row.empty:return
    r=row.iloc[0]
    a,b,c,d=st.columns(4); a.metric('Transaction',f'{r.amount:,.2f} {r.currency}'); b.metric('US$ Equivalent',f'{r.usd_amount:,.2f}' if pd.notna(r.usd_amount) else '—'); c.metric('Risk',f'{r.risk_level} ({r.risk_score})'); d.metric('Status',r.status)
    st.write(f"**Applicant:** {r.applicant_name} · **Type:** {r.applicant_type}")
    st.write(f"**Transaction:** {r.transaction_type} · **Direction:** {r.direction} · **Country:** {r.country} · **Bank:** {r.bank}")
    st.write(f"**ISIC:** {r.isic_class_code} — {r.isic_class_name}")
    st.write(f"**FX:** {r.currency} → USD at {r.usd_rate} · Effective {r.fx_effective_date} · {r.fx_source}")
    with st.expander('KYC / Beneficial Ownership / Source of Funds',expanded=True):
        try: st.json(json.loads(r.kyc_json or '{}'))
        except Exception: st.write(r.kyc_json)
    with st.expander('Compliance Assessment',expanded=True):
        try:
            comp=json.loads(r.compliance_json or '{}'); st.json(comp)
        except Exception: st.write(r.compliance_json)
    with st.expander('Document Register',expanded=False): st.dataframe(docs,use_container_width=True,hide_index=True)
    with st.expander('Status History',expanded=False): st.dataframe(hist,use_container_width=True,hide_index=True)
    if role in {'officer','compliance','management'}:
        comment=st.text_area('Officer / Compliance comment',key=f'comment_{ref}')
        actions=['QUERY','UNDER REVIEW','REQUEST ENHANCED DUE DILIGENCE','REFER TO COMPLIANCE','RECOMMEND APPROVAL','RECOMMEND REJECTION']
        if role=='compliance': actions += ['COMPLIANCE CLEARED','COMPLIANCE ESCALATED']
        if role=='officer': actions += ['APPROVE','REJECT']
        if role=='management': actions += ['APPROVE','REJECT']
        action=st.selectbox('Workflow action',actions,key=f'action_{ref}')
        if st.button('Apply Workflow Action',type='primary',key=f'apply_{ref}'):
            new={'QUERY':'QUERIED','UNDER REVIEW':'UNDER REVIEW','REQUEST ENHANCED DUE DILIGENCE':'ENHANCED DUE DILIGENCE','REFER TO COMPLIANCE':'REFERRED TO COMPLIANCE','RECOMMEND APPROVAL':'RECOMMENDED','RECOMMEND REJECTION':'RECOMMENDED','APPROVE':'APPROVED','REJECT':'REJECTED','COMPLIANCE CLEARED':'COMPLIANCE CLEARED','COMPLIANCE ESCALATED':'COMPLIANCE ESCALATED'}[action]
            conn=get_conn(); conn.execute('UPDATE applications SET status=?,updated_at=CURRENT_TIMESTAMP WHERE reference_no=?',(new,ref)); conn.execute('INSERT INTO application_status_history(reference_no,status,changed_by,comment) VALUES(?,?,?,?)',(ref,new,current_user()['username'],comment or action));
            if comment: conn.execute('INSERT INTO application_comments(reference_no,comment,created_by) VALUES(?,?,?)',(ref,comment,current_user()['username']))
            conn.commit(); conn.close(); audit(current_user()['username'],'WORKFLOW_ACTION',ref,f'{action}: {comment}'); st.success(f'{ref} updated to {new}.'); st.rerun()


def rules_engine_module(role):
    """Dedicated Module 2 workspace, separate from the Application Portal UI."""
    catalog=rule_catalog(active_only=True)
    categories={}
    for r in catalog:
        categories[r['category']]=categories.get(r['category'],0)+1
    sources=len({r['source_url'] for r in catalog})

    st.markdown("""<div class="rules-shell"><div class="eyebrow">MODULE 2 · CAPITAL FLOWS · EXCHANGE CONTROL</div><h1>Exchange Control Rules Engine</h1><p>Institutional decision-support for testing transactions against configured Exchange Control rules, documenting the rule path, identifying missing information and routing cases for the appropriate level of review.</p><span class="rules-badge">ECRE-2026.03 · Versioned · Explainable · Source-linked</span></div>""",unsafe_allow_html=True)
    st.markdown('<div class="engine-note"><b>Control principle:</b> the engine provides a transparent decision-support signal. It does not replace an authorised officer, formal regulatory authority approval, legal interpretation, or applicable legislation/directives.</div>',unsafe_allow_html=True)
    st.write('')
    c1,c2,c3,c4=st.columns(4)
    for col,num,label,note in [(c1,len(catalog),'Active rules','Configured and enabled'),(c2,len(categories),'Rule domains','Imports, exports, FX, KYC/AML and reporting'),(c3,sources,'Regulatory sources','Regulatory reference links'),(c4,'ECRE 2026.03','Engine version','Current configured ruleset')]:
        col.markdown(f'<div class="rule-module-kpi"><div class="num">{num}</div><div class="label">{label}</div><div class="note">{note}</div></div>',unsafe_allow_html=True)
    st.markdown('### Decision workflow')
    fcols=st.columns(4)
    flow=[('01','INGEST','Capture transaction, KYC, counterparty, currency and supporting information.'),('02','CLASSIFY','Determine direction, transaction type, regulatory domain and relevant conditions.'),('03','TEST','Run active rules and record PASS, REVIEW, BLOCK, ESCALATE, INFO or N/A.'),('04','ROUTE','Produce an explainable decision signal, evidence checklist and review path.')]
    for col,(step,title,desc) in zip(fcols,flow):
        col.markdown(f'<div class="flow-card"><div class="step">STEP {step}</div><div class="title">{title}</div><div class="desc">{desc}</div></div>',unsafe_allow_html=True)
    st.markdown('### Rule domains')
    cat_desc={'Imports':'Importer registration, payment route and delivery/service period controls.','Exports':'Exporter registration, declaration and export-proceeds controls.','Foreign Payments':'Third-country and other foreign-payment controls.','Foreign Exchange':'FX-rate and conversion controls.','Reporting':'CEBAS/statistical and exchange-control reporting controls.','KYC / AML':'Identity, beneficial ownership, source-of-funds and enhanced-review controls.'}
    cols=st.columns(3)
    for i,(cat,count) in enumerate(sorted(categories.items())):
        cols[i%3].markdown(f'<div class="rule-category-card"><span class="count">{count}</span><div class="cat">{cat}</div><div class="desc">{cat_desc.get(cat,"Configured Exchange Control control domain.")}</div></div>',unsafe_allow_html=True)
    st.markdown('### Module navigation')
    nav=st.radio('Rules Engine workspace',['Overview','Live Rule Test','Rule Library','Regulatory Map','Decision & Audit'],horizontal=True,key=f'rules_nav_{role}')
    if nav=='Live Rule Test':
        st.markdown('#### Live Rule Test')
        exchange_control_rules_portal(role=role,precheck=(role=='applicant'))
    elif nav=='Rule Library':
        st.markdown('#### Rule Library')
        df=pd.DataFrame([{k:r[k] for k in ['rule_id','title','category','severity','action','effective_date','active']} for r in catalog])
        a,b,c=st.columns(3)
        search=a.text_input('Search rule ID / title / text',key=f'lib_search_{role}')
        cat=b.selectbox('Domain',['All']+sorted(df.category.unique()),key=f'lib_cat_{role}')
        sev=c.multiselect('Severity',sorted(df.severity.unique()),default=sorted(df.severity.unique()),key=f'lib_sev_{role}')
        view=df.copy()
        if cat!='All': view=view[view.category==cat]
        view=view[view.severity.isin(sev)]
        if search: view=view[view.apply(lambda row: search.lower() in ' '.join(map(str,row.values)).lower(),axis=1)]
        st.dataframe(view,use_container_width=True,hide_index=True)
        st.caption(f'{len(view)} of {len(df)} active rules displayed.')
    elif nav=='Regulatory Map':
        st.markdown('#### Regulatory Map')
        grouped={}
        for r in catalog: grouped.setdefault(r['source_title'],[]).append(r)
        for source,rules in grouped.items():
            with st.expander(f'{source} · {len(rules)} linked rule(s)',expanded=True):
                st.markdown(f'<a class="resource-link" href="{rules[0]["source_url"]}" target="_blank">Open regulatory reference</a>',unsafe_allow_html=True)
                for r in rules:
                    st.markdown(f'**{r["rule_id"]} — {r["title"]}** · {r["severity"]} · {r["action"]}')
                    st.caption(r['description'])
    elif nav=='Decision & Audit':
        st.markdown('#### Decision & Audit Trail')
        conn=get_conn()
        logs=pd.read_sql_query("SELECT event_at,username,action,reference_no,details FROM audit_log WHERE action LIKE '%RULE%' OR action LIKE '%APPLICATION%' ORDER BY id DESC LIMIT 250",conn)
        conn.close()
        st.dataframe(logs,use_container_width=True,hide_index=True)
        st.info('Every production decision should retain the tested inputs, ruleset version, triggered rules, explanations, officer action and supporting evidence.')
    else:
        st.markdown('### What Module 2 controls')
        c1,c2=st.columns([1.4,1])
        with c1:
            st.markdown("""**1. Regulatory applicability** — identify the relevant Exchange Control domain and transaction pathway.

**2. Transaction conditions** — test direction, transaction type, value, currency, country, counterparties and linked transactions.

**3. KYC / AML controls** — test identity, beneficial ownership, source of funds and enhanced-review indicators.

**4. Documentary evidence** — identify documents needed to support the transaction and explain gaps.

**5. Workflow routing** — convert rule results into a transparent review signal and retain the audit trail.""")
        with c2:
            st.markdown('#### Current ruleset')
            st.metric('Rules',len(catalog))
            st.metric('Regulatory sources',sources)
            st.metric('Engine status','ACTIVE')
            st.caption('Rules are versioned so future directives can be introduced without losing the historical ruleset used for earlier cases.')

def officer_portal(role):
    tabs=st.tabs(['📂 Case Management','⚖️ Exchange Control Rules Engine'])
    with tabs[0]:
        st.subheader('Exchange Control Case Management')
        conn=get_conn(); df=pd.read_sql_query('SELECT * FROM applications ORDER BY id DESC',conn); conn.close()
        if df.empty:
            st.info('No applications available.')
        else:
            c1,c2,c3,c4=st.columns(4)
            statuses=sorted(df.status.dropna().unique()); risks=sorted(df.risk_level.dropna().unique())
            sf=c1.multiselect('Status',statuses,default=statuses); rf=c2.multiselect('Risk',risks,default=risks); search=c3.text_input('Search reference / applicant'); decision=c4.multiselect('Compliance decision',sorted(df.compliance_decision.dropna().unique()),default=sorted(df.compliance_decision.dropna().unique()))
            view=df[df.status.isin(sf)&df.risk_level.isin(rf)&df.compliance_decision.isin(decision)].copy()
            if search: view=view[view.reference_no.astype(str).str.contains(search,case=False,na=False)|view.applicant_name.astype(str).str.contains(search,case=False,na=False)]
            st.dataframe(view[['reference_no','applicant_name','transaction_type','direction','amount','currency','usd_amount','risk_level','compliance_decision','status','submission_date']],use_container_width=True,hide_index=True)
            if not view.empty:
                ref=st.selectbox('Open Application',view.reference_no.tolist())
                show_case(ref,role)
    with tabs[1]:
        exchange_control_rules_portal(role=role)

def management_portal():
    tabs=st.tabs(['📊 Executive Dashboard','⚖️ Rules Engine'])
    with tabs[0]:
            st.subheader('Capital Flows Executive Dashboard')
            m=get_dashboard_metrics(); cols=st.columns(6)
            for col,(k,v) in zip(cols,m.items()): col.metric(k,v)
            c1,c2=st.columns(2)
            with c1: st.markdown('### Application Status'); st.dataframe(get_application_status(),use_container_width=True,hide_index=True)
            with c2:
                flow=get_monthly_flows(); st.markdown('### Monthly Capital Flows'); st.dataframe(flow,use_container_width=True,hide_index=True)
                if not flow.empty: st.line_chart(flow.set_index('month')[['inflows','outflows']])
            conn=get_conn(); apps=pd.read_sql_query('SELECT * FROM applications ORDER BY id DESC',conn); conn.close()
            st.download_button('Download Applications Excel',applications_to_excel(apps),'exchange_control_applications.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            st.divider(); indicator_admin(); st.divider(); st.markdown('### Exchange Rate Administration')
            label=st.selectbox('Currency',currency_choices()); code=currency_code(label); info=get_rate_info(code); rate=st.number_input('Rate: USD value of one unit of selected currency',min_value=0.0,value=float(info['rate_to_usd'] or 0.0),format='%.10f'); source=st.text_input('Rate source',value=info['source'] or 'Approved institutional source'); eff=st.date_input('Effective date',value=date.today())
            if st.button('Save Exchange Rate',type='primary'): save_fx_rate(code,rate,source,eff); audit(current_user()['username'],'UPDATE_FX_RATE',details=f'{code}={rate} effective={eff}'); st.success(f'Saved FX rate for {code}.')
            st.caption('The prototype stores an auditable rate/source/effective date. Any institutional deployment should replace manual loading with an approved rate feed and retain the complete historical time series.')
            st.divider(); st.markdown('### Audit Log')
            conn=get_conn(); logs=pd.read_sql_query('SELECT event_at,username,action,reference_no,details FROM audit_log ORDER BY id DESC LIMIT 500',conn); conn.close(); st.dataframe(logs,use_container_width=True,hide_index=True)
    with tabs[1]:
        exchange_control_rules_portal(role='management')


render_sidebar(); portal_header()
if 'user' not in st.session_state:
    about_section()
    login()
else:
    u=current_user(); t1,t2=st.columns([5,1]); t1.markdown(f'<div class="signed-in-banner">🔐 Signed in as <strong>{u["username"]}</strong> · <span>{u["role"]}</span></div>', unsafe_allow_html=True)
    if t2.button('Sign out'): audit(u['username'],'LOGOUT'); del st.session_state.user; st.session_state['system_module']='1 · Application & Case Portal'; st.rerun()
    selected_module=st.session_state.get('system_module','1 · Application & Case Portal')
    if selected_module.startswith('2 ·'):
        rules_engine_module(u['role'])
    else:
        about_section()
        if u['role']=='applicant': applicant_portal()
        elif u['role'] in {'officer','compliance'}: officer_portal(u['role'])
        else: management_portal()
