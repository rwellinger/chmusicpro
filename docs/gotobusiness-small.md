# Business Plan: KI-Musik-Plattform als SaaS

**Erstellt:** 2025-02-02
**Zielgruppe:** Entscheidungsträger ohne IT-Hintergrund

---

## 1. Executive Summary

### Was ist das Produkt?

Eine KI-gestützte Musik-Produktions-Plattform, die Künstlern und Produzenten hilft:
- **Song-Texte** mit KI-Unterstützung zu schreiben
- **Musik** automatisch zu generieren
- **Cover-Bilder** per KI zu erstellen
- **Projekte** zu organisieren und zu verwalten

### Aktueller Stand

Die Plattform funktioniert bereits vollständig für **einen einzelnen Nutzer**. Alle Kernfunktionen sind implementiert und getestet.

### Ziel

Transformation zu einer **SaaS-Plattform** (Software-as-a-Service), bei der sich viele Kunden über das Internet registrieren und die Plattform gegen monatliche Gebühr nutzen können.

---

## 2. Entwicklungskosten mit Claude Code

### Kostenvorteil durch KI-gestützte Entwicklung

| Position | Traditionelle Entwicklung | Mit Claude Code |
|----------|---------------------------|-----------------|
| Monatliche Kosten | Entwicklergehälter | ~95 EUR (Abo-Gebühr) |
| Zeitraum | 5-6 Monate | 3-6 Monate |
| **Gesamtkosten** | **85.000-150.000 EUR** | **285-570 EUR** |

**Hinweis:** Die Claude Code-Kosten beinhalten nur das KI-Abo. Arbeitszeit für Planung, Testing und Projektmanagement kommen hinzu, sind aber deutlich geringer als bei traditioneller Entwicklung.

---

## 3. Was muss umgesetzt werden?

### Bereich 1: Benutzer-Registrierung

**Aktuell:** Nutzer können sich nur intern registrieren (kein öffentlicher Zugang).

**Benötigt:**
- Anmeldeformular im Internet
- E-Mail-Bestätigung (Verifizierung)
- Schutz vor automatisierten Anmeldungen (Bots)
- Passwort-Zurücksetzen per E-Mail

### Bereich 2: Kunden-Trennung (Mandantenfähigkeit)

**Aktuell:** Alle Daten liegen in einem gemeinsamen Bereich.

**Benötigt:**
- Jeder Kunde sieht **nur seine eigenen** Projekte und Daten
- Strenge Trennung verhindert versehentlichen Datenzugriff
- Administratoren können ihren Kundenbereich verwalten

### Bereich 3: Abo-System und Bezahlung

**Aktuell:** Keine Bezahlfunktion vorhanden.

**Benötigt:**

| Paket | Preis/Monat | Zielgruppe |
|-------|-------------|------------|
| **Free** | 0 EUR | Ausprobieren, Hobby-Nutzer |
| **Pro** | 19 EUR | Aktive Musiker, Produzenten |
| **Business** | 49 EUR | Teams, professionelle Studios |

- Integration mit **Stripe** (sicherer Zahlungsanbieter)
- Automatische Rechnungsstellung
- Nutzungslimits je nach Paket

### Bereich 4: Rechtliches und Datenschutz

**Benötigt:**
- Allgemeine Geschäftsbedingungen (AGB)
- Datenschutzerklärung (DSGVO-konform)
- Möglichkeit zur Daten-Löschung auf Kundenwunsch
- Protokollierung von Nutzeraktionen (Audit-Log)

---

## 4. Skalierungsstufen und Infrastrukturkosten

### Stufe 1: Start (bis 100 Nutzer)

| Position | Monatliche Kosten |
|----------|-------------------|
| Server-Infrastruktur | ~1.500 EUR |
| Externe KI-Dienste | ~200 EUR |
| Support/Betrieb | ~500 EUR |
| **Gesamt** | **~2.200 EUR** |

**Einnahmen-Potenzial:** ~500 EUR/Monat (bei 10% zahlenden Nutzern)

### Stufe 2: Wachstum (bis 1.000 Nutzer)

| Position | Monatliche Kosten |
|----------|-------------------|
| Server-Cluster | ~8.000 EUR |
| Externe KI-Dienste | ~2.000 EUR |
| Support/Betrieb | ~3.000 EUR |
| **Gesamt** | **~13.000 EUR** |

**Einnahmen-Potenzial:** ~4.500 EUR/Monat (bei typischem Nutzer-Mix)

### Stufe 3: Enterprise (bis 10.000 Nutzer)

| Position | Monatliche Kosten |
|----------|-------------------|
| Server-Farm | ~30.000 EUR |
| Externe KI-Dienste | ~10.000 EUR |
| Support/Betrieb | ~10.000 EUR |
| **Gesamt** | **~50.000 EUR** |

**Einnahmen-Potenzial:** ~45.000 EUR/Monat

---

## 5. Break-Even-Analyse

### Wann wird die Plattform profitabel?

**Beispielrechnung bei 1.000 registrierten Nutzern:**

| Nutzergruppe | Anzahl | Einnahmen/Monat |
|--------------|--------|-----------------|
| Free (85%) | 850 | 0 EUR |
| Pro (10%) | 100 | 1.900 EUR |
| Business (5%) | 50 | 2.450 EUR |
| **Gesamt** | 1.000 | **4.350 EUR** |

**Laufende Kosten:** ~13.000 EUR/Monat

**Break-Even-Punkt:** Etwa **3.000 zahlende Nutzer** benötigt
- Davon ca. 300 Pro-Abonnenten (19 EUR)
- Davon ca. 150 Business-Abonnenten (49 EUR)

---

## 6. Zeitplan

| Phase | Zeitraum | Meilenstein |
|-------|----------|-------------|
| **Phase 1** | Monat 1-3 | Registrierung + Kunden-Trennung |
| **Phase 2** | Monat 3-5 | Abo-System + Bezahlung |
| **Phase 3** | Monat 5-6 | Rechtliches + Beta-Test |
| **Launch** | Monat 6+ | Öffentlicher Start |

---

## Zusammenfassung

| Aspekt | Wert |
|--------|------|
| **Entwicklungskosten (Claude Code)** | 285-570 EUR |
| **Entwicklungszeit** | 3-6 Monate |
| **Monatliche Betriebskosten (Start)** | ~2.200 EUR |
| **Break-Even** | ~3.000 zahlende Nutzer |
| **Vergleich traditionelle Entwicklung** | 85.000-150.000 EUR |

---

*Technische Details: siehe `docs/gotobusiness.md`*
