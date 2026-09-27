import os, csv, io
try:
    import pycountry
except Exception:
    pycountry=None


def _countries():
    if pycountry:
        vals=sorted({c.name for c in pycountry.countries})
        vals=[v for v in vals if v!='Zimbabwe']
        return ['Zimbabwe']+vals
    return ['Zimbabwe','South Africa','Zambia','Botswana','Mozambique','United Kingdom','United States','China','United Arab Emirates','India']


def _currencies():
    data=[]
    if pycountry:
        for c in pycountry.currencies:
            data.append((c.alpha_3,c.name))
    extra=[('ZWG','Zimbabwe Gold (ZiG)'),('USD','United States dollar'),('EUR','Euro'),('GBP','Pound sterling'),('ZAR','South African rand'),('BWP','Botswana pula')]
    merged={code:name for code,name in data}
    for code,name in extra: merged[code]=name
    return sorted(merged.items())

countries=_countries()
currency_items=_currencies()

def currency_choices(): return [f'{code} — {name}' for code,name in currency_items]

def currency_code(choice): return choice.split(' — ',1)[0]

banks=[
'AFC Commercial Bank Limited','BancABC Zimbabwe Limited','CBZ Bank Limited','Ecobank Zimbabwe Limited',
'FBC Bank Limited','FBC Crown Bank Limited','First Capital Bank Zimbabwe Limited','Metbank Limited',
'Nedbank Zimbabwe Limited','NMB Bank Limited','Stanbic Bank Zimbabwe Limited','TN CyberTech Bank Limited',
'ZB Bank Limited','Central Africa Building Society (CABS)','National Building Society (NBS)',
"People's Own Savings Bank (POSB)",'African Century Limited','EmpowerBank Limited','GetBucks Microfinance Bank Limited',
'InnBucks Microbank Limited','Success Microfinance Bank','Zimbabwe Women’s Microfinance Bank Limited',
'Mukuru Financial Services Zimbabwe Limited','Infrastructure and Development Bank of Zimbabwe (IDBZ)',
'Small and Medium Enterprises Development Corporation (SMEDCO)','AFC Land & Development Bank of Zimbabwe Limited'
]

ISIC_URL='https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_4_english_structure.Txt'
ISIC_CACHE=os.path.join(os.path.dirname(__file__),'data','isic_rev4.txt')
FALLBACK_SECTIONS={'A':'Agriculture, forestry and fishing','B':'Mining and quarrying','C':'Manufacturing','D':'Electricity, gas, steam and air conditioning supply','E':'Water supply; sewerage, waste management and remediation activities','F':'Construction','G':'Wholesale and retail trade; repair of motor vehicles and motorcycles','H':'Transportation and storage','I':'Accommodation and food service activities','J':'Information and communication','K':'Financial and insurance activities','L':'Real estate activities','M':'Professional, scientific and technical activities','N':'Administrative and support service activities','O':'Public administration and defence; compulsory social security','P':'Education','Q':'Human health and social work activities','R':'Arts, entertainment and recreation','S':'Other service activities','T':'Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use','U':'Activities of extraterritorial organizations and bodies'}

# Preferred source: ISIC4Kit, which packages the Rev.4 hierarchy locally.
# This gives the portal all 21 sections, 88 divisions, 238 groups and 419 classes
# without relying on a live internet request during normal application use.
def _load_from_isic4kit():
    try:
        from isic4kit import ISIC4Classifier
        clf=ISIC4Classifier(language='en')
        rows=[]
        for letter in 'ABCDEFGHIJKLMNOPQRSTU':
            try: sec=clf.get_section(letter)
            except Exception: continue
            sc=str(sec.code).upper(); rows.append((sc,str(sec.description)))
            for div in getattr(sec,'divisions',[]):
                dc=str(div.code).zfill(2); rows.append((dc,str(div.description)))
                for grp in getattr(div,'groups',[]):
                    gc=str(grp.code).zfill(3); rows.append((gc,str(grp.description)))
                    for cls in getattr(grp,'classes',[]):
                        cc=str(cls.code).zfill(4); rows.append((cc,str(cls.description)))
        if len(rows)>=700: return rows
    except Exception:
        pass
    return None

def _load_from_un_csv():
    os.makedirs(os.path.dirname(ISIC_CACHE),exist_ok=True)
    text=None
    if os.path.exists(ISIC_CACHE):
        try: text=open(ISIC_CACHE,encoding='utf-8').read()
        except Exception: text=None
    if text is None:
        try:
            import urllib.request
            with urllib.request.urlopen(ISIC_URL,timeout=12) as r: text=r.read().decode('utf-8')
            open(ISIC_CACHE,'w',encoding='utf-8').write(text)
        except Exception: text=None
    if text:
        rows=[]
        for line in text.splitlines():
            line=line.strip()
            if not line or line.lower().startswith('code'): continue
            parts=line.split('\t')
            if len(parts)>=2: rows.append((parts[0].strip(),parts[1].strip()))
            else:
                p=line.split('  ',1)
                if len(p)==2: rows.append((p[0].strip(),p[1].strip()))
        if len(rows)>=700: return rows
    return None

def _load_isic():
    rows=_load_from_isic4kit()
    if rows: return rows
    rows=_load_from_un_csv()
    if rows: return rows
    return list(FALLBACK_SECTIONS.items())

_rows=_load_isic()
def _hierarchy(rows):
    sec=None; div=None; grp=None
    out={'sections':{},'divisions':{},'groups':{},'classes':{}}
    for code,name in rows:
        if len(code)==1 and code.isalpha(): sec=code.upper(); out['sections'][sec]=name
        elif len(code)==2 and code.isdigit() and sec: div=code; out['divisions'].setdefault(sec,{})[div]=name
        elif len(code)==3 and code.isdigit() and div: grp=code; out['groups'].setdefault(div,{})[grp]=name
        elif len(code)==4 and code.isdigit() and grp: out['classes'].setdefault(grp,{})[code]=name
    if len(out['sections'])<21: out['sections']=FALLBACK_SECTIONS
    return out

H=_hierarchy(_rows)
isic_sections=H['sections']
def get_divisions(s): return H['divisions'].get(s,{})
def get_groups(d): return H['groups'].get(d,{})
def get_classes(g): return H['classes'].get(g,{})
