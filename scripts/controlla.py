#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlla le pagine pubblicate, tutte le lingue, prima di spingere.

    python3 scripts/controlla.py

Legge i FILE, non il sito pubblico: serve dopo lingue.py e prima del commit.
Esce con codice 1 se trova un errore; gli avvisi li stampa e basta.

Cosa guarda, per ogni pagina di lingue.PAGINE in ogni lingua:
  - title <= 60 caratteri, description 120-160, entrambi unici nel sito;
  - un solo <h1> e un solo <main>;
  - ogni blocco JSON-LD si legge come JSON;
  - canonical uguale all'indirizzo della pagina, hreflang per tutte le
    lingue + x-default, e reciproci (la pagina indicata indica questa);
  - nelle lingue tradotte nessun elemento rimasto col testo italiano, e
    nessuna frase del corpo identica a quella italiana (salvo nomi propri);
  - ogni link e ogni immagine interni portano a un file che esiste;
  - il blocco dell'assistente identico in tutte le pagine;
e poi sitemap.xml (gli indirizzi giusti, con gli alternate) e _redirects
(una regola 301! per pagina e lingua, nessuna catena e nessun giro).
"""
import html, io, json, os, re, sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lingue

R = lingue.RADICE
TUTTE = ('it',) + lingue.LINGUE
errori, avvisi = [], []

# Frasi che restano uguali in tutte le lingue: nomi propri e indirizzi.
UGUALI = {'Prà de la Fam', 'Filippo Parisini', 'colgoapp@gmail.com', 'Colgo',
          'COLGO', 'FAQ', 'IT', 'EN', 'FR', 'DE', 'ES', 'PIN', 'QR', 'B&B'}
# Parole che, da sole, dicono "questa frase e' italiana".
# Parole che non esistono (o quasi) in en/fr/de/es: due in una frase di una
# pagina tradotta vogliono dire testo italiano scritto senza data-*.
SOLO_IT = re.compile(r"\b(della|delle|degli|nella|nelle|sono|anche|perché|questo|questa|struttura|ospite|ospiti|scaricare|nulla|niente|quando|tutto|gli|il|che)\b", re.I)
ITALIANE = re.compile(r"\b(il|lo|gli|della|delle|degli|che|non|una|sono|anche|perché|questo|questa|nella|alla|dal|dalla|più|ogni|tuo|tua|struttura|camera|ospite|cliente)\b", re.I)


def file_di(pagina, l):
    return os.path.join(R, pagina) if l == 'it' else os.path.join(R, l, pagina)


def leggi(p):
    return io.open(p, encoding='utf-8').read()


class Testi(HTMLParser):
    """Testo visibile (fuori da script/style/svg), e gli elementi con data-it."""
    SALTA = {'script', 'style', 'svg', 'head'}

    def __init__(self, lingua):
        super().__init__(convert_charrefs=True)
        self.l = lingua
        self.dentro = 0
        self.testi = []
        self.non_tradotti = []
        self.pila = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SALTA:
            self.dentro += 1
        d = dict(attrs)
        if 'data-it' in d and self.l != 'it':
            self.pila.append((tag, d, []))
        else:
            self.pila.append((tag, None, None))

    def handle_endtag(self, tag):
        if tag in self.SALTA:
            self.dentro = max(0, self.dentro - 1)
        # chiude fino al tag corrispondente (HTML tollerante)
        while self.pila:
            t, d, buf = self.pila.pop()
            if d is not None:
                visto = re.sub(r'\s+', ' ', ''.join(buf)).strip()
                it = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', d['data-it']))).strip()
                tr = d.get('data-' + self.l)
                if tr is None:
                    self.non_tradotti.append('manca data-%s: %s' % (self.l, it[:60]))
                elif visto and visto == it and tr.strip() != d['data-it'].strip():
                    self.non_tradotti.append('testo italiano: %s' % it[:60])
            if t == tag:
                break

    def handle_data(self, data):
        if not self.dentro:
            t = re.sub(r'\s+', ' ', data).strip()
            if t:
                self.testi.append(t)
        for _, d, buf in self.pila:
            if buf is not None:
                buf.append(data)


def controlla_pagina(pagina, l, visti_t, visti_d):
    f = file_di(pagina, l)
    if not os.path.exists(f):
        errori.append('%s: manca' % os.path.relpath(f, R)); return None
    s = leggi(f)
    nome = os.path.relpath(f, R)

    t = re.search(r'<title>(.*?)</title>', s, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', s)
    t = html.unescape(t.group(1).strip()) if t else ''
    d = html.unescape(d.group(1)) if d else ''
    if not t or len(t) > 60:
        errori.append('%s: title di %d caratteri' % (nome, len(t)))
    if not (120 <= len(d) <= 160):
        errori.append('%s: description di %d caratteri' % (nome, len(d)))
    # uguale alla STESSA pagina in un'altra lingua (un nome proprio come
    # «Privacy Policy») e' un avviso; uguale a un'altra pagina e' un errore
    for testo, visti, cosa in ((t, visti_t, 'title'), (d, visti_d, 'description')):
        if testo in visti:
            (avvisi if os.path.basename(visti[testo]) == pagina else errori).append(
                '%s: %s uguale a %s' % (nome, cosa, visti[testo]))
        visti.setdefault(testo, nome)

    for tag in ('h1', 'main'):
        n = len(re.findall(r'<%s[\s>]' % tag, s))
        if n != 1:
            errori.append('%s: %d <%s>' % (nome, n, tag))

    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(b)
        except ValueError as e:
            errori.append('%s: JSON-LD non valido (%s)' % (nome, e))

    atteso = lingue.indirizzo(pagina, l)
    c = re.search(r'<link rel="canonical" href="([^"]*)"', s)
    if not c or c.group(1) != atteso:
        errori.append('%s: canonical %s, atteso %s' % (nome, c and c.group(1), atteso))
    alt = dict(re.findall(r'<link rel="alternate" hreflang="([^"]*)" href="([^"]*)"', s))
    voluti = {x: lingue.indirizzo(pagina, x) for x in TUTTE}
    voluti['x-default'] = lingue.indirizzo(pagina, 'it')
    if alt != voluti:
        errori.append('%s: hreflang diversi dall\'atteso' % nome)

    p = Testi(l)
    p.feed(s)
    for x in p.non_tradotti:
        errori.append('%s: %s' % (nome, x))
    return s, p.testi


def link_interni(nome, s):
    """Ogni href/src che comincia con / deve portare a un file del sito."""
    corpo = re.sub(r'<script\b.*?</script>', '', s, flags=re.S)
    for u in re.findall(r'(?:href|src)="(/[^"]*)"', corpo):
        if u.startswith('//'):
            continue
        p = u.split('#')[0].split('?')[0]
        if p == '' :
            continue
        cand = [p.lstrip('/')]
        if p.endswith('/'):
            cand = [p.lstrip('/') + 'index.html']
        elif not os.path.splitext(p)[1]:
            cand.append(p.lstrip('/') + '.html')
        if not any(os.path.isfile(os.path.join(R, c)) for c in cand):
            errori.append('%s: link rotto %s' % (nome, u))


def widget(s):
    m = re.search(r'<!-- ══ colgo-assistente ══.*?(?=<script>document\.querySelectorAll\(\'\.faq-q\'\)|</body>)', s, re.S)
    return m.group(0) if m else None


def main():
    visti_t, visti_d = {}, {}
    testi_it = {}
    widget_ref = {}          # per lingua: il blocco e' tradotto anche lui
    pagine = [p for p in lingue.PAGINE if p not in lingue.SOLO_ITALIANO]
    for pagina in pagine:
        for l in TUTTE:
            r = controlla_pagina(pagina, l, visti_t, visti_d)
            if r is None:
                continue
            s, testi = r
            link_interni(os.path.relpath(file_di(pagina, l), R), s)
            w = widget(s)
            if w is not None and pagina != 'privacy.html':
                if l not in widget_ref:
                    widget_ref[l] = (w, pagina)
                elif w != widget_ref[l][0]:
                    errori.append('%s/%s: blocco dell\'assistente diverso da %s' % (l, pagina, widget_ref[l][1]))
            if l == 'it':
                testi_it[pagina] = set(testi)
            else:
                # frasi del corpo uguali a quelle italiane
                for t in testi:
                    if t in UGUALI:
                        continue
                    if (t in testi_it[pagina] and len(t.split()) >= 3 and ITALIANE.search(t)) \
                            or len(set(w.lower() for w in SOLO_IT.findall(t))) >= 2:
                        errori.append('%s/%s: frase in italiano: %s' % (l, pagina, t[:70]))

    # hreflang reciproci: chi indica una pagina deve essere indicato da lei
    for pagina in pagine:
        for l in TUTTE:
            s = leggi(file_di(pagina, l))
            for x, u in re.findall(r'<link rel="alternate" hreflang="([^"]*)" href="([^"]*)"', s):
                if x == 'x-default':
                    continue
                altra = leggi(file_di(pagina, x))
                if lingue.indirizzo(pagina, l) not in altra:
                    errori.append('%s/%s: hreflang %s non reciproco' % (l, pagina, x))

    # sitemap
    sm = leggi(os.path.join(R, 'sitemap.xml'))
    locs = re.findall(r'<loc>([^<]*)</loc>', sm)
    attesi = {lingue.indirizzo(p, l) for p in pagine for l in TUTTE}
    if set(locs) != attesi or len(locs) != len(attesi):
        errori.append('sitemap: %d indirizzi, attesi %d (mancano %s, in piu\' %s)' % (
            len(locs), len(attesi), sorted(attesi - set(locs))[:5], sorted(set(locs) - attesi)[:5]))
    for blocco in re.findall(r'<url>.*?</url>', sm, re.S):
        if len(re.findall(r'hreflang=', blocco)) != len(TUTTE) + 1:
            errori.append('sitemap: alternate incompleti in %s' % re.search(r'<loc>([^<]*)', blocco).group(1))

    # _redirects
    regole = []
    for riga in leggi(os.path.join(R, '_redirects')).splitlines():
        riga = riga.strip()
        if riga and not riga.startswith('#'):
            regole.append(riga.split())
    da = {r[0]: r for r in regole}
    for p in pagine:
        for l in TUTTE:
            pre = '' if l == 'it' else '/' + l
            src = f'{pre}/{p}'
            dst = f'{pre}/' if p == 'index.html' else f'{pre}/{p[:-5]}'
            r = da.get(src)
            if not r or r[1] != dst or r[2] != '301!':
                errori.append('_redirects: manca %s -> %s 301!' % (src, dst))
    for r in regole:
        if r[1] in da and da[r[1]] is not r:
            errori.append('_redirects: catena %s -> %s -> %s' % (r[0], r[1], da[r[1]][1]))
        if r[0] == r[1]:
            errori.append('_redirects: giro su se stessa %s' % r[0])
    for pre in ('', '/en', '/fr', '/de', '/es'):
        if da.get(f'{pre}/registrati', [None, None])[1] != 'https://app.colgo.app/registrati':
            errori.append('_redirects: %s/registrati non porta all\'app' % pre)
    for l in lingue.LINGUE:
        if da.get(f'/{l}/*', [None, None])[1:3] != [f'/{l}/404.html', '404']:
            errori.append('_redirects: manca la 404 di /%s' % l)

    n = len(pagine) * len(TUTTE)
    print('%d pagine controllate (%d x %d lingue), sitemap %d indirizzi, %d regole in _redirects'
          % (n, len(pagine), len(TUTTE), len(locs), len(regole)))
    for a in avvisi:
        print('  avviso:', a)
    for e in errori:
        print('  ERRORE:', e)
    if errori:
        sys.exit(1)
    print('nessun errore')


if __name__ == '__main__':
    main()
