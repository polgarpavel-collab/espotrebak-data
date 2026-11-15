#!/usr/bin/env python3
"""eSpotřebák – denní generátor indexu tonerů a inkoustů pro vyhledávač (/najdi-nahradni-dil).

Vstupy:  feed e-shopu (heureka_cz.xml), předchozí index (toner-index.json), vyrazeno.txt (ITEM_ID, které se nesmí vrátit).
Výstupy: toner-index.json (veřejný, čte ho vyhledávač), report.json + report.md (co se změnilo, co nešlo spárovat).

Co dělá:
 1. Produkty z indexu, které ve feedu už nejsou (nebo jsou vyřazené), odebere.
 2. U zbylých obnoví název, cenu a obrázek z feedu.
 3. Nové tonery/inkousty z feedu přiřadí k tiskárnám podle kódu originálu (OEM kód jako CELÉ slovo, např. TN2420,
    CF259A, PG-545, CL-41). Kód se nikdy nehledá uvnitř jiného čísla (41 ≠ 4541B001). Nový produkt dostane stejné
    tiskárny jako produkty v indexu, které mají stejný kód. Co spárovat nejde, jde do reportu.
 4. Vyčistí seznam tiskáren: Canon modely zařazené pod HP, jméno značky zopakované v modelu, divné znaky,
    duplicity lišící se jen mezerou/pomlčkou/tečkou nebo předponou I-SENSYS.
 5. Do veřejného souboru nezapisuje kódy dodavatele (pole k) ani nic interního.

Nové TISKÁRNY se tu nevytvářejí – ty pocházejí z eLocatoru dodavatele (sběr pod přihlášením, viz esp-toner-generator-postup.md).

Použití: esp_toner_index.py <feed.xml nebo URL> <predchozi-index.json> <vystupni-slozka> [vyrazeno.txt]
"""
import sys, re, json, datetime, collections, urllib.request, io, os
import xml.etree.ElementTree as ET

CAT_RE = re.compile(r'^(Tonery a cartridge \| (Tonery – laserový tisk|Cartridge – inkoustový tisk)|Výprodej skladu \| Tonery a cartridge)')
BRANDS = ['HP', 'Canon', 'Epson', 'Brother', 'Lexmark', 'Xerox', 'Kyocera', 'Samsung', 'OKI', 'Ricoh', 'Sharp',
          'Konica Minolta', 'Minolta', 'Dell', 'Panasonic']
# barvy jako v indexu (pole col)
COLW = [('photo black', 'pbk'), ('matt black', 'mbk'), ('matte black', 'mbk'), ('light light black', 'lbk'),
        ('light black', 'lbk'), ('light cyan', 'lc'), ('light magenta', 'lm'), ('photo cyan', 'lc'),
        ('photo magenta', 'lm'), ('vivid magenta', 'm'), ('light gray', 'gy'), ('light grey', 'gy'), ('gray', 'gy'),
        ('grey', 'gy'), ('black', 'bk'), ('cyan', 'c'), ('magenta', 'm'), ('yellow', 'y'), ('red', 'r'),
        ('blue', 'b'), ('green', 'g'), ('orange', 'o')]
# tokeny, které nejsou kódy náplní (výtěžnost, objem, hmotnost, kusy, výkon…)
UNIT_RE = re.compile(r'^\d+(?:[.,]\d+)?(STR|STRAN|ML|L|G|KG|KS|PCS|W|MM|M|X)$')
MAX_TOKEN_SHARE = 40     # kód sdílený víc než 40 produkty v indexu není kód náplně (je to obecné slovo/řada)


def log(*a):
    print(*a, file=sys.stderr)


# ---------------------------------------------------------------- vstupy
def read_bytes(src):
    if re.match(r'^https?://', src):
        last = None
        for _ in range(3):
            try:
                req = urllib.request.Request(src, headers={'User-Agent': 'espotrebak-index/1'})
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.read()
            except Exception as e:  # síť na runneru občas zakolísá
                last = e
        raise last
    with open(src, 'rb') as f:
        return f.read()


def feed_items(raw):
    for _, e in ET.iterparse(io.BytesIO(raw)):
        if e.tag != 'SHOPITEM':
            continue
        it = {c.tag: (c.text or '').strip() for c in e}
        e.clear()
        yield it


def slug(url):
    return re.sub(r'^https?://[^/]+/', '', url).strip('/')


# ---------------------------------------------------------------- vlastnosti produktu
def colof(name):
    n = name.lower()
    if re.search(r'\bcmyk\b|black\s*/\s*colou?r|black\+colou?r|\bbk/cmy\b|\d-pack|multipack|\bsada\b', n):
        return 'set'
    if re.search(r'(?<![a-z])(tri-?colou?r|colou?r)(?![a-z])', n):
        return 'col'
    for w, c in COLW:
        if re.search(r'(?<![a-z])' + re.escape(w) + r'(?![a-z])', n):
            return c
    return None


def brand_of(cat, name, manuf):
    p = [x.strip() for x in cat.split('|')]
    if len(p) > 2 and p[2]:
        return p[2]
    for b in BRANDS:   # „UPrint kompatibilní toner s Brother TN2420“ → Brother
        if re.search(r'\b' + re.escape(b) + r'\b', name):
            return b
    return manuf or ''


def is_ink(cat, name):
    if 'Cartridge – inkoustový' in cat:
        return True
    if 'Tonery – laserový' in cat:
        return False
    return bool(re.search(r'\bink\b|inkoust', name, re.I)) and not re.search(r'toner', name, re.I)


def is_compatible(name):
    return bool(re.search(r'kompatibiln|renovovan|remanuf|repasovan|alternativ', name, re.I))


def code_tokens(name):
    """Kódy náplní z názvu jako celá slova, normalizované (bez pomlček a teček), např.
    'UPrint kompatibilní ink s PG40+CL41, C-40/41 PACK, black/color, 25+3x18ml' → {PG40, CL41, C40}
    'HP originální toner CF259A, HP 59A, black, 3000str.' → {CF259A, HP59A}"""
    n = name.upper()
    n = re.sub(r'\bHP\s+(\d{2,3}[A-Z]{0,3})\b', r'HP\1', n)          # „HP 59A“, „HP 305XL“ → jeden kód
    out = set()
    for tok in re.split(r'[\s,;/+()]+', n):
        t = re.sub(r'[-.]', '', tok)
        if len(t) < 3 or not re.search(r'\d', t):
            continue
        if UNIT_RE.match(t) or re.fullmatch(r'\d+', t) and len(t) > 4 \
                or re.fullmatch(r'\d+(PACK|BALENI|KS)', t) or re.match(r'^\d+X\d+', t):
            continue
        if re.fullmatch(r'\d{1,2}', t):
            continue
        out.add(t)
    return out


MULTI = {'set', 'col', None}


def same_colour(a, b):
    """černá se nepáruje s azurovou apod.; sady a barevné (tri-colour) se párují s čímkoli"""
    ca, cb = a.get('col'), b.get('col')
    return ca in MULTI or cb in MULTI or ca == cb


# ---------------------------------------------------------------- čištění seznamu tiskáren
BRAND_PREFIX = {'HP': r'^(HP|HEWLETT[- ]PACKARD)\s+', 'Canon': r'^CANON\s+', 'Brother': r'^BROTHER\s+',
                'Epson': r'^EPSON\s+', 'Xerox': r'^XEROX\s+', 'Lexmark': r'^LEXMARK\s+'}
CANON_SERIES = re.compile(r'^(I-?SENSYS|ISENSYS|PIXMA|MAXIFY|SELPHY|IMAGERUNNER|IR[\s-]?C?\d|LBP|MF\d|FAX-?L|SMARTBASE|BJC|IMAGECLASS)')


def clean_printers(P, S, rep):
    P2 = []
    for b, m, s in P:
        orig = m
        m = re.sub(r'[^\x20-\x7E]', '', m)
        m = re.sub(r'\s+', ' ', m).strip()
        for nb, rx in BRAND_PREFIX.items():
            if re.match(rx, m):
                m = re.sub(rx, '', m)
                if nb != b:
                    rep['tiskarny_preznaceny'].append(f'{b} {orig} → {nb} {m}')
                    b = nb
                break
        if b == 'HP' and CANON_SERIES.match(m):
            rep['tiskarny_preznaceny'].append(f'HP {orig} → Canon {m}')
            b = 'Canon'
        if m:
            P2.append([b, m, s])

    def key(p):
        m = p[1].upper()
        if p[0] == 'Canon':
            m = re.sub(r'^I-?SENSYS\s+', '', m)
        return p[0] + '|' + re.sub(r'[\s\-_./]', '', m)

    groups = collections.OrderedDict()
    for p in P2:
        groups.setdefault(key(p), []).append(p)
    skey = {tuple(sorted(x)): i for i, x in enumerate(S)}
    out = []
    for arr in groups.values():
        if len(arr) == 1:
            out.append(arr[0])
            continue
        names = sorted({p[1] for p in arr},
                       key=lambda a: (-('SENSYS' in a), len(re.split(r'[\s-]', a)), len(a), a))
        name = re.sub(r'^ISENSYS', 'I-SENSYS', names[0])
        members = tuple(sorted({t for p in arr for t in S[p[2]]}))
        si = skey.get(members)
        if si is None:
            si = len(S)
            S.append(list(members))
            skey[members] = si
        out.append([arr[0][0], name, si])
        rep['tiskarny_slouceno'] += 1
    return out


# ---------------------------------------------------------------- hlavní běh
def main():
    feed_src, prev_path, out_dir = sys.argv[1:4]
    excl_path = sys.argv[4] if len(sys.argv) > 4 else None
    today = datetime.date.today().isoformat()
    os.makedirs(out_dir, exist_ok=True)

    prev = json.loads(read_bytes(prev_path).decode('utf-8'))
    T0, S0, P0 = prev['T'], prev['S'], prev['P']
    excluded = set()
    if excl_path and os.path.exists(excl_path):
        excluded = {l.split('#')[0].strip() for l in open(excl_path, encoding='utf-8')} - {''}

    feed = {}
    for it in feed_items(read_bytes(feed_src)):
        cat = it.get('CATEGORYTEXT', '')
        if not CAT_RE.match(cat) or it.get('ITEM_ID') in excluded:
            continue
        sl = slug(it.get('URL', ''))
        if sl:
            feed[sl] = it
    if len(feed) < 1000:   # pojistka: rozbitý/prázdný feed nesmí smazat vyhledávač
        raise SystemExit(f'Feed má jen {len(feed)} tonerů/inkoustů – index se NEPŘEPISUJE.')

    rep = {'datum': today, 'odebrano': [], 'pridano': [], 'nesparovano': [], 'tiskarny_preznaceny': [],
           'tiskarny_slouceno': 0}

    def product(it, old=None):
        name = re.sub(r'\s+', ' ', it.get('PRODUCTNAME', '')).strip()
        cat = it.get('CATEGORYTEXT', '')
        t = {'b': brand_of(cat, name, it.get('MANUFACTURER', '')), 'n': name, 'u': slug(it['URL']),
             'i': it.get('IMGURL', '') or '', 'p': int(round(float(it.get('PRICE_VAT') or 0)))}
        col = colof(name) or (old or {}).get('col')
        if col:
            t['col'] = col
        if (old.get('x') if old else is_ink(cat, name)):
            t['x'] = 1
        if (old.get('c') if old else is_compatible(name)):
            t['c'] = 1
        return t

    # 1+2) ponechané produkty s čerstvými údaji, mapování starých indexů na nové
    T, remap = [], {}
    for i, t in enumerate(T0):
        it = feed.get(t['u'])
        if not it:
            rep['odebrano'].append(t['n'])
            continue
        remap[i] = len(T)
        T.append(product(it, t))
    S = [[remap[t] for t in s if t in remap] for s in S0]

    # 3) nové produkty → tiskárny podle kódu originálu
    tok_of = [code_tokens(t['n']) for t in T]
    share = collections.Counter(tok for ts in tok_of for tok in ts)
    sets_of = collections.defaultdict(set)
    for si, s in enumerate(S):
        for ti in s:
            sets_of[ti].add(si)
    by_tok = collections.defaultdict(set)    # kód → produkty v indexu (jen produkty, které mají tiskárny)
    for ti, ts in enumerate(tok_of):
        if not sets_of[ti]:
            continue
        for tok in ts:
            if share[tok] <= MAX_TOKEN_SHARE:
                by_tok[tok].add(ti)
    set_brands = collections.defaultdict(set)    # sada → značky tiskáren, které ji používají
    for b, _m, si in P0:
        set_brands[si].add(b)
    known = {t['u'] for t in T}
    for sl, it in feed.items():
        if sl in known:
            continue
        nt = product(it)
        toks = code_tokens(nt['n'])
        matches = set()
        for tok in toks:
            for ti in by_tok.get(tok, ()):
                # stejný typ (toner × inkoust) a stejná značka tiskárny, jinak to není náhrada
                if bool(T[ti].get('x')) == bool(nt.get('x')) and T[ti]['b'] == nt['b'] and same_colour(T[ti], nt):
                    matches.add(ti)
        target = set()
        for ti in matches:
            target |= {si for si in sets_of[ti] if nt['b'] in set_brands[si]}
        if not target:
            rep['nesparovano'].append({'n': nt['n'], 'u': '/' + nt['u'], 'kody': sorted(toks)})
            continue
        ni = len(T)
        T.append(nt)
        for si in target:
            S[si].append(ni)
        rep['pridano'].append({'n': nt['n'], 'u': '/' + nt['u'],
                               'podle': sorted({T[ti]['n'] for ti in matches})[:3], 'sad': len(target)})

    # 4) tiskárny: odebrat ty bez náplní, vyčistit, seřadit
    P = [p for p in P0 if S[p[2]]]
    P = clean_printers(P, S, rep)
    # zahodit nepoužité sady a přečíslovat
    used = sorted({p[2] for p in P})
    sidx = {o: n for n, o in enumerate(used)}
    S = [sorted(set(S[o])) for o in used]
    P = sorted(([b, m, sidx[s]] for b, m, s in P), key=lambda p: (p[0], p[1]))

    same = prev.get('v') == 3 and prev.get('T') == T and prev.get('S') == S and prev.get('P') == P
    out = {'v': 3, 'd': prev['d'] if same else today, 'T': T, 'S': S, 'P': P}
    raw = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    assert all(0 <= ti < len(T) for s in S for ti in s) and all(0 <= p[2] < len(S) for p in P)
    with open(os.path.join(out_dir, 'toner-index.json'), 'w', encoding='utf-8') as f:
        f.write(raw)

    # nespárované: v reportu jen ty, které přibyly od minulého běhu (stav v nesparovano.txt)
    st_path = os.path.join(out_dir, 'nesparovano.txt')
    seen_before = set()
    if os.path.exists(st_path):
        seen_before = {l.strip() for l in open(st_path, encoding='utf-8')} - {''}
    rep['nesparovano_nove'] = [p for p in rep['nesparovano'] if p['u'] not in seen_before] if seen_before else []
    rep['nesparovano_dle_znacky'] = dict(collections.Counter(
        brand_of('', p['n'], p['n'].split(' ')[0]) for p in rep['nesparovano']).most_common())
    with open(st_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(p['u'] for p in rep['nesparovano'])) + '\n')

    summary = {'datum': today, 'produktu': len(T), 'sad': len(S), 'tiskaren': len(P),
               'odebrano': len(rep['odebrano']), 'pridano': len(rep['pridano']),
               'nesparovano': len(rep['nesparovano']), 'nesparovano_nove': len(rep['nesparovano_nove']),
               'tiskarny_preznaceny': len(rep['tiskarny_preznaceny']),
               'tiskarny_slouceno': rep['tiskarny_slouceno'], 'velikost_kb': round(len(raw.encode()) / 1024)}
    rep['souhrn'] = summary
    with open(os.path.join(out_dir, 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    md = [f'# Index tonerů a inkoustů – {today}', '',
          f"- Produktů ve vyhledávači: **{summary['produktu']}**, tiskáren: **{summary['tiskaren']}**, velikost {summary['velikost_kb']} KB",
          f"- Nově přidáno: **{summary['pridano']}**, odebráno (už nejsou v e-shopu): **{summary['odebrano']}**",
          f"- Nespárováno (nejsou ve vyhledávači): **{summary['nesparovano']}**, z toho nově: **{summary['nesparovano_nove']}**",
          '- Nespárované podle značky: ' + ', '.join(f'{k} {v}' for k, v in rep['nesparovano_dle_znacky'].items()), '']
    if rep['nesparovano_nove']:
        md += ['## Nově nespárované (přibyly do e-shopu, ale neumím je přiřadit k tiskárně)', '']
        md += [f"- {p['n']}" for p in rep['nesparovano_nove'][:300]] + ['']
    if rep['pridano']:
        md += ['## Nově přidané', ''] + [f"- {p['n']} – podle: {'; '.join(p['podle'])}" for p in rep['pridano'][:300]] + ['']
    if rep['odebrano']:
        md += ['## Odebrané', ''] + [f'- {n}' for n in rep['odebrano'][:300]] + ['']
    with open(os.path.join(out_dir, 'report.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
