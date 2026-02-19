# Spezifikationen: Lokale KI via Ollama (10 User)

**Stand:** Februar 2026
**Kontext:** chmusicpro -- Lokaler Betrieb aller KI-Features via Ollama fuer 10 gleichzeitige Benutzer

---

## 1. KI-Features der Anwendung (Ist-Zustand)

Die Anwendung nutzt aktuell **25 KI-Templates** in **6 Kategorien**.

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

Alle KI-Operationen muessen in der **Eingabesprache** antworten koennen:

- **Deutsch** -- Primaersprache der meisten User
- **Englisch** -- Primaersprache fuer Lyrics im Musikbereich
- **Franzoesisch, Italienisch, Spanisch** -- Sekundaersprachen

Uebersetzungs-Templates erfordern **hochwertige Uebersetzung** zwischen diesen Sprachen. Besonders kritisch: Die Uebersetzung muss nicht nur korrekt sein, sondern bei Lyrics auch **singbar** und **poetisch** bleiben.

### Token-Charakteristik pro Aufgabentyp

| Aufgabentyp | Typischer Input | Typischer Output | Gesamt-Tokens |
|-------------|----------------|-----------------|---------------|
| Lyrics generieren | 100-500 Tokens | 500-2000 Tokens | 600-2500 |
| Section verbessern/umschreiben | 200-1000 Tokens | 100-500 Tokens | 300-1500 |
| Uebersetzung | 500-2000 Tokens | 500-2000 Tokens | 1000-4000 |
| Beschreibungen | 500-2000 Tokens | 50-300 Tokens | 550-2300 |
| Prompt-Verbesserung | 20-100 Tokens | 50-150 Tokens | 70-250 |
| Titel generieren | 100-500 Tokens | 5-15 Tokens | 105-515 |
| Workshop (Inspiration etc.) | 50-500 Tokens | 200-1000 Tokens | 250-1500 |

Die meisten Operationen bleiben unter 4000 Tokens gesamt. Eine **Kontextlaenge von 8192 Tokens** reicht fuer alle Use Cases.

---

## 2. Modell-Empfehlungen

### Zwei-Modell-Strategie (empfohlen)

| Rolle | Modell | Einsatz |
|-------|--------|---------|
| **Hauptmodell** (Qualitaet) | **Qwen3-32B** | Lyrics, Uebersetzung, Workshop, Beschreibungen |
| **Schnellmodell** (Speed) | **Qwen3-8B** | Titel, schnelle Prompt-Verbesserung |

Beide Modelle sind **Open Source** (Apache 2.0, lizenzfrei). Alle 5 Zielsprachen nativ unterstuetzt (119 Sprachen trainiert).

### Hauptmodell-Kandidaten

| Modell | Parameter | Sprachen | VRAM (Q4_K_M) | Staerken | Schwaechen |
|--------|----------|----------|---------------|----------|------------|
| **Qwen3-32B** | 32B (dense) | 119 Sprachen | ~22 GB | Beste Qualitaet/Groesse-Ratio, exzellent multilingual | Braucht ~22 GB nur fuer Weights |
| **Qwen3-30B-A3B** (MoE) | 30B / 3B aktiv | 119 Sprachen | ~20 GB | Geschwindigkeit eines 3B-Modells, Qualitaet eines 30B | MoE weniger erprobt unter Last |
| **Mistral Small 3.1** | 24B | 25+ Sprachen | ~16 GB | Stark bei europaeischen Sprachen (FR!), 128K Kontext | Etwas kleiner als Qwen3-32B |
| **Qwen3-14B** | 14B | 119 Sprachen | ~11 GB | Gute Qualitaet, deutlich weniger VRAM | Lyrics-Qualitaet merkbar unter 32B |

### Schnellmodell-Kandidaten

| Modell | Parameter | VRAM (Q4_K_M) | Einsatz |
|--------|----------|---------------|---------|
| **Qwen3-8B** | 8B | ~6 GB | Titel, schnelle Prompts, Fallback |
| **Llama 3.2 3B** | 3B | ~2.5 GB | Ultra-schnelle Titel |

### Empfehlung nach Qualitaetsstufe

| Stufe | Hauptmodell | Schnellmodell | Beschreibung |
|-------|-------------|---------------|-------------|
| **Optimal** | Qwen3-32B (Q4_K_M) | Qwen3-8B | Beste lokale Qualitaet fuer Lyrics und Uebersetzung |
| **Ausgewogen** | Qwen3-30B-A3B (MoE) | Qwen3-8B | Nahe an 32B-Qualitaet, deutlich schneller |
| **Kompakt** | Qwen3-14B (Q4_K_M) | Llama 3.2 3B | Gute Qualitaet, weniger Hardware noetig |

---

## 3. VRAM- und Speicher-Anforderungen

### Berechnung fuer 10 User (8K Kontext, KV-Cache Q8_0)

KV-Cache-Quantisierung (Q8_0) halbiert den Cache-Bedarf bei minimalem Qualitaetsverlust.

| Konfiguration | Modell-Weights | KV-Cache (10 Slots) | Gesamt (10 Slots) |
|---------------|----------------|---------------------|-------------------|
| Qwen3-14B + Qwen3-8B | 17 GB | 16 GB | **33 GB** |
| Qwen3-32B + Qwen3-8B | 28 GB | 21 GB | **49 GB** |
| Qwen3-30B-A3B + Qwen3-8B | 26 GB | 16 GB | **42 GB** |

### Praxisbetrachtung: 4 statt 10 parallele Slots

Bei 10 Usern sind realistisch **2-4 gleichzeitige KI-Requests** zu erwarten. Restliche Requests werden in einer Queue nacheinander abgearbeitet. Mit 4 parallelen Slots:

| Konfiguration | Modell-Weights | KV-Cache (4 Slots, Q8) | Gesamt |
|---------------|----------------|------------------------|--------|
| **Qwen3-14B + Qwen3-8B** | 17 GB | 6.4 GB | **~24 GB** |
| **Qwen3-32B + Qwen3-8B** | 28 GB | 8.4 GB | **~37 GB** |
| **Qwen3-30B-A3B + Qwen3-8B** | 26 GB | 6.4 GB | **~33 GB** |

---

## 4. Geschwindigkeit und Antwortzeiten

### Bewertungsskala

| Bewertung | Tokens/Sekunde | Typische Strophe (~100 Tokens) | User-Erlebnis |
|-----------|---------------|-------------------------------|---------------|
| Exzellent | 30+ tok/s | 2-3 Sekunden | Fuehlt sich wie schnelles Tippen an |
| Gut | 15-30 tok/s | 3-7 Sekunden | Angenehmes Streaming |
| Akzeptabel | 8-15 tok/s | 7-13 Sekunden | Spuerbare Verzoegerung, ertraeglich |
| Grenzwertig | 5-8 tok/s | 13-20 Sekunden | Frustrierend bei haeufiger Nutzung |

### Geschwindigkeit pro Hardware (Single-User)

| Hardware | Qwen3-8B | Qwen3-14B | Qwen3-32B |
|----------|----------|-----------|-----------|
| RTX 4090 (24 GB) | ~95 tok/s | ~64 tok/s | ~34 tok/s |
| RTX 5090 (32 GB) | ~130 tok/s | ~90 tok/s | ~61 tok/s |
| RTX 6000 Ada (48 GB) | ~100 tok/s | ~50 tok/s | ~26 tok/s |
| A100 80GB | ~138 tok/s | ~80 tok/s | ~45 tok/s |
| M4 Max 128GB | ~70 tok/s | ~40 tok/s | ~28 tok/s |
| M3 Ultra 192GB | ~90 tok/s | ~55 tok/s | ~38 tok/s |

### Geschwindigkeit bei 4 gleichzeitigen Requests

| Hardware | Qwen3-32B (4 parallel) | Bewertung | Qwen3-14B (4 parallel) | Bewertung |
|----------|----------------------|-----------|----------------------|-----------|
| RTX 4090 (24 GB) | VRAM reicht nicht | -- | ~16 tok/s | Gut |
| RTX 5090 (32 GB) | ~15 tok/s | Gut | ~22 tok/s | Gut |
| RTX 6000 Ada (48 GB) | ~7 tok/s | Grenzwertig | ~13 tok/s | Akzeptabel |
| A100 80GB | ~11 tok/s | Akzeptabel | ~20 tok/s | Gut |
| M4 Max 128GB | ~7 tok/s | Grenzwertig | ~10 tok/s | Akzeptabel |
| M3 Ultra 192GB | ~10 tok/s | Akzeptabel | ~14 tok/s | Akzeptabel |

---

## 5. Hardware-Szenarien

### Szenario A: Kompakt (Qwen3-14B Hauptmodell)

**VRAM-Bedarf:** ~24 GB (4 parallele Slots, Q8 KV-Cache)
**Qualitaet:** Gut -- fuer einfache Lyrics und Uebersetzungen ausreichend. Bei komplexen kreativen Aufgaben merkbar schwaecher.

| Hardware-Option | VRAM | Geschwindigkeit (4 parallel) | Bewertung |
|----------------|------|------------------------------|-----------|
| 1x RTX 4090 | 24 GB | ~16 tok/s pro User | Schnell, VRAM knapp |
| 1x RTX 5090 | 32 GB | ~22 tok/s pro User | Schnell, VRAM komfortabel |
| M4 Max 64GB | 64 GB (unified) | ~10 tok/s pro User | Ausreichend |

**Minimale Spezifikation:**
- GPU: 1x mit mindestens 24 GB VRAM
- System-RAM: 32 GB
- CPU: 8+ Kerne
- Storage: 100 GB SSD

---

### Szenario B: Ausgewogen (Qwen3-32B Hauptmodell) -- EMPFOHLEN

**VRAM-Bedarf:** ~37 GB (4 parallele Slots, Q8 KV-Cache)
**Qualitaet:** Sehr gut -- hochwertige Lyrics in allen 5 Sprachen, poetische Uebersetzungen, kreative Workshop-Aufgaben.

| Hardware-Option | VRAM | Geschwindigkeit (4 parallel) | Bewertung |
|----------------|------|------------------------------|-----------|
| 1x RTX 6000 Ada | 48 GB | ~7 tok/s pro User | Akzeptabel |
| 1x A100 80GB | 80 GB | ~11 tok/s pro User | Gut |
| M4 Max 128GB | 128 GB (unified) | ~7 tok/s pro User | Akzeptabel |
| M3 Ultra 192GB | 192 GB (unified) | ~10 tok/s pro User | Akzeptabel-Gut |

**Minimale Spezifikation:**
- GPU: 1x mit mindestens 48 GB VRAM
- System-RAM: 64 GB
- CPU: 16+ Kerne
- Storage: 200 GB SSD

---

## 6. Qualitaetsvergleich Modellgroessen fuer Lyrics

| Aspekt | 14B | 32B |
|--------|-----|-----|
| Einfache Lyrics (EN) | Gut | Sehr gut |
| Komplexe Lyrics (Metaphern, Poetik) | Maessig | Gut |
| Lyrics (DE) | Gut | Sehr gut |
| Lyrics (FR/IT/ES) | Maessig-Gut | Gut |
| Poetische Uebersetzung | Maessig | Gut |
| Workshop (kreatives Brainstorming) | Gut | Sehr gut |
| Prompt-Verbesserung | Gut | Gut |
| Titel generieren | Gut | Gut |

32B trifft den Sweet-Spot -- signifikant besser als 14B bei kreativen Aufgaben.

---

## 7. Zusammenfassung der Hardware-Anforderungen

| | Kompakt (14B) | Ausgewogen (32B) |
|---|---|---|
| **Hauptmodell** | Qwen3-14B | Qwen3-32B |
| **Schnellmodell** | Qwen3-8B | Qwen3-8B |
| **Min. VRAM** | 24 GB | 48 GB |
| **Min. System-RAM** | 32 GB | 64 GB |
| **Min. CPU-Kerne** | 8 | 16 |
| **Min. Storage** | 100 GB SSD | 200 GB SSD |
| **Tok/s (4 parallel)** | 10-22 | 7-13 |
| **Antwortzeit (Strophe)** | 5-10s | 8-15s |
| **Lyrics-Qualitaet** | Gut | Sehr gut |
| **Uebersetzungsqualitaet** | Maessig-Gut | Gut |
| **GPU-Optionen** | RTX 4090 / RTX 5090 | RTX 6000 Ada / A100 |
| **Apple-Option** | M4 Max 64GB | M4 Max 128GB |

---

## 8. Erwartete User-Erfahrung (Szenario B, 10 User)

| Situation | Antwortzeit (Strophe ~100 Tokens) |
|-----------|------------------------------------|
| 1-2 User generieren gleichzeitig | 5-10 Sekunden |
| 3-4 User generieren gleichzeitig | 8-15 Sekunden |
| 5+ User gleichzeitig (selten) | 15-30 Sekunden |
| Ganzen Song generieren (~500 Tokens) | 35-70 Sekunden |
| Titel generieren (Schnellmodell) | 1-2 Sekunden |
| Prompt verbessern (Schnellmodell) | 2-4 Sekunden |

Typisches Nutzungsverhalten: User arbeitet 1-5 Minuten am Text, klickt "Generieren", wartet wenige Sekunden, arbeitet weiter. Die KI wird nicht permanent beansprucht.

---

## 9. Skalierung: 100, 500, 1000 User

### Gleichzeitigkeits-Schaetzung

| Registrierte User | Gleichzeitig aktiv | Gleichzeitige KI-Requests (Peak) | Benoetigte parallele Slots |
|--------------------|-------------------|----------------------------------|---------------------------|
| 10 | 3-5 | 1-3 | 4 |
| 100 | 10-15 | 4-8 | 8-10 |
| 500 | 50-75 | 15-25 | 20-30 |
| 1000 | 100-150 | 30-50 | 40-60 |

### 100 User

Ein einzelner leistungsstarker GPU-Server reicht noch aus.

| Aspekt | Anforderung |
|--------|-------------|
| Parallele Slots | 8-10 |
| Gesamt-VRAM | ~50 GB |
| GPU | 1x mit 80 GB VRAM |
| System-RAM | 64-128 GB |
| CPU | 16-32 Kerne |
| Antwortzeit (Strophe, Peak) | 15-25 Sekunden |

### 500 User

Ein einzelner Server reicht nicht mehr. Es braucht **mehrere GPU-Server** hinter einem Load Balancer.

```
                    ┌─────────────────┐
                    │  Load Balancer   │
                    └────────┬────────┘
               ┌─────────────┼─────────────┐
               v             v             v
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Ollama 1 │  │ Ollama 2 │  │ Ollama 3 │
        │ GPU 80GB │  │ GPU 80GB │  │ GPU 80GB │
        │ 8 Slots  │  │ 8 Slots  │  │ 8 Slots  │
        └──────────┘  └──────────┘  └──────────┘
              24 parallele Slots total
```

| Aspekt | Anforderung |
|--------|-------------|
| GPU-Server | 3-4 Stueck |
| Parallele Slots total | 24-32 |
| GPUs | 3-4x mit je 80 GB VRAM |
| Zusaetzlich | Load Balancer, Health Checks, Monitoring |
| Antwortzeit (Strophe, Peak) | 15-25 Sekunden |

Jede Ollama-Instanz muss das komplette Modell im eigenen VRAM halten -- kein Modell-Sharing zwischen Instanzen.

### 1000 User

Erfordert einen GPU-Cluster mit professionellem Inference-Framework (vLLM oder TGI statt Ollama).

```
                    ┌─────────────────┐
                    │  Load Balancer   │
                    └────────┬────────┘
               ┌─────────────┼─────────────┐
               v             v             v
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ vLLM /   │  │ vLLM /   │  │ vLLM /   │
        │ TGI Node │  │ TGI Node │  │ TGI Node │
        │ 2x GPU   │  │ 2x GPU   │  │ 2x GPU   │
        └──────────┘  └──────────┘  └──────────┘
           6x GPU = ~60 parallele Slots
```

| Aspekt | Anforderung |
|--------|-------------|
| Inference-Framework | vLLM oder TGI (2-4x effizienter als Ollama durch Continuous Batching) |
| GPUs | 6-8x mit je 80 GB VRAM |
| Parallele Slots total | 48-64 |
| System-RAM pro Node | 128-256 GB |
| CPU pro Node | 32-64 Kerne |
| Netzwerk | 10-25 Gbit/s zwischen Nodes |
| Zusaetzlich | Kubernetes, Monitoring, Auto-Scaling |
| Antwortzeit (Strophe, Peak) | 13-20 Sekunden |

Anpassung an chmusicpro minimal: vLLM bietet die gleiche API wie Ollama.

### Uebersicht Skalierung (Qwen3-32B)

| | 10 User | 100 User | 500 User | 1000 User |
|---|---|---|---|---|
| **Gleichzeitige KI-Requests** | 1-3 | 4-8 | 15-25 | 30-50 |
| **Parallele Slots** | 4 | 8-10 | 24-32 | 48-64 |
| **GPUs** | 1x 48GB+ | 1x 80GB | 3-4x 80GB | 6-8x 80GB |
| **Framework** | Ollama | Ollama | Ollama + Load Balancer | vLLM / TGI |
| **Architektur** | Single Server | Single Server | Multi-Instance Cluster | GPU-Cluster |
| **Antwortzeit (Strophe)** | 8-15s | 15-25s | 15-25s | 13-20s |
| **Komplexitaet** | Minimal | Gering | Mittel | Hoch |

### Kernaussagen

1. **Bis 100 User** -- ein einzelner Server genuegt.
2. **Ab 500 User** -- mehrere GPU-Server mit Load Balancing.
3. **Ab 1000 User** -- professionelles Inference-Framework statt Ollama (gleiche API, minimaler Umbau).
4. **Linearer GPU-Bedarf** -- Verzehnfachung der User erfordert grob Verzehnfachung der GPU-Leistung.
5. **Hybrid-Alternative ab 500+ User** -- einfache Aufgaben lokal, komplexe via Cloud-API (OpenAI/Claude). Gaengigste Strategie im SaaS-Betrieb.