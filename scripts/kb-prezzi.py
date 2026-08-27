#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rimette i prezzi STAGIONALI nella voce «prezzi» di kb.json, in tutte e cinque
le lingue.

    python3 scripts/kb-prezzi.py

Perche' esiste. La voce «prezzi» di kb.json — il materiale che l'assistente
del sito cita — elenca per ogni piano il prezzo al mese e all'anno. Lo
stagionale, aggiunto alla pagina il 27/08 come terzo stato dell'interruttore,
non c'era: l'assistente rispondeva correttamente «59€» a chi chiedeva il Pro,
e a chi chiedeva lo stagionale parlava di mensile e annuale, perche' non
sapeva che esistesse un terzo prezzo.

⚠️ E non e' un dimenticanza isolata: il generatore originale di kb.json
(«kb.py», citato nei commenti) NON E' MAI STATO NEL REPO — verificato su tutta
la storia di git. Quindi quella voce si puo' solo scrivere a mano, ed e'
esattamente il modo in cui i numeri divergono. Questo script sta nel repo
apposta: e' ripetibile, e va rilanciato ogni volta che i prezzi cambiano.

Come sono scelte le parole. NON sono tradotte qui: si ricavano dalla pagina
vera. L'etichetta sotto il prezzo («per 7 mesi +IVA») esiste gia' in tutte e
cinque le lingue nel markup di prezzi.html; lo script la prende da li' e le
toglie il suffisso IVA nello stesso modo in cui la voce annuale di kb.json e'
gia' priva del suo. Cosi' non si inventa terminologia, e quello che dice
l'assistente non puo' divergere da quello che il visitatore legge a schermo.

Idempotente: se lo stagionale c'e' gia', non tocca niente. E tocca SOLO la
voce «prezzi»: il resto del file non si muove di un byte (verificato a fine
esecuzione, non promesso).
"""
import json, os, re, sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINGUE = ('it', 'en', 'fr', 'de', 'es')


def testo(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


def dati_pagina(lingua):
    """Dalla pagina vera: i sei stagionali in ordine, e le etichette annuale/stagionale."""
    f = os.path.join(RADICE, '' if lingua == 'it' else lingua, 'prezzi.html')
    s = open(f, encoding='utf-8').read()

    stag = re.findall(r'data-seasonal="(\d+)"', s)
    if len(stag) != 6:
        sys.exit('%s: attesi 6 data-seasonal, trovati %d — la pagina e cambiata?' % (f, len(stag)))

    def etichetta(classe):
        m = re.search(r'<span class="%s"[^>]*>(.*?)</span>' % classe, s, re.S)
        if not m:
            sys.exit('%s: manca <span class="%s">' % (f, classe))
        return testo(m.group(1))

    return stag, etichetta('pp-a'), etichetta('pp-s')


def main():
    p = os.path.join(RADICE, 'kb.json')
    prima = open(p, encoding='utf-8').read()
    kb = json.loads(prima)

    for lingua in LINGUE:
        stag, lab_ann, lab_stag = dati_pagina(lingua)
        voce = kb[lingua]['pagine']['prezzi']
        pezzi = voce.split(' || ')

        # L'etichetta annuale in kb.json e' priva del suffisso IVA che invece
        # ha a schermo: qui misuro quel suffisso e lo tolgo alla stagionale.
        base_ann = next((b for b in (lab_ann[:i] for i in range(len(lab_ann), 0, -1))
                         if b.strip() and b.strip() in voce), None)
        if not base_ann:
            sys.exit('%s: "%s" non compare nella voce prezzi' % (lingua, lab_ann))
        base_ann = base_ann.strip()
        suffisso = lab_ann[len(base_ann):]                  # es. " +IVA", " zzgl. MwSt."
        base_stag = lab_stag[:len(lab_stag) - len(suffisso)].strip() if suffisso else lab_stag

        n = 0
        for i, pezzo in enumerate(pezzi):
            m = re.search(r'(\d+€ %s)(?:,\s*\d+€ %s)?(\s*\()'
                          % (re.escape(base_ann), re.escape(base_stag)), pezzo)
            if not m:
                continue
            pezzi[i] = pezzo[:m.end(1)] + ', %s€ %s' % (stag[n], base_stag) + pezzo[m.start(2):]
            n += 1
        if n != 6:
            sys.exit('%s: attesi 6 piani, trovati %d' % (lingua, n))

        kb[lingua]['pagine']['prezzi'] = ' || '.join(pezzi)
        print('  %s  «%s»  →  %s' % (lingua, base_stag, ' '.join(stag)))

    # senza newline finale, come fa kb-pagina.py: sono due script che scrivono
    # lo stesso file, e se divergessero su questo ogni giro alternato
    # produrrebbe una differenza fantasma.
    dopo = json.dumps(kb, ensure_ascii=False, separators=(',', ':'))
    open(p, 'w', encoding='utf-8').write(dopo)

    # verifica: e cambiata SOLO la voce prezzi
    a, b = json.loads(prima), json.loads(dopo)
    for l in LINGUE:
        for k in a[l]:
            if k == 'pagine':
                for pg in a[l][k]:
                    if pg != 'prezzi' and a[l][k][pg] != b[l][k][pg]:
                        sys.exit('ERRORE: toccata anche la pagina %s/%s' % (l, pg))
            elif a[l][k] != b[l][k]:
                sys.exit('ERRORE: toccata anche la chiave %s/%s' % (l, k))
    print('\n  ✓ toccata solo la voce «prezzi»; il resto di kb.json e identico')


if __name__ == '__main__':
    main()
