#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera le versioni inglese, francese e tedesca del sito in /en /fr /de.

    python3 scripts/lingue.py

PERCHE' — il sito e' gia' quadrilingue, ma le traduzioni vivono negli attributi
data-en / data-fr / data-de e vengono applicate dal browser. Un motore di
ricerca non le vede: legge il markup, che e' italiano. Quindi il sito che vende
il multilingua, per il mondo, e' monolingua. E hreflang non si puo' nemmeno
dichiarare, perche' hreflang vuole un indirizzo per lingua e qui l'indirizzo non
cambia mai.

Qui il testo tradotto viene scritto DENTRO il markup, una volta per lingua, e
ogni lingua prende il suo indirizzo. Le pagine italiane restano dove sono e come
sono: sono la sorgente, non una copia.

Le pagine generate sono file veri, da committare: Netlify pubblica la cartella
cosi' com'e', non c'e' nessun passo di costruzione dalla sua parte.
"""
import io, os, re, shutil, sys
from html.parser import HTMLParser

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINGUE = ('en', 'fr', 'de')
SITO = 'https://colgo.app'

# privacy.html NON viene tradotta: il corpo dell'informativa e' testo legale
# scritto in italiano, e solo dieci etichette hanno i data-*. Tradurne meta'
# sarebbe peggio che tenerla in una lingua sola — e un'informativa approssimata
# e' un rischio, non un dettaglio. Resta a /privacy per tutti, e nessuna pagina
# dichiara che ne esiste una versione inglese: perche' non esiste.
SOLO_ITALIANO = {'privacy.html'}

PAGINE = ['index.html', 'come-funziona.html', 'faq.html', 'hotel.html', 'negozio.html',
          'organizzazione.html', 'per-chi.html', 'perche-digitale.html', 'prezzi.html',
          'privacy.html', 'ristorante.html']

LOCALE = {'it': 'it_IT', 'en': 'en_GB', 'fr': 'fr_FR', 'de': 'de_DE'}

# Titolo e descrizione non stanno negli attributi data-*: sono l'unica cosa che
# va tradotta a mano. Sono anche cio' che si legge nei risultati di ricerca.
META = {
 'index.html': {
  'en': ("Colgo — The digital catalogue for any business",
         "Colgo puts your catalogue on your customers' phones. Configurable, always up to date, without complications."),
  'fr': ("Colgo — Le catalogue numérique pour tout établissement",
         "Colgo apporte votre catalogue sur le téléphone de vos clients. Configurable, toujours à jour, sans complications."),
  'de': ("Colgo — Der digitale Katalog für jeden Betrieb",
         "Colgo bringt Ihren Katalog auf das Handy Ihrer Gäste. Konfigurierbar, immer aktuell, ohne Komplikationen.")},
 'come-funziona.html': {
  'en': ("How Colgo works — Digital catalogue for hospitality",
         "See how Colgo works: QR code in the room, automatic multilingual catalogue, real-time requests to reception. No app, no downloads."),
  'fr': ("Comment fonctionne Colgo — Catalogue numérique pour l'hébergement",
         "Découvrez comment fonctionne Colgo : QR code en chambre, catalogue multilingue automatique, demandes en temps réel à la réception. Aucune application, aucun téléchargement."),
  'de': ("So funktioniert Colgo — Digitaler Katalog für Beherbergungsbetriebe",
         "So funktioniert Colgo: QR-Code im Zimmer, automatisch mehrsprachiger Katalog, Anfragen in Echtzeit an die Rezeption. Keine App, kein Download.")},
 'faq.html': {
  'en': ("FAQ — Colgo", "Frequently asked questions about Colgo. Everything you want to know before you start."),
  'fr': ("FAQ — Colgo", "Questions fréquentes sur Colgo. Tout ce que vous voulez savoir avant de commencer."),
  'de': ("FAQ — Colgo", "Häufige Fragen zu Colgo. Alles, was Sie vor dem Start wissen möchten.")},
 'hotel.html': {
  'en': ("Colgo for hotels, B&Bs and farm stays — Digital catalogue for guests",
         "Colgo for hospitality: guests scan the QR in the room or get the link before arrival, explore services and send requests to reception in real time."),
  'fr': ("Colgo pour hôtels, B&B et fermes-auberges — Catalogue numérique pour les clients",
         "Colgo pour l'hôtellerie : les clients scannent le QR en chambre ou reçoivent le lien avant l'arrivée, explorent les services et envoient des demandes en temps réel à la réception."),
  'de': ("Colgo für Hotels, B&Bs und Ferienhöfe — Digitaler Katalog für Gäste",
         "Colgo für die Hotellerie: Gäste scannen den QR im Zimmer oder erhalten den Link vor der Anreise, entdecken Leistungen und senden Anfragen in Echtzeit an die Rezeption.")},
 'negozio.html': {
  'en': ("Colgo for shops and boutiques — Digital catalogue in the window",
         "Colgo for retail: customers scan the QR in the window, even when the shop is closed, browse the catalogue and prepare their list before walking in."),
  'fr': ("Colgo pour boutiques et magasins — Catalogue numérique en vitrine",
         "Colgo pour le commerce : le client scanne le QR en vitrine, même magasin fermé, parcourt le catalogue et prépare sa liste avant même d'entrer."),
  'de': ("Colgo für Geschäfte und Boutiquen — Digitaler Katalog im Schaufenster",
         "Colgo für den Handel: Kunden scannen den QR im Schaufenster, auch bei geschlossenem Laden, blättern im Katalog und stellen ihre Liste zusammen, bevor sie eintreten.")},
 'organizzazione.html': {
  'en': ("Access and catalogue — who sees what in Colgo, and how you govern it",
         "Six diagrams: access levels from owner to waiter, the request queue for staff, one PIN for several venues, catalogue visibility, the editor and multi-venue."),
  'fr': ("Accès et catalogue — qui voit quoi dans Colgo, et comment le gouverner",
         "Six schémas : les niveaux d'accès du propriétaire au serveur, la file des demandes au personnel, un PIN pour plusieurs sites, la visibilité du catalogue, l'éditeur et le multi-site."),
  'de': ("Zugriffe und Katalog — wer in Colgo was sieht, und wie Sie ihn steuern",
         "Sechs Schaubilder: Zugriffsebenen vom Inhaber bis zum Kellner, die Anfrage-Warteschlange fürs Personal, eine PIN für mehrere Standorte, Sichtbarkeit des Katalogs, der Editor und Mehrstandort.")},
 'per-chi.html': {
  'en': ("Who Colgo is for — Hotels, B&Bs, campsites, restaurants, shops",
         "Colgo adapts to hotels, B&Bs, farm stays, campsites, restaurants, beach clubs and shops. One configurable system for any business with a catalogue."),
  'fr': ("Pour qui est Colgo — Hôtels, B&B, campings, restaurants, boutiques",
         "Colgo s'adapte aux hôtels, B&B, fermes-auberges, campings, restaurants, établissements balnéaires et boutiques. Un seul système configurable pour tout établissement avec un catalogue."),
  'de': ("Für wen Colgo ist — Hotels, B&Bs, Campingplätze, Restaurants, Geschäfte",
         "Colgo passt sich Hotels, B&Bs, Ferienhöfen, Campingplätzen, Restaurants, Strandbädern und Geschäften an. Ein konfigurierbares System für jeden Betrieb mit einem Katalog.")},
 'perche-digitale.html': {
  'en': ("Why digital — the numbers behind the QR catalogue",
         "QR adoption, the language barrier, staff shortages, the cost of paper: the industry data explaining why a digital catalogue beats the printed sheet."),
  'fr': ("Pourquoi le numérique — les chiffres derrière le catalogue par QR",
         "Adoption des QR, barrière de la langue, manque de personnel, coût du papier : les données du secteur qui expliquent pourquoi un catalogue numérique bat la feuille imprimée."),
  'de': ("Warum digital — die Zahlen hinter dem QR-Katalog",
         "QR-Verbreitung, Sprachbarriere, Personalmangel, Papierkosten: die Branchendaten, die erklären, warum ein digitaler Katalog das gedruckte Blatt schlägt.")},
 'prezzi.html': {
  'en': ("Pricing — Colgo",
         "Colgo pricing for hotels, restaurants and shops. One price per business, not per room or table. Monthly or yearly."),
  'fr': ("Tarifs — Colgo",
         "Tarifs Colgo pour hôtels, restaurants et boutiques. Un prix par établissement, pas par chambre ou par table. Mensuel ou annuel."),
  'de': ("Preise — Colgo",
         "Colgo-Preise für Hotels, Restaurants und Geschäfte. Ein Preis pro Betrieb, nicht pro Zimmer oder Tisch. Monatlich oder jährlich.")},
 'privacy.html': {
  'en': ("Privacy Policy — Colgo", None),
  'fr': ("Politique de confidentialité — Colgo", None),
  'de': ("Datenschutzerklärung — Colgo", None)},
 'ristorante.html': {
  'en': ("Colgo for restaurants and bars — Digital orders from the table",
         "Colgo for food service: the waiter handles orders from their own page, the customer can order by scanning the table QR — the order always goes straight to the kitchen."),
  'fr': ("Colgo pour restaurants et bars — Commandes numériques depuis la table",
         "Colgo pour la restauration : le serveur gère les commandes depuis sa page personnelle, le client peut commander en scannant le QR de la table — la commande arrive toujours directement en cuisine."),
  'de': ("Colgo für Restaurants und Bars — Digitale Bestellungen vom Tisch",
         "Colgo für die Gastronomie: Der Kellner verwaltet Bestellungen auf seiner eigenen Seite, der Gast kann per Tisch-QR bestellen — die Bestellung geht immer direkt in die Küche.")},
}

VUOTI = {'br','img','meta','link','input','hr','source','path','circle','rect','line',
         'polygon','polyline','ellipse','use','stop','col','area','feturbulence',
         'fegaussianblur','base','embed','track','wbr'}


class Traduci(HTMLParser):
    """Riscrive il contenuto degli elementi che hanno data-<lingua>.

    Nessun annidamento fra elementi tradotti (verificato: 863 elementi, 0
    annidati), quindi appena se ne incontra uno si puo' saltare tutto il suo
    contenuto fino alla chiusura e mettere al suo posto la traduzione."""

    def __init__(self, lingua):
        super().__init__(convert_charrefs=False)
        self.l = lingua
        self.fuori = []
        self.salta = None      # (nome tag, profondita')
        self.tradotti = 0

    def emetti(self, t):
        if self.salta is None:
            self.fuori.append(t)

    def handle_starttag(self, tag, attrs):
        grezzo = self.get_starttag_text()
        if self.salta is not None:
            if tag == self.salta[0] and tag not in VUOTI and not grezzo.rstrip().endswith('/>'):
                self.salta = (self.salta[0], self.salta[1] + 1)
            return
        d = dict(attrs)
        valore = d.get('data-' + self.l)
        if valore is not None and 'data-it' in d:
            self.fuori.append(grezzo)
            self.fuori.append(valore)
            self.tradotti += 1
            if tag not in VUOTI and not grezzo.rstrip().endswith('/>'):
                self.salta = (tag, 1)
            return
        self.fuori.append(grezzo)

    def handle_endtag(self, tag):
        if self.salta is not None:
            if tag == self.salta[0]:
                n = self.salta[1] - 1
                if n == 0:
                    self.salta = None
                    self.fuori.append(f'</{tag}>')
                else:
                    self.salta = (self.salta[0], n)
            return
        self.fuori.append(f'</{tag}>')

    def handle_startendtag(self, tag, attrs):
        self.emetti(self.get_starttag_text())

    def handle_data(self, d):        self.emetti(d)
    def handle_comment(self, d):     self.emetti(f'<!--{d}-->')
    def handle_decl(self, d):        self.emetti(f'<!{d}>')
    def handle_pi(self, d):          self.emetti(f'<?{d}>')
    def unknown_decl(self, d):       self.emetti(f'<![{d}]>')
    def handle_entityref(self, n):   self.emetti(f'&{n};')
    def handle_charref(self, n):     self.emetti(f'&#{n};')


def indirizzo(pagina, lingua):
    base = SITO + ('' if lingua == 'it' else '/' + lingua)
    return base + '/' if pagina == 'index.html' else f'{base}/{pagina[:-5]}'


def alternate(pagina):
    """hreflang per tutte le lingue + x-default sull'italiano (la sorgente)."""
    lingue = ('it',) if pagina in SOLO_ITALIANO else ('it',) + LINGUE
    r = [f'  <link rel="alternate" hreflang="{l}" href="{indirizzo(pagina, l)}" />'
         for l in lingue]
    r.append(f'  <link rel="alternate" hreflang="x-default" href="{indirizzo(pagina, "it")}" />')
    return '\n'.join(r) + '\n'


def rifai_link(html, lingua):
    """I collegamenti interni devono restare nella lingua che si sta leggendo.

    Si toccano solo gli indirizzi che iniziano con "/" e finiscono in .html (o
    la home): le ancore, i mailto e i link a app.colgo.app non c'entrano."""
    def f(m):
        virg, url = m.group(1), m.group(2)
        if url == '/':
            return f'href={virg}/{lingua}/{virg}'
        if re.match(r'^/[a-z0-9\-]+\.html(#.*)?$', url):
            if url.lstrip('/').split('#')[0] in SOLO_ITALIANO:
                return m.group(0)          # la privacy resta quella italiana
            return f'href={virg}/{lingua}{url}{virg}'
        if url.startswith('/#'):
            return f'href={virg}/{lingua}/{url[1:]}{virg}'
        return m.group(0)
    return re.sub(r'href=(["\'])([^"\']*)\1', f, html)


# Nelle pagine tradotte i pulsanti della lingua non riscrivono il testo: portano
# all'indirizzo di quella lingua. E' l'unico comportamento coerente con l'avere
# un indirizzo per lingua — altrimenti si potrebbe leggere l'inglese a /fr/.
NAVIGA = """
    // Pagine generate per lingua: qui il selettore NAVIGA, non riscrive. Ogni
    // lingua ha il suo indirizzo, e l'indirizzo deve dire il vero.
    function setLang(l) {
      var supp = ['it','en','fr','de'];
      if (supp.indexOf(l) === -1) return;
      try { localStorage.setItem('colgo_lang', l); } catch (e) {}
      var p = location.pathname.replace(/^\\/(en|fr|de)(?=\\/|$)/, '');
      if (!p || p === '/') p = '/';
      location.href = (l === 'it' ? '' : '/' + l) + (p === '/' ? '/' : p) + location.hash;
    }
"""


def genera(pagina, lingua):
    sorgente = io.open(os.path.join(RADICE, pagina), encoding='utf-8').read()

    p = Traduci(lingua)
    p.feed(sorgente)
    s = ''.join(p.fuori)

    s = s.replace('<html lang="it">', f'<html lang="{lingua}">', 1)

    titolo, descr = META[pagina][lingua]
    s = re.sub(r'<title>.*?</title>', lambda m: f'<title>{titolo}</title>', s, count=1, flags=re.S)
    for prop in ('og:title', 'twitter:title'):
        s = re.sub(rf'(<meta (?:property|name)="{prop}" content=")[^"]*(")', rf'\g<1>{titolo}\g<2>', s)
    if descr:
        for attr in (r'<meta name="description" content="', r'<meta property="og:description" content="',
                     r'<meta name="twitter:description" content="'):
            s = re.sub(re.escape(attr) + r'[^"]*"', attr + descr + '"', s)

    s = s.replace(f'<meta property="og:locale" content="it_IT" />',
                  f'<meta property="og:locale" content="{LOCALE[lingua]}" />')

    url = indirizzo(pagina, lingua)
    s = re.sub(r'\n?  <link rel="alternate" hreflang="[^"]*" href="[^"]*" />', '', s)
    s = re.sub(r'<link rel="canonical" href="[^"]*" />', f'<link rel="canonical" href="{url}" />', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*" />', f'<meta property="og:url" content="{url}" />', s)
    s = s.replace('<link rel="canonical"', alternate(pagina) + '  <link rel="canonical"', 1)

    s = rifai_link(s, lingua)

    # il selettore attivo e' quello della lingua che si sta leggendo
    s = s.replace('<button class="lang-btn active" onclick="setLang(\'it\')">IT</button>',
                  '<button class="lang-btn" onclick="setLang(\'it\')">IT</button>')
    s = s.replace(f'<button class="lang-btn" onclick="setLang(\'{lingua}\')">{lingua.upper()}</button>',
                  f'<button class="lang-btn active" onclick="setLang(\'{lingua}\')">{lingua.upper()}</button>')

    # via la vecchia setLang (riscrive il testo) e l'avvio automatico, che qui
    # manderebbe l'utente altrove appena arrivato
    s = re.sub(r'\n\s*function setLang\(lang\) \{.*?\n\s{4}\}\n', NAVIGA, s, count=1, flags=re.S)
    s = re.sub(r'\n\s*\(function \(\) \{\s*\n\s*var supported = \[.*?setLang\(initial\);\s*\n\s*\}\)\(\);', '', s, flags=re.S)

    return s, p.tradotti


def main():
    tot = 0
    for l in LINGUE:
        d = os.path.join(RADICE, l)
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d)
        for pagina in PAGINE:
            if pagina in SOLO_ITALIANO: continue
            s, n = genera(pagina, l)
            io.open(os.path.join(d, pagina), 'w', encoding='utf-8').write(s)
            tot += n
        print(f'/{l}: {len(PAGINE) - len(SOLO_ITALIANO)} pagine')
    print(f'{tot} elementi tradotti scritti nel markup')

    # ── italiane: solo hreflang, il resto non si tocca ──
    for pagina in PAGINE:
        f = os.path.join(RADICE, pagina)
        s = io.open(f, encoding='utf-8').read()
        s = re.sub(r'\n?  <link rel="alternate" hreflang="[^"]*" href="[^"]*" />', '', s)
        s = s.replace('  <link rel="canonical"', alternate(pagina) + '  <link rel="canonical"', 1)
        io.open(f, 'w', encoding='utf-8').write(s)
    print(f'{len(PAGINE)} pagine italiane: aggiunto hreflang')

    # ── sitemap: 44 indirizzi ──
    import subprocess, datetime
    def lastmod(p):
        d = subprocess.run(['git','log','-1','--format=%cs','--',p], capture_output=True,
                           text=True, cwd=RADICE).stdout.strip()
        return d or datetime.date.today().isoformat()
    PRIO = {'index.html':'1.0','come-funziona.html':'0.9','prezzi.html':'0.9','hotel.html':'0.8',
            'ristorante.html':'0.8','negozio.html':'0.8','perche-digitale.html':'0.8',
            'organizzazione.html':'0.7','per-chi.html':'0.7','faq.html':'0.7','privacy.html':'0.3'}
    voci = []
    for pagina in sorted(PAGINE, key=lambda x: (-float(PRIO[x]), x)):
        lm = lastmod(pagina)
        lingue = ('it',) if pagina in SOLO_ITALIANO else ('it',) + LINGUE
        for l in lingue:
            alt = '\n'.join(f'    <xhtml:link rel="alternate" hreflang="{x}" href="{indirizzo(pagina, x)}"/>'
                            for x in lingue)
            alt += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{indirizzo(pagina, "it")}"/>'
            voci.append(f"""  <url>
    <loc>{indirizzo(pagina, l)}</loc>
{alt}
    <lastmod>{lm}</lastmod>
    <priority>{PRIO[pagina]}</priority>
  </url>""")
    io.open(os.path.join(RADICE, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + '\n'.join(voci) + '\n</urlset>\n')
    print(f'sitemap.xml: {len(voci)} indirizzi')


if __name__ == '__main__':
    main()
