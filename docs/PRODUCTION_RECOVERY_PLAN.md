# 🚨 Production Database Recovery Plan

**Datum:** 2025-10-21
**Problem:** Songs werden nicht mehr angezeigt nach Migration auf Produktion
**Aktuelle Alembic-Version auf Prod:** 0f864573b58a

---

## Problem-Analyse

### Was ist passiert?
1. Code wurde deployed mit neuen SQLAlchemy Models (`sketch_id`, `song_sketches`)
2. Aber Migration `d4641a241b98` wurde NICHT auf Produktion ausgeführt
3. Backend versucht Songs zu laden → SQL-Error wegen fehlender Spalte `sketch_id`
4. Daher: Keine Songs werden angezeigt (obwohl Daten noch in DB sind)

### Fehlende Migrationen auf Produktion
```
✅ 0f864573b58a - add_lyric_parsing_rules_table (AKTUELL)
❌ 234ea0f4b6c3 - base64_encode_lyric_parsing_rule_replacements
❌ d4641a241b98 - add_song_sketches_table
```

---

## Recovery-Steps (IN DIESER REIHENFOLGE!)

### SCHRITT 1: Backup erstellen (KRITISCH!)
```bash
# SSH auf Production Server
ssh rob@<production-server>

# PostgreSQL Backup
docker exec -t chmusicpro-postgres-1 pg_dump -U aiuser -d aiproxy > /tmp/aiproxy_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup auf lokalen Rechner kopieren
scp rob@<production-server>:/tmp/aiproxy_backup_*.sql ~/Desktop/
```

### SCHRITT 2: Alembic-Status auf Produktion prüfen
```bash
# Im chmusicprosrv Container
docker exec -it chmusicpro-chmusicprosrv-1 bash
cd /app
alembic current
alembic history | head -20
```

**Erwartetes Ergebnis:**
```
0f864573b58a (current)
```

### SCHRITT 3: Fehlende Migrationen anwenden
```bash
# Im chmusicprosrv Container (oder direkt im Docker Command)
docker exec -it chmusicpro-chmusicprosrv-1 alembic upgrade head

# Oder als einzelne Steps:
docker exec -it chmusicpro-chmusicprosrv-1 alembic upgrade 234ea0f4b6c3
docker exec -it chmusicpro-chmusicprosrv-1 alembic upgrade d4641a241b98
```

**Was passiert:**
1. Migration `234ea0f4b6c3`: Encodiert `replacement` Werte in `lyric_parsing_rules` zu Base64
2. Migration `d4641a241b98`:
   - Erstellt Tabelle `song_sketches`
   - Fügt Spalte `sketch_id` zur `songs` Tabelle hinzu (nullable!)
   - Erstellt Foreign Key Constraint

### SCHRITT 4: Verifizierung
```bash
# Alembic Version prüfen
docker exec -it chmusicpro-chmusicprosrv-1 alembic current

# Sollte zeigen:
# d4641a241b98 (head)
```

```sql
-- PostgreSQL Tabellen prüfen
docker exec -it chmusicpro-postgres-1 psql -U aiuser -d aiproxy -c "\d songs"
-- Sollte jetzt sketch_id Spalte zeigen

docker exec -it chmusicpro-postgres-1 psql -U aiuser -d aiproxy -c "\dt"
-- Sollte song_sketches Tabelle zeigen

-- Songs-Daten prüfen
docker exec -it chmusicpro-postgres-1 psql -U aiuser -d aiproxy -c "SELECT COUNT(*) FROM songs;"
```

### SCHRITT 5: Backend-Container neu starten
```bash
# Container neu starten, damit Model-Änderungen aktiv werden
docker restart chmusicpro-chmusicprosrv-1
docker restart chmusicpro-celery-worker-1

# Logs prüfen
docker logs -f chmusicpro-chmusicprosrv-1
```

### SCHRITT 6: Funktionstest
1. **Frontend öffnen:** https://<production-server>
2. **Songs-Übersicht öffnen**
3. **Verifizieren:** Songs werden wieder angezeigt
4. **Test:** Song-Details öffnen, abspielen testen

---

## Rollback-Plan (falls Probleme auftreten)

### Option 1: Migration rückgängig machen
```bash
docker exec -it chmusicpro-chmusicprosrv-1 alembic downgrade 0f864573b58a
docker restart chmusicpro-chmusicprosrv-1
```

**ABER ACHTUNG:** Das würde nur funktionieren, wenn der alte Code deployed wäre!

### Option 2: Backup wiederherstellen
```bash
# Backup auf Server kopieren
scp ~/Desktop/aiproxy_backup_*.sql rob@<production-server>:/tmp/

# Restore
ssh rob@<production-server>
docker exec -i chmusicpro-postgres-1 psql -U aiuser -d aiproxy < /tmp/aiproxy_backup_*.sql
```

---

## Lessons Learned & Best Practices

### ❌ Was schiefgelaufen ist:
1. **Code deployed OHNE Migrationen auszuführen**
2. **Keine Synchronisation zwischen Code-Deployment und DB-Migration**
3. **Kein Pre-Deployment Check der Alembic-Version**

### ✅ Zukünftig:
1. **IMMER Deployment-Reihenfolge einhalten:**
   ```
   1. Backup erstellen
   2. Alembic Migrations ausführen
   3. Code deployen
   4. Backend-Container neu starten
   5. Funktionstest
   ```

2. **Pre-Deployment Checklist:**
   - [ ] Backup erstellt
   - [ ] Alembic current version geprüft
   - [ ] Migration Script geprüft
   - [ ] Rollback-Plan erstellt
   - [ ] Migrations auf Test-DB getestet

3. **Automatisierung:**
   - Migration-Script in Docker-Entrypoint einbauen?
   - Health-Check für Schema-Konsistenz?

---

## Kontakt bei Problemen
- **GitHub Issues:** https://github.com/rwellinger/chmusicpro/issues

**Status:** ⏳ Warte auf Bestätigung für Durchführung
