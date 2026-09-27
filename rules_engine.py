"""Digital Exchange Control Rules Engine — Prototype.

This module is a transparent decision-support layer. It applies configured,
traceable rules to an exchange-control transaction and returns an explanation
for every rule. It is not a substitute for legal interpretation, officer
judgement, or a formal regulatory determination.
"""
from datetime import date

RBZ_HOME = "https://www.rbz.co.zw/"
REG_FRAMEWORK = "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management/regulatory-framework"
DIRECTIVES = "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management/directives-circulars-and-orders"
FXD5 = "https://www.rbz.co.zw/documents/Regulations_Acts/2026/Foreign_Exchange_Guidelines_FXD5_version_2._March_2026.pdf"
FXD5_2026 = "https://www.rbz.co.zw/documents/Regulations_Acts/2026/FOREIGN_EXCHANGE_DIRECTIVE_FXD5-2026_DATED_2_MARCH_2026.pdf"
IMPORTS = "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management/foreign-investment-trade-framework/103-imports-administration"
FOREIGN_TRADE = "https://www.rbz.co.zw/index.php/regulation-supervision/capital-flows-management/foreign-investment-trade-framework"


def _rule(rule_id, title, category, severity, action, description, source_title, source_url, effective_date="2026-03-02"):
    return {
        "rule_id": rule_id,
        "title": title,
        "category": category,
        "severity": severity,
        "action": action,
        "description": description,
        "source_title": source_title,
        "source_url": source_url,
        "effective_date": effective_date,
        "active": 1,
    }


RULE_CATALOG = [
    _rule("EC-001", "Importer registration", "Imports", "High", "REVIEW",
          "Importing companies must be registered with the Reserve Bank before effecting import payments through an Authorised Dealer.",
          "Foreign Investment & Trade Framework — Imports Administration", IMPORTS),
    _rule("EC-002", "Current-account import payment route", "Imports", "Medium", "INFO",
          "Foreign payments for imports of goods and services are described under the applicable framework as being effected through Authorised Dealers without prior Exchange Control approval, subject to the applicable framework.",
          "Foreign Investment & Trade Framework — Imports Administration", IMPORTS),
    _rule("EC-003", "Import delivery / service period", "Imports", "High", "REVIEW",
          "After an import payment, the importer has a stated grace period of up to 90 days to receive the goods or services; extensions may be sought where delivery/service provision is delayed.",
          "Foreign Investment & Trade Framework — Imports Administration", IMPORTS),
    _rule("EC-004", "Export declaration", "Exports", "High", "REVIEW",
          "The regulatory framework states that exports from Zimbabwe are declared on Form CD1 through the bank that raised the documentation in CEPECS.",
          "Foreign Investment & Trade Framework — Export Facilitation", FOREIGN_TRADE),
    _rule("EC-005", "Exporter registration", "Exports", "High", "REVIEW",
          "The regulatory framework states that exporters are required to register once with a bank using the prescribed exporter registration information.",
          "Foreign Investment & Trade Framework — Export Facilitation", FOREIGN_TRADE),
    _rule("EC-006", "Exporter foreign-currency retention", "Exports", "High", "REVIEW",
          "FXD5/2026 states that the foreign-currency retention threshold for exporters is 70% of gross export proceeds, with 30% sold at the prevailing applicable interbank rate.",
          "Foreign Exchange Directive FXD5/2026", FXD5_2026),
    _rule("EC-007", "Third-party country payment", "Foreign Payments", "Critical", "ESCALATE",
          "FXD5 states that third-party country payments require prior regulatory authority approval and supporting documentation.",
          "Foreign Exchange Transactions Guidelines — FXD5 Version 2.0", FXD5),
    _rule("EC-008", "Foreign payment reporting", "Reporting", "Medium", "INFO",
          "The regulatory framework states that banks report foreign payments on CEBAS for statistical and exchange-control accounting purposes.",
          "Foreign Investment & Trade Framework — Imports Administration", IMPORTS),
    _rule("EC-009", "FX rate availability", "Foreign Exchange", "High", "BLOCK",
          "A valid approved FX rate/effective date must be available before the portal can complete its automated USD-equivalent calculation.",
          "Prototype control — auditable FX administration", RBZ_HOME),
    _rule("KYC-001", "Identity completeness", "KYC / AML", "High", "BLOCK",
          "Customer identity information must be complete and supported by documentary evidence before submission.",
          "Portal KYC control / applicable AML-CFT framework", RBZ_HOME),
    _rule("KYC-002", "Beneficial ownership", "KYC / AML", "High", "BLOCK",
          "Legal persons and arrangements require beneficial-owner information sufficient for risk-sensitive review.",
          "Portal KYC control / applicable AML-CFT framework", RBZ_HOME),
    _rule("AML-001", "Source of funds", "KYC / AML", "High", "BLOCK",
          "Source-of-funds information is required for the portal's transaction-level compliance assessment.",
          "Portal KYC / compliance control", RBZ_HOME),
    _rule("AML-002", "PEP / sanctions / adverse information", "KYC / AML", "Critical", "ESCALATE",
          "A positive PEP, sanctions concern, or material adverse legal/regulatory declaration routes the case for enhanced compliance review.",
          "Portal compliance control", RBZ_HOME),
]


def rule_catalog(active_only=False):
    rows = [dict(x) for x in RULE_CATALOG]
    if active_only:
        rows = [x for x in rows if x.get("active")]
    return rows


def required_documents(tx, applicant_type=""):
    common = [
        "Identity / incorporation evidence",
        "Proof of residential / registered address",
        "Evidence supporting the transaction purpose",
        "Source-of-funds evidence",
    ]
    specific = {
        "Foreign Direct Investment": ["Investment/share subscription agreement", "Beneficial ownership / ownership structure evidence"],
        "Dividend Repatriation": ["Board/shareholder dividend resolution or declaration", "Financial statements / evidence of distributable profits", "Tax evidence where applicable"],
        "External Borrowing": ["Signed loan agreement", "Repayment schedule", "Lender and beneficial-owner information"],
        "Loan Repayment": ["Loan agreement", "Repayment statement / lender confirmation"],
        "Disinvestment": ["Sale/disinvestment agreement", "Evidence of original investment"],
        "Portfolio Investment": ["Investment statement / contract", "Counterparty details"],
        "Intercompany Loan": ["Intercompany loan agreement", "Group structure / beneficial ownership information"],
        "Offshore Investment": ["Investment proposal/agreement", "Beneficial ownership and counterparty information"],
        "Trade Payment": ["Commercial invoice", "Contract / purchase order where applicable"],
        "Royalty / Management Fee": ["Service/licence agreement", "Invoice and supporting evidence"],
    }
    extras = []
    if tx == "Trade Payment":
        extras += ["Importer registration evidence", "Evidence of supplier/counterparty details"]
    if tx == "Other Capital Transfer":
        extras += ["Detailed transaction justification", "Regulatory basis / supporting correspondence where applicable"]
    return common + specific.get(tx, ["Supporting transaction agreement / invoice"]) + extras


def _result(rule, status, explanation, triggered=False):
    return {
        **rule,
        "status": status,
        "triggered": triggered,
        "explanation": explanation,
    }


def evaluate_rules(app, active_only=True):
    """Evaluate an application/transaction dictionary and return explainable results."""
    a = dict(app or {})
    rules = rule_catalog(active_only=active_only)
    out = []

    direction = a.get("direction", "")
    tx = a.get("transaction_type", "")
    usd = float(a.get("usd_amount") or 0)
    importer_registered = a.get("importer_registered", "Unknown")
    exporter_registered = a.get("exporter_registered", "Unknown")
    export_declared = a.get("export_declared_cd1", "Unknown")
    third_party = a.get("third_party_country_payment", "Unknown")
    days = a.get("days_since_payment")
    fx_rate = a.get("usd_rate")
    identity_verified = bool(a.get("identity_verified"))
    beneficial_owner = bool(a.get("beneficial_owner"))
    source_funds = bool(a.get("source_funds"))
    pep = a.get("pep") == "Yes"
    sanctions = a.get("sanctions") == "Yes"
    adverse = a.get("adverse_media") == "Yes"

    for r in rules:
        rid = r["rule_id"]
        if rid == "EC-001":
            if tx != "Trade Payment" or direction != "Outflow":
                out.append(_result(r, "N/A", "This rule applies to outward trade/import payments."))
            elif importer_registered == "Yes":
                out.append(_result(r, "PASS", "Importer registration has been confirmed for this test."))
            elif importer_registered == "No":
                out.append(_result(r, "BLOCK", "Importer registration is not confirmed; obtain/verify registration before processing.", True))
            else:
                out.append(_result(r, "REVIEW", "Importer registration status is not captured; verify before processing.", True))

        elif rid == "EC-002":
            if tx != "Trade Payment" or direction != "Outflow":
                out.append(_result(r, "N/A", "This rule applies to outward trade/import payments."))
            else:
                out.append(_result(r, "INFO", "The public import framework describes import foreign payments through Authorised Dealers without prior Exchange Control approval, subject to the applicable rules."))

        elif rid == "EC-003":
            if tx != "Trade Payment" or direction != "Outflow":
                out.append(_result(r, "N/A", "This rule applies to outward trade/import payments."))
            elif days is None:
                out.append(_result(r, "REVIEW", "Days since payment were not supplied; confirm the 90-day delivery/service period where relevant.", True))
            elif float(days) <= 90:
                out.append(_result(r, "PASS", f"The stated period is {days} day(s), within the 90-day period."))
            else:
                out.append(_result(r, "REVIEW", f"The stated period is {days} day(s), beyond 90 days; confirm whether an extension has been obtained.", True))

        elif rid == "EC-004":
            if tx != "Trade Payment" or direction != "Inflow":
                out.append(_result(r, "N/A", "This rule is relevant to exports / inward trade proceeds."))
            elif export_declared == "Yes":
                out.append(_result(r, "PASS", "Export CD1/CEPECS declaration is marked complete."))
            elif export_declared == "No":
                out.append(_result(r, "REVIEW", "Export declaration is not confirmed; verify Form CD1/CEPECS treatment.", True))
            else:
                out.append(_result(r, "REVIEW", "Export declaration status is not captured; verify Form CD1/CEPECS treatment.", True))

        elif rid == "EC-005":
            if tx != "Trade Payment" or direction != "Inflow":
                out.append(_result(r, "N/A", "This rule is relevant to exporters."))
            elif exporter_registered == "Yes":
                out.append(_result(r, "PASS", "Exporter registration is marked complete."))
            elif exporter_registered == "No":
                out.append(_result(r, "REVIEW", "Exporter registration is not confirmed; verify registration before processing export proceeds.", True))
            else:
                out.append(_result(r, "REVIEW", "Exporter registration status is not captured; verify before processing.", True))

        elif rid == "EC-006":
            if tx != "Trade Payment" or direction != "Inflow":
                out.append(_result(r, "N/A", "This rule is relevant to exporter foreign-currency proceeds."))
            else:
                retention = a.get("export_retention_pct")
                if retention is None:
                    out.append(_result(r, "REVIEW", "Export retention percentage was not supplied; verify the applicable FXD5 retention treatment.", True))
                elif float(retention) <= 70:
                    out.append(_result(r, "PASS", f"Captured exporter retention is {retention:.2f}%, not above the stated 70% threshold."))
                else:
                    out.append(_result(r, "REVIEW", f"Captured exporter retention is {retention:.2f}%, above the stated 70% threshold; verify the transaction treatment.", True))

        elif rid == "EC-007":
            if third_party == "Yes":
                out.append(_result(r, "ESCALATE", "Third-party country payment identified: prior regulatory authority approval and supporting documentation should be verified.", True))
            elif third_party == "No":
                out.append(_result(r, "PASS", "Payment is marked as not being a third-party country payment."))
            else:
                out.append(_result(r, "REVIEW", "Third-party country payment status is not captured; verify the payment chain and ultimate beneficiary before processing.", True))

        elif rid == "EC-008":
            out.append(_result(r, "INFO", "Foreign payments are subject to the applicable reporting requirements; The regulatory framework states that banks report foreign payments on CEBAS."))

        elif rid == "EC-009":
            if fx_rate is not None and float(fx_rate) > 0:
                out.append(_result(r, "PASS", "A positive FX rate is available for the automated USD conversion."))
            else:
                out.append(_result(r, "BLOCK", "No valid FX rate is available for the selected currency/effective date.", True))

        elif rid == "KYC-001":
            out.append(_result(r, "PASS" if identity_verified else "BLOCK",
                                "Identity completeness is confirmed." if identity_verified else "Identity information is not marked complete/verified.",
                                not identity_verified))

        elif rid == "KYC-002":
            out.append(_result(r, "PASS" if beneficial_owner else "BLOCK",
                                "Beneficial ownership information is present." if beneficial_owner else "Beneficial ownership information is missing.",
                                not beneficial_owner))

        elif rid == "AML-001":
            out.append(_result(r, "PASS" if source_funds else "BLOCK",
                                "Source of funds is present." if source_funds else "Source of funds is missing.",
                                not source_funds))

        elif rid == "AML-002":
            if sanctions:
                out.append(_result(r, "ESCALATE", "Sanctions concern declared: stop routine processing and route to the appropriate compliance process.", True))
            elif pep or adverse:
                out.append(_result(r, "ESCALATE", "PEP/adverse-information indicator declared: enhanced compliance review is indicated.", True))
            else:
                out.append(_result(r, "PASS", "No PEP, sanctions or material adverse-information indicator has been declared."))

    blocking = [x for x in out if x["status"] == "BLOCK"]
    escalations = [x for x in out if x["status"] == "ESCALATE"]
    reviews = [x for x in out if x["status"] == "REVIEW"]
    passes = [x for x in out if x["status"] == "PASS"]
    infos = [x for x in out if x["status"] == "INFO"]

    # Transparent risk score: this is a workflow signal, not a legal conclusion.
    score = 0
    score += 40 * len(blocking)
    score += 25 * len(escalations)
    score += 10 * len(reviews)
    if usd >= 1_000_000:
        score += 20
    elif usd >= 250_000:
        score += 10
    score = min(100, score)
    level = "Low" if score < 25 else ("Medium" if score < 60 else "High")
    decision = "BLOCKED_PENDING_INFORMATION" if blocking else ("ENHANCED_REVIEW" if escalations or reviews else "STANDARD_REVIEW")

    return {
        "engine_version": "ECRE-2026.03",
        "evaluated_at": str(date.today()),
        "risk_score": score,
        "risk_level": level,
        "decision": decision,
        "blocking": blocking,
        "escalations": escalations,
        "reviews": reviews,
        "passes": passes,
        "info": infos,
        "results": out,
        "disclaimer": "Decision-support only. The Rules Engine does not constitute legal advice, a formal Exchange Control determination, or an approval/rejection by a regulatory authority.",
    }


# Backward-compatible function used by the application submission workflow.
def validate_application(app):
    result = evaluate_rules(app)
    return {
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "decision": result["decision"],
        "blocking": [x["explanation"] for x in result["blocking"]],
        "escalation": [x["explanation"] for x in result["escalations"]],
        "flags": [x["explanation"] for x in result["reviews"] + result["info"]],
        "engine_version": result["engine_version"],
        "rule_results": result["results"],
    }
