import io
import pandas as pd

def applications_to_excel(df):
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as writer:
        df.to_excel(writer,index=False,sheet_name='Applications')
        if 'status' in df:
            df.groupby('status',dropna=False).size().reset_index(name='applications').to_excel(writer,index=False,sheet_name='Status Summary')
        if 'risk_level' in df:
            df.groupby('risk_level',dropna=False).size().reset_index(name='applications').to_excel(writer,index=False,sheet_name='Risk Summary')
    return out.getvalue()
