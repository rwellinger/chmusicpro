# Hardware-Sizing: Lokale KI via Ollama (10 User)

**Stand:** Februar 2026
**Kontext:** chmusicpro -- Lokaler Betrieb aller KI-Features via Ollama fuer 10 gleichzeitige Benutzer

---

## 1. KI-Features der Anwendung (Ist-Zustand)

Die Anwendung nutzt aktuell **25 KI-Templates** in **6 Kategorien**. Alle Aufrufe laufen ueber einen einheitlichen Endpoint (`/api/v1/ollama/chat/generate-unified`), der das passende Template aus der Datenbank laedt und an das konfigurierte Modell weiterleitet.

### Uebersicht aller KI-Operationen

| Kategorie | Aktion | Beschreibung | Anforderung |
|-----------|--------|--------------|-------------|
| **Lyrics** | `generate` | Komplette Songtexte aus Thema/Konzept generieren | Kreatives Schreiben, Songstruktur |
| **Lyrics** | `improve-section` | Einzelne Strophe/Refrain verbessern (mit Gesamtkontext) | Kontextverstaendnis, Kreativitaet |
| **Lyrics** | `rewrite-section` | Strophe komplett neu schreiben | Kreatives Schreiben |
| **Lyrics** | `condense-section` | Prosatext in singbare Lyrics verdichten | Textverstaendnis, Verdichtung |
| **Lyrics** | `optimize-phrasing` | Lyrics fuer Musik-KI optimieren (4-8 Worte/Zeile) | Textreformatierung |
| **Lyrics** | `translate` | Lyrics uebersetzen (DE/FR/IT/ES -> EN) | Mehrsprachige Uebersetzung |
| **Description** | `generate-long` | Marketing-Beschreibung aus Lyrics (max 1000 Zeichen) | Zusammenfassung, Marketing-Texte |
| **Description** | `generate-short` | Kurzbeschreibung aus Langbeschreibung (max 150 Zeichen) | Verdichtung |
| **Description** | `generate-tags` | 10 Such-Tags generieren | Keyword-Extraktion |
| **Image** | `enhance` | Bildprompt technisch verbessern | Promptverstaendnis |
| **Image** | `enhance-cover` | Album-Cover-Prompt verbessern | Promptverstaendnis |
| **Image** | `enhance-fast` | Schnelle Prompt-Verbesserung (kleines Modell) | Einfache Textverarbeitung |
| **Image** | `interpret-lyric` | Visuelle Szene aus Lyrics ableiten | Abstraktion, Kreativitaet |
| **Image** | `translate` | Bildprompt ins Englische uebersetzen | Uebersetzung |
| **Music** | `enhance` | Musikstil-Prompt verfeinern | Genre-/Musikwissen |
| **Music** | `enhance-suno` | Suno-optimierter Musikstil-Prompt | Spezifisches Prompt-Format |
| **Music** | `translate` | Musikstil-Beschreibung uebersetzen | Uebersetzung, Musikterminologie |
| **Titel** | `generate` | Songtitel aus Lyrics generieren (2-5 Worte) | Kreatives Schreiben |
| **Titel** | `generate-fast` | Schneller Titel (kleines Modell) | Einfache Textgenerierung |
| **Workshop** | `connect-inspire` | Inspirationen zu Thema generieren | Brainstorming, Kreativitaet |
| **Workshop** | `collect-mindmap` | Strukturierte Mindmap erstellen | Strukturierung, Kreativitaet |
| **Workshop** | `collect-stories` | Story-Ideen generieren | Narratives Schreiben |
| **Workshop** | `collect-words` | Wortbibliothek fuer Lyrics | Wortschatz, Kreativitaet |
| **Workshop** | `shape-rhymes` | Reimmuster aus Wortliste | Phonetik, Kreativitaet |

### Sprachliche Anforderungen

Alle Templates muessen in der **Eingabesprache** antworten koennen. Konkret:

- **Deutsch** -- Primaersprache der meisten User
- **Englisch** -- Primaersprache fuer Lyrics im Musikbereich
- **Franzoesisch, Italienisch, Spanisch** -- Sekundaersprachen

Uebersetzungs-Templates (lyrics/translate, image/translate, music/translate) erfordern **hochwertige Uebersetzung** zwischen diesen Sprachen. Besonders kritisch: Die Uebersetzung muss nicht nur korrekt sein, sondern bei Lyrics auch **singbar** und **poetisch** bleiben.

### Token-Charakteristik pro Aufgabentyp

| Aufgabentyp | Typischer Input | Typischer Output | Gesamt-Tokens |
|-------------|----------------|-----------------|---------------|
| Lyrics generieren | 100-500 Tokens (Seed-Text) | 500-2000 Tokens (ganzer Song) | 600-2500 |
| Section verbessern/umschreiben | 200-1000 Tokens (Section + Kontext) | 100-500 Tokens | 300-1500 |
| Uebersetzung | 500-2000 Tokens (Songtext) | 500-2000 Tokens | 1000-4000 |
| Beschreibungen | 500-2000 Tokens (Lyrics) | 50-300 Tokens | 550-2300 |
| Prompt-Verbesserung | 20-100 Tokens | 50-150 Tokens | 70-250 |
| Titel generieren | 100-500 Tokens | 5-15 Tokens | 105-515 |
| Workshop (Inspiration etc.) | 50-500 Tokens | 200-1000 Tokens | 250-1500 |

**Fazit:** Die meisten Operationen bleiben unter 4000 Tokens gesamt. Eine **Kontextlaenge von 8192 Tokens** reicht fuer alle Use Cases problemlos.

---

## 2. Modell-Empfehlungen fuer Ollama

### Zwei-Modell-Strategie (empfohlen)

Nicht alle Aufgaben brauchen das gleiche Modell. Die Anwendung nutzt bereits heute zwei Modelle:

| Rolle | Aktuell | Empfehlung Lokal | Einsatz |
|-------|---------|------------------|---------|
| **Hauptmodell** (Qualitaet) | gpt-oss:20b | **Qwen3-32B** oder **Qwen3-30B-A3B** | Lyrics, Uebersetzung, Workshop, Beschreibungen |
| **Schnellmodell** (Speed) | llama3.2:3b | **Qwen3-8B** oder **Llama 3.2 3B** | Titel, schnelle Prompt-Verbesserung |

### Modell-Kandidaten im Detail

#### Hauptmodell-Kandidaten (Kreatives Schreiben + Uebersetzung)

| Modell | Parameter | Sprachen | VRAM (Q4_K_M) | Staerken | Schwaechen |
|--------|----------|----------|---------------|----------|------------|
| **Qwen3-32B** | 32B (dense) | 119 Sprachen (alle 5 abgedeckt) | ~22 GB | Beste Qualitaet/Groesse-Ratio, exzellent multilingual, starkes kreatives Schreiben | Braucht ~22 GB nur fuer Weights |
| **Qwen3-30B-A3B** (MoE) | 30B total / 3B aktiv | 119 Sprachen | ~20 GB | Geschwindigkeit eines 3B-Modells, Qualitaet eines 30B | MoE weniger erprobt unter Last |
| **Mistral Small 3.1** | 24B | 25+ Sprachen (alle 5 explizit) | ~16 GB | Stark bei europaeischen Sprachen (FR!), 128K Kontext | Etwas kleiner als Qwen3-32B |
| **Qwen3-14B** | 14B | 119 Sprachen | ~11 GB | Gute Qualitaet, deutlich weniger VRAM | Lyrics-Qualitaet merkbar unter 32B |
| **Llama 3.3 70B** | 70B | 8 Sprachen (alle 5 dabei) | ~46 GB | Beste kreative Qualitaet auf Englisch | Enorm viel VRAM, langsam |
| **Qwen 2.5 72B** | 72B | 29+ Sprachen | ~51 GB | Beste Uebersetzungsqualitaet (Flores-101) | Wie Llama 70B: extrem viel VRAM |

#### Schnellmodell-Kandidaten (Titel, Fast-Varianten)

| Modell | Parameter | VRAM (Q4_K_M) | Speed (RTX 4090) | Einsatz |
|--------|----------|---------------|-------------------|---------|
| **Qwen3-8B** | 8B | ~6 GB | ~95 tok/s | Titel, schnelle Prompts, Fallback |
| **Llama 3.2 3B** | 3B | ~2.5 GB | ~150+ tok/s | Ultra-schnelle Titel |
| **Gemma 2 9B** | 9B | ~6.5 GB | ~85 tok/s | Alternative zu Qwen3-8B |

### Empfehlung nach Qualitaetsstufe

| Stufe | Hauptmodell | Schnellmodell | Beschreibung |
|-------|-------------|---------------|-------------|
| **Optimal** | Qwen3-32B (Q4_K_M) | Qwen3-8B | Beste lokale Qualitaet fuer Lyrics und Uebersetzung |
| **Ausgewogen** | Qwen3-30B-A3B (MoE) | Qwen3-8B | Nahe an 32B-Qualitaet, deutlich schneller pro Request |
| **Kompakt** | Qwen3-14B (Q4_K_M) | Llama 3.2 3B | Gute Qualitaet, weniger Hardware noetig |

**Warum Qwen3?** Die Qwen3-Familie deckt alle 5 Zielsprachen (EN, DE, FR, IT, ES) nativ ab (119 Sprachen trainiert) und erreicht bei kreativen Schreibaufgaben und Uebersetzungen State-of-the-Art-Qualitaet in dieser Groessenklasse. Alternative: Mistral Small 3.1 (besonders stark bei Franzoesisch).

---

## 3. VRAM- und Speicher-Anforderungen

### Formel

```
Benoetigter VRAM = Modell-Weights + (Anzahl parallele Slots x KV-Cache pro Slot)
```

Der **KV-Cache** waechst linear mit der Kontextlaenge und muss fuer jeden parallelen Benutzer separat allokiert werden.

### Berechnung fuer 10 User (8K Kontext)

#### Mit Standard KV-Cache (FP16)

| Konfiguration | Weights | KV-Cache/Slot | 4 Slots | 10 Slots | Gesamt (10) |
|---------------|---------|---------------|---------|----------|-------------|
| Qwen3-14B + Qwen3-8B | 11 + 6 = 17 GB | ~2 GB / ~1.2 GB | - | 20 + 12 = 32 GB | **49 GB** |
| Qwen3-32B + Qwen3-8B | 22 + 6 = 28 GB | ~3 GB / ~1.2 GB | - | 30 + 12 = 42 GB | **70 GB** |
| Qwen3-30B-A3B + Qwen3-8B | 20 + 6 = 26 GB | ~2 GB / ~1.2 GB | - | 20 + 12 = 32 GB | **58 GB** |
| Llama 3.3 70B + Qwen3-8B | 46 + 6 = 52 GB | ~2.2 GB / ~1.2 GB | - | 22 + 12 = 34 GB | **86 GB** |

#### Mit KV-Cache-Quantisierung (Q8_0) -- empfohlen

Ollama unterstuetzt seit 2024 die Quantisierung des KV-Caches selbst (via Flash Attention). Q8_0 halbiert den KV-Cache-Bedarf bei minimalem Qualitaetsverlust.

| Konfiguration | Weights | KV-Cache/Slot (Q8) | 10 Slots | Gesamt (10) |
|---------------|---------|---------------------|----------|-------------|
| **Qwen3-14B + Qwen3-8B** | 17 GB | ~1 GB / ~0.6 GB | 10 + 6 = 16 GB | **33 GB** |
| **Qwen3-32B + Qwen3-8B** | 28 GB | ~1.5 GB / ~0.6 GB | 15 + 6 = 21 GB | **49 GB** |
| **Qwen3-30B-A3B + Qwen3-8B** | 26 GB | ~1 GB / ~0.6 GB | 10 + 6 = 16 GB | **42 GB** |
| **Llama 3.3 70B + Qwen3-8B** | 52 GB | ~1.1 GB / ~0.6 GB | 11 + 6 = 17 GB | **69 GB** |

### Praxisbetrachtung: Braucht man wirklich 10 parallele Slots?

In der Realitaet werden **nicht alle 10 User gleichzeitig** eine KI-Anfrage absetzen. Typisches Nutzungsverhalten:

- User schreibt Lyrics -> klickt "Verbessern" -> wartet ~5-15 Sekunden -> liest Ergebnis -> arbeitet 1-5 Minuten weiter -> naechster Request
- **Gleichzeitigkeitsfaktor**: Bei 10 Usern sind realistisch **2-4 gleichzeitige Requests** zu erwarten
- Restliche Requests landen in Ollamas Queue (FIFO) und werden nacheinander abgearbeitet

**Empfehlung:** `OLLAMA_NUM_PARALLEL=4` als optimaler Kompromiss zwischen VRAM-Bedarf und Wartezeit.

| Konfiguration | Weights | 4 parallele Slots (Q8 KV) | Gesamt |
|---------------|---------|---------------------------|--------|
| **Qwen3-14B + Qwen3-8B** | 17 GB | 4 + 2.4 = 6.4 GB | **~24 GB** |
| **Qwen3-32B + Qwen3-8B** | 28 GB | 6 + 2.4 = 8.4 GB | **~37 GB** |
| **Qwen3-30B-A3B + Qwen3-8B** | 26 GB | 4 + 2.4 = 6.4 GB | **~33 GB** |

---

## 4. Geschwindigkeit und Antwortzeiten

### Was ist "akzeptabel"?

| Bewertung | Tokens/Sekunde | Typische Strophe (~100 Tokens) | User-Erlebnis |
|-----------|---------------|-------------------------------|---------------|
| Exzellent | 30+ tok/s | 2-3 Sekunden | Fuehlt sich wie schnelles Tippen an |
| Gut | 15-30 tok/s | 3-7 Sekunden | Angenehmes Streaming, interaktiv nutzbar |
| Akzeptabel | 8-15 tok/s | 7-13 Sekunden | Spuerbare Verzoegerung, aber ertraeglich |
| Grenzwertig | 5-8 tok/s | 13-20 Sekunden | Frustrierend bei haeufiger Nutzung |
| Unbrauchbar | <5 tok/s | 20+ Sekunden | Nicht praxistauglich |

### Geschwindigkeit pro Hardware (Single-User, volle GPU-Auslastung)

| Hardware | Qwen3-8B | Qwen3-14B | Qwen3-32B | Llama 70B |
|----------|----------|-----------|-----------|-----------|
| RTX 4090 (24 GB) | ~95 tok/s | ~64 tok/s | ~34 tok/s | Passt nicht |
| RTX 5090 (32 GB) | ~130 tok/s | ~90 tok/s | ~61 tok/s | Passt nicht |
| RTX 6000 Ada (48 GB) | ~100 tok/s | ~50 tok/s | ~26 tok/s | ~14 tok/s |
| 2x RTX 6000 Ada (96 GB) | ~100 tok/s | ~50 tok/s | ~35 tok/s | ~18 tok/s |
| A100 80GB | ~138 tok/s | ~80 tok/s | ~45 tok/s | ~20 tok/s |
| H100 80GB | ~144 tok/s | ~85 tok/s | ~50 tok/s | ~25 tok/s |
| M4 Max 128GB | ~70 tok/s | ~40 tok/s | ~28 tok/s | ~10 tok/s |
| M3 Ultra 192GB | ~90 tok/s | ~55 tok/s | ~38 tok/s | ~22 tok/s |

### Geschaetzte Geschwindigkeit bei 4 gleichzeitigen Requests

Bei parallelen Requests teilt sich die Bandbreite. Grobe Faustregel: Durchsatz pro User ≈ Single-User-Speed / Anzahl parallele Requests (variiert je nach Batching-Effizienz).

| Hardware | Qwen3-32B (4 parallel) | Bewertung | Qwen3-14B (4 parallel) | Bewertung |
|----------|----------------------|-----------|----------------------|-----------|
| RTX 4090 (24 GB) | VRAM reicht nicht | -- | ~16 tok/s | Gut |
| RTX 5090 (32 GB) | ~15 tok/s | Gut | ~22 tok/s | Gut |
| RTX 6000 Ada (48 GB) | ~7 tok/s | Grenzwertig | ~13 tok/s | Akzeptabel |
| 2x RTX 6000 Ada (96 GB) | ~9 tok/s | Akzeptabel | ~13 tok/s | Akzeptabel |
| A100 80GB | ~11 tok/s | Akzeptabel | ~20 tok/s | Gut |
| H100 80GB | ~13 tok/s | Akzeptabel | ~21 tok/s | Gut |
| M4 Max 128GB | ~7 tok/s | Grenzwertig | ~10 tok/s | Akzeptabel |
| M3 Ultra 192GB | ~10 tok/s | Akzeptabel | ~14 tok/s | Akzeptabel |

**Hinweis:** Queued Requests (User 5-10) warten zusaetzlich, bis ein Slot frei wird. Bei ~100 Token Output und ~10 tok/s dauert ein Request ~10 Sekunden. Ein gequeueter User wartet also maximal eine zusaetzliche Wartezeit von 10-30 Sekunden.

---

## 5. Hardware-Szenarien

### Szenario A: Kompakt (Qwen3-14B Hauptmodell)

**Modelle:** Qwen3-14B (Q4_K_M) + Qwen3-8B (Q4_K_M)
**VRAM-Bedarf:** ~24 GB (4 parallele Slots, Q8 KV-Cache)
**Qualitaet:** Gut -- fuer einfache Lyrics und Uebersetzungen ausreichend. Bei komplexen kreativen Aufgaben (Workshop, poetische Uebersetzungen) merkbar schwaecher als 32B.

| Hardware-Option | VRAM | Geschwindigkeit (4 parallel) | Bewertung |
|----------------|------|------------------------------|-----------|
| **1x RTX 4090** | 24 GB | ~16 tok/s pro User | Schnell, VRAM knapp |
| **1x RTX 5090** | 32 GB | ~22 tok/s pro User | Schnell, VRAM komfortabel |
| **M4 Max 64GB** | 64 GB (unified) | ~10 tok/s pro User | Ausreichend, viel Reserve |

**Minimale Server-Spezifikation:**
- GPU: 1x mit mindestens 24 GB VRAM
- RAM: 32 GB System-RAM (neben GPU-VRAM)
- CPU: 8+ Kerne (fuer Ollama-Overhead und Anwendung)
- Storage: 100 GB SSD (Modelle + Anwendung)

---

### Szenario B: Ausgewogen (Qwen3-32B Hauptmodell) -- EMPFOHLEN

**Modelle:** Qwen3-32B (Q4_K_M) + Qwen3-8B (Q4_K_M)
**VRAM-Bedarf:** ~37 GB (4 parallele Slots, Q8 KV-Cache)
**Qualitaet:** Sehr gut -- hochwertige Lyrics in allen 5 Sprachen, poetische Uebersetzungen, kreative Workshop-Aufgaben.

| Hardware-Option | VRAM | Geschwindigkeit (4 parallel) | Bewertung |
|----------------|------|------------------------------|-----------|
| **1x RTX 6000 Ada** | 48 GB | ~7 tok/s pro User | Akzeptabel, VRAM komfortabel |
| **1x A100 80GB** | 80 GB | ~11 tok/s pro User | Gut, viel Reserve |
| **1x H100 80GB** | 80 GB | ~13 tok/s pro User | Gut, viel Reserve |
| **M4 Max 128GB** | 128 GB (unified) | ~7 tok/s pro User | Akzeptabel |
| **M3 Ultra 192GB** | 192 GB (unified) | ~10 tok/s pro User | Akzeptabel-Gut |

**Minimale Server-Spezifikation:**
- GPU: 1x mit mindestens 48 GB VRAM
- RAM: 64 GB System-RAM
- CPU: 16+ Kerne
- Storage: 200 GB SSD

**Alternative mit MoE:** Qwen3-30B-A3B statt Qwen3-32B -- aehnliche Qualitaet, braucht ~33 GB VRAM statt ~37 GB, und ist deutlich schneller pro Request (da nur 3B Parameter pro Token aktiviert werden). Verhaelt sich unter Last aber weniger vorhersagbar als dense-Modelle.

---

### Szenario C: Premium (70B Hauptmodell)

**Modelle:** Llama 3.3 70B oder Qwen 2.5 72B (Q4_K_M) + Qwen3-8B
**VRAM-Bedarf:** ~56-69 GB (4 parallele Slots, Q8 KV-Cache)
**Qualitaet:** Exzellent -- nahe an GPT-4-Qualitaet bei Lyrics und Uebersetzung. Spuerbar besser als 32B bei komplexen kreativen Aufgaben.

| Hardware-Option | VRAM | Geschwindigkeit (4 parallel) | Bewertung |
|----------------|------|------------------------------|-----------|
| **1x A100 80GB** | 80 GB | ~5 tok/s pro User | Grenzwertig |
| **1x H100 80GB** | 80 GB | ~6 tok/s pro User | Grenzwertig-Akzeptabel |
| **2x RTX 6000 Ada** | 96 GB | ~5 tok/s pro User | Grenzwertig |
| **M3 Ultra 192GB** | 192 GB (unified) | ~5-6 tok/s pro User | Grenzwertig |

**Minimale Server-Spezifikation:**
- GPU: 1x mit mindestens 80 GB VRAM oder 2x mit je 48 GB
- RAM: 128 GB System-RAM
- CPU: 32+ Kerne
- Storage: 300 GB SSD

**Einschaetzung:** Ein 70B-Modell liefert die beste Qualitaet, ist aber bei 4 parallelen Usern an der Grenze des Ertraeglichen (~5-6 tok/s). Fuer eine Strophe (~100 Tokens) wartet man ~17-20 Sekunden. Bei gequeueten Requests addiert sich das schnell.

---

## 6. Ollama-Konfiguration fuer 10 User

### Empfohlene Umgebungsvariablen

```bash
# Parallele Requests (4 ist der Sweet-Spot fuer 10 User)
OLLAMA_NUM_PARALLEL=4

# Flash Attention aktivieren (noetig fuer KV-Cache-Quantisierung)
OLLAMA_FLASH_ATTENTION=1

# KV-Cache-Quantisierung (Q8_0 = halber Speicher, minimaler Qualitaetsverlust)
OLLAMA_KV_CACHE_TYPE=q8_0

# Maximale Queue-Laenge (Standard 512 ist OK)
OLLAMA_MAX_QUEUE=512

# Beide Modelle gleichzeitig geladen halten
OLLAMA_MAX_LOADED_MODELS=2

# GPU-Layers: Alle Layer auf GPU (0 = auto, was meistens korrekt ist)
# Nur anpassen wenn VRAM knapp
OLLAMA_GPU_LAYERS=0
```

### Modelfile-Anpassungen

```dockerfile
# Hauptmodell (Qwen3-32B)
FROM qwen3:32b
PARAMETER num_ctx 8192
PARAMETER temperature 0.7

# Schnellmodell (Qwen3-8B)
FROM qwen3:8b
PARAMETER num_ctx 4096
PARAMETER temperature 0.5
```

---

## 7. Empfehlung

### Primaere Empfehlung: Szenario B (Qwen3-32B)

Fuer 10 User mit Fokus auf **Lyrics-Qualitaet in 5 Sprachen** bietet Szenario B das beste Verhaeltnis aus Qualitaet und Antwortzeit:

**Hardware-Kern:**
- **GPU:** 1x mit 48-80 GB VRAM (RTX 6000 Ada, A100, oder H100)
- **RAM:** 64 GB System-RAM
- **CPU:** 16+ Kerne (moderne Architektur)
- **Storage:** 200 GB NVMe SSD

**Software:**
- Hauptmodell: **Qwen3-32B** (Q4_K_M) -- Lyrics, Uebersetzung, Workshop, Beschreibungen
- Schnellmodell: **Qwen3-8B** (Q4_K_M) -- Titel, Fast-Varianten
- `OLLAMA_NUM_PARALLEL=4`, Flash Attention + Q8 KV-Cache

**Erwartete User-Erfahrung:**
- 4 User gleichzeitig aktiv: ~7-13 tok/s pro User (je nach GPU) -> Strophe in 8-15 Sekunden
- User 5-10 in Queue: zusaetzlich 10-15 Sekunden Wartezeit
- Worst Case (alle 10 gleichzeitig): bis zu 30 Sekunden fuer eine Strophe

### Alternative: Apple Silicon

Falls ein Mac Studio bevorzugt wird:
- **M4 Max 128GB**: Passt fuer Qwen3-32B, ~7 tok/s bei 4 parallelen Requests. Grenzwertig aber machbar.
- **M3 Ultra 192GB** (aktuell groesste Option): ~10 tok/s bei 4 parallelen Requests. Komfortabler, aber aeltere Architektur.
- **Vorteil:** Unified Memory (kein GPU/CPU-Split), leiser Betrieb, geringer Stromverbrauch (40-80W vs 300-700W bei Datacenter-GPUs)
- **Nachteil:** Deutlich geringere Speicherbandbreite als dedizierte GPUs (546-800 GB/s vs 2000-3000+ GB/s)

### Qualitaetsvergleich Modellgroessen fuer Lyrics

| Aspekt | 14B | 32B | 70B |
|--------|-----|-----|-----|
| Einfache Lyrics (EN) | Gut | Sehr gut | Exzellent |
| Komplexe Lyrics (Metaphern, Poetik) | Maessig | Gut | Sehr gut |
| Lyrics (DE) | Gut | Sehr gut | Sehr gut |
| Lyrics (FR/IT/ES) | Maessig-Gut | Gut | Sehr gut |
| Poetische Uebersetzung | Maessig | Gut | Sehr gut |
| Workshop (kreatives Brainstorming) | Gut | Sehr gut | Exzellent |
| Prompt-Verbesserung | Gut | Gut | Gut (Overhead unnoetig) |
| Titel generieren | Gut | Gut (Overhead unnoetig) | Gut (Overhead unnoetig) |

**Fazit:** 32B trifft den Sweet-Spot -- signifikant besser als 14B bei kreativen Aufgaben, waehrend der Sprung von 32B auf 70B zwar spuerbar, aber nicht so dramatisch ist. Die Hardware-Anforderungen fuer 70B sind dagegen fast doppelt so hoch.

---

## 8. Zusammenfassung der Hardware-Anforderungen

| | Kompakt (14B) | Ausgewogen (32B) | Premium (70B) |
|---|---|---|---|
| **Hauptmodell** | Qwen3-14B | Qwen3-32B | Llama 3.3 70B / Qwen 2.5 72B |
| **Schnellmodell** | Qwen3-8B | Qwen3-8B | Qwen3-8B |
| **Min. VRAM** | 24 GB | 48 GB | 80 GB |
| **Min. System-RAM** | 32 GB | 64 GB | 128 GB |
| **Min. CPU-Kerne** | 8 | 16 | 32 |
| **Min. Storage** | 100 GB SSD | 200 GB SSD | 300 GB SSD |
| **Tok/s (4 parallel)** | 10-22 | 7-13 | 5-6 |
| **Lyrics-Qualitaet** | Gut | Sehr gut | Exzellent |
| **Uebersetzungsqualitaet** | Maessig-Gut | Gut | Sehr gut |
| **GPU-Optionen** | RTX 4090/5090 | RTX 6000 Ada / A100 | A100 / H100 / 2x RTX 6000 Ada |
| **Apple-Option** | M4 Max 64GB | M4 Max 128GB | M3 Ultra 192GB |

---

## 9. Skalierung: 100, 500, 1000 User

### Grundannahmen

Die folgenden Schaetzungen basieren auf dem **ausgewogenen Szenario (Qwen3-32B + Qwen3-8B)** und diesen Annahmen:

- **Gleichzeitigkeitsfaktor:** ~10-15% der registrierten User sind gleichzeitig aktiv, davon setzt ca. jeder 3. gerade einen KI-Request ab
- **Durchschnittlicher Request:** ~100-500 Tokens Output, ~10 Sekunden Generierungszeit
- **Akzeptable Wartezeit:** max. 30 Sekunden (inkl. Queue)

| Registrierte User | Gleichzeitig aktiv | Gleichzeitige KI-Requests (Peak) | Benoetigte parallele Slots |
|--------------------|-------------------|----------------------------------|---------------------------|
| 10 | 3-5 | 1-3 | 4 |
| 100 | 10-15 | 4-8 | 8-10 |
| 500 | 50-75 | 15-25 | 20-30 |
| 1000 | 100-150 | 30-50 | 40-60 |

### 100 User

**Herausforderung:** 4-8 gleichzeitige KI-Requests, Peak bis 10-12.

**Architektur:** Ein einzelner leistungsstarker GPU-Server reicht noch aus, braucht aber mehr parallele Slots.

| Aspekt | Anforderung |
|--------|-------------|
| Parallele Slots | `OLLAMA_NUM_PARALLEL=8` |
| VRAM (Qwen3-32B, 8 Slots, Q8 KV) | 22 GB (Weights) + 8 x 1.5 GB (KV) = **~34 GB** |
| VRAM (+ Qwen3-8B, 8 Slots) | + 6 GB + 8 x 0.6 GB = **~16 GB** |
| **Gesamt-VRAM** | **~50 GB** |
| GPU | 1x A100 80GB oder 1x H100 80GB |
| Tok/s pro User (8 parallel) | ~4-6 tok/s (A100) / ~5-7 tok/s (H100) |
| System-RAM | 64-128 GB |
| CPU | 16-32 Kerne |

**Bewertung:** Machbar mit einem einzelnen Server. Antwortzeiten werden spuerbar laenger (15-25 Sekunden fuer eine Strophe bei Peak-Last), bleiben aber ertraeglich. Queue-Wartezeiten bei kurzen Peaks (>8 gleichzeitig) von 10-20 Sekunden.

---

### 500 User

**Herausforderung:** 15-25 gleichzeitige KI-Requests, Peak bis 30-40.

**Architektur:** Ein einzelner Server reicht nicht mehr. Es braucht **mehrere Ollama-Instanzen** hinter einem Load Balancer.

```
                    ┌─────────────────┐
                    │  Load Balancer   │
                    │  (nginx/HAProxy) │
                    └────────┬────────┘
               ┌─────────────┼─────────────┐
               v             v             v
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Ollama 1 │  │ Ollama 2 │  │ Ollama 3 │
        │ GPU: A100│  │ GPU: A100│  │ GPU: A100│
        │ 8 Slots  │  │ 8 Slots  │  │ 8 Slots  │
        └──────────┘  └──────────┘  └──────────┘
              24 parallele Slots total
```

| Aspekt | Anforderung |
|--------|-------------|
| Ollama-Instanzen | 3-4 (je `OLLAMA_NUM_PARALLEL=8`) |
| Parallele Slots total | 24-32 |
| GPUs | 3-4x A100 80GB oder 3-4x H100 80GB |
| VRAM pro GPU | ~50 GB (je Qwen3-32B + Qwen3-8B mit 8 Slots) |
| Tok/s pro User (24 parallel, 3 GPUs) | ~4-6 tok/s |
| System-RAM pro Server | 64-128 GB |
| CPU pro Server | 16-32 Kerne |
| Storage | Shared Model Storage (NFS/S3) oder lokale Kopien |

**Zusaetzliche Infrastruktur:**
- **Load Balancer** vor den Ollama-Instanzen (Round-Robin oder Least-Connections)
- **Health Checks** fuer automatisches Failover
- **Shared Storage** fuer Modell-Downloads (vermeidet 4x Download derselben Weights)
- **Monitoring** (GPU-Auslastung, Queue-Laenge, Antwortzeiten)

**Bewertung:** Signifikanter Infrastruktur-Sprung. Nicht mehr "ein Server", sondern ein kleiner Cluster. Die Anwendung (chmusicprosrv) selbst muss nicht angepasst werden -- der Load Balancer verteilt die Requests transparent. Antwortzeiten bleiben bei ~15-25 Sekunden wenn genuegend Slots vorhanden.

**Achtung:** Jede Ollama-Instanz muss das komplette Modell in ihrem eigenen VRAM halten. 4 GPUs bedeuten 4x die Modell-Weights im Speicher -- es gibt kein Modell-Sharing zwischen Instanzen.

---

### 1000 User

**Herausforderung:** 30-50 gleichzeitige KI-Requests, Peak bis 60-80.

**Architektur:** Erfordert einen dedizierten Inference-Cluster mit professionellem Serving-Framework.

```
                    ┌─────────────────┐
                    │  Load Balancer   │
                    │  (nginx/Traefik) │
                    └────────┬────────┘
               ┌─────────────┼─────────────┐
               v             v             v
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ vLLM /   │  │ vLLM /   │  │ vLLM /   │
        │ TGI Node │  │ TGI Node │  │ TGI Node │
        │ 2x H100  │  │ 2x H100  │  │ 2x H100  │
        └──────────┘  └──────────┘  └──────────┘
           6x H100 = ~60 parallele Slots
```

| Aspekt | Anforderung |
|--------|-------------|
| Inference-Framework | **vLLM** oder **TGI** statt Ollama (effizienteres Batching) |
| GPUs | 6-8x H100 80GB (oder aequivalent) |
| Parallele Slots total | 48-64 |
| System-RAM pro Node | 128-256 GB |
| CPU pro Node | 32-64 Kerne |
| Netzwerk | 10-25 Gbit/s zwischen Nodes |

**Warum nicht mehr Ollama?**

Ab dieser Groessenordnung wird Ollama zum Engpass. Professionelle Inference-Frameworks bieten:

| Feature | Ollama | vLLM / TGI |
|---------|--------|------------|
| Continuous Batching | Nein (feste Slots) | Ja (dynamisch, deutlich effizienter) |
| PagedAttention | Nein | Ja (vLLM) -- bis zu 2-4x bessere VRAM-Nutzung |
| Tensor Parallelism | Nein (nur Layer-Split) | Ja (Modell ueber mehrere GPUs verteilt) |
| Throughput bei Last | Begrenzt durch Slot-Anzahl | Skaliert dynamisch mit Batch-Groesse |
| Token/s bei 50 parallelen Requests | ~2-3 tok/s pro User | ~5-8 tok/s pro User (dank Batching) |

**Continuous Batching** ist der entscheidende Unterschied: Waehrend Ollama feste Slots reserviert (8 Slots = 8x KV-Cache permanent allokiert), fuegt vLLM neue Requests dynamisch in laufende Batches ein und gibt KV-Cache frei, sobald ein Request fertig ist. Das ergibt bei gleicher Hardware 2-4x mehr Durchsatz.

**Bewertung:** Bei 1000 Usern verlassen wir den Bereich "lokaler Server" und betreten "Inference-Infrastruktur". Es braucht:
- Professionelles Inference-Framework (vLLM, TGI, oder Triton Inference Server)
- GPU-Cluster mit mehreren Nodes
- Orchestrierung (Kubernetes mit GPU-Operator)
- Monitoring und Auto-Scaling
- Anpassung von chmusicprosrv: Statt Ollama-API wird die OpenAI-kompatible API von vLLM angesprochen (minimaler Aufwand, da vLLM die gleiche API bietet)

---

### Uebersicht Skalierung (Szenario B: Qwen3-32B)

| | 10 User | 100 User | 500 User | 1000 User |
|---|---|---|---|---|
| **Gleichzeitige KI-Requests** | 1-3 | 4-8 | 15-25 | 30-50 |
| **Parallele Slots** | 4 | 8-10 | 24-32 | 48-64 |
| **GPUs** | 1x 48GB+ | 1x 80GB | 3-4x 80GB | 6-8x 80GB |
| **Inference-Framework** | Ollama | Ollama | Ollama + Load Balancer | vLLM / TGI |
| **Architektur** | Single Server | Single Server | Multi-Instance Cluster | GPU-Cluster + Kubernetes |
| **Tok/s pro User (Peak)** | ~7-13 | ~4-6 | ~4-6 | ~5-8 (mit vLLM) |
| **Antwortzeit (Strophe)** | 8-15s | 15-25s | 15-25s | 13-20s |
| **Infrastruktur-Komplexitaet** | Minimal | Gering | Mittel | Hoch |
| **Anpassung an chmusicpro** | Keine | Keine | Load Balancer Config | Ollama-URL auf vLLM umlenken |

### Kernaussagen

1. **Bis 100 User** laesst sich das mit einem einzelnen Server betreiben. Ollama genuegt als Inference-Framework.

2. **Ab 500 User** braucht es mehrere GPU-Server mit Load Balancing. Ollama funktioniert noch, aber die Infrastruktur wird deutlich komplexer.

3. **Ab 1000 User** sollte man Ollama durch ein professionelles Framework (vLLM, TGI) ersetzen. Der Umbau in chmusicprosrv ist minimal (gleiche API), aber die Infrastruktur erfordert GPU-Cluster-Management.

4. **Linearer GPU-Bedarf:** Jede Verzehnfachung der User erfordert grob eine Verzehnfachung der GPU-Leistung -- es gibt kaum Skaleneffekte bei Inference (ausser durch effizienteres Batching mit vLLM).

5. **Alternative ab 500+ User:** Hybrid-Ansatz -- einfache/schnelle Aufgaben (Titel, Prompt-Verbesserung) lokal auf einem kleinen Modell, komplexe Aufgaben (Lyrics, Uebersetzung) via Cloud-API (OpenAI/Claude). Das reduziert die lokale GPU-Last erheblich und ist die gaengige Strategie im SaaS-Betrieb.

---

## 10. Richtpreise (Stand Februar 2026)

Die folgenden Preise sind Richtwerte und koennen je nach Verfuegbarkeit und Verhandlung variieren.

### Kauf-Optionen (einmalig)

| Option | Beschreibung | Richtpreis |
|--------|--------------|------------|
| **Mac Studio M4 Max 128GB** | Kompakt, leise, 128GB Unified Memory, 546 GB/s Bandbreite | **~CHF 4'000** |
| **Mac Studio M3 Ultra 96GB** | Mehr Bandbreite (800 GB/s), 96GB reicht fuer 32B | **~CHF 4'000** |
| **GPU: RTX 6000 Ada 48GB** | Karte allein, 48GB GDDR6, professionelle Workstation-GPU | **~CHF 6'500-7'500** |
| **Workstation + RTX 6000 Ada** | Komplettsystem (16-Core CPU, 64GB RAM, NVMe, GPU) | **~CHF 10'000-13'000** |
| **GPU: A100 80GB (gebraucht)** | Datacenter-GPU, Vorgaengergeneration, gute Verfuegbarkeit | **~CHF 5'000-12'000** |
| **Server + A100 80GB (neu)** | Komplett-Server mit A100, 128GB RAM, NVMe | **~CHF 15'000-25'000** |
| **GPU: H100 80GB** | Aktuelle Datacenter-Spitzenklasse | **~CHF 25'000-40'000** |

### Miet-Optionen Schweiz (monatlich, Daten bleiben in der Schweiz)

| Anbieter | Standort | GPU / VRAM | Typ | Richtpreis |
|----------|----------|-----------|-----|------------|
| **Nine.ch** | Zuerich | A100 40GB | Dedizierter Bare-Metal-Server, Root-Zugang | **CHF 850/Mt** |
| **cloudscale.ch** | Schweiz | L40S 48GB | Cloud-Instanz, Self-Service, sekundengenau | **ab CHF 2.20/Std** |
| **Exoscale** | Zuerich | RTX Pro 6000 96GB | Cloud-Instanz, Self-Service, sekundengenau | **EUR 1.84/Std** |
| **Exoscale** | Genf | A30 24GB (1 GPU) | Cloud-Instanz, guenstigste Option | **EUR 0.58/Std** |
| **Hikube** | Schweiz | H100/A100/L40S | GPU-as-a-Service, auf Anfrage | **Auf Anfrage** |
| **Safe Swiss Cloud** | Schweiz | H100/L4 | Dediziert, Compliance-fokussiert (FINMA) | **Auf Anfrage** |
| **CloudSigma** | Zuerich | A100 | IaaS Cloud, konfigurierbar | **Auf Anfrage** |

### Miet-Optionen Ausland (guenstiger, Daten ausserhalb CH)

| Anbieter | Standort | GPU / VRAM | Typ | Richtpreis |
|----------|----------|-----------|-----|------------|
| **Hetzner GEX131** | Nuernberg (DE) | RTX Pro 6000 96GB | Dedizierter Server | **EUR 889/Mt** |
| **RunPod** | Diverse (USA/EU) | A100 80GB | Cloud, on-demand | **~USD 1'015/Mt** |
| **Vast.ai** | Diverse | A100 80GB | Marketplace, variabel | **ab ~USD 525/Mt** |

### Hochrechnung fuer Dauerbetrieb (24/7, 12 Monate)

| Option | Einmalig | Monatlich | Total 1. Jahr | Total 3. Jahr |
|--------|---------|-----------|---------------|---------------|
| **Mac Studio M4 Max 128GB** (Kauf) | CHF 4'000 | CHF 0 (Strom ~20) | **~CHF 4'240** | **~CHF 4'720** |
| **Workstation + RTX 6000 Ada** (Kauf) | CHF 11'000 | CHF 0 (Strom ~50) | **~CHF 11'600** | **~CHF 12'800** |
| **Nine.ch A100 40GB** (Miete, CH) | CHF 0 | CHF 850 | **~CHF 10'200** | **~CHF 30'600** |
| **Exoscale RTX Pro 6000** (Miete, CH, 24/7) | CHF 0 | ~CHF 1'350 | **~CHF 16'200** | **~CHF 48'600** |
| **Hetzner GEX131** (Miete, DE) | CHF 0 | ~CHF 900 | **~CHF 10'800** | **~CHF 32'400** |

**Hinweis zu On-Demand-Preisen:** Exoscale und cloudscale.ch rechnen pro Stunde/Sekunde ab. Bei Nutzung nur waehrend Buerozeiten (10h/Tag, 22 Tage/Mt) statt 24/7 reduzieren sich die Kosten auf ca. 30% der obigen Werte.

---

## 11. Schweizer Anbieter im Detail

### Empfohlene Anbieter (GPU-Server in der Schweiz)

#### Nine.ch -- Dedizierter GPU-Server

- **Standort:** Zuerich (2 unabhaengige Standorte)
- **GPU:** NVIDIA A100 40GB
- **Typ:** Bare-Metal Root-Server (voller Zugang, Ollama direkt installierbar)
- **Spezifikation:** Intel Xeon Silver 4210R, 384GB RAM, 2x 1.92TB NVMe
- **Preis:** CHF 850/Monat
- **Datenhoheit:** Schweizer Firma, Schweizer Rechenzentren, Schweizer Recht
- **Bewertung:** Beste Option fuer immer-aktiven Ollama-Betrieb. A100 40GB reicht fuer Qwen3-32B (Q4_K_M). Voller Root-Zugang, keine Einschraenkungen. 2 Wochen kostenlose Testphase verfuegbar.

#### Exoscale -- Cloud-GPU on-demand

- **Standort:** Zuerich (CH-DK-2) und Genf (CH-GVA-2)
- **GPUs verfuegbar:**

| GPU | VRAM | Standort | vCPU | RAM | Preis/Std |
|-----|------|----------|------|-----|-----------|
| A30 | 24 GB | Genf | 12 | 56 GB | EUR 0.58 |
| A30 (2x) | 48 GB | Genf | 16 | 90 GB | EUR 1.16 |
| RTX Pro 6000 | 96 GB | Zuerich | 36 | 120 GB | EUR 1.84 |
| RTX Pro 6000 (2x) | 192 GB | Zuerich | 72 | 240 GB | EUR 3.68 |

- **Typ:** Cloud-Instanz, Self-Service, sekundengenaue Abrechnung
- **Datenhoheit:** Europaeische Firma (A1 Telekom Austria), Schweizer Rechenzentren, kein US Cloud Act
- **Bewertung:** Flexibelste Option. RTX Pro 6000 mit 96GB VRAM ist massiv ueberdimensioniert fuer Qwen3-32B -- bietet aber Reserve fuer groessere Modelle. Ideal wenn man nicht 24/7 laufen will.

#### cloudscale.ch -- Cloud-GPU Self-Service

- **Standort:** Schweiz
- **GPU:** NVIDIA L40S 48GB (bis zu 4 GPUs)
- **Typ:** Cloud-Instanz, Self-Service, sekundengenaue Abrechnung
- **Preis:** ab CHF 2.20/Std
- **Datenhoheit:** Schweizer Firma, alle Daten in der Schweiz, kein US Cloud Act
- **Bewertung:** L40S mit 48GB VRAM ist der Sweet-Spot fuer Qwen3-32B. Unkomplizierter Self-Service.

### Weitere Schweizer Anbieter

#### Hikube -- GPU-as-a-Service

- **Standort:** Schweiz (ISO 27001, GDPR, LP-zertifiziert)
- **GPUs:** H100 80GB, A100 80GB, L40S 48GB
- **Typ:** GPU dynamisch an Instanzen anbindbar
- **Preis:** Auf Anfrage ("Request a Demo")
- **Bewertung:** Gute GPU-Auswahl, aber Enterprise-orientiert. Fuer groessere Setups interessant.

#### Safe Swiss Cloud -- Compliance-fokussiert

- **Standort:** Schweiz
- **GPUs:** H100 80GB, L4 24GB
- **Typ:** Dedizierte GPU-Instanzen (Minimum 1 Monat)
- **Zertifizierungen:** FADP, EU-GDPR, FINMA, BAFIN, HIPAA, C5, NIS2
- **Preis:** Auf Anfrage
- **Bewertung:** Ideal wenn regulatorische Compliance (z.B. FINMA) gefordert ist. Fuer ein Musik-Tool eher ueberdimensioniert.

#### Infomaniak -- Staerkste Datenhoheit

- **Standort:** Genf (Tier III+)
- **GPUs:** L4 24GB, A2 16GB
- **Typ:** Public Cloud (OpenStack-basiert)
- **Datenhoheit:** 100% Schweizer Firma, Schweizer Personal, kein Outsourcing, keine auslaendischen Abhaengigkeiten
- **Bewertung:** Beste Datenhoheits-Story am Markt, aber GPU-Angebot zu schwach fuer Qwen3-32B. L4 (24GB) reicht nur fuer 14B-Modelle. Eher geeignet fuer leichtere KI-Workloads.

#### Swisscom Swiss AI Platform -- Enterprise

- **Standort:** Swisscom-Rechenzentren, Schweiz
- **GPUs:** NVIDIA H100 SuperPOD (DGX-Systeme)
- **Typ:** Managed Platform (GPU-Miete, GenAI Studio, AI Work Hub)
- **Preis:** Auf Anfrage (Enterprise Sales)
- **Bewertung:** Erste NVIDIA SuperPOD der Schweiz. Fuer Grossunternehmen und Modell-Training. Fuer einen Ollama-Einzelserver massiv ueberdimensioniert.

### Colocation (eigene Hardware in Schweizer Rechenzentrum stellen)

Falls ein Mac Studio oder eigener Server gekauft und in einem Schweizer RZ betrieben werden soll:

| Anbieter | Standort | Bemerkung |
|----------|----------|-----------|
| **Green Datacenter** | Zuerich/Aargau (6 Standorte) | Premium, 100% erneuerbare Energie, PUE 1.3-1.4 |
| **Nine.ch** | Zuerich (2 Standorte) | 24/7 Zugang, kompakt |
| **Infomaniak** | Genf | Tier III+, Housing/Colocation |
| **Equinix** | Zuerich | Enterprise-Colocation |
| **Swisscom Telehousing** | 8 Standorte schweizweit | Nationale Abdeckung |

**Colocation-Kosten:** Typisch CHF 80-200/Mt fuer 1-2 Hoeheneinheiten (1U-2U) inklusive Strom und Anbindung. Ein Mac Studio benoetigt minimal Platz.

### Empfehlung fuer 10 User in der Schweiz

| Variante | Loesung | Ungefaehr |
|----------|---------|-----------|
| **Guenstigste (Kauf)** | Mac Studio M4 Max 128GB + Colocation bei Green/Nine.ch | ~CHF 4'000 einmalig + ~CHF 150/Mt Colocation |
| **Einfachste (Miete)** | Nine.ch A100 40GB Bare-Metal | CHF 850/Mt, sofort einsatzbereit |
| **Flexibelste (on-demand)** | Exoscale RTX Pro 6000 96GB in Zuerich | EUR 1.84/Std (nur zahlen wenn genutzt) |
| **Bester VRAM/Preis (Miete)** | cloudscale.ch L40S 48GB | ab CHF 2.20/Std |
