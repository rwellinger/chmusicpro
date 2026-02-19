# Betriebskosten: Lokale KI fuer chmusicpro

**Stand:** Februar 2026
**Zielgruppe:** Business / Sales
**Szenario:** 10 User, lokale KI via Ollama, alle Sprachen (DE, EN, FR, IT, ES)

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

Typische Nutzung: Ein User arbeitet 1-5 Minuten am Text, klickt dann auf "Verbessern" oder "Uebersetzen", wartet wenige Sekunden auf das Ergebnis, arbeitet weiter. Die KI wird **nicht permanent** beansprucht.

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
| 1-2 User gleichzeitig aktiv | 5-10 Sekunden | Angenehm |
| 3-4 User gleichzeitig aktiv | 8-15 Sekunden | OK |
| 5+ User gleichzeitig (selten) | 15-30 Sekunden | Spuerbar, aber ertraeglich |

Bei 10 registrierten Usern sind erfahrungsgemaess **2-4 gleichzeitig aktiv** und davon **1-2 gerade am Generieren**. Wartezeiten ueber 15 Sekunden sind die Ausnahme, nicht die Regel.

---

## Varianten und was sie kosten

### Variante A: Eigene Hardware kaufen (Mac Studio)

Ein Apple Mac Studio M4 Max mit 128GB Speicher reicht fuer 10 User.

| Posten | Einmalig | Monatlich |
|--------|---------|-----------|
| Mac Studio M4 Max 128GB | CHF 4'000 | -- |
| Colocation (Schweizer Rechenzentrum) | -- | ~CHF 150 |
| Strom | -- | ~CHF 20 |
| **Total** | **CHF 4'000** | **~CHF 170** |

| | 1. Jahr | 3 Jahre | Pro User/Monat (10 User) |
|---|---------|---------|--------------------------|
| **Kosten** | ~CHF 6'000 | ~CHF 10'100 | **~CHF 28** |

**Vorteile:** Guenstigste Variante auf 3 Jahre. Kompaktes, leises Geraet. Geringer Stromverbrauch (~50W unter Last).
**Nachteile:** Hardware-Investition vorab. Bei Defekt muss Ersatz beschafft werden. Etwas langsamere Antwortzeiten als Datacenter-GPUs.

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

**Vorteile:** Keine Investition, sofort einsatzbereit. Professionelles Rechenzentrum mit Redundanz. Schnellere Antwortzeiten als Mac Studio. Voller Root-Zugang (Ollama direkt installierbar). 2 Wochen Gratis-Test.
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
| | Mac Studio (Kauf) | Nine.ch (Miete CH) | Cloud on-demand (CH) | Hetzner (Miete DE) |
| **Investition** | CHF 4'000 | CHF 0 | CHF 0 | CHF 0 |
| **Monatlich** | CHF 170 | CHF 850 | CHF 415-485 | CHF 900 |
| **Pro User/Mt** | **CHF 28** | **CHF 85** | **CHF 42-49** | **CHF 90** |
| **Kosten 1. Jahr** | CHF 6'000 | CHF 10'200 | CHF 5'000-5'800 | CHF 10'800 |
| **Kosten 3 Jahre** | CHF 10'100 | CHF 30'600 | CHF 15'000-17'500 | CHF 32'400 |
| **Daten in CH** | Ja (Colocation) | Ja | Ja | Nein (DE) |
| **Antwortzeit** | 8-15s | 5-10s | 5-10s | 5-10s |
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

**Variante A (Mac Studio kaufen)** -- langfristig am guenstigsten:
- CHF 4'000 einmalig, danach nur ~CHF 170/Mt
- ~CHF 28 pro User und Monat ab dem 2. Jahr
- Amortisiert sich gegenueber Miete nach ~6 Monaten

### Wichtig fuer die Kalkulation

- **Keine Lizenzkosten** fuer die KI-Modelle (Open Source, Apache 2.0)
- **Keine API-Gebuehren** -- im Gegensatz zu OpenAI/Claude fallen keine Kosten pro Anfrage an
- **Fixkosten statt variable Kosten** -- egal ob ein User 10 oder 100 Anfragen pro Tag stellt
- Die genannten Kosten decken **nur die KI-Infrastruktur** ab. Server fuer die Webanwendung selbst (PostgreSQL, MinIO, nginx) kommen separat dazu, sind aber deutlich guenstiger (~CHF 20-50/Mt)

---

## Was passiert bei mehr Usern?

| User | Loesung | Ungefaehre Zusatzkosten |
|------|---------|------------------------|
| **10** | 1 Server / 1 Mac Studio | Wie oben |
| **25** | Gleiche Hardware reicht (Wartezeiten steigen leicht) | CHF 0 zusaetzlich |
| **50** | Zweiter Server oder staerkere GPU noetig | ~2x Kosten |
| **100** | 1 leistungsstarker Server (A100 80GB) | ~CHF 850-1'500/Mt |
| **500+** | Mehrere GPU-Server mit Load Balancer | ~CHF 3'000-5'000/Mt |

Die Architektur skaliert stufenweise. Bis ~25 User reicht die gleiche Hardware bei etwas laengeren Wartezeiten (15-25s statt 8-15s). Danach wird stufenweise aufgestockt.