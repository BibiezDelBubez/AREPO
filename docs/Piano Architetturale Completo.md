# **Enigmistica Suite \- Piano Architetturale e Specifiche Tecniche**

Questo documento definisce l'architettura, le tecnologie e le logiche implementative per una suite professionale dedicata agli autori di giochi enigmistici in lingua italiana.

## **1\. Architettura di Base e Stack Tecnologico**

L'applicazione segue rigidamente il pattern **MVC (Model-View-Controller)** per garantire il principio **DRY (Don't Repeat Yourself)** e l'assoluta indipendenza della logica di calcolo dall'interfaccia utente.

### **1.1 Stack Tecnologico**

* **Linguaggio:** Python 3.10+  
* **Interfaccia Grafica (GUI):** PySide6 (Qt for Python). Permette il rendering ad alte prestazioni, essenziale per griglie complesse e manipolazione di immagini (Rebus).  
* **Database:** SQLite con ORM SQLAlchemy.  
* **Esportazione:** ReportLab (per PDF vettoriali) e librerie Qt native per SVG/PNG.  
* **Strutture Dati Motore:** DAWG (Directed Acyclic Word Graph) e Trie, implementati in Cython o Python puro, per ricerche posizionali (es. pattern matching C..A..V.).

### **1.2 Struttura del Progetto (Albero delle Directory)**

enigmistica\_suite/  
├── core/                           \# \[MODEL\] Nessuna dipendenza da PySide6  
│   ├── engine/                     \# Strutture dati e algoritmi a bassa latenza  
│   │   ├── dawg\_builder.py         \# Costruttore del grafo delle parole  
│   │   └── syllabifier.py          \# Motore regex per sillabazione e prosodia  
│   ├── modules/                    \# Logica di business specifica  
│   │   ├── rebus\_logic.py          \# Logica chiavi, grafemi, stereoscopici  
│   │   ├── verse\_logic.py          \# Metrica, rime, combinazioni (bisenzi, zeppe)  
│   │   └── crossword\_logic.py      \# Backtracking, validazione griglia  
│   └── database/  
│       ├── connection.py           \# Setup SQLite  
│       └── models.py               \# Schemi SQLAlchemy  
├── controllers/                    \# \[CONTROLLER\] Intermediari  
│   ├── main\_controller.py          \# Gestore routing e state dell'app  
│   ├── rebus\_controller.py         \# Ascolta UI, interroga core.modules, aggiorna UI  
│   └── ...  
├── ui/                             \# \[VIEW\] Interfaccia utente  
│   ├── assets/                     \# Icone SVG, font, QSS (fogli di stile)  
│   ├── components/                 \# Widget atomici (es. OdooCard, GridCell)  
│   ├── layouts/                    \# Strutture di pagina  
│   └── main\_window.py              \# Finestra root  
├── data/                           \# Dati in locale (sync tramite cloud)  
│   ├── core\_dictionary.sqlite      \# DB pre-compilato READ-ONLY (fornito con l'app)  
│   └── user\_dictionary.sqlite      \# DB utente per overlay e customizzazioni  
└── app.py                          \# Entry point dell'eseguibile

## **2\. L'Interfaccia Grafica (UI/UX Stile "Odoo App")**

L'obiettivo è abbandonare l'estetica antiquata dei software tradizionali per abbracciare un design pulito, *flat* e orientato alla produttività, simile a Odoo o alle moderne app Android Material Design.

### **2.1 Layout Strutturale**

* **Side Navigation (Drawer):** Barra laterale sinistra (colore scuro es. \#2C3E50 o viola Odoo \#714B67) con icone SVG per navigare tra i moduli (Rebus, Versi, Cruciverba, Dizionario). Collassabile a sole icone.  
* **Top Bar:** Briciole di pane (Breadcrumbs), ricerca globale nel dizionario, stato della sincronizzazione del DB.  
* **Workspace (Area Centrale):** Sfondo grigio chiaro (\#F4F5F7). Il contenuto è organizzato in **Cards** (sfondo bianco, border-radius: 8px, box-shadow leggero).

### **2.2 Esempio di implementazione stile via QSS (Qt Style Sheets)**

Le classi PySide6 (es. QFrame, QPushButton) verranno stilizzate globalmente:

/\* Stile base per le Card \*/  
QFrame\#OdooCard {  
    background-color: \#FFFFFF;  
    border: 1px solid \#E0E2E6;  
    border-radius: 8px;  
    padding: 16px;  
}  
/\* Stile per i pulsanti primari (Call to Action) \*/  
QPushButton.PrimaryAction {  
    background-color: \#017E84; /\* Teal moderno \*/  
    color: white;  
    font-family: 'Inter', sans-serif;  
    font-weight: 600;  
    border-radius: 4px;  
    padding: 8px 16px;  
    border: none;  
}  
QPushButton.PrimaryAction:hover { background-color: \#016266; }

## **3\. Gestione Dati e Cloud: Architettura a Doppio Strato (Hybrid Layering)**

Per evitare all'utente di dover inserire centinaia di migliaia di parole a mano, l'applicazione utilizza **due database SQLite simultanei**. In fase di esecuzione, il Core li unisce, dando sempre priorità alle scelte dell'utente.

### **3.1 Livello 1: core\_dictionary.sqlite (Fornito con l'app)**

È un file *Read-Only* precompilato dallo sviluppatore (circa 100-200 MB), che garantisce che il software sia potente fin dal primo avvio.

* **Fonti per la compilazione:**  
  * *Morph-it\!*: Oltre 500.000 forme flesse italiane.  
  * *Wikizionario (Dump XML)*: Per estrarre definizioni base per decine di migliaia di lemmi.  
  * *Liste di frequenza (es. Paisà, corpus ODL)*: Assegnano un "peso" o "rarità" iniziale (es. "CANE" rarità 1, "ORITTEROPO" rarità 5).  
  * *Wikipedia/DB Geografici*: Per nomi di fiumi, città, personaggi storici.

### **3.2 Livello 2: user\_dictionary.sqlite (Il DB Personale)**

Questo è il file "leggero" dell'utente, salvato nella sua cartella Cloud personale (es. Google Drive/OneDrive \- *BYOS: Bring Your Own Storage*). Salva solo le *differenze* rispetto al Core:

* **Override Definizioni:** L'utente aggiunge la sua definizione a una parola già esistente nel Core.  
* **Blacklisting:** L'utente marca una parola del Core come is\_excluded \= True per non vederla mai più generata negli schemi.  
* **Nuovi Inserimenti:** Neologismi o parole mancanti.

### **3.3 Schema Relazionale (User & Core unificati virtualmente)**

\# core/database/models.py  
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey  
from sqlalchemy.orm import declarative\_base, relationship

Base \= declarative\_base()

class Word(Base):  
    \_\_tablename\_\_ \= 'words'  
    id \= Column(Integer, primary\_key=True)  
    term \= Column(String(100), unique=True, index=True) \# Es: "ROMA"  
    length \= Column(Integer, index=True)                \# 4  
    vowel\_pattern \= Column(String(100))                 \# "CVCV" (Utile per ricerca regex)  
    rarity \= Column(Integer, default=3)                 \# 1 (Comune) a 5 (Astruso)  
    is\_flexed \= Column(Boolean, default=False)          \# È una forma declinata/coniugata?  
    is\_proper\_name \= Column(Boolean, default=False)     \# Geografia, Nomi, ecc.  
    tags \= Column(String(200))                          \# "città, italia, 4-lettere"  
    is\_excluded \= Column(Boolean, default=False)        \# Flag per la Blacklist utente  
      
    definitions \= relationship("Definition", back\_populates="word")

class Definition(Base):  
    \_\_tablename\_\_ \= 'definitions'  
    id \= Column(Integer, primary\_key=True)  
    word\_id \= Column(Integer, ForeignKey('words.id'))  
    clue \= Column(String(500))                          \# "La capitale d'Italia"  
    author \= Column(String(100))                        \# Per distinguere "Sistema" vs "Utente"  
    is\_favorite \= Column(Boolean, default=False)        \# Preferenza dell'utente  
      
    word \= relationship("Word", back\_populates="definitions")

## **4\. Specifiche Tecniche dei Moduli Core**

### **4.1 Modulo Rebus, Anarebus e Stereoscopici (In Sviluppo)**

* **Analizzatore Sintattico Rebus:** Dato un testo risolutivo (es. "LA MELA"), l'algoritmo deve scomporlo in \[Grafema\] \+ \[Chiave (Word)\].  
* **Stereoscopici:** Interfaccia PySide6 che carica due immagini affiancate (QLabel con QPixmap). L'utente può tracciare rettangoli di interesse per evidenziare le differenze, associando ad ogni differenza una chiave testuale.  
* **Controller:** Riceve le combinazioni generate dal Core, le filtra interrogando SQLite per verificare l'esistenza delle parole chiave, e le mostra nella View.

### **4.2 Modulo Giochi in Versi (L'Assistente Metrico)**

Questo modulo funge da IDE (Integrated Development Environment) per il poeta enigmista.

* **Motore Sillabico (Prosodia):** Implementazione di un algoritmo basato su Regex che analizza le vocali adiacenti.  
  * Riconosce la **Sinalefe** (vocale finale di parola \+ vocale iniziale della successiva formano una sillaba metrica).  
  * Gestisce forzature tramite tag (es. uso di \<dieresi\>paziente\</dieresi\> per alterare il computo sillabico).  
* **Motore Combinatorio:** Dato un termine base (es. PARCO), interroga il DB per trovare:  
  * *Anagrammi:* PORCA, CARPO  
  * *Zeppe:* P\[o\]RCO \-\> P\[or\]TICO (ricerca P\*RCO in SQLite)  
  * *Cambi:* \[P\]ARCO \-\> \[B\]ARCO, \[M\]ARCO  
* **Editor Visuale (View):** Un QTextEdit avanzato che, alla fine di ogni riga, stampa dinamicamente il numero di sillabe (es. \[11\]) colorandolo di verde se combacia col metro scelto, o di rosso se errato.

### **4.3 Modulo Cruciverba & Derivati**

È il cuore computazionale della suite.

* **Indicizzazione RAM (Il DAWG):** Al lancio del modulo Cruciverba, l'applicazione preleva l'unione dei due DB (core \+ user scartando le esclusioni) e carica la colonna term in un DAWG (Directed Acyclic Word Graph). Questo permette ricerche con pattern posizionali (es. .O.A) in frazioni di millisecondo.  
* **Editor Griglia (View):** Utilizzo di QTableWidget o QGraphicsScene per disegnare la griglia.  
  * Tasto destro: toggle casella nera/bianca.  
  * Simmetria automatica (opzionale): piazzando una casella nera in alto a sinistra, se ne piazza una speculare in basso a destra.  
* **Motore di Backtracking (Core):** Quando l'utente preme "Auto-Completa" su un'area parziale, l'algoritmo esegue una Depth-First Search (DFS) incrociata sul DAWG.  
* **Gestione Varianti:**  
  * *Sillabici:* La cella della griglia accetta fino a 3-4 caratteri. L'interrogazione non viene fatta per lettera, ma per sillabe (richiede la scomposizione sillabica preventiva del DB in memoria).  
  * *Incroci Obbligati:* Schema senza caselle nere predefinite. L'algoritmo valuta anche la validità della posizione di blocco.

## **5\. Esportazione, Stampa e Publishing**

Un aspetto cruciale è la generazione del file finale da inviare alle redazioni o stampare.

* **PDF Vettoriale (ReportLab):** Generazione di PDF multipagina.  
  * Pagina 1: Griglia vuota scalata, numerazione posta in un offset in alto a sinistra del quadrato, font definizioni diviso in colonne (Orizzontali / Verticali).  
  * Pagina 2: Soluzione con griglia riempita.  
* **Immagini High-Res:** Possibilità di esportare singoli componenti in SVG o PNG a 300 DPI tramite le funzioni render() nativamente offerte dalle QGraphicsScene di Qt, garantendo che lo spessore dei bordi e la nitidezza dei font siano tipograficamente ineccepibili.

## **6\. Roadmap Consigliata di Sviluppo**

1. **Fase 1: Data Engineering & Core Database**  
   * Sviluppare gli script Python per fare il *parsing* di Morph-it\! e dei dump di Wikizionario.  
   * Generare il primo core\_dictionary.sqlite (il layer di base sterminato).  
   * Inizializzare repository Python, configurare SQLAlchemy per gestire l'interazione trasparente tra Core DB e User DB.  
2. **Fase 2: Interfaccia Core e "App Shell"**  
   * Creare la finestra principale (MainWindow), la Sidebar di navigazione.  
   * Scrivere i file QSS per stilizzare l'app secondo il design language di Odoo.  
   * Creare la vista "Dizionario" per permettere all'utente di aggiungere definizioni, bannare parole scomode (blacklisting) e aggiungere neologismi.  
3. **Fase 3: Integrazione e Raffinamento Modulo Rebus**  
   * Prendere i tuoi script attuali di Rebus e Anarebus e "spezzarli" secondo MVC.  
   * Implementare le logiche matematico/linguistiche nel Core e collegarle all'interfaccia.  
4. **Fase 4: Modulo Giochi in Versi**  
   * Sviluppare la classe Syllabifier con regex per l'italiano.  
   * Creare il Custom Text Editor per l'evidenziazione sintattica di metrica e rime.  
   * Connettere l'editor al DB per suggerire gli anagrammi.  
5. **Fase 5: Il "Mostro Finale" \- Motore Cruciverba**  
   * Sviluppo della struttura DAWG in memoria partendo dai dati filtrati del DB.  
   * Creazione dell'Editor Grafico per la Griglia (gestione caselle, simmetria, numerazione automatica).  
   * Sviluppo dell'algoritmo di backtracking ricorsivo per l'auto-completamento assistito.  
   * Modulo di esportazione PDF (ReportLab).