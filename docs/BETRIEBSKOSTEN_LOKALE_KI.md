# Betriebskosten: Lokale KI fuer chmusicpro

**Stand:** Februar 2026
**Zielgruppe:** Business / Sales
**Szenario:** 10 User, lokale KI via Ollama, alle Sprachen (DE, EN, FR, IT, ES)

---

## Anforderungen

### Geschaeftliche Anforderungen

- **Zielgruppe:** Songwriter und Musikproduzenten (Einzelpersonen, kleine Labels)
- **Startphase:** 10 registrierte User pro Mandant (Domain)
- **Sprachen:** Deutsch, Englisch, Franzoesisch, Italienisch, Spanisch
- **Datenhoheit:** Alle Daten und KI-Verarbeitung sollen in der Schweiz bleiben ("Swissness") -- keine Cloud-APIs wie OpenAI oder Claude
- **Verfuegbarkeit:** Buerozeiten (ca. 8-18 Uhr), kein 24/7-SLA noetig
- **Antwortzeit:** Maximal 10-15 Sekunden pro KI-Anfrage im Normalbetrieb

### Technische Anforderungen

- **KI-Modell:** Open-Source LLM (Qwen3-32B) via Ollama, lokal betrieben
- **GPU zwingend:** LLM-Inferenz erfordert dedizierte GPU-Hardware fuer akzeptable Antwortzeiten (siehe Abschnitt "Warum eine VPS ohne GPU nicht funktioniert")
- **Betriebssystem:** Linux (Ubuntu 24.04, ARM64) bevorzugt -- professioneller Serverbetrieb
- **Netzwerk:** HTTPS, erreichbar ueber das Internet (Reverse Proxy vor der App)

### Annahmen zur Nutzung (wichtig fuer die Dimensionierung)

Die KI wird **nicht permanent** beansprucht. Der typische Arbeitsablauf eines Songwriters:

1. User arbeitet **1-5 Minuten** am Text (schreiben, lesen, nachdenken)
2. Klickt auf "Generieren", "Verbessern" oder "Uebersetzen"
3. Wartet **wenige Sekunden** auf das KI-Ergebnis (~60-80 Tokens)
4. Arbeitet wieder **1-5 Minuten** manuell weiter

Das heisst: Pro User entsteht **alle 2-5 Minuten eine KI-Anfrage**, die jeweils **7-10 Sekunden** GPU-Zeit benoetigt. Bei 10 registrierten Usern sind erfahrungsgemaess:

- **2-4 gleichzeitig eingeloggt** (nicht alle arbeiten zur selben Zeit)
- **1-2 davon gerade am Generieren** (die anderen tippen, lesen, denken)
- **Gleichzeitige KI-Anfragen sind selten** -- die GPU ist den Grossteil der Zeit idle

Diese Annahme ist zentral fuer die Dimensionierung: Ein einzelner GPU-Server reicht fuer 10 User, weil die KI-Last **sporadisch** anfaellt und sich zeitlich verteilt.

---

## Was macht die KI in der App?

Die KI unterstuetzt Songwriter bei ihrer taeglichen Arbeit:

| Funktion | Beispiel |
|----------|---------|
| **Songtexte schreiben** | Aus einer Idee einen kompletten Songtext generieren |
| **Texte verbessern** | Einzelne Strophen umschreiben, verdichten, verfeinern |
| **Uebersetzen** | Lyrics zwischen DE/EN/FR/IT/ES uebersetzen -- poetisch, nicht woertlich |
| **Beschreibungen** | Marketing-Texte fuer Streaming-Plattformen generieren |
| **Kreativ-Workshop** | Brainstorming, Mindmaps, Reimvorschlaege, Wortbibliotheken |
| **Titel finden** | Passenden Songtitel aus dem Text ableiten |
| **Prompts verbessern** | Eingaben fuer Bild- und Musik-KI optimieren |

Alle Funktionen erzeugen **kurze Textantworten** (eine Strophe, ein Titel, ein Absatz) -- keine langen Dokumente oder Analysen. Das haelt die Tokens pro Anfrage niedrig (~60-80 Tokens Output) und die Antwortzeiten kurz.

---

## Welches KI-Modell?

| Rolle | Modell | Wofuer |
|-------|--------|--------|
| **Hauptmodell** | Qwen3-32B | Lyrics, Uebersetzung, Workshop, Beschreibungen -- alle anspruchsvollen Aufgaben |
| **Schnellmodell** | Qwen3-8B | Titel generieren, schnelle Prompt-Verbesserungen |

Beide Modelle sind **Open Source** und **lizenzfrei** nutzbar (Apache 2.0). Keine laufenden Lizenzkosten. Alle 5 Zielsprachen nativ unterstuetzt.

**Qualitaetseinschaetzung Qwen3-32B:**

| Aufgabe | Qualitaet |
|---------|-----------|
| Einfache Lyrics (EN/DE) | Sehr gut |
| Komplexe Lyrics (Metaphern, Poetik) | Gut |
| Uebersetzen (DE/EN/FR/IT/ES) | Gut |
| Beschreibungen & Marketing-Texte | Sehr gut |
| Workshop (Brainstorming, Reime) | Sehr gut |

---

## Antwortzeiten

Was erlebt der User, wenn er auf "Generieren" klickt?

| Situation | Wartezeit fuer eine Strophe | Bewertung |
|-----------|----------------------------|-----------|
| 1-2 User gleichzeitig aktiv | 7-10 Sekunden | Angenehm |
| 3-4 User gleichzeitig aktiv | 10-20 Sekunden | OK |
| 5+ User gleichzeitig (selten) | 20-40 Sekunden | Spuerbar, aber ertraeglich |

Basierend auf gemessenen **~9-10 Tokens/Sekunde** fuer Qwen3-32B auf dem NVIDIA GB10 (HP ZGX Nano). Eine Strophe umfasst ca. 60-80 Tokens. Wie im Abschnitt "Annahmen zur Nutzung" beschrieben, sind gleichzeitige KI-Anfragen selten -- die meisten Wartezeiten liegen im Bereich 7-10 Sekunden.

**Wichtig:** Ohne GPU-Hardware (z.B. auf einer VPS mit nur CPU) wuerden dieselben Anfragen **2-5 Minuten** statt Sekunden dauern. Das ist fuer ein kommerzielles Produkt nicht tragbar.

---

## Varianten und was sie kosten

### Variante A: Eigene Hardware kaufen (HP ZGX Nano G1n AI Station)

Die HP ZGX Nano G1n ist eine kompakte AI-Workstation mit NVIDIA GB10 Grace Blackwell Superchip. Laeuft nativ unter Ubuntu 24.04 (ARM64) -- konzipiert als AI-Server, kein umfunktionierter Desktop-Rechner.

| Eigenschaft | Wert |
|-------------|------|
| **Prozessor** | NVIDIA GB10 Grace Blackwell (20-Core ARM64 CPU + Blackwell GPU) |
| **RAM** | 128 GB kohaerenter Unified Memory (CPU + GPU geteilt) |
| **Speicher** | 1 TB NVMe SSD |
| **GPU-Leistung** | 1'000 TOPS (FP4), Modelle bis 200B Parameter lokal moeglich |
| **Betriebssystem** | Ubuntu 24.04 / NVIDIA DGX OS (Linux-nativ) |
| **Stromverbrauch** | 30-50W idle, ~160W Inferenz, max 206W |
| **Formfaktor** | Kompakt (Mini-PC Groesse), rack-faehig |

| Posten | Einmalig | Monatlich |
|--------|---------|-----------|
| HP ZGX Nano G1n (128GB, 1TB) | CHF 3'920 | -- |
| Colocation (Schweizer Rechenzentrum) | -- | ~CHF 150 |
| Strom (~100W Durchschnitt, 24/7) | -- | ~CHF 40 |
| **Total** | **CHF 3'920** | **~CHF 190** |

| | 1. Jahr | 3 Jahre | Pro User/Monat (10 User) |
|---|---------|---------|--------------------------|
| **Kosten** | ~CHF 6'200 | ~CHF 10'760 | **~CHF 30** |

**Vorteile:** Guenstigste Variante auf 3 Jahre. Professionelle AI-Hardware (kein Desktop als Server). Linux-nativ (ARM64, Ubuntu 24.04). NVIDIA Blackwell GPU mit echten Tensor Cores. Kompakt und rack-faehig. Modelle bis 200B Parameter moeglich.
**Nachteile:** Hardware-Investition vorab. Bei Defekt muss Ersatz beschafft werden.

*Preis: CHF 3'920 bei Digitec (Stand Februar 2026)*

---

### Variante B: Dedizierter Server mieten (Schweiz)

Ein gemieteter Bare-Metal-Server bei Nine.ch in Zuerich mit NVIDIA A100 GPU.

| Posten | Einmalig | Monatlich |
|--------|---------|-----------|
| Nine.ch GPU-Server (A100 40GB, Zuerich) | -- | CHF 850 |
| **Total** | **CHF 0** | **~CHF 850** |

| | 1. Jahr | 3 Jahre | Pro User/Monat (10 User) |
|---|---------|---------|--------------------------|
| **Kosten** | ~CHF 10'200 | ~CHF 30'600 | **~CHF 85** |

**Vorteile:** Keine Investition, sofort einsatzbereit. Professionelles Rechenzentrum mit Redundanz. Schnellere Antwortzeiten als HP ZGX Nano (A100 hat hoehere Memory Bandwidth). Voller Root-Zugang (Ollama direkt installierbar). 2 Wochen Gratis-Test.
**Nachteile:** Laufende Kosten, auf 3 Jahre deutlich teurer als Kauf.

---

### Variante C: Cloud on-demand (Schweiz)

GPU-Instanz bei einem Schweizer Cloud-Anbieter, nur aktiv wenn gebraucht.

| Anbieter | GPU / VRAM | Standort | Pro Stunde |
|----------|-----------|----------|------------|
| **cloudscale.ch** | L40S 48GB | Schweiz | CHF 2.20 |
| **Exoscale** | RTX Pro 6000 96GB | Zuerich | EUR 1.84 |

Rechenbeispiel: Buerozeiten (10h/Tag, 22 Tage/Monat = 220h):

| | Monatlich (220h) | 1. Jahr | Pro User/Monat (10 User) |
|---|-----------------|---------|--------------------------|
| **cloudscale.ch** | ~CHF 485 | ~CHF 5'800 | **~CHF 49** |
| **Exoscale** | ~CHF 415 | ~CHF 5'000 | **~CHF 42** |

**Vorteile:** Keine Investition. Zahlen nur wenn aktiv. Flexibel skalierbar. Schweizer Rechenzentrum.
**Nachteile:** Muss gestartet/gestoppt werden (automatisierbar). Bei 24/7-Betrieb teurer als Nine.ch.

---

### Variante D: Server mieten (Deutschland -- guenstiger, nicht CH)

Dedizierter GPU-Server bei Hetzner in Nuernberg.

| Posten | Einmalig | Monatlich |
|--------|---------|-----------|
| Hetzner GEX131 (RTX Pro 6000 96GB) | -- | ~CHF 900 |
| **Total** | **CHF 0** | **~CHF 900** |

| | 1. Jahr | 3 Jahre | Pro User/Monat (10 User) |
|---|---------|---------|--------------------------|
| **Kosten** | ~CHF 10'800 | ~CHF 32'400 | **~CHF 90** |

**Vorteile:** Sehr leistungsfaehige GPU (96GB VRAM). Hetzner ist zuverlaessig und etabliert.
**Nachteile:** Daten liegen in Deutschland, nicht in der Schweiz. Aehnlicher Preis wie Nine.ch bei weniger Datenhoheit.

---

## Vergleich auf einen Blick

| | Variante A | Variante B | Variante C | Variante D |
|---|---|---|---|---|
| | HP ZGX Nano (Kauf) | Nine.ch (Miete CH) | Cloud on-demand (CH) | Hetzner (Miete DE) |
| **Investition** | CHF 3'920 | CHF 0 | CHF 0 | CHF 0 |
| **Monatlich** | CHF 190 | CHF 850 | CHF 415-485 | CHF 900 |
| **Pro User/Mt** | **CHF 30** | **CHF 85** | **CHF 42-49** | **CHF 90** |
| **Kosten 1. Jahr** | CHF 6'200 | CHF 10'200 | CHF 5'000-5'800 | CHF 10'800 |
| **Kosten 3 Jahre** | CHF 10'760 | CHF 30'600 | CHF 15'000-17'500 | CHF 32'400 |
| **Daten in CH** | Ja (Colocation) | Ja | Ja | Nein (DE) |
| **Antwortzeit** | 7-10s | 5-8s | 5-8s | 5-8s |
| **Betriebssystem** | Ubuntu 24.04 | Linux | Linux | Linux |
| **Flexibilitaet** | Gering | Mittel | Hoch | Mittel |
| **Aufwand Setup** | Mittel | Gering | Gering | Gering |

---

## Empfehlung

### Fuer den Start (Proof of Concept / erste 10 User)

**Variante C (Cloud on-demand)** -- Exoscale oder cloudscale.ch:
- Kein Risiko, keine Investition
- ~CHF 42-49 pro User und Monat
- Sofort skalierbar wenn mehr User dazukommen
- Jederzeit kuendbar

### Fuer stabilen Betrieb (10 User, laeuft gut)

**Variante A (HP ZGX Nano G1n kaufen)** -- langfristig am guenstigsten:
- CHF 3'920 einmalig, danach nur ~CHF 190/Mt (inkl. hoeherer Stromverbrauch als Desktop-Hardware)
- ~CHF 30 pro User und Monat ab dem 2. Jahr
- Amortisiert sich gegenueber Miete nach ~6 Monaten
- Professionelle AI-Hardware mit Linux (Ubuntu 24.04, ARM64)
- NVIDIA Blackwell GPU -- kein Desktop-Rechner als Server

### Wichtig fuer die Kalkulation

- **Keine Lizenzkosten** fuer die KI-Modelle (Open Source, Apache 2.0)
- **Keine API-Gebuehren** -- im Gegensatz zu OpenAI/Claude fallen keine Kosten pro Anfrage an
- **Fixkosten statt variable Kosten** -- egal ob ein User 10 oder 100 Anfragen pro Tag stellt
- Die genannten Kosten decken **nur die KI-Infrastruktur** ab. Server fuer die Webanwendung selbst (PostgreSQL, MinIO, nginx) kommen separat dazu, sind aber deutlich guenstiger (~CHF 20-50/Mt)

---

## Was passiert bei mehr Usern?

| User | Loesung | Ungefaehre Zusatzkosten |
|------|---------|------------------------|
| **10** | 1x HP ZGX Nano G1n | Wie oben |
| **25** | Gleiche Hardware reicht (Wartezeiten steigen leicht) | CHF 0 zusaetzlich |
| **50** | Zweite HP ZGX Nano oder staerkere GPU noetig | ~2x Kosten |
| **100** | 1 leistungsstarker Server (A100 80GB) | ~CHF 850-1'500/Mt |
| **500+** | Mehrere GPU-Server mit Load Balancer | ~CHF 3'000-5'000/Mt |

Die Architektur skaliert stufenweise. Bis ~25 User reicht die gleiche Hardware bei etwas laengeren Wartezeiten (15-25s statt 7-10s). Danach wird stufenweise aufgestockt.

---

## Warum eine VPS ohne GPU nicht funktioniert

Eine haeufig gestellte Frage: "Kann man das nicht einfach auf einer guenstigen VPS laufen lassen?"

| | GPU-Hardware (HP ZGX Nano) | VPS ohne GPU (z.B. Hetzner CAX) |
|---|---|---|
| **Qwen3-32B Antwortzeit** | 7-10 Sekunden | **2-5 Minuten** |
| **Tokens pro Sekunde** | ~9-10 tok/s | ~0.5-1 tok/s |
| **Gleichzeitige User** | 3-5 ohne Probleme | 1 User blockiert alles |
| **Kundenerlebnis** | Professionell | Unzumutbar |

LLM-Inferenz ist eine GPU-gebundene Aufgabe. Ohne dedizierte GPU-Hardware (sei es NVIDIA, Apple Silicon mit Neural Engine, oder vergleichbare Beschleuniger) sind die Antwortzeiten fuer ein kommerzielles Produkt **nicht tragbar**. Kein zahlender Kunde wartet 2-5 Minuten auf eine KI-Antwort.
