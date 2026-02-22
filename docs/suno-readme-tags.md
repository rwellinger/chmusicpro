# Suno README: Tags & Lyrics-Feld Referenz

> Tags kommen ins **Lyrics-Feld** (Custom Mode) — immer in eckigen Klammern `[Tag]`  
> auf eigener Zeile, vor der Sektion die sie beschreiben.  
> Der **Style-Prompt** ist ein separates Feld für Genre, Mood, Instrumente, BPM.

---

## Allgemeine Regeln (gilt für beides)

### Platzierung
- Tags gehören ins **Lyrics-Feld**, nicht in den Style-Prompt
- Jeder Tag auf **eigene Zeile**, vor dem Inhalt der Sektion
- Reihenfolge der Tags = Reihenfolge im Song
- Maximal **3.000 Zeichen** im Custom Lyrics-Feld

### Goldene Regeln
- **Weniger ist mehr:** 1–2 Genres, 2–3 Instrumente, 1–2 Moods im Style-Prompt
- **Komma-getrennt** im Style-Prompt funktioniert besser als ganze Sätze
- **Positiv formulieren:** beschreibe was du willst, nicht was du nicht willst
- **Ein Instrumental-Tag pro Stelle** — nicht mehrere Solo-Tags stapeln
- Tags sind **Vorschläge, keine Befehle** — Suno interpretiert, nicht gehorcht
- Kleine Wortänderungen können den Output komplett verändern → immer Varianten generieren

### Pipe-Syntax für erweiterte Tags
Tags können mit `|` kombiniert werden für mehr Kontext:
```
[Verse | soft | intimate]
[Chorus | powerful | layered vocals]
[Intro | ambient | minimal]
```

---

## Teil 1: Song mit Lyrics

### Structure Tags (Grundgerüst)

| Tag | Funktion |
|---|---|
| `[Intro]` | Eröffnung, setzt Atmosphäre |
| `[Verse]` / `[Verse 1]` / `[Verse 2]` | Erzählende Strophe |
| `[Pre-Chorus]` | Spannungsaufbau vor dem Chorus |
| `[Chorus]` | Haupthook, melodischer Höhepunkt |
| `[Post-Chorus]` | Nachklang nach dem Chorus |
| `[Bridge]` | Kontrastsektion, emotionale Wendung |
| `[Outro]` | Abschluss |
| `[Interlude]` | Musikalische Pause zwischen Sektionen |
| `[Refrain]` | Alternative zu Chorus (kürzerer Wiederkehr-Part) |

### Instrumental-Sektionen (innerhalb eines Vocal-Songs)

| Tag | Funktion |
|---|---|
| `[Instrumental Break]` | Allgemeiner instrumentaler Abschnitt |
| `[Guitar Solo]` | Gitarrensolo |
| `[Piano Solo]` | Klaviersolo |
| `[Saxophone Solo]` | Saxophonsolo |
| `[Violin Solo]` | Geigensolo |
| `[Trumpet Solo]` | Trompetensolo |
| `[Drum Solo]` | Schlagzeugsolo |
| `[Bass Solo]` | Basssolo |
| `[Synth Solo]` | Synthesizer-Solo |
| `[Harmonica Solo]` | Mundharmonika-Solo |
| `[Flute Solo]` | Flötensolo |
| `[Organ Solo]` | Orgelsolo |
| `[Percussion Break]` | Perkussions-Break |
| `[Bluegrass Fiddle Break]` | Genre-spezifischer Break |

> **Tipp:** Solo-Tags funktionieren am besten wenn das Instrument auch im Style-Prompt erwähnt wird.  
> z.B. `[Guitar Solo]` + Style: "..., electric guitar, ..."

### Trick: Instrumentale Passage erzwingen
Sinnlosen Text oder Interpunktion unter einem Solo-Tag kann helfen:
```
[Guitar Solo]
. .! .. .! !! ...
```
Nicht 100% zuverlässig, aber oft effektiv um Vocals in diesem Abschnitt zu unterdrücken.

### Vocal-Tags (Gesangssteuerung)

| Tag | Funktion |
|---|---|
| `[Male Vocal]` / `[Female Vocal]` | Geschlecht der Stimme |
| `[Duet]` | Zwei Stimmen |
| `[Choir]` / `[Harmony]` | Chor / Harmonien |
| `[Backup Vocals]` | Hintergrundgesang |
| `[Spoken Word]` / `[Spoken]` | Gesprochener Text |
| `[Whisper]` / `[Whispered]` | Geflüstert |
| `[Belting]` / `[Belted]` | Kräftig gesungen |
| `[Falsetto]` | Kopfstimme |
| `[Rap]` / `[Rapping]` | Rap-Delivery |
| `[Ad-lib]` | Improvisierte Einwürfe |
| `[Humming]` | Summen |
| `[Scatting]` | Jazz-Scat |
| `[Narration]` | Erzählerisch |
| `[Chanting]` | Skandieren |

### Vocal-Charakter (im Style-Prompt ODER als Tag)

| Beschreibung | Wirkung |
|---|---|
| `soft`, `gentle` | Leise, zart |
| `powerful`, `strong` | Kräftig, dominant |
| `raspy`, `gritty` | Rau, kratzig |
| `smooth`, `silky` | Glatt, geschmeidig |
| `breathy` | Hauchig |
| `warm`, `soulful` | Warm, seelenvoll |
| `nasal`, `bright` | Nasal, hell |
| `deep`, `low` | Tief |
| `vibrato` | Mit Vibrato |
| `auto-tuned` | Auto-Tune Effekt |

### Dynamik-Tags

| Tag | Funktion |
|---|---|
| `[Crescendo]` | Lauter werdend |
| `[Decrescendo]` | Leiser werdend |
| `[A Cappella]` | Nur Gesang, keine Instrumente |
| `[Call and Response]` | Ruf und Antwort |

### Ending-Tags

| Tag | Funktion |
|---|---|
| `[Outro]` | Standard-Ende |
| `[Outro: Fade Out]` | Ausblenden |
| `[Outro: Big Finish]` | Großes Finale |
| `[End]` | Harter Stopp |
| `[Fade Out]` | Sanftes Ausblenden |

### Song mit Lyrics: Beispiel-Template

```
[Intro | ambient | piano]

[Verse 1 | soft | intimate]
Walking through the morning light
Every step feels new tonight
Finding words I couldn't say
Watching shadows fade away

[Pre-Chorus]
And I can feel it rising

[Chorus | powerful | layered vocals]
We are more than just the broken parts
We are fire burning in the dark
Hold on tight, don't let this moment go
We are everything we need to know

[Instrumental Break]

[Verse 2 | warm]
Silence speaks between the lines
Every scar becomes a sign
Nothing lost and nothing wrong
We were here where we belong

[Pre-Chorus]
And I can feel it rising

[Chorus | powerful | layered vocals]
We are more than just the broken parts
We are fire burning in the dark
Hold on tight, don't let this moment go
We are everything we need to know

[Bridge | whispered | minimal]
Let it fall, let it break
Every wall, every mistake

[Guitar Solo]

[Chorus | belted | big finish]
We are more than just the broken parts
We are fire burning in the dark
Hold on tight, don't let this moment go
We are everything we need to know

[Outro: Fade Out]
```

### Lyrics-Tipps für Songs
- **Silbenanzahl** an die Melodie anpassen (1 Silbe = 1 Note)
- **Kurze Zeilen** (4–8 Wörter) → Suno singt sauberer
- **Einfache Sprache** → klarere Vocals
- **Chorus wiederholen** → Hookline festigen
- **Reime** helfen Suno bei der Phrasierung, sind aber kein Muss
- **Verse ≠ Chorus:** unterschiedliche Zeilenlänge für Kontrast
- Lyrics vor dem Generieren auf Silbenzahl prüfen — zu viel Text = gehetzt

---

## Teil 2: EDM / Instrumental (ohne Lyrics)

### Voraussetzung
- **Instrumental-Toggle:** AN
- Lyrics-Feld nur für Structure-Tags, **kein Text**

### Structure Tags für EDM

| Tag | Funktion |
|---|---|
| `[Intro]` | Atmosphärischer Einstieg, erste Sounds |
| `[Build]` / `[Build-Up]` | Gradueller Spannungsaufbau vor dem Drop |
| `[Drop]` | Hauptteil — Bass, Kick, volle Energie |
| `[Breakdown]` | Ruhiger Abschnitt nach dem Drop, Entspannung |
| `[Instrumental Break]` | Pause/Solo-Sektion |
| `[Rise]` / `[Riser]` | Ansteigende Spannung (kürzer als Build) |
| `[Climax]` | Energetischer Höhepunkt |
| `[Transition]` | Übergang zwischen Sektionen |
| `[Ambient]` | Atmosphärisch, zurückhaltend |
| `[Percussion Break]` | Nur Rhythmus/Drums |
| `[Synth Solo]` | Synthesizer-Solo |
| `[Bass Drop]` | Betonter Bass-Einsatz |
| `[Outro]` | Auslauf |
| `[Fade Out]` | Sanftes Ende |

### EDM-spezifische Tricks

**Energie-Steuerung über Pipe-Syntax:**
```
[Intro | ambient | minimal]
[Build-Up | rising energy | tension]
[Drop | full energy | heavy bass]
[Breakdown | atmospheric | stripped]
[Build-Up | rising | dramatic]
[Drop | peak energy | euphoric]
[Outro | fading | minimal]
```

**Subgenre-Strukturen:**

Progressive House / Trance:
```
[Intro]
[Build-Up]
[Drop]
[Breakdown]
[Build-Up]
[Drop]
[Outro]
```

Drum & Bass / Dubstep:
```
[Intro]
[Build-Up]
[Drop]
[Percussion Break]
[Build-Up]
[Drop]
[Bass Drop]
[Outro]
```

Melodic Techno:
```
[Intro | ambient | minimal]
[Build-Up | hypnotic | layered]
[Drop | driving | deep bass]
[Breakdown | atmospheric]
[Build-Up | tension | rising]
[Climax | peak energy]
[Outro | fading | reverb tail]
```

Ambient / Chill:
```
[Intro | soft | atmospheric]
[Ambient]
[Build | slow | gentle rise]
[Climax | warm | lush]
[Breakdown | minimal]
[Ambient]
[Outro: Fade Out]
```

### EDM Style-Prompt Tipps
- **BPM immer angeben** — entscheidend für Subgenre
- **Kick/Bass-Charakter** beschreiben: "heavy kick", "rolling bass", "sub bass"
- **Synth-Typen** spezifizieren: "arpeggiated synths", "warm pads", "acid squelch"
- **Mix-Charakter** angeben: "clean mix", "lo-fi", "wide stereo", "punchy"
- **Atmosphäre:** "dark", "euphoric", "hypnotic", "ethereal", "aggressive"

---

## Teil 3: Sound Effects & Atmosphäre (beide Varianten)

| Tag | Wirkung |
|---|---|
| `[Rain]` / `[Thunder]` | Regen/Donner |
| `[Wind]` | Wind |
| `[Birds Chirping]` | Vogelgezwitscher |
| `[Crowd Noise]` / `[Applause]` | Publikum/Applaus |
| `[Vinyl Crackle]` | Vinyl-Knistern |
| `[Static]` | Rauschen |
| `[Heartbeat]` | Herzschlag |
| `[Footsteps]` | Schritte |
| `[Ocean Waves]` | Meeresrauschen |
| `[Clock Ticking]` | Uhr-Ticken |
| `[Whispers]` | Hintergrund-Flüstern |

> **Achtung:** Sound Effects sind unzuverlässiger als Structure-Tags.  
> Besser im Style-Prompt beschreiben als im Lyrics-Feld, wenn möglich.

---

## Teil 4: Cheat Sheet — Style-Prompt Feld

Der Style-Prompt ist **separat** vom Lyrics-Feld. Hier kommt rein:

```
[Genre], [BPM], [Instrumente], [Vocal-Typ], [Mood/Atmosphäre], [Mix-Charakter]
```

**Beispiele:**

```
Indie pop, 110 BPM, acoustic guitar, warm male vocals, bright and uplifting, clean mix
```

```
Melodic techno, 124 BPM, rolling bass, airy synths, dark atmosphere, hypnotic groove
```

```
Soul ballad, 72 BPM, electric piano, smooth female vocals, warm vintage tone, intimate
```

### Komma-Trennung > Ganze Sätze
❌ `I want a beautiful 80s song with lots of synths and a breathy female voice`  
✅ `80s synthpop, breathy female vocals, lush synths, nostalgic, polished mix`

---

## Teil 5: Häufige Fehler

| Fehler | Lösung |
|---|---|
| Tags in den Style-Prompt geschrieben | Tags gehören ins Lyrics-Feld |
| Zu viele Tags gleichzeitig | Max 2–3 Attribute pro Sektion |
| Solo-Tag aber Instrument nicht im Style-Prompt | Instrument in beiden Feldern erwähnen |
| Zu viel Text pro Zeile → gehetzt | Kürzen, max 8 Wörter pro Zeile |
| Keine Structure-Tags → chaotische Struktur | Immer mindestens [Verse] + [Chorus] |
| "No drums" statt positiver Beschreibung | "acoustic, minimal, soft percussion" |
| Widersprüchliche Genre-Tags | Ein Hauptgenre, optional ein Subgenre |
| Sound Effects im Lyrics-Feld statt Style-Prompt | Effects sind im Style-Prompt zuverlässiger |
| Gleichen Prompt 1x generiert und aufgegeben | Immer 3–5 Varianten pro Idee |
