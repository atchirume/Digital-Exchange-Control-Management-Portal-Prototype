from datetime import date
from database import get_conn

SEEDED = {
    'USD': (1.0,'Reference interbank / USD base','2026-09-24'),
    'ZWG': (1/26.6347,'Reference interbank average','2026-09-24'),
    'GBP': (1/35.2684,'Reference interbank average','2026-09-24'),
    'EUR': (1/30.3236,'Reference interbank average','2026-09-24'),
    'ZAR': (0.6145/26.6347,'Reference interbank average; derived from ZWG/ZAR','2026-09-24'),
    'BWP': (1.9643/26.6347,'Reference interbank average; derived from BWP/ZWG','2026-09-24'),
}


def seed_fx_rates():
    conn=get_conn(); c=conn.cursor()
    for cur,(rate,source,effective) in SEEDED.items():
        c.execute('''INSERT OR IGNORE INTO fx_rates(currency,rate_to_usd,source,effective_date)
                     VALUES(?,?,?,?)''',(cur,rate,source,effective))
    conn.commit(); conn.close()


def ensure_currency_rows(currency_items):
    conn=get_conn(); c=conn.cursor()
    for code,_ in currency_items:
        c.execute('INSERT OR IGNORE INTO fx_rates(currency,rate_to_usd,source,effective_date) VALUES(?,?,?,?)',
                  (code,None,'Not yet loaded',''))
    conn.commit(); conn.close()


def get_rate_to_usd(currency, effective_date=None):
    conn=get_conn()
    if effective_date:
        row=conn.execute('''SELECT rate_to_usd FROM fx_rates WHERE currency=? AND effective_date=?''',(currency,str(effective_date))).fetchone()
    else:
        row=conn.execute('SELECT rate_to_usd FROM fx_rates WHERE currency=?',(currency,)).fetchone()
    conn.close(); return float(row['rate_to_usd']) if row and row['rate_to_usd'] is not None else None


def get_rate_info(currency, effective_date=None):
    conn=get_conn()
    if effective_date:
        row=conn.execute('SELECT rate_to_usd,source,effective_date FROM fx_rates WHERE currency=? AND effective_date=?',(currency,str(effective_date))).fetchone()
    else:
        row=conn.execute('SELECT rate_to_usd,source,effective_date FROM fx_rates WHERE currency=?',(currency,)).fetchone()
    conn.close()
    if not row: return {'rate_to_usd':None,'source':None,'effective_date':None}
    return {'rate_to_usd':float(row['rate_to_usd']) if row['rate_to_usd'] is not None else None,'source':row['source'],'effective_date':row['effective_date']}


def convert_to_usd(amount,currency,effective_date=None):
    rate=get_rate_to_usd(currency,effective_date)
    if amount is None or rate is None or rate<=0: return None
    return float(amount)*rate


def save_fx_rate(currency,rate,source,effective_date=None):
    effective=str(effective_date or date.today())
    conn=get_conn()
    # One current row per currency for the V3 prototype; institutional version should retain a full time series.
    conn.execute('''INSERT INTO fx_rates(currency,rate_to_usd,source,effective_date)
                    VALUES(?,?,?,?)
                    ON CONFLICT(currency) DO UPDATE SET rate_to_usd=excluded.rate_to_usd,
                    source=excluded.source,effective_date=excluded.effective_date,
                    updated_at=CURRENT_TIMESTAMP''',(currency,float(rate),source,effective))
    conn.commit(); conn.close()
