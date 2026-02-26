# Technische Spezifikationen fuer Offerte-Anfrage

Ergaenzung zum Dokument "Anforderungen an KI-Rechenleistung".

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
- Beide Modelle muessen gleichzeitig geladen sein (~26-30 GB VRAM), damit kein zeitaufwaendiger Modellwechsel noetig ist

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
