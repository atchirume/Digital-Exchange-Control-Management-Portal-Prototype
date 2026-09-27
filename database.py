import sqlite3, os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "exchange_control.db",
)
DOC_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "documents",
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DOC_DIR, exist_ok=True)

    conn = get_conn()
    c = conn.cursor()

    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS applications(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          reference_no TEXT UNIQUE NOT NULL,
          applicant_name TEXT NOT NULL,
          applicant_type TEXT,
          registration_no TEXT,
          transaction_type TEXT,
          direction TEXT,
          purpose TEXT,
          country TEXT,
          sector TEXT,
          isic_section_code TEXT,
          isic_section_name TEXT,
          isic_division_code TEXT,
          isic_division_name TEXT,
          isic_group_code TEXT,
          isic_group_name TEXT,
          isic_class_code TEXT,
          isic_class_name TEXT,
          currency TEXT,
          amount REAL,
          usd_amount REAL,
          usd_rate REAL,
          fx_effective_date TEXT,
          fx_source TEXT,
          bank TEXT,
          transaction_date TEXT,
          submission_date TEXT,
          status TEXT,
          risk_score INTEGER DEFAULT 0,
          risk_level TEXT,
          compliance_decision TEXT,
          description TEXT,
          created_by TEXT,
          kyc_json TEXT,
          compliance_json TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS application_status_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          reference_no TEXT,
          status TEXT,
          changed_by TEXT,
          comment TEXT,
          changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS application_comments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          reference_no TEXT,
          comment TEXT,
          created_by TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS documents(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          reference_no TEXT NOT NULL,
          document_type TEXT,
          original_name TEXT,
          stored_path TEXT,
          uploaded_by TEXT,
          uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          sha256 TEXT,
          file_size INTEGER
        );

        CREATE TABLE IF NOT EXISTS reference_values(
          category TEXT,
          value TEXT,
          active INTEGER DEFAULT 1,
          PRIMARY KEY(category,value)
        );

        CREATE TABLE IF NOT EXISTS fx_rates(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          currency TEXT UNIQUE,
          rate_to_usd REAL,
          source TEXT,
          effective_date TEXT,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT,
          action TEXT,
          reference_no TEXT,
          details TEXT,
          event_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS compliance_rules(
          rule_id TEXT PRIMARY KEY,
          rule_name TEXT,
          description TEXT,
          active INTEGER DEFAULT 1,
          severity TEXT,
          action TEXT
        );

        CREATE TABLE IF NOT EXISTS exchange_control_rule_registry(
          rule_id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          category TEXT,
          severity TEXT,
          action TEXT,
          description TEXT,
          source_title TEXT,
          source_url TEXT,
          effective_date TEXT,
          active INTEGER DEFAULT 1,
          version TEXT DEFAULT 'ECRE-2026.03',
          updated_by TEXT,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS portal_indicators(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          indicator_key TEXT UNIQUE NOT NULL,
          label TEXT NOT NULL,
          value TEXT,
          unit TEXT,
          display_date TEXT,
          source TEXT,
          active INTEGER DEFAULT 1,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    conn.commit()
    conn.close()


def seed_reference_data():
    conn = get_conn()
    c = conn.cursor()

    txs = [
        "Foreign Direct Investment",
        "Dividend Repatriation",
        "External Borrowing",
        "Loan Repayment",
        "Disinvestment",
        "Portfolio Investment",
        "Intercompany Loan",
        "Offshore Investment",
        "Trade Payment",
        "Royalty / Management Fee",
        "Other Capital Transfer",
    ]

    purposes = [
        "Investment",
        "Dividend / Profit Repatriation",
        "Borrowing",
        "Debt Service",
        "Disinvestment",
        "Portfolio Transaction",
        "Intercompany Financing",
        "Offshore Investment",
        "Trade",
        "Services / Royalties",
        "Other",
    ]

    for value in txs:
        c.execute(
            "INSERT OR IGNORE INTO reference_values(category,value) "
            "VALUES('transaction_type',?)",
            (value,),
        )

    for value in purposes:
        c.execute(
            "INSERT OR IGNORE INTO reference_values(category,value) "
            "VALUES('purpose_category',?)",
            (value,),
        )

    rules = [
        (
            "KYC-001",
            "Customer identification",
            "Identity and core customer information must be captured before submission.",
            "High",
            "BLOCK",
        ),
        (
            "KYC-002",
            "Beneficial ownership",
            "Beneficial-owner information must be captured for legal persons/arrangements.",
            "High",
            "BLOCK",
        ),
        (
            "AML-001",
            "Source of funds",
            "Source-of-funds information is required for risk assessment.",
            "High",
            "BLOCK",
        ),
        (
            "AML-002",
            "PEP declaration",
            "PEP status requires compliance review and risk-sensitive handling.",
            "High",
            "ESCALATE",
        ),
        (
            "AML-003",
            "Sanctions declaration",
            "Potential sanctions concerns require compliance review.",
            "Critical",
            "ESCALATE",
        ),
        (
            "AML-004",
            "Unusual/large transaction",
            "Complex, unusual or large transactions require attention and documented review.",
            "Medium",
            "ESCALATE",
        ),
        (
            "FX-001",
            "FX rate availability",
            "A valid effective-date FX rate is required to compute the USD equivalent.",
            "Medium",
            "BLOCK",
        ),
    ]

    for rid, name, description, severity, action in rules:
        c.execute(
            """
            INSERT OR IGNORE INTO compliance_rules
            (rule_id,rule_name,description,severity,action)
            VALUES(?,?,?,?,?)
            """,
            (rid, name, description, severity, action),
        )

    # Seed the richer Exchange Control Rules Engine registry.
    try:
        from rules_engine import rule_catalog
        for rr in rule_catalog():
            c.execute(
                """
                INSERT OR IGNORE INTO exchange_control_rule_registry
                (rule_id,title,category,severity,action,description,source_title,source_url,effective_date,active,version)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (rr['rule_id'], rr['title'], rr['category'], rr['severity'], rr['action'],
                 rr['description'], rr['source_title'], rr['source_url'], rr['effective_date'],
                 rr.get('active',1), 'ECRE-2026.03'),
            )
    except Exception:
        # Database initialisation must remain available even if the rule module
        # is unavailable during an early bootstrap/import.
        pass

    indicators = [
        (
            "inflation_yoy",
            "ZiG Annual Inflation",
            "3.7",
            "%",
            "September 2026",
            "Configured portal reference value",
        ),
        (
            "policy_rate",
            "Bank Policy Rate",
            "30",
            "%",
            "September 2026",
            "Configured portal reference value",
        ),
        (
            "usd_zwg",
            "USD / ZWG Exchange Rate",
            "26.1",
            "ZWG per USD",
            "24 September 2026",
            "Configured portal reference value",
        ),
    ]

    for row in indicators:
        c.execute(
            """
            INSERT OR IGNORE INTO portal_indicators
            (indicator_key,label,value,unit,display_date,source)
            VALUES (?,?,?,?,?,?)
            """,
            row,
        )

    conn.commit()
    conn.close()
