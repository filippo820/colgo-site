# colgo-site

Sito di presentazione di Colgo. HTML statico, pubblicato da Netlify così com'è:
**non c'è nessun passo di costruzione dalla sua parte**.

## Come è fatto

- **Le pagine italiane nella radice sono la sorgente.** `/en /fr /de /es` sono
  file veri, **generati** da `scripts/lingue.py` a partire dagli attributi
  `data-en/fr/de/es`. Si modifica l'italiano e si rigenera — mai il contrario.
- `scripts/lingue.py` produce anche **hreflang, canonical, il `sitemap.xml`
  (75 indirizzi) e il blocco `FAQPage`**, che ricava leggendo `.faq-q` / `.faq-a`
  dalla pagina: i dati strutturati non possono dire domande che non ci sono.
- `kb.json` è il materiale dell'**assistente del sito**. Non è una copia
  interna: `api/site-chat.js` (nell'altro repo, `~/stayring`) fa
  `fetch('https://colgo.app/kb.json')` e lo tiene in memoria **dieci minuti**.
  ⚠️ **Si aggiorna con `git push`, non con un caricamento**: non esiste un passo
  separato.
- `scripts/kb-pagina.py` e `scripts/kb-prezzi.py` scrivono voci di `kb.json`
  ricavandole dalle pagine. La whitelist di `kb-pagina.py` **non copre tutte le
  classi**: su molte pagine estrae meno di quello che c'è già dentro `kb.json`.

⚠️ **`widget.py` non esiste.** Un commento in ogni pagina dice che il blocco
dell'assistente è «generato da widget.py — non modificare a mano», ma il
generatore non è su disco né nella storia di questo repo né in quella di
`stayring` (verificato). Finché non ricompare, **quel blocco è il sorgente**:
si modifica lì, e se il generatore torna vanno riportate dentro le modifiche.

## Regole di scrittura già decise

- **Testo**: 16px per il testo che si legge, 15 per i bottoni, 14 per le
  etichette maiuscole spaziate, **mai sotto i 12**. Sta scritto nel blocco
  «Scala tipografica leggibile» di ogni pagina.
- **Nomi dei concorrenti**: la pagina `/confronto` li fa, perché è costruita per
  chi cerca «Colgo vs X». **`kb.json` no**: l'assistente parla con chi è già sul
  sito, e nominarglieli è pubblicità a spese nostre. Passa l'argomento, non
  l'elenco.
- Sul confronto **non si mette in tabella quello che non c'è ancora** (i
  pagamenti), e dove il prezzo del concorrente non è pubblico si scrive «non
  pubblicato» invece di stimarlo.

## Sessione del 27/08/2026 — il sito nascondeva il confronto, e il widget non chiedeva lo spagnolo
Partita da una frase sola: *«sul sito di Colgo non trovo la parte di confronto
con i concorrenti»*. C'era. Il problema era dove.

### 🔴 Una pagina con UN solo link in entrata, dentro il blocco «Link legali»
`/confronto` esisteva in cinque lingue e stava nel sitemap con priorità 0.9 — e
in tutto il sito era linkata **una volta**, nella riga che nel markup si chiama
`<!-- Link legali -->`, in fila con Privacy e Cookie Policy, stesso grigio.
⚠️ E non era sola: **`perche-digitale`, `qr-code-in-camera`,
`catalogo-complesso`, `struttura-stagionale` avevano ZERO link fuori dal piede**
— verificato scandendo il corpo di tutte le pagine, non a occhio.
→ CONFRONTO nel menù delle 71 pagine con barra; piede in **tre righe** (pagine ·
Approfondimenti · legali), così il contenuto non sembra un documento legale; e un
blocco **«Da leggere anche»** con link **contestuali, diversi per pagina**, che
come testo portano il **titolo della destinazione**. Da 0 a 7 link nel corpo per
`/confronto`, 4 · 3 · 3 · 2 per le altre.

### 🔑 La pagina citava tabelle che non esistevano
Il testo diceva già *«non mettiamo IN TABELLA quello che non abbiamo ancora»* e
*«qui una TABELLA non si può fare»* — e nel file **non c'era un solo `<table>`**:
il confronto erano quattro paragrafi di prosa, e in prosa un assistente
attribuisce il prezzo al prodotto sbagliato. Aggiunte due tabelle (il negozio no,
e la pagina spiega perché), **senza una cifra nuova**: ogni numero viene dai
paragrafi o dal JSON-LD di `prezzi.html`.
I nomi dei concorrenti entrano negli `h2` e in tre domande, perché *«Colgo vs
Gastfreund»* è la domanda che si digita: il `FAQPage` passa da 4 a 7 domande ×5
lingue, e lo ricava `lingue.py` dagli attributi.
La didascalia dice **per cosa** si paga, altrimenti si legge «29 contro 39» e
Colgo sembra caro: diversi concorrenti contano **per alloggio**, quindi partono
più bassi e crescono con la struttura. «Diversi», non «tutti»: per singolo
prodotto il dato non è pubblico.

### 🔴 L'assistente citava un prezzo vecchio, in produzione
`kb.json` dava **Ristorazione Pro a 69 €/690 €** quando il listino dice 59/590:
**dieci euro di troppo, a voce, a ogni visitatore, in quattro lingue**. E diceva
«quattro lingue» quando `prezzi.html` ne dichiara cinque. Verificato con `curl`
che fosse ancora così sul sito pubblico prima di correggerlo.
Aggiunto il blocco **spagnolo**: `perche-digitale` generato da `kb-pagina.py` con
lingua `es`, **197 segmenti presi dal sito** (dal `data-es` dello stesso
elemento, così l'assistente usa le parole delle pagine e non parafrasi), 95
segmenti e 18 domande tradotti.

### 🔴 Il sito si contraddiceva sulle lingue, in tre modi
- Il **testo visibile** diceva `4 LINGUE` mentre i `data-*` dicevano 5, su
  `come-funziona`, `hotel`, `per-chi`. Le pagine italiane sono la sorgente e
  `lingue.py` **non ne riscrive il corpo**: chi leggeva in italiano vedeva 4,
  tutti gli altri 5.
- **`data-es` scritto due volte** sullo stesso elemento, negli stessi tre punti.
- **`IT · EN · DE · FR · ES · ES`**: spagnolo elencato due volte, in quattro
  lingue su cinque, testo visibile compreso.

### 🔴 Il widget non chiedeva mai lo spagnolo
`api/site-chat.js` accetta `es` da tempo e `kb.json` ora ce l'ha, ma nel blocco
dell'assistente c'era `var L = ['it','en','fr','de']`: da `/es/` la funzione
`lang()` non trovava `es` e ripiegava su `it`, quindi partiva **`lingua:'it'`** e
la risposta tornava in italiano. **La correzione all'endpoint era arrivata a un
widget che non la chiedeva.** Verificato in produzione *prima* di spingere.
⚠️ `T` ha una voce per lingua **nell'ordine di `L`**: senza la quinta, `T[k][4]`
è `undefined` e `dice()` ripiega su `T[k][0]`, di nuovo italiano. Aggiunte tutte
e sei. Verificato intercettando la `fetch`: da `/es/` parte `lingua:"es"`, e le
altre quattro non si sono spostate di posto.
🔑 Confermato dalla risposta vera: *«¿Es un **alojamiento (hotel, B&B, casa
rural)**…?»* — quelle parole sono testualmente la voce spagnola di `kb.json`, non
spagnolo generico del modello. La catena si vede tutta: widget → endpoint → kb.

### 🔴 Testo piccolo: la passata del 16/08 veniva annullata dopo
Misurato il **valore calcolato dal browser** su tutte e 75 le pagine, a 1280 e a
390px, aprendole in iframe — non leggendo il CSS. Ed è lì che stava il difetto:
`.faq-category` è **nella** scala a 14px, ma su quattro pagine una regola locale
a 12px arriva **dopo** il blocco e vince. Le pagine e i blocchi nati dopo il
16/08 non hanno mai ricevuto la scala (il blocco stagionale di `prezzi.html`
aveva cinque classi sotto i 14; `.stag-req` è una **frase**, portata a 16).
⚠️ **Il peggiore era invisibile leggendo il CSS**: i numeri `01`–`04` negli SVG
di `come-funziona` e `hotel` hanno `font-size="12"` dentro un `viewBox` da 1200
reso a 1000 → **scala 0,83 → 10px sullo schermo**. Portati a 16 (13,3 resi).
E `.colgo-nota` stava a **10,5px** ed è una frase intera: era il testo più
piccolo del sito.

### 📐 Da ricordare
- **Per il testo piccolo, misurare il reso, non leggere le regole.** Il caso
  degli SVG non compare in nessun `font-size` del CSS.
- **Due terminali sullo stesso repo**: `main` si muove sotto i piedi. `fetch`
  prima di spingere, e **controllare il conteggio delle righe del proprio
  commit** — il mio doveva essere 750 tolte e 750 aggiunte, tutte del widget, ed
  è così che ho escluso di aver inghiottito il lavoro dell'altro con `git add -A`.
- **`/llms.txt`** con i limiti del prodotto in cima (niente PMS, niente messaggi
  automatici, niente pagamenti, niente Glovo/Deliveroo): un riassunto che li
  omette è sbagliato, e tanto vale scriverli noi.

## Sessione del 21/10/2026 — SEO tecnica, fase 1 (branch `seo-fase-1`, pubblicato)
Partita da un audit. Un commit per punto, niente su `main` finché non c'è l'ok.
**Pubblicato il 21/10/2026 con il merge `91efaf0`** (`--no-ff`, ramo `seo-fase-1`
conservato). Verificato in produzione con curl: `/prezzi.html` → 301 → `/prezzi`
→ 200 (un salto, nessun loop), `/en/xyz` → 404 con la pagina inglese, font
`immutable` per un anno, schermate 7 giorni, HTML ancora `max-age=0`.

### 🔴 Title e description: la home non diceva cosa vende
Home a 113 caratteri di description, prezzi e FAQ con title da 11–14
(«FAQ — Colgo»). Riscritti in cinque lingue, **senza cifre di prezzo** (un
prezzo nei meta invecchia in cinque posti alla volta: vedi kb.json il 27/08).
Ora **tutte le 75** hanno title ≤ 60 e description 120–160; fuori misura c'erano
anche `/en/privacy` (101) e `/fr/confronto` (161).

### 🔑 L'immagine social è quadrata
`colgo-og.png` è **1254×1254**, non 1200×630. Non ritagliata: il logo è al
centro e largo quanto l'immagine, quindi il taglio 1,91:1 di
`summary_large_image` lo lascia intero. Un'immagine 1200×630 dedicata resta da
fare. `og:locale:alternate` e l'alt tradotto li scrive `lingue.py`.

### 📐 lingue.py ora genera anche
- **BreadcrumbList** (Home › pagina) sulle 70 interne, con le etichette che il
  sito usa già nel menu. ⚠️ Il vecchio blocco si toglie **prima** di toccare il
  FAQPage: la pulizia del FAQPage cerca il suo blocco attaccato a `</head>`, e
  con le briciole in mezzo si porterebbe via anche loro.
- La **description del SoftwareApplication** della home, sostituita per lingua
  (il blocco JSON-LD viene copiato nelle tradotte).
- **`404.html` per lingua** (lista `SERVIZIO`: fuori da sitemap, hreflang e
  briciole). La sorgente è `404.html` italiana, nata dalla testa di `faq.html`.

### 🔑 Netlify
- `/prezzi` e `/prezzi.html` rispondevano **entrambi 200**. `_redirects` ha 75
  regole `301!` esplicite. Verificate con **`netlify dev`** (150 casi, nessun
  loop) — **non** su un deploy vero: per questo sito Netlify non fa deploy dei
  branch. Sono in un commit a sé: se in produzione danno guai, si reverte solo
  quello.
- ⚠️ **I link interni puntano ancora a `/pagina.html`**: con i 301 ogni clic
  interno fa un salto. Da sistemare (in `lingue.py`/`rifai_link` e nelle
  sorgenti) prima o insieme alla pubblicazione.
- `netlify dev` **sovrascrive sempre `cache-control`**: `_headers` lo legge
  (verificato con un'intestazione di prova) ma la cache lunga si vede solo in
  produzione.

### 🔑 Font in casa, identici al pixel
Google serve **font variabili**: 9 file in tutto, non 18 statici. Usati quelli
(con la versione nel nome, quindi `immutable` è sicuro). Serve anche il
sottoinsieme **vietnamese**: gli accenti combinanti U+0300/0301 di `prezzi` e
dello spagnolo arrivano da lì. `privacy.html` non usava font web e non li ha.

### 📐 Da ricordare
- **Per confrontare screenshot, scattare a fasce scorrendo**, non a pagina
  intera: lo screenshot "fullPage" sposta barra e bottone fissi e, se si
  spengono le animazioni, lascia il titolo dell'hero a opacità zero. Fermare
  `setInterval` (l'occhio) e le animazioni infinite. Le schermate JPG danno
  rumore anche confrontando una versione con se stessa.
- 🔴 **GA4 parte prima del consenso, e il banner non esiste**: `gtag` si carica
  nel `<head>` di tutte le 75 pagine, senza Consent Mode. L'informativa invece
  dice che i cookie analitici «richiedono il tuo consenso» e cita «il banner
  presente al primo accesso». Solo riferito, non toccato.
