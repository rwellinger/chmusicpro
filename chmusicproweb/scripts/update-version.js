#!/usr/bin/env node

/**
 * Script zum Aktualisieren der app-version.json
 * Wird vor jedem Build ausgeführt
 *
 * Liest Version aus package.json und schreibt sie in src/assets/app-version.json
 */

const fs = require('fs');
const path = require('path');

// Pfade definieren
const packageJsonPath = path.join(__dirname, '..', 'package.json');
const versionFilePath = path.join(__dirname, '..', 'src', 'assets', 'app-version.json');

try {
  // package.json lesen
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const version = packageJson.version;

  if (!version) {
    console.error('❌ Fehler: Keine Version in package.json gefunden');
    process.exit(1);
  }

  // Version-Daten erstellen
  const versionData = {
    version: version,
    buildDate: new Date().toISOString()
  };

  // Assets-Verzeichnis erstellen falls nicht vorhanden
  const assetsDir = path.dirname(versionFilePath);
  if (!fs.existsSync(assetsDir)) {
    fs.mkdirSync(assetsDir, { recursive: true });
  }

  // app-version.json schreiben
  fs.writeFileSync(
    versionFilePath,
    JSON.stringify(versionData, null, 2),
    'utf8'
  );

  console.log(`✅ Version ${version} erfolgreich in app-version.json geschrieben`);
  console.log(`   Build-Datum: ${versionData.buildDate}`);
  console.log(`   Pfad: ${versionFilePath}`);

} catch (error) {
  console.error('❌ Fehler beim Aktualisieren der app-version.json:', error.message);
  process.exit(1);
}
