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
           'struttura-stagionale.html',
           'confronto.html',
           # 23/10/2026: la pagina "Chi siamo" e tre guide
           'chi-siamo.html', 'menu-digitale-qr-code.html',
           'guida-digitale-ospiti.html', 'catalogo-digitale-negozio.html']

# Pagine di servizio: generate in ogni lingua ma FUORI da sitemap, hreflang e
# briciole. Non hanno canonical (una 404 non ha un indirizzo suo), quindi
# genera() non vi scrive nemmeno gli hreflang. Netlify le usa con le regole
# "/en/*  /en/404.html  404" di _redirects.
SERVIZIO = ['404.html']

LOCALE = {'it': 'it_IT', 'en': 'en_GB', 'fr': 'fr_FR', 'de': 'de_DE', 'es': 'es_419'}

# Il testo alternativo dell'anteprima social: l'immagine e' il solo logo, e
# l'alt dice quello, non uno slogan.
ALT_OG = {'it': 'Logo di Colgo', 'en': 'Colgo logo', 'fr': 'Logo de Colgo',
          'de': 'Colgo-Logo', 'es': 'Logo de Colgo'}

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
 'chi-siamo.html': {
  'en': ('About us — Colgo, born at a family business on Lake Garda',
         "Who is behind Colgo: born at a family business on Lake Garda, what it does, who it's for and how we work, with the product's limits stated first."),
  'fr': ('Qui sommes-nous — Colgo, né au bord du lac de Garde',
         "Qui est derrière Colgo : né dans une structure familiale au bord du lac de Garde, ce qu'il fait, à qui il sert et comment nous travaillons, limites d'abord."),
  'de': ('Über uns — Colgo, entstanden in einem Betrieb am Gardasee',
         'Wer hinter Colgo steht: entstanden in einem Familienbetrieb am Gardasee, was es kann, für wen es ist und wie wir arbeiten, mit den Grenzen vorweg.'),
  'es': ('Quiénes somos — Colgo, nacido junto al lago de Garda',
         'Quién está detrás de Colgo: nacido en un establecimiento familiar del lago de Garda, qué hace, para quién es y cómo trabajamos, con los límites primero.')},
 'menu-digitale-qr-code.html': {
  'en': ('QR code menus: how they work and what you need',
         "How a QR code menu works and what it should have: languages, hours per category, variants with their own price, table orders. And what it doesn't do."),
  'fr': ('Menu numérique par QR : fonctionnement et essentiel',
         "Comment fonctionne un menu numérique par QR code et ce qu'il doit avoir : langues, horaires par catégorie, variantes avec leur prix, commandes à table."),
  'de': ('Digitale Speisekarte per QR: wie sie funktioniert',
         'Wie eine digitale Speisekarte per QR-Code funktioniert und was sie können muss: Sprachen, Zeiten je Kategorie, Varianten mit Preis, Bestellung am Tisch.'),
  'es': ('Menú digital con QR: cómo funciona y qué hace falta',
         'Cómo funciona un menú digital con código QR y qué debe tener: idiomas, horarios por categoría, variantes con su precio, pedidos desde la mesa. Y qué no hace.')},
 'guida-digitale-ospiti.html': {
  'en': ('Digital guest guide: what to include and how',
         'What to put in the digital guide of a hotel, B&B or farm stay: arrival, Wi-Fi, opening hours, services, requests to reception. Before arrival and in the room.'),
  'fr': ("Livret d'accueil numérique : que mettre dedans",
         "Le contenu du livret d'accueil numérique d'un hôtel ou d'un B&B : arrivée, Wi-Fi, horaires, services, demandes à la réception. Avant l'arrivée et en chambre."),
  'de': ('Digitale Gästemappe: was hineingehört und wie',
         'Was in die digitale Gästemappe von Hotel, B&B oder Ferienhof gehört: Anreise, WLAN, Zeiten, Leistungen, Anfragen an die Rezeption. Vor Anreise und im Zimmer.'),
  'es': ('Guía digital para huéspedes: qué poner y cómo',
         'Qué poner en la guía digital de un hotel, B&B o casa rural: llegada, Wi-Fi, horarios, servicios, solicitudes a recepción. Antes de llegar y en la habitación.')},
 'catalogo-digitale-negozio.html': {
  'en': ('Digital catalogue for shops, without e-commerce',
         "How to show a shop's products on customers' phones without opening an online store: QR code in the window, variants, availability and the counter list."),
  'fr': ('Catalogue numérique pour boutiques, sans site marchand',
         "Montrer les produits d'une boutique sur le téléphone des clients sans ouvrir de site marchand : QR en vitrine, variantes, disponibilité et liste au comptoir."),
  'de': ('Digitaler Katalog fürs Geschäft, ohne Onlineshop',
         'Wie ein Geschäft seine Produkte aufs Handy der Kunden bringt, ohne Onlineshop: QR-Code im Schaufenster, Varianten, Verfügbarkeit und die Liste für die Theke.'),
  'es': ('Catálogo digital para tiendas, sin tienda online',
         'Cómo mostrar los productos de una tienda en el teléfono de los clientes sin abrir una tienda online: QR en la vitrina, variantes, disponibilidad y la lista.')},
 '404.html': {
  'en': ("Page not found — Colgo",
         "The page you were looking for isn't here: the address has changed or contains a mistake. Go back to the home page, pricing, the FAQ or try the Colgo demo."),
  'fr': ("Page introuvable — Colgo",
         "La page que vous cherchez n'existe pas : l'adresse a changé ou contient une erreur. Revenez à l'accueil, aux tarifs, à la FAQ ou essayez la démo de Colgo."),
  'de': ("Seite nicht gefunden — Colgo",
         "Die gesuchte Seite gibt es nicht: Die Adresse hat sich geändert oder enthält einen Fehler. Zurück zur Startseite, zu den Preisen, zur FAQ oder zur Demo."),
  'es': ("Página no encontrada — Colgo",
         "La página que buscabas no existe: la dirección cambió o tiene un error. Vuelve al inicio, a los precios, a las preguntas frecuentes o prueba la demo.")},
 'confronto.html': {
  'en': ("Colgo and the alternatives: the comparison",
         "Competitor prices read on their own pages on 25/08/2026, with the row where we're behind written first: no property management system integration."),
  'fr': ("Colgo et les alternatives : le comparatif",
         "Prix des concurrents relevés sur leurs pages le 25/08/2026, avec la ligne où nous sommes en retard en premier : aucune intégration au logiciel de gestion."),
  'de': ("Colgo und die Alternativen: der Vergleich",
         "Wettbewerberpreise, am 25.08.2026 auf deren Seiten gelesen, mit der Zeile, in der wir hinterherhinken, zuerst: keine PMS-Anbindung."),
  'es': ("Colgo y las alternativas: la comparativa",
         "Precios de la competencia leídos en sus páginas el 25/08/2026, con la fila donde estamos por detrás escrita primero: sin integración con el sistema de gestión.")},
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
  'en': ("Colgo — QR digital catalogue for hotels and restaurants",
         "QR digital catalogue for hotels, restaurants and shops: customers open it on their phone, in their own language, with no app. Try the demo or 30 days free."),
  'fr': ("Colgo — Catalogue numérique QR pour hôtels et restaurants",
         "Catalogue numérique QR pour hôtels, restaurants et boutiques : le client l'ouvre sur son téléphone, dans sa langue, sans appli. Démo ou 30 jours gratuits."),
  'de': ("Colgo — Digitaler QR-Katalog für Hotels und Restaurants",
         "Digitaler QR-Katalog für Hotels, Restaurants und Geschäfte: Kunden öffnen ihn am Handy, in ihrer Sprache, ohne App. Demo ansehen oder 30 Tage gratis."),
  'es': ("Colgo — Catálogo digital por QR para hoteles y restaurantes",
         "Catálogo digital por QR para hoteles, restaurantes y tiendas: tus clientes lo abren en el teléfono, en su idioma, sin app. Prueba la demo o 30 días gratis.")},
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
  'en': ("Colgo FAQ — Questions on digital catalogues and QR codes",
         "Answers on costs, whether customers need an app, languages, QR codes and setup for hotels, restaurants and shops: what to know before trying Colgo."),
  'fr': ("FAQ Colgo — Questions sur le catalogue numérique et le QR",
         "Réponses sur les coûts, l'appli côté clients, les langues, les QR codes et la mise en route pour hôtels, restaurants et boutiques, avant d'essayer Colgo."),
  'de': ("Colgo FAQ — Fragen zu digitalem Katalog und QR-Code",
         "Antworten zu Kosten, App für Kunden, Sprachen, QR-Codes und Start für Hotels, Restaurants und Geschäfte: was Sie wissen sollten, bevor Sie Colgo testen."),
  'es': ("Preguntas frecuentes de Colgo — catálogo digital y QR",
         "Respuestas sobre costos, app para los clientes, idiomas, códigos QR y puesta en marcha para hoteles, restaurantes y tiendas, antes de probar Colgo.")},
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
  # Niente cifre qui: un prezzo ripetuto nei meta e' un prezzo che invecchia
  # in cinque posti alla volta (e' gia' successo con kb.json).
  'en': ("Colgo pricing — one price per business, not per room",
         "One price per business, not per room or table, monthly or yearly, with a 30-day free trial. Plans for hotels, restaurants and shops."),
  'fr': ("Tarifs Colgo — un prix par établissement, pas par chambre",
         "Un prix par établissement, pas par chambre ni par table, mensuel ou annuel, avec 30 jours d'essai gratuit. Des formules pour hôtels, restaurants et boutiques."),
  'de': ("Colgo Preise — ein Preis pro Betrieb, nicht pro Zimmer",
         "Ein Preis pro Betrieb, nicht pro Zimmer oder Tisch, monatlich oder jährlich, mit 30 Tagen kostenlosem Test. Tarife für Hotels, Restaurants und Geschäfte."),
  'es': ("Precios de Colgo — un precio por negocio, no por habitación",
         "Un precio por negocio, no por habitación ni por mesa, mensual o anual, con 30 días de prueba gratis. Planes para hoteles, restaurantes y tiendas.")},
 'privacy.html': {
  'en': ("Privacy Policy — Colgo",
         "Colgo privacy policy: what personal data we collect, why, how long we keep it, which third parties are involved and how to exercise your rights."),
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

# Nomi per il BreadcrumbList (Home › pagina). Non sono testo nuovo: sono le
# etichette che il sito usa gia' nel menu e nel piede, nelle stesse lingue.
BRICIOLE = {
 'index.html':                ('Home', 'Home', 'Accueil', 'Startseite', 'Inicio'),
 'come-funziona.html':        ('Come funziona', 'How it works', 'Comment ça marche', "So funktioniert's", 'Cómo funciona'),
 'organizzazione.html':       ('Accessi e catalogo', 'Access & catalogue', 'Accès et catalogue', 'Zugriffe & Katalog', 'Accesos y catálogo'),
 'prezzi.html':               ('Prezzi', 'Pricing', 'Tarifs', 'Preise', 'Precios'),
 'confronto.html':            ('Confronto', 'Comparison', 'Comparatif', 'Vergleich', 'Comparativa'),
 'faq.html':                  ('FAQ', 'FAQ', 'FAQ', 'FAQ', 'Preguntas frecuentes'),
 'hotel.html':                ('Hotel', 'Hotel', 'Hôtel', 'Hotel', 'Hotel'),
 'ristorante.html':           ('Ristorante', 'Restaurant', 'Restaurant', 'Restaurant', 'Restaurante'),
 'negozio.html':              ('Negozio', 'Shop', 'Boutique', 'Geschäft', 'Tienda'),
 'per-chi.html':              ('Per chi', "Who it's for", 'Pour qui', 'Für wen', 'Para quién'),
 'perche-digitale.html':      ('Perché digitale', 'Why digital', 'Pourquoi le numérique', 'Warum digital', 'Por qué digital'),
 'privacy.html':              ('Privacy Policy', 'Privacy Policy', 'Politique de confidentialité', 'Datenschutzerklärung', 'Política de Privacidad'),
 'qr-code-in-camera.html':    ('QR in camera', 'In-room QR', 'QR en chambre', 'QR im Zimmer', 'QR en la habitación'),
 'catalogo-complesso.html':   ('Cataloghi complessi', 'Complex catalogues', 'Catalogues complexes', 'Komplexe Kataloge', 'Catálogos complejos'),
 'struttura-stagionale.html': ('Stagionali', 'Seasonal', 'Saisonnier', 'Saisonbetrieb', 'De temporada'),
 'chi-siamo.html':            ('Chi siamo', 'About us', 'Qui sommes-nous', 'Über uns', 'Quiénes somos'),
 'menu-digitale-qr-code.html':     ('Menù digitale con QR', 'QR code menu', 'Menu numérique QR', 'Digitale Speisekarte', 'Menú digital con QR'),
 'guida-digitale-ospiti.html':     ('Guida per gli ospiti', 'Guest guide', "Livret d'accueil", 'Gästemappe', 'Guía para huéspedes'),
 'catalogo-digitale-negozio.html': ('Catalogo per negozi', 'Shop catalogue', 'Catalogue boutique', 'Katalog fürs Geschäft', 'Catálogo para tiendas'),
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


RE_BRICIOLE = re.compile(r'\n<!-- Briciole: generato da scripts/lingue\.py.*?</script>\n(?=</head>)', re.S)


def briciole(html, pagina, lingua):
    """BreadcrumbList Home › pagina, nella lingua che si sta leggendo.

    ⚠️ Il vecchio blocco va tolto con RE_BRICIOLE PRIMA di toccare il FAQPage,
    e questa si chiama DOPO: la pulizia del FAQPage cerca il suo blocco subito
    prima di </head>, e con le briciole in mezzo si porterebbe via anche loro."""
    import json as _json
    html = RE_BRICIOLE.sub('', html)
    if pagina == 'index.html' or pagina not in BRICIOLE:
        return html
    i = ('it',) + LINGUE
    grafo = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1,
             "name": BRICIOLE['index.html'][i.index(lingua)], "item": indirizzo('index.html', lingua)},
            {"@type": "ListItem", "position": 2,
             "name": BRICIOLE[pagina][i.index(lingua)], "item": indirizzo(pagina, lingua)},
        ],
    }
    blocco = ('\n<!-- Briciole: generato da scripts/lingue.py. Non si modifica a mano. -->\n'
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


def locali_alternative(html, lingua):
    """og:locale:alternate per le altre quattro lingue, subito dopo og:locale.

    Prima si tolgono quelle gia' presenti: l'italiano le riceve da qui e la
    generazione copia il suo <head>, quindi senza la pulizia si raddoppiano."""
    html = re.sub(r'\n  <meta property="og:locale:alternate" content="[^"]*" />', '', html)
    righe = ''.join(f'\n  <meta property="og:locale:alternate" content="{LOCALE[l]}" />'
                    for l in ('it',) + LINGUE if l != lingua)
    return re.sub(r'(<meta property="og:locale" content="[^"]*" />)', lambda m: m.group(1) + righe,
                  html, count=1)


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
    s = locali_alternative(s, lingua)
    s = s.replace(f'<meta property="og:image:alt" content="{ALT_OG["it"]}" />',
                  f'<meta property="og:image:alt" content="{ALT_OG[lingua]}" />')

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
    s = RE_BRICIOLE.sub('', RE_ABOUT.sub('', s))
    if 'faq-q' in s:
        s = faqpage(s, lingua, indirizzo(pagina, lingua))
    s = briciole(s, pagina, lingua)
    # per ultimo: la pulizia delle briciole cerca il loro blocco attaccato a </head>
    if pagina == ABOUT:
        s = chi_siamo(s, lingua, titolo, descr)

    # la description della home sta anche nel JSON-LD (SoftwareApplication):
    # quella italiana si sostituisce con quella della lingua
    if pagina == 'index.html':
        import json as _json
        it_descr = re.search(r'<meta name="description" content="([^"]*)"', sorgente).group(1)
        vecchia = '"description": ' + _json.dumps(it_descr, ensure_ascii=False)
        assert vecchia in s, 'index.html: la description del JSON-LD non e\' quella della pagina'
        s = s.replace(vecchia, '"description": ' + _json.dumps(descr, ensure_ascii=False))

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


# Piede: i link alle pagine nuove li scrive questo script in TUTTE le sorgenti
# italiane, non si aggiungono a mano. Il 27/08 quattro pagine avevano zero link
# fuori dal piede perche' ognuna andava ricordata in sedici file; qui basta una
# riga. Nell'ordine it en fr de es, come BRICIOLE.
PIEDE_PAGINE = [
 ('chi-siamo.html', ('Chi siamo', 'About us', 'Qui sommes-nous', 'Über uns', 'Quiénes somos')),
]
PIEDE_APPROFONDIMENTI = [
 ('menu-digitale-qr-code.html',     ('Menù digitale con QR', 'QR code menu', 'Menu numérique QR', 'Digitale Speisekarte', 'Menú digital con QR')),
 ('guida-digitale-ospiti.html',     ('Guida per gli ospiti', 'Guest guide', "Livret d'accueil", 'Gästemappe', 'Guía para huéspedes')),
 ('catalogo-digitale-negozio.html', ('Catalogo per negozi', 'Shop catalogue', 'Catalogue boutique', 'Katalog fürs Geschäft', 'Catálogo para tiendas')),
]


def _ancora(pagina, nomi, stile=''):
    dati = ' '.join(f'data-{l}="{n}"' for l, n in zip(('it',) + LINGUE, nomi))
    stile = f' style="{stile}"' if stile else ''
    return f'<a href="/{pagina}"{stile} {dati}>{nomi[0]}</a>'


def piede(s, nome):
    """Aggiunge al piede i link di PIEDE_PAGINE e PIEDE_APPROFONDIMENTI che
    mancano. Rifarlo non cambia niente: un link gia' presente non si ripete.

    Tre forme di piede: quella comune (classi footer-links), quella della home
    (stili in linea) e quella minima dell'informativa. Una pagina che non ne
    ha nessuna ferma lo script: meglio saperlo che perdere il link."""
    m = re.search(r'<footer>.*?</footer>', s, re.S)
    if not m:
        raise SystemExit(f'{nome}: nessun <footer>')
    f = vecchio = m.group(0)

    def aggiungi(trova, voci, chiusura, rientro, stile=''):
        """trova(f) restituisce la riga ATTUALE: dopo ogni inserimento cambia."""
        nonlocal f
        for pagina, nomi in voci:
            if f'href="/{pagina}"' in f:
                continue
            riga = trova(f)
            f = f.replace(riga, riga[:-len(chiusura)] + f'\n{rientro}{_ancora(pagina, nomi, stile)}' + chiusura, 1)

    if '<div class="footer-links footer-approfondimenti">' in f:
        aggiungi(lambda t: re.search(r'<div class="footer-links">.*?\n  </div>', t, re.S).group(0),
                 PIEDE_PAGINE, '\n  </div>', '    ')
        aggiungi(lambda t: re.search(r'<div class="footer-links footer-approfondimenti">.*?\n  </div>', t, re.S).group(0),
                 PIEDE_APPROFONDIMENTI, '\n  </div>', '    ')
    elif 'data-it="Approfondimenti"' in f:
        # home: righe con stili in linea, si copia lo stile dei link vicini
        trova = lambda t: re.search(r'\n      <div style="[^"]*">\n        <span [^>]*data-it="Approfondimenti".*?\n      </div>', t, re.S).group(0)
        stile = re.search(r'<a href="/[^"]*" style="([^"]*)"', trova(f)).group(1)
        aggiungi(trova, PIEDE_APPROFONDIMENTI, '\n      </div>', '        ', stile)
        # le pagine (Chi siamo) in una riga loro, sopra gli Approfondimenti
        mancano = [(p, n) for p, n in PIEDE_PAGINE if f'href="/{p}"' not in f]
        if mancano:
            appr = trova(f)
            c = re.search(r'\n      <!-- Approfondimenti:.*?-->(?=' + re.escape(appr) + ')', f, re.S)
            if c:
                appr = c.group(0) + appr
            apri = re.search(r'\n      <div style="[^"]*">', appr).group(0)
            link = ''.join(f'\n        {_ancora(p, n, stile)}' for p, n in mancano)
            f = f.replace(appr, f'\n      <!-- Pagine: le scrive scripts/lingue.py (PIEDE_PAGINE) -->{apri}{link}\n      </div>\n' + appr, 1)
    elif re.search(r'<footer>\n  © 2026 Colgo', f):
        # informativa: una riga sola
        for pagina, nomi in PIEDE_PAGINE:
            if f'href="/{pagina}"' not in f:
                f = f.replace('<a href="mailto:', f'{_ancora(pagina, nomi)} · <a href="mailto:', 1)
    else:
        raise SystemExit(f'{nome}: piede di forma sconosciuta, aggiungi il caso a piede()')
    return s.replace(vecchio, f, 1)


# Nel menu «CHI SIAMO» portava alla sezione della home: ora che la pagina c'e',
# porta alla pagina.
def menu_chi_siamo(s):
    return re.sub(r'<a href="/?#storia"( class="active")? data-it="CHI SIAMO"',
                  r'<a href="/chi-siamo.html"\1 data-it="CHI SIAMO"', s)


ABOUT = 'chi-siamo.html'
RE_ABOUT = re.compile(r'\n<!-- Chi siamo: generato da scripts/lingue\.py.*?</script>\n(?=</head>)', re.S)


def chi_siamo(html, lingua, titolo, descr):
    """AboutPage + Organization per la pagina «Chi siamo», nella lingua letta.

    L'Organization non si riscrive: si legge dal JSON-LD della home, cosi'
    resta UNA entita' (stesso @id) e non due che col tempo si contraddicono."""
    import json as _json
    html = RE_ABOUT.sub('', html)
    home = io.open(os.path.join(RADICE, 'index.html'), encoding='utf-8').read()
    for blocco in re.findall(r'<script type="application/ld\+json">(.*?)</script>', home, re.S):
        dati = _json.loads(blocco)
        org = next((n for n in dati.get('@graph', []) if n.get('@type') == 'Organization'), None)
        if org:
            break
    else:
        raise SystemExit('index.html: Organization non trovata nel JSON-LD')
    url = indirizzo(ABOUT, lingua)
    grafo = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "AboutPage", "@id": url + "#pagina", "url": url,
             "name": titolo, "description": descr, "inLanguage": lingua,
             "isPartOf": {"@id": SITO + "/#sito"},
             "about": {"@id": org["@id"]}, "mainEntity": {"@id": org["@id"]}},
            org,
        ],
    }
    blocco = ('\n<!-- Chi siamo: generato da scripts/lingue.py (l\'Organization e\' quella\n'
              '     della home). Non si modifica a mano. -->\n'
              '<script type="application/ld+json">\n'
              + _json.dumps(grafo, ensure_ascii=False, indent=2) + '\n</script>\n</head>')
    return html.replace('</head>', blocco, 1)


def controlla_voce_attiva():
    """Ogni pagina puo' evidenziare al massimo la PROPRIA voce di menu.

    Le quattro pagine del 25/08 sono nate copiando per-chi.html e ne hanno
    ereditato il class="active": confronto evidenziava se stessa E "per chi",
    le altre tre evidenziavano una pagina in cui non sei. Nessuno se n'e'
    accorto per due giorni perche' il segno e' solo un colore.
    Costa niente controllarlo qui, dove passa ogni modifica al sito.
    """
    import glob
    guai = []
    for f in sorted(glob.glob(os.path.join(RADICE, '*.html'))):
        nome = os.path.basename(f)
        s = open(f, encoding='utf-8').read()
        m = re.search(r'<div class="nav-links">(.*?)</div>', s, re.S)
        if not m:
            continue
        att = [re.search(r'href="([^"]+)"', a).group(1)
               for a in re.findall(r'<a\b[^>]*>.*?</a>', m.group(1), re.S)
               if re.search(r'class="[^"]*\bactive\b', a)]
        if len(att) > 1:
            guai.append('%s evidenzia %d voci: %s' % (nome, len(att), ', '.join(att)))
        elif att and att[0].lstrip('/') != nome:
            guai.append('%s evidenzia %s' % (nome, att[0]))
    if guai:
        raise SystemExit('VOCE DI MENU SBAGLIATA:\n  ' + '\n  '.join(guai))


def main():
    # prima di tutto il piede e il menu, nelle sorgenti: le lingue si generano
    # da qui, quindi devono gia' averli
    for pagina in PAGINE + SERVIZIO:
        f = os.path.join(RADICE, pagina)
        s = io.open(f, encoding='utf-8').read()
        nuovo = menu_chi_siamo(piede(s, pagina))
        if nuovo != s:
            io.open(f, 'w', encoding='utf-8').write(nuovo)
    controlla_voce_attiva()
    tot = 0
    for l in LINGUE:
        d = os.path.join(RADICE, l)
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d)
        for pagina in PAGINE + SERVIZIO:
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
        s = locali_alternative(s, 'it')
        # il FAQPage si rigenera anche qui: e' l'unico blocco di dati
        # strutturati che NON si scrive a mano nel file
        s = RE_BRICIOLE.sub('', RE_ABOUT.sub('', s))
        s = re.sub(r'\n<!-- FAQ: generato da scripts/lingue\.py.*?</script>\n(?=</head>)', '', s, flags=re.S)
        if 'faq-q' in s:
            s = faqpage(s, 'it', indirizzo(pagina, 'it'))
        s = briciole(s, pagina, 'it')
        if pagina == ABOUT:
            import html as _html
            s = chi_siamo(s, 'it',
                          _html.unescape(re.search(r'<title>(.*?)</title>', s).group(1)),
                          _html.unescape(re.search(r'<meta name="description" content="([^"]*)"', s).group(1)))
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
            'qr-code-in-camera.html':'0.8','catalogo-complesso.html':'0.8','struttura-stagionale.html':'0.8','confronto.html':'0.9',
            'chi-siamo.html':'0.6','menu-digitale-qr-code.html':'0.8','guida-digitale-ospiti.html':'0.8',
            'catalogo-digitale-negozio.html':'0.8'}
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
