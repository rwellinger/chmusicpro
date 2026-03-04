# Anforderungen an KI-Rechenleistung



## Welches KI-Modell?

| Rolle | Modell | Wofuer |
|-------|--------|--------|
| **Hauptmodell** | Qwen3-32B | Text, Uebersetzung, Workflow, Beschreibungen -- alle anspruchsvollen Aufgaben |
| **Schnellmodell** | Qwen3-8B | Titel generieren, schnelle Prompt-Verbesserungen |


Beide Modelle sind **Open Source** und **lizenzfrei** nutzbar (Apache 2.0). Keine laufenden Lizenzkosten. Alle 5 Zielsprachen nativ unterstuetzt.

Beide Modelle muessen **gleichzeitig geladen** sein (~26-30 GB VRAM zusammen), damit kein zeitaufwaendiger Modellwechsel noetig ist.

---

## Annahmen zur Nutzung

Die KI wird **nicht permanent** beansprucht.

1. User arbeitet **1-5 Minuten**
2. Klickt auf "Generieren", "Verbessern" oder "Uebersetzen"
3. Wartet **wenige Sekunden** auf das KI-Ergebnis (~60-80 Tokens)
4. Arbeitet wieder **1-5 Minuten** manuell weiter

Bei 10 registrierten Usern sind erfahrungsgemaess:

- **2-4 gleichzeitig eingeloggt** (nicht alle arbeiten zur selben Zeit)
- **1-2 davon nutzen aktiv die KI** (die anderen tippen, lesen, denken)

Ein einzelner GPU-Server reicht fuer 10 User, weil die KI-Last **sporadisch** anfaellt und sich zeitlich verteilt.

---

## Antwortzeiten

| Situation | Wartezeit fuer eine Strophe | Bewertung |
|-----------|----------------------------|-----------|
| 1-2 User gleichzeitig aktiv | 7-10 Sekunden | Angenehm |
| 3-4 User gleichzeitig aktiv | 10-20 Sekunden | OK |
| 5+ User gleichzeitig (selten) | 20-40 Sekunden | Spuerbar, aber ertraeglich |

Basierend auf gemessenen ~9-10 Tokens/Sekunde fuer Qwen3-32B auf vergleichbarer GPU-Hardware. Ohne GPU-Hardware (z.B. auf einer VPS mit nur CPU) wuerden dieselben Anfragen **2-5 Minuten** statt Sekunden dauern. Das ist fuer ein kommerzielles Produkt nicht tragbar.

---

## Architektur: Zwei getrennte Server

Unsere Loesung besteht aus **zwei getrennten Servern**, die ueber ein internes Netzwerk kommunizieren:

```
Internet (HTTPS)
      |
[Application Server]  --- internes Netz ---  [KI-Server]
 Webanwendung                                  Ollama + GPU
 Datenbank                                     KI-Modelle
 Dateispeicher
```

---

## Server 1: Application Server (keine GPU noetig)

Auf diesem Server laeuft die Webanwendung mit allen Diensten ausser der KI.

| Anforderung | Wert |
|-------------|------|
| **CPU** | 4 Cores |
| **RAM** | 16 GB |
| **Speicher** | 100 GB SSD |
| **Betriebssystem** | Linux (Ubuntu 24.04) |
| **Netzwerk** | Oeffentlich erreichbar (HTTPS, Ports 80/443), statische IP |
| **Zugang** | Root/Sudo (fuer Docker + TLS-Zertifikate) |

**Was laeuft darauf:**
- Nginx (Webserver + Reverse Proxy)
- Flask Backend (Python 3.12, REST API)
- PostgreSQL 17 (Datenbank)
- MinIO (S3-kompatibler Objektspeicher fuer Bilder/Dateien)
- Alles containerisiert via Docker

---

## Server 2: KI-Server (GPU zwingend)

Auf diesem Server laeuft ausschliesslich Ollama mit den KI-Modellen. Die GPU ist zwingend -- ohne GPU sind die Antwortzeiten nicht tragbar (Minuten statt Sekunden).

| Anforderung | Wert |
|-------------|------|
| **GPU** | NVIDIA mit mindestens 48 GB VRAM (z.B. L40S, RTX Pro 6000) |
| **CPU** | 4 Cores |
| **RAM** | 32 GB |
| **Speicher** | 100 GB NVMe SSD |
| **Betriebssystem** | Linux (Ubuntu 24.04) |
| **Netzwerk** | Nur intern erreichbar (zum Application Server), nicht oeffentlich |
| **Zugang** | Root/Sudo (fuer Docker + NVIDIA-Treiber) |

**Was laeuft darauf:**
- Ollama (KI-Inference-Server, als Docker-Container)
- NVIDIA Treiber + Container Toolkit (fuer GPU-Zugriff aus Docker)
- KI-Modelle: Qwen3-32B (~20-24 GB VRAM) und Qwen3-8B (~5-6 GB VRAM)
- Beide Modelle gleichzeitig geladen (~26-30 GB VRAM)

---

## Netzwerk zwischen den Servern

| Punkt | Beschreibung |
|-------|-------------|
| **Verbindung** | Application Server ruft KI-Server via HTTP auf (Ollama API, Port 11434) |
| **Bandbreite** | Gering -- nur Text (JSON), keine Video-/Audio-Streams |
| **Sicherheit** | KI-Server soll nicht oeffentlich erreichbar sein (nur internes Netz oder VPN) |

---

## Zusammenfassung

| | Application Server | KI-Server |
|---|---|---|
| **GPU** | Keine | 48 GB VRAM (NVIDIA) |
| **CPU** | 4 Cores | 4 Cores |
| **RAM** | 16 GB | 32 GB |
| **Speicher** | 100 GB SSD | 100 GB NVMe |
| **Oeffentlich** | Ja (HTTPS) | Nein (nur intern) |
| **Software** | Docker, Nginx, PostgreSQL, MinIO | Docker, Ollama, NVIDIA Toolkit |
