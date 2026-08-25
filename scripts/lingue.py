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
LINGUE = ('en', 'fr', 'de', 'es')
SITO = 'https://colgo.app'

# Il 17/08 l'informativa e' stata tradotta per intero (899 parole, terminologia
# GDPR ufficiale nelle tre lingue) e quindi entra anche lei. Le versioni tradotte
# portano una riga in piu': in caso di discrepanza fa fede l'italiano. E' la
# prassi per i documenti legali tradotti, e qui e' anche vera — la traduzione e'
# di lavoro, non asseverata.
SOLO_ITALIANO = set()

PREVALE_ITALIANO = {
 'en': 'This is a translation for convenience. In case of any discrepancy, the Italian version prevails.',
 'fr': 'Ceci est une traduction de courtoisie. En cas de divergence, la version italienne prévaut.',
 'de': 'Dies ist eine Übersetzung zur Erleichterung. Bei Abweichungen ist die italienische Fassung maßgeblich.',
 'es': 'Esta es una traducción de cortesía. En caso de discrepancia, prevalece la versión italiana.',
}

PAGINE = ['index.html', 'come-funziona.html', 'faq.html', 'hotel.html', 'negozio.html',
          'organizzazione.html', 'per-chi.html', 'perche-digitale.html', 'prezzi.html',
          'privacy.html', 'ristorante.html',
           'qr-code-in-camera.html', 'catalogo-complesso.html',
           'struttura-stagionale.html']

LOCALE = {'it': 'it_IT', 'en': 'en_GB', 'fr': 'fr_FR', 'de': 'de_DE', 'es': 'es_419'}

# Titolo e descrizione non stanno negli attributi data-*: sono l'unica cosa che
# va tradotta a mano. Sono anche cio' che si legge nei risultati di ricerca.
# Nomi dei tre segmenti dentro il JSON-LD dei prezzi. Stesso schema di META:
# il blocco viene copiato tale e quale nelle pagine tradotte, quindi senza
# questa tabella la pagina inglese direbbe "Struttura ricettiva" in italiano.
# Le CIFRE non si toccano mai: sono le stesse in tutte le lingue.
OFFERTE = {
 'en': {'Struttura ricettiva': 'Accommodation', 'Ristorante': 'Restaurant', 'Negozio': 'Shop'},
 'fr': {'Struttura ricettiva': 'Hébergement',   'Ristorante': 'Restaurant', 'Negozio': 'Boutique'},
 'de': {'Struttura ricettiva': 'Unterkunft',    'Ristorante': 'Restaurant', 'Negozio': 'Geschäft'},
 'es': {'Struttura ricettiva': 'Alojamiento',   'Ristorante': 'Restaurante','Negozio': 'Tienda'},
}

META = {
 'struttura-stagionale.html': {
  'en': ("Seasonal business: do you pay while closed?",
         "Eight monthly instalments for seven active months, charged once when you open. During the off months the catalogue pauses but the QR codes stay valid."),
  'fr': ("Établissement saisonnier : paie-t-on fermé ?",
         "Huit mensualités pour sept mois actifs, prélevées une fois à l'ouverture. Pendant les mois de repos le catalogue est en pause mais les QR restent valables."),
  'de': ("Saisonbetrieb: zahlt man auch geschlossen?",
         "Acht Monatsraten für sieben aktive Monate, einmalig bei Öffnung abgebucht. In den Ruhemonaten pausiert der Katalog, die QR-Codes bleiben gültig."),
  'es': ("Negocio de temporada: ¿se paga cerrado?",
         "Ocho mensualidades por siete meses activos, cobradas una vez al abrir. En los meses de descanso el catálogo se pausa pero los QR siguen válidos.")},
 'qr-code-in-camera.html': {
  'en': ("In-room QR codes: what you need to start",
         "What you actually need for an in-room QR code: size, printing, what the guest sees, and what happens if you rename a room."),
  'fr': ("QR en chambre : ce qu'il faut pour démarrer",
         "Ce qu'il faut vraiment pour un QR en chambre : taille, impression, ce que voit le client et ce qui arrive si vous renommez une chambre."),
  'de': ("QR im Zimmer: was man zum Start braucht",
         "Was ein QR-Code im Zimmer wirklich braucht: Größe, Druck, was der Gast sieht und was passiert, wenn Sie ein Zimmer umbenennen."),
  'es': ("QR en la habitación: qué hace falta para empezar",
         "Qué hace falta de verdad para un QR en la habitación: tamaño, impresión, qué ve el huésped y qué pasa si cambias el nombre de una habitación.")},
 'catalogo-complesso.html': {
  'en': ("Complex menu: can a digital catalogue cope?",
         "Nested subcategories, prices per size, hours per category and stock re-checked when the order is sent. With the limits stated: no PMS, no till."),
  'fr': ("Menu complexe : un catalogue numérique tient-il ?",
         "Sous-catégories imbriquées, prix par taille, horaires par catégorie et stock revérifié à l'envoi. Avec les limites annoncées : ni PMS ni caisse."),
  'de': ("Komplexe Karte: hält ein digitaler Katalog das aus?",
         "Verschachtelte Unterkategorien, Preise je Größe, Zeiten je Kategorie und beim Absenden erneut geprüfter Bestand. Mit den Grenzen: kein PMS, keine Kasse."),
  'es': ("Menú complejo: ¿aguanta un catálogo digital?",
         "Subcategorías anidadas, precios por talla, horarios por categoría y stock recomprobado al enviar. Con los límites dichos: ni PMS ni caja.")},
 'index.html': {
  'en': ("Colgo — The digital catalogue for any business",
         "Colgo puts your catalogue on your customers' phones. Configurable, always up to date, without complications."),
  'fr': ("Colgo — Le catalogue numérique pour tout établissement",
         "Colgo apporte votre catalogue sur le téléphone de vos clients. Configurable, toujours à jour, sans complications."),
  'de': ("Colgo — Der digitale Katalog für jeden Betrieb",
         "Colgo bringt Ihren Katalog auf das Handy Ihrer Gäste. Konfigurierbar, immer aktuell, ohne Komplikationen."),
  'es': ("Colgo — El catálogo digital para cualquier negocio",
         "Colgo lleva tu catálogo al teléfono de tus clientes. Configurable, siempre al día, sin complicaciones.")},
 'come-funziona.html': {
  'en': ("How Colgo works — Digital catalogue for hospitality",
         "See how Colgo works: QR code in the room, automatic multilingual catalogue, real-time requests to reception. No app, no downloads."),
  'fr': ("Comment fonctionne Colgo — catalogue numérique par QR",
         "QR code en chambre, catalogue multilingue automatique, demandes en temps réel à la réception. Aucune application, aucun téléchargement."),
  'de': ("So funktioniert Colgo — digitaler Katalog per QR",
         "So funktioniert Colgo: QR-Code im Zimmer, automatisch mehrsprachiger Katalog, Anfragen in Echtzeit an die Rezeption. Keine App, kein Download."),
  'es': ("Cómo funciona Colgo — catálogo digital por QR",
         "Mira cómo funciona Colgo: código QR en la habitación, catálogo multiidioma automático, solicitudes en tiempo real a recepción. Sin app, sin descargas.")},
 'faq.html': {
  'en': ("FAQ — Colgo", "Frequently asked questions about Colgo. Everything you want to know before you start."),
  'fr': ("FAQ — Colgo", "Questions fréquentes sur Colgo. Tout ce que vous voulez savoir avant de commencer."),
  'de': ("FAQ — Colgo", "Häufige Fragen zu Colgo. Alles, was Sie vor dem Start wissen möchten."),
  'es': ("Preguntas frecuentes — Colgo",
         "Respuestas a las dudas más comunes sobre Colgo: precios, idiomas, configuración, pagos y seguridad de los datos.")},
 'hotel.html': {
  'en': ("Colgo for hotels, B&Bs and farm stays — digital catalogue",
         "Colgo for hospitality: guests scan the QR in the room or get the link before arrival, explore services and send requests to reception in real time."),
  'fr': ("Colgo pour hôtels et fermes-auberges — catalogue numérique",
         "Les clients scannent le QR en chambre ou reçoivent le lien avant l'arrivée : ils explorent les services et envoient leurs demandes à la réception."),
  'de': ("Colgo für Hotels, B&Bs und Ferienhöfe — digitaler Katalog",
         "Gäste scannen den QR im Zimmer oder erhalten den Link vor der Anreise, entdecken Leistungen und senden Anfragen an die Rezeption."),
  'es': ("Colgo para hoteles, B&B y casas rurales — catálogo digital",
         "El huésped escanea el QR de la habitación o recibe el enlace antes de llegar, recorre los servicios y envía solicitudes a recepción.")},
 'negozio.html': {
  'en': ("Colgo for shops and boutiques — digital catalogue",
         "Colgo for retail: customers scan the QR in the window, even when the shop is closed, browse the catalogue and prepare their list before walking in."),
  'fr': ("Colgo pour boutiques et magasins — catalogue en vitrine",
         "Colgo pour le commerce : le client scanne le QR en vitrine, même magasin fermé, parcourt le catalogue et prépare sa liste avant même d'entrer."),
  'de': ("Colgo für Geschäfte — digitaler Katalog im Schaufenster",
         "Kunden scannen den QR im Schaufenster, auch bei geschlossenem Laden, blättern im Katalog und stellen ihre Liste zusammen."),
  'es': ("Colgo para tiendas y boutiques — catálogo digital",
         "Colgo para comercios: el cliente escanea el QR de la vitrina, incluso con la tienda cerrada, recorre el catálogo y arma su lista para el mostrador.")},
 'organizzazione.html': {
  'en': ("Access and catalogue — who sees what in Colgo",
         "Six diagrams: access levels from owner to waiter, the request queue for staff, one PIN for several venues, catalogue visibility."),
  'fr': ("Accès et catalogue — qui voit quoi dans Colgo",
         "Six schémas : les niveaux d'accès du propriétaire au serveur, la file des demandes au personnel, un PIN pour plusieurs sites, la visibilité du catalogue."),
  'de': ("Zugriffe und Katalog — wer in Colgo was sieht",
         "Sechs Schaubilder: Zugriffsebenen vom Inhaber bis zum Kellner, die Anfrage-Warteschlange, eine PIN für mehrere Standorte, Sichtbarkeit des Katalogs."),
  'es': ("Accesos y catálogo — quién ve qué en Colgo",
         "Seis esquemas: niveles de acceso del titular al mesero, la fila de solicitudes del staff, un PIN para varias sedes, visibilidad del catálogo y editor.")},
 'per-chi.html': {
  'en': ("Who Colgo is for — hotels, campsites, restaurants, shops",
         "Colgo adapts to hotels, B&Bs, farm stays, campsites, restaurants, beach clubs and shops. One configurable system for any business with a catalogue."),
  'fr': ("Pour qui est Colgo — hôtels, campings, restaurants",
         "Colgo s'adapte aux hôtels, B&B, campings, restaurants, établissements balnéaires et boutiques. Un système configurable pour chaque contexte."),
  'de': ("Für wen Colgo ist — Hotels, Campingplätze, Restaurants",
         "Colgo passt sich Hotels, B&Bs, Campingplätzen, Restaurants, Strandbädern und Geschäften an. Ein konfigurierbares System für jeden Betrieb."),
  'es': ("Para quién es Colgo — hoteles, campings, restaurantes",
         "Colgo se adapta a hoteles, B&B, casas rurales, campings, restaurantes, balnearios y tiendas. Un solo sistema configurable para cada contexto.")},
 'perche-digitale.html': {
  'en': ("Why digital — the numbers behind the QR catalogue",
         "QR adoption, the language barrier, staff shortages, the cost of paper: the industry data explaining why a digital catalogue beats the printed sheet."),
  'fr': ("Pourquoi le numérique — les chiffres du catalogue par QR",
         "Adoption des QR, barrière de la langue, manque de personnel, coût du papier : les données du secteur derrière le catalogue numérique."),
  'de': ("Warum digital — die Zahlen hinter dem QR-Katalog",
         "QR-Verbreitung, Sprachbarriere, Personalmangel, Papierkosten: die Branchendaten, die erklären, warum ein digitaler Katalog das gedruckte Blatt schlägt."),
  'es': ("Por qué digital — los números detrás del catálogo por QR",
         "Adopción del QR, la barrera del idioma, la falta de personal, el costo del papel: los datos del sector detrás del catálogo digital.")},
 'prezzi.html': {
  'en': ("Pricing — Colgo",
         "Colgo pricing for hotels, restaurants and shops. One price per business, not per room or table. Monthly or yearly."),
  'fr': ("Tarifs — Colgo",
         "Tarifs Colgo pour hôtels, restaurants et boutiques. Un prix par établissement, pas par chambre ou par table. Mensuel ou annuel."),
  'de': ("Preise — Colgo",
         "Colgo-Preise für Hotels, Restaurants und Geschäfte. Ein Preis pro Betrieb, nicht pro Zimmer oder Tisch. Monatlich oder jährlich."),
  'es': ("Precios — Colgo",
         "Precios de Colgo para hoteles, restaurantes y tiendas. Un precio por negocio, no por habitación ni por mesa. Mensual o anual, con 30 días de prueba gratis.")},
 'privacy.html': {
  'en': ("Privacy Policy — Colgo",
         "Colgo privacy policy: what data we collect, why, how long we keep it and how to exercise your rights."),
  'fr': ("Politique de confidentialité — Colgo",
         "Politique de confidentialité de Colgo : quelles données nous collectons, pourquoi, combien de temps et comment exercer vos droits."),
  'de': ("Datenschutzerklärung — Colgo",
         "Datenschutzerklärung von Colgo: welche Daten wir erheben, warum, wie lange wir sie speichern und wie Sie Ihre Rechte ausüben."),
  'es': ("Política de Privacidad — Colgo",
         "Cómo Colgo recoge, usa y protege los datos personales, conforme al RGPD. Datos recogidos, finalidades, terceros, conservación y derechos del interesado.")},
 'ristorante.html': {
  'en': ("Colgo for restaurants and bars — orders from the table",
         "The waiter handles orders from their own page, the customer can order by scanning the table QR. The order always goes straight to the kitchen."),
  'fr': ("Colgo pour restaurants et bars — commandes à table",
         "Le serveur gère les commandes depuis sa page personnelle, le client peut commander en scannant le QR de la table. La commande arrive en cuisine."),
  'de': ("Colgo für Restaurants und Bars — Bestellungen am Tisch",
         "Der Kellner verwaltet Bestellungen auf seiner eigenen Seite, der Gast bestellt per Tisch-QR. Die Bestellung geht direkt in die Küche."),
  'es': ("Colgo para restaurantes y bares — pedidos desde la mesa",
         "El mesero maneja los pedidos desde su propia página, o el cliente pide escaneando el QR de la mesa. El pedido llega a la cocina al instante.")},
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


def faqpage(html, lingua, url):
    """Dati strutturati della FAQ, RICAVATI dalla pagina.

    Non una copia scritta a mano: domande e risposte si leggono dagli stessi
    attributi che producono il testo visibile, quindi il markup non puo' dire
    una cosa diversa da quella che il lettore vede, ne' contenere domande che
    nella pagina non ci sono.

    Regola: quello che sta DOPO uno stacco di paragrafo (<br/><br/>) resta
    fuori. Serve per la domanda sui pagamenti, dove la riga sul lavoro in corso
    e' testo normale e non deve finire in un blocco che gli assistenti citano
    come se fosse la risposta.

    ⚠️ Serve un parser, non un regex: gli attributi contengono <br/>, quindi
    qualsiasi `[^>]*` si ferma DENTRO l'attributo e perde la coppia. Con il
    regex uscivano 12 domande su 13, e proprio quella dei pagamenti.
    """
    import json as _json
    from html.parser import HTMLParser as _HP

    # ⚠️ Prima si TOGLIE un eventuale blocco gia' presente. Il file italiano lo
    # contiene (glielo scrive questo stesso script) e la generazione lo copia
    # dentro le tradotte: senza questa riga la pagina inglese finiva con DUE
    # FAQPage, il primo dei quali in italiano.
    html = re.sub(r'\n<!-- FAQ: generato da scripts/lingue\.py.*?</script>\n(?=</head>)',
                  '', html, flags=re.S)

    class Raccogli(_HP):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.voci = []
            self.attesa = None
        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            classe = d.get('class', '')
            if 'faq-q' in classe:
                self.attesa = d.get('data-' + lingua)
            elif 'faq-a' in classe and self.attesa:
                r = d.get('data-' + lingua)
                if r:
                    self.voci.append((self.attesa, r))
                self.attesa = None

    r = Raccogli()
    r.feed(html)
    if not r.voci:
        return html

    def pulisci(t):
        t = re.sub(r'<[^>]+>', ' ', t)
        for a, b in (('&amp;', '&'), ('&quot;', '"'), ('&#39;', "'"),
                     ('&nbsp;', ' '), ('&ugrave;', 'ù'), ('&eacute;', 'é')):
            t = t.replace(a, b)
        return re.sub(r'\s+', ' ', t).strip()

    voci = []
    for d, risp in r.voci:
        risp = re.split(r'<br\s*/?>\s*<br\s*/?>', risp)[0]
        voci.append({
            "@type": "Question",
            "name": pulisci(d),
            "acceptedAnswer": {"@type": "Answer", "text": pulisci(risp)},
        })

    grafo = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": url + "#faq",
        "inLanguage": lingua,
        "mainEntity": voci,
    }
    blocco = ('\n<!-- FAQ: generato da scripts/lingue.py leggendo gli attributi della\n'
              '     pagina. Non si modifica a mano: rispecchia sempre le domande che\n'
              '     ci sono davvero, nella lingua che si sta leggendo. -->\n'
              '<script type="application/ld+json">\n'
              + _json.dumps(grafo, ensure_ascii=False, indent=2) + '\n</script>\n</head>')
    return html.replace('</head>', blocco, 1)


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
NAVIGA_NON_PIU_USATA = """
    // Pagine generate per lingua: qui il selettore NAVIGA, non riscrive. Ogni
    // lingua ha il suo indirizzo, e l'indirizzo deve dire il vero.
    function setLang(l) {
      var supp = ['it','en','fr','de','es'];
      if (supp.indexOf(l) === -1) return;
      try { localStorage.setItem('colgo_lang', l); } catch (e) {}
      var p = location.pathname.replace(/^\\/(en|fr|de|es)(?=\\/|$)/, '');
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

    # Le immagini hanno percorsi RELATIVI ("screenshots/…", "colgo-logo.png"):
    # da /en/index.html puntano a /en/screenshots/… che non esiste. In una
    # sottocartella vanno resi assoluti, o la pagina tradotta e' senza immagini —
    # ed e' un difetto che si vede solo caricandole davvero, non leggendo il
    # markup.
    s = re.sub(r'(src|href)="(?!/|https?:|mailto:|#|data:)([^"]+)"', r'\1="/\2"', s)

    # Le schermate dell'app esistono anche nella lingua della pagina: chi legge
    # /de deve vedere l'app in tedesco, non in italiano. Dove la versione
    # tradotta NON esiste ancora si tiene quella italiana — meglio una lingua
    # sola che due mescolate nella stessa immagine.
    def tradotta(m):
        nome = m.group(2)
        return f'src="/screenshots/{lingua}/{nome}"' if os.path.exists(
            os.path.join(RADICE, 'screenshots', lingua, nome)) else m.group(0)
    s = re.sub(r'src="/screenshots/([a-z]{2}/)?([^"/]+)"', tradotta, s)

    # il selettore attivo e' quello della lingua che si sta leggendo
    s = s.replace('<button class="lang-btn active" onclick="setLang(\'it\')">IT</button>',
                  '<button class="lang-btn" onclick="setLang(\'it\')">IT</button>')
    s = s.replace(f'<button class="lang-btn" onclick="setLang(\'{lingua}\')">{lingua.upper()}</button>',
                  f'<button class="lang-btn active" onclick="setLang(\'{lingua}\')">{lingua.upper()}</button>')

    # ovunque ci siano domande, non solo su faq.html: le pagine costruite
    # su una domanda hanno il loro blocco in fondo
    if 'faq-q' in s:
        s = faqpage(s, lingua, indirizzo(pagina, lingua))

    if pagina == 'prezzi.html':
        # solo le ETICHETTE dei segmenti: le cifre restano quelle che sono
        for it_, tr in OFFERTE[lingua].items():
            s = s.replace('"name": "%s — ' % it_, '"name": "%s — ' % tr)
            s = s.replace('"category": "%s"' % it_, '"category": "%s"' % tr)

    # la riga sul valore legale, solo nelle versioni tradotte dell'informativa
    if pagina == 'privacy.html':
        s = s.replace('</header>',
                      f'  <div class="privacy-prevale">{PREVALE_ITALIANO[lingua]}</div>\n</header>', 1)

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
        # il FAQPage si rigenera anche qui: e' l'unico blocco di dati
        # strutturati che NON si scrive a mano nel file
        s = re.sub(r'\n<!-- FAQ: generato da scripts/lingue\.py.*?</script>\n(?=</head>)', '', s, flags=re.S)
        if 'faq-q' in s:
            s = faqpage(s, 'it', indirizzo(pagina, 'it'))
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
            'organizzazione.html':'0.7','per-chi.html':'0.7','faq.html':'0.7','privacy.html':'0.3',
            'qr-code-in-camera.html':'0.8','catalogo-complesso.html':'0.8','struttura-stagionale.html':'0.8'}
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
