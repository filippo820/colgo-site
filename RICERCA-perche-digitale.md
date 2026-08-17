# Ricerca: «Perché digitale» — dati per il sito Colgo

> Documento fornito dall'utente il **16/08/2026**. Riportato integralmente qui sotto
> (sezione «Documento originale»). Sopra, solo lo stato di ciò che è già stato fatto,
> perché una parte era già in produzione quando il documento è arrivato.

---

## Stato al 17/08/2026 — tutto fatto e in produzione

| pezzo del documento | stato |
|---|---|
| Striscia numeri in `index.html` | ✅ **in produzione** (17/08) |
| Pagina `perche-digitale.html` | ✅ **in produzione** (17/08) |
| Link nel piede (non nel menu) | ✅ **in produzione** (17/08), su 10 pagine |
| Chatbot sul sito | ✅ fatto il 16/08 — vedi sotto |

### Com'è stata realizzata (17/08)

**Striscia in home** — dopo la sezione IL PROBLEMA, non più in alto: lì il lettore ha
appena letto che i quattro modi di comunicare non funzionano, e la striscia è la prova
che non è un'opinione nostra. Quattro numeri scelti dall'utente: 5× scansioni QR dal
2021 · 9 su 10 ristoranti full-service (USA) · 76% dei viaggiatori nella propria lingua
· 2 su 3 hotel a corto di personale.

**Pagina** — sei blocchi in ordine di lettura (adozione → lingua → persone → costo della
carta → dove va il mondo → ambiente), ognuno con le sue cifre e una riga di conseguenza
per chi legge. Il riquadro col framing «più servizi con le stesse persone» sta nel
blocco sulle persone. La nota sulle fonti sta **prima** degli inviti finali: chi ha
appena letto ventuno numeri ha diritto di sapere quali reggono, prima che gli si chieda
qualcosa.

**Regola sulle fonti applicata alla lettera.** Tolti: il nome Four Seasons e quello di
McKinsey (non li possiamo linkare), il +25% di soddisfazione e il +12-18% di ricavi —
sono la promessa che, se non si avvera, costa il cliente. Smussati: i costi di stampa
(«qualche migliaio di euro l'anno, secondo stime di settore», detto in chiaro che la
stima viene da chi vende software) e i ~14 minuti.

**Due cose emerse verificando, che nel documento non c'erano:**

1. **I due dati sulla CO2 si contraddicono fra loro.** «2,5 g per foglio» e «3,3 kg per
   kg di carta» non stanno insieme: un A4 da 80 g/m² pesa 5 g, quindi il secondo ne
   darebbe ~16 g, sei volte tanto. Sulla pagina ne è rimasto **uno solo**, quello per
   chilo, senza equivalenze per foglio che il lettore possa rifare a mente.
2. **L'argomento ecologico, fatto onestamente, è piccolo** alla scala di una singola
   struttura: chili, non tonnellate. Su richiesta dell'utente («deve convincere») il
   blocco è stato scritto per convincere **cambiando perno, non gonfiando le cifre**:
   è l'unica scelta ambientale che non chiede di rinunciare a niente (la più pulita è
   anche la più economica e la più veloce da aggiornare); il foglio plastificato non è
   carta ma un composito che il riciclo non separa; ed è l'unico argomento della pagina
   che il cliente vede da solo. La frase «una struttura da sola non salva una foresta»
   è rimasta apposta: è quella che rende credibile il resto.

**`kb.json`** — la pagina è stata aggiunta al materiale dell'assistente in tutte e
quattro le lingue, con un nuovo `scripts/kb-pagina.py` che **resta nel repo** (il
generatore precedente viveva in una cartella temporanea ed è andato perduto). Aggiorna
una sola pagina per volta e si ferma da solo se qualcos'altro nel file si è mosso.

⚠️ La voce `home` di `kb.json` è ferma alle 18:11 del 16/08 e non è stata rigenerata:
riscriverla cambierebbe l'intera voce. I quattro numeri della striscia l'assistente li
conosce comunque, perché arrivano dalla pagina nuova.

### Il chatbot è già in piedi, e coincide quasi del tutto con la specifica

Costruito il 16/08/2026, prima che questo documento arrivasse. Confronto punto per punto:

| specifica | com'è stato fatto |
|---|---|
| widget in basso a destra | ✅ così |
| risponde a «quanto costa», «serve installare», «funziona per un campeggio» | ✅ provato: prezzi esatti per settore |
| base di conoscenza dai contenuti del sito, **niente invenzioni** | ✅ `kb.json` **estratto dalle pagine** (13 FAQ + 9 pagine + i 6 listini letti dalle card), rigenerabile con `scratchpad/kb.py`. Non una copia scritta a mano: una copia diverge al primo cambio di prezzo, e diverge in silenzio |
| API Claude, stessa dello stack | ✅ `claude-haiku-4-5`, stessa `ANTHROPIC_API_KEY` già usata per le traduzioni del catalogo |
| multilingua IT/EN/FR/DE | ✅ tutte e quattro, risponde nella lingua della pagina anche se il visitatore scrive in un'altra |
| fallback onesto → colgoapp@gmail.com | ✅ frase fissa, provata: a «vi integrate con Zucchetti?» risponde che non lo trova nel sito |
| **dove ospitare la logica** | Vercel edge (`api/site-chat.js`), **non** Netlify Functions: la chiave Anthropic è già lì, e il sito marketing è statico su Netlify |
| **costi per visitatore** | ~1 centesimo di euro per conversazione da cinque domande. Il materiale è marcato come riutilizzabile: la prima domanda lo paga per intero, le successive un decimo |
| **rate limiting anti-abuso** | ✅ nel **database**, non in memoria (l'edge runtime è senza stato e replicato): 15 domande/ora e 60/giorno per visitatore, **500/giorno in totale**. Migration 069 + 070. Dell'IP si salva solo l'impronta, per due giorni |
| «se ha senso ora in fase pilota o dopo» | fatto ora — è costato mezza giornata e il tetto rende il caso peggiore di pochi euro |

**Oltre la specifica:** dal 16/08 l'assistente non è solo uno sportello informazioni ma
**accompagna alla prova** — chiede di che attività si tratta, dà il prezzo di quel settore
soltanto, e propone la demo a chi guarda o i 30 giorni a chi ha già capito. Se qualcuno
dice che non è interessato, si ferma.

### Nota per chi scriverà la pagina «perché digitale»

La regola sulle fonti scritta in fondo al documento (**«secondo dati di settore» / «gli
studi indicano», senza inchiodarsi a cifre al centesimo, senza citare fonti che non
possiamo linkare**) vale anche per il **chatbot**: se la pagina entra nel sito, i suoi
numeri finiscono automaticamente in `kb.json` e l'assistente comincerà a citarli. Un
numero fragile scritto in una pagina diventa un numero che un assistente ripete a voce
a ogni visitatore — quindi va scelto con più cura di quanta ne meriterebbe da solo.

---

## Documento originale

Obiettivo: aggiungere al sito marketing (colgo.app) una sezione/pagina che argomenta con
dati perché un catalogo digitale batte i vecchi metodi (cartaceo, telefonate, richieste
ripetute alla reception).

### STRUTTURA CONSIGLIATA (approccio ibrido)

1. **Striscia numeri in `index.html`** — 3-4 statistiche chiave, una riga ciascuna,
   scorribili in 5 secondi. Dà credibilità immediata senza appesantire la home.
2. **Nuova pagina dedicata `perche-digitale.html`** — i 6 argomenti completi qui sotto,
   con contesto. Stesso stile/palette/i18n a 4 lingue (IT/EN/FR/DE) del resto del sito.
3. **Link alla nuova pagina nel footer** (non nel menu principale, per non affollarlo).
4. **Uso extra**: la pagina serve come link da mandare in email/DM di outreach
   («qui i numeri del perché»).

### I 6 ARGOMENTI CON DATI

#### 1. L'adozione QR è la nuova baseline (non una moda)
- Scansioni QR: **+433%** dal 2021
- **87%** dei ristoranti full-service usa menù QR
- Utenti USA che scansionano QR: oltre **100 milioni** nel 2025 (erano ~52M nel 2020)
- **96%** degli albergatori investe in tecnologia contactless
- **94%** degli ospiti preferisce check-in/out da mobile
- I menù QR riducono i tempi di servizio di **~14 minuti** in media

#### 2. Il mercato giapponese/asiatico (dove va il mondo)
- In Giappone il **62,1%** dei consumatori usa ordinazione mobile/QR al ristorante
  (+20% vs 2022)
- Oltre il **60%** dei ristoranti nelle grandi città giapponesi offre ordinazione QR —
  adozione superiore alla maggior parte dei mercati
- Mercato self-ordering giapponese proiettato a **500 miliardi di yen entro il 2028** —
  cambiamento strutturale, non moda
- Driver: **61%** dei ristoranti giapponesi segnala carenza di personale (stesso problema
  dell'hospitality italiana)
- Anche in Europa: in Francia il **59%** preferisce menù QR al cartaceo

#### 3. Barriera linguistica (il multilingua ha numeri dietro)
- **76%** dei viaggiatori preferisce interagire nella propria lingua (**84%** tra i non
  anglofoni)
- **61%** degli ospiti ordinerebbe più volentieri room service/attività se potesse farlo
  nella propria lingua
- Four Seasons: comunicare nella lingua madre dell'ospite = **+26%** punteggi di
  soddisfazione tra viaggiatori internazionali
- Chiamate multilingue gestite da persone: **3-5x più lente**

#### 4. Costi reali del cartaceo
- Ristorante da 50 tavoli: **~$2.400-4.800/anno** solo di stampa menù
- Locali indipendenti: media **~$3.847/anno** in stampa menù (senza contare tempo staff
  per progettare/plastificare/sostituire)
- Digitale riduce l'uso di carta fino al **75%**
- Strutture con guest messaging: **-30%** chiamate alla reception, **+25%** punteggi
  soddisfazione
- Upselling via messaggistica: **+12-18%** ricavi per prenotazione

#### 5. Argomento ecologico
- Ogni kg di carta prodotta = **~3,3 kg di CO2** rilasciata
- Ogni foglio stampato = **~2,5 g di CO2**
- Industria carta: **13-15%** di tutto il legno raccolto globalmente
- 1 tonnellata di carta = **38.000-75.000 litri d'acqua** consumata
- Settore carta/cellulosa: **5° consumatore mondiale di energia** (~4-5% dell'energia
  globale)
- Carta in discarica → metano, gas serra **25x più potente** della CO2
- 1 tonnellata di carta riciclata salva **~17 alberi** (non stamparla affatto è ancora
  meglio)

**Angolo pratico per il sito:** un hotel che ristampa menù/listini/info più volte a
stagione può tradurre fogli → CO2 → equivalenze concrete.

#### 6. Personale che lavora meglio (argomento forte per l'Italia)
- **67%** degli hotel affronta ancora carenza di personale (era 80%+ nel 2023)
- McKinsey: automazione + analytics riducono i carichi operativi fino al **30%**
- Studi di settore: automazione = **+20-35%** produttività
- Circolo vizioso senza tecnologia (documentato): team sotto organico → straordinari e
  troppe mansioni → livello servizio cala → offerta ridotta (es. orari ristorante
  limitati) → reputazione ne risente
- Upselling automatizzato (early check-in, late check-out, colazione, spa) cattura ricavi
  che un team sotto organico non ha la banda di proporre — può ripagare da solo il costo
  del software
- Lato umano: liberare lo staff dai compiti ripetitivi = migliore qualità di vita
  lavorativa, più tempo per il tocco personale

> **FRAMING IMPORTANTE:** comunicare «più servizi con le stesse persone», **NON** «meno
> personale» — coerente con lo slogan «Digitale dove serve. Umano dove conta.»

### NOTA SULLA QUALITÀ DELLE FONTI (per il copy)

- **Dati più solidi:** adozione QR (Statista, National Restaurant Association, report di
  settore concordanti) e Giappone (più fonti indipendenti convergono su ~60%)
- **Dati più deboli:** costi stampa e percentuali soddisfazione vengono spesso da blog di
  vendor (bias promozionale possibile)
- **REGOLA PER IL SITO:** usare formule tipo «secondo dati di settore» / «gli studi
  indicano» senza inchiodarsi a cifre al centesimo. Evitare di citare fonti specifiche
  che non possiamo linkare direttamente.

### IDEA AGGIUNTIVA: CHATBOT SUL SITO

Aggiungere al sito marketing una chat che risponde alle domande e curiosità dei
visitatori (potenziali clienti gestori).

Concetto:
- Widget chat sul sito (angolo in basso a destra, pattern standard)
- Risponde a domande tipo: «quanto costa?», «serve installare qualcosa?», «funziona per
  un campeggio?», «come funzionano i PIN?»
- Base di conoscenza: contenuti già esistenti del sito (FAQ, come funziona,
  organizzazione, pagine settore) — il chatbot **NON deve inventare**, solo attingere da
  contenuti approvati
- Coerenza con il resto dello stack: valutare se usare l'API Claude (già usata per le
  traduzioni del catalogo) con un system prompt che limita le risposte ai contenuti del
  sito
- Multilingua: deve rispondere nella lingua del visitatore (IT/EN/FR/DE minimo), coerente
  con il posizionamento multilingua del prodotto
- Fallback onesto: se non sa rispondere, invita a scrivere a colgoapp@gmail.com invece di
  inventare
- Da valutare con Claude Code: costi API per visitatore, rate limiting anti-abuso, dove
  hostare la logica (Netlify Functions? Vercel edge function sull'app?), e se ha senso
  ora in fase pilota o dopo

> **Mostrami il piano prima di applicare qualsiasi modifica.**
