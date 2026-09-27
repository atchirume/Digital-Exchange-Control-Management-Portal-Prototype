import pandas as pd
from database import get_conn

def get_dashboard_metrics():
    conn=get_conn(); q=pd.read_sql_query('SELECT * FROM applications',conn); conn.close()
    if q.empty:return {'Applications':0,'Pending':0,'Approved':0,'Rejected':0,'Total US$ Value':'0','High Risk':0}
    pending=int(q.status.isin(['SUBMITTED','UNDER REVIEW','QUERIED','RECOMMENDED','ENHANCED DUE DILIGENCE','BLOCKED PENDING INFORMATION']).sum())
    return {'Applications':len(q),'Pending':pending,'Approved':int((q.status=='APPROVED').sum()),'Rejected':int((q.status=='REJECTED').sum()),
            'Total US$ Value':f"{q.usd_amount.fillna(0).sum():,.0f}",'High Risk':int((q.risk_level=='High').sum())}

def get_application_status():
    conn=get_conn(); d=pd.read_sql_query('SELECT status,COUNT(*) applications FROM applications GROUP BY status ORDER BY applications DESC',conn); conn.close(); return d

def get_monthly_flows():
    conn=get_conn(); d=pd.read_sql_query('''SELECT substr(submission_date,1,7) month,
      SUM(CASE WHEN direction='Inflow' THEN usd_amount ELSE 0 END) inflows,
      SUM(CASE WHEN direction='Outflow' THEN usd_amount ELSE 0 END) outflows
      FROM applications GROUP BY substr(submission_date,1,7) ORDER BY month''',conn); conn.close(); return d
