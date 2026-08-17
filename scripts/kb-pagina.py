#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggiorna kb.json — il materiale che l'assistente del sito cita — con il
contenuto di UNA pagina, in tutte e quattro le lingue.

    python3 scripts/kb-pagina.py perche-digitale.html

Perche' esiste, e perche' sta nel repo e non in una cartella temporanea:
kb.json non si aggiorna da solo. Se una pagina nuova non finisce qui dentro,
l'assistente non sa che esiste; se ci finisce, comincia a ripeterne i numeri
a voce a ogni visitatore. In entrambi i casi e' una decisione, non un
automatismo — e va potuta rifare fra sei mesi senza riscrivere lo script.

Tocca SOLO la voce della pagina indicata: il resto del file non si muove di
un byte (verificato a fine esecuzione, non promesso).
"""
import io, json, os, re, sys
from html.parser import HTMLParser

LINGUE = ('it', 'en', 'fr', 'de')

# Che cosa entra nel materiale: il testo che argomenta. Restano fuori il
# menu', il piede, i pulsanti e il widget dell'assistente — sono navigazione,
# non contenuto, e nel materiale farebbero solo rumore.
CLASSI = (
    'page-label', 'page-title', 'page-sub', 'pd-nota-alta',
    'pd-eyebrow', 'pd-titolo', 'pd-n-cifra', 'pd-n-testo', 'pd-testo',
    'pd-quindi', 'pd-riquadro-frase', 'pd-riquadro-firma',
    'pd-fonti-tit', 'pd-fonti-testo', 'cta-headline',
    # classi delle altre pagine, se un giorno si rigenerano da qui
    'section-label', 'section-title', 'section-sub', 'venue-type',
    'venue-title', 'venue-desc', 'venue-tag', 'step-title', 'step-desc',
)


class Estrai(HTMLParser):
    """Raccoglie, in ordine di lettura, il testo degli elementi in CLASSI.

    Il testo lo prende da data-<lingua> quando c'e' (e' li' che vive la
    traduzione), altrimenti dal contenuto del tag — serve per le cifre come
    76%, che sono uguali in tutte le lingue e non hanno attributi."""

    def __init__(self, lingua):
        super().__init__(convert_charrefs=True)
        self.lingua = lingua
        self.pezzi = []        # (classe, testo)
        self.dentro = None     # classe dell'elemento che sto leggendo
        self.buffer = []
        self.prof = 0

    def handle_starttag(self, tag, attrs):
        if self.dentro is not None:
            self.prof += 1
            return
        d = dict(attrs)
        classi = (d.get('class') or '').split()
        scelta = next((c for c in classi if c in CLASSI), None)
        if scelta is None:
            return
        testo = d.get('data-' + self.lingua) or d.get('data-it')
        if testo is not None:
            self.pezzi.append((scelta, testo))
        else:
            self.dentro, self.buffer, self.prof = scelta, [], 0

    def handle_data(self, data):
        if self.dentro is not None:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if self.dentro is None:
            return
        if self.prof > 0:
            self.prof -= 1
            return
        self.pezzi.append((self.dentro, ''.join(self.buffer)))
        self.dentro = None


def pulisci(t):
    t = re.sub(r'<[^>]+>', ' ', t)                 # via i tag dentro gli attributi
    t = (t.replace('&nbsp;', ' ').replace('&amp;', '&')
          .replace('&times;', '×').replace('&agrave;', 'à').replace('&egrave;', 'è')
          .replace('&eacute;', 'é').replace('&#39;', "'").replace('&quot;', '"'))
    t = re.sub(r'\s+', ' ', t).strip()
    return re.sub(r'\s+([.,;:!?])', r'\1', t)      # niente spazio prima della punteggiatura


def testo_pagina(html, lingua):
    p = Estrai(lingua)
    p.feed(html)
    fuori = []
    for classe, grezzo in p.pezzi:
        t = pulisci(grezzo)
        if not t:
            continue
        # la cifra e la sua didascalia sono una cosa sola: separate, il modello
        # potrebbe accoppiare il numero sbagliato alla frase sbagliata
        if classe == 'pd-n-testo' and fuori and fuori[-1][0] == 'pd-n-cifra':
            fuori[-1] = ('pd-n', fuori[-1][1] + ' ' + t)
        else:
            fuori.append((classe, t))
    return ' · '.join(t for _, t in fuori)


def main():
    if len(sys.argv) != 2:
        sys.exit('uso: python3 scripts/kb-pagina.py <pagina.html>')
    radice = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nome = os.path.basename(sys.argv[1])
    slug = re.sub(r'\.html$', '', nome)
    html = io.open(os.path.join(radice, nome), encoding='utf-8').read()

    percorso = os.path.join(radice, 'kb.json')
    kb = json.load(io.open(percorso, encoding='utf-8'))
    prima = {l: dict(kb[l]['pagine']) for l in LINGUE}

    for l in LINGUE:
        t = testo_pagina(html, l)
        if not t:
            sys.exit('%s: nessun testo estratto — controlla CLASSI' % l)
        kb[l]['pagine'][slug] = t
        print('%s · %s: %d caratteri' % (l, slug, len(t)))

    # nessuna altra pagina si e' mossa
    for l in LINGUE:
        for k, v in prima[l].items():
            if k != slug and kb[l]['pagine'][k] != v:
                sys.exit('la pagina %s/%s e cambiata: mi fermo' % (l, k))

    io.open(percorso, 'w', encoding='utf-8').write(
        json.dumps(kb, ensure_ascii=False, separators=(',', ':')))
    print('kb.json aggiornato (%s)' % slug)


if __name__ == '__main__':
    main()
