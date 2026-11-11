# Radiostream-Setup mit diesem Fork (Stand 11.11.2026)

Dieses Dokument beschreibt die Installation, für die der Branch `chrischan`
gepflegt wird: drei Internetradio-Streams, die rund um die Uhr über Bluetooth
an drei UKW-Sender gehen. Die Funktionen des Add-ons selbst stehen in
[`bluetooth_audio_manager/DOCS.md`](../bluetooth_audio_manager/DOCS.md); hier
geht es um Hardware, PulseAudio, die Home-Assistant-Seite und die Entscheidungen
dahinter.

MAC-Adressen, Config-Entry-IDs und Gerätenamen der Handys stehen bewusst nicht
hier (öffentliches Repository) – sie liegen in den HA-Helfern
(`input_text.radiostream_address_map` usw.).

Die Konfiguration selbst – Automationen, Skripte, Dashboard `radio-streams`,
REST-Befehle, Universal-Media-Player und Senderlisten-Sensor – liegt als
anonymisierter Export unter [`docs/chrischan-ha/`](chrischan-ha/); dort
beschreibt die [README](chrischan-ha/README.md) Platzhalter, nötige Helfer und
das Einspielen.

## 1. Aufbau

| Box | Frequenz | MPD-Port | Steckdose |
|-----|----------|----------|-----------|
| ES-BT17 | 87.5 MHz | 6600 | `switch.dose_bt_87_5` |
| ES-BT17 | 105.9 MHz | 6601 | `switch.dose_bt_105_9` |
| ES-BT17 | 97.0 MHz | 6602 | `switch.dose_bt_97_0` |

- **Host:** Home Assistant OS auf einem Fujitsu Futro S740, PulseAudio 17 im
  Audio-Plugin (`hassio_audio`).
- **Boxen:** ES-BT17 empfangen Bluetooth (A2DP, SBC) und senden auf UKW. Sie
  haben keine Pairing-Taste – gepairt bzw. neu verbunden wird per Stromzyklus
  über ihre Zigbee-Steckdose.
- **Bluetooth-Adapter:**
  - Realtek RTL8761B als USB-Stick (USB 2.0, mit Verlängerungskabel) –
    ausschließlich für dieses Add-on, in den App Settings per MAC fest
    eingestellt. In der HA-Bluetooth-Integration ist er ignoriert
    (Doppelzugriff HA + Add-on führte früher zu Kernel-Abstürzen).
  - Intel AX210 (intern) – gehört HA, passives Scannen.
- **Streams:** RADIO BOB! über die MPD-Instanzen des Add-ons. In HA gibt es pro
  Box zwei Player: `media_player.musik_radiostream_<p>` (MPD-Integration, wird
  von Automationen/Skripten gesteuert) und `media_player.radiostream_<p>_sender`
  (Universal-Media-Player-Wrapper aus YAML, fürs Dashboard).

## 2. Add-on

- Installiert als lokal gebautes Add-on `1b3a7c56_bluetooth_audio_manager`
  aus diesem Branch, Version `2.1.0-cc.17`. Das ursprüngliche scyto-Add-on
  (`d4261985`) wurde am 06.11.2026 deinstalliert; sein Repository ist noch
  eingetragen, falls ein Rückweg nötig ist.
- **App Settings:** Adapter = Realtek-MAC, Auto-Reconnect an,
  *Prefer 44.1 kHz Bluetooth audio* an. Lautstärke-Sperre und ihren Wert
  (*Locked volume*) setzt HA (Abschnitt 4). Der Wert wirkt auf die
  MPD-Lautstärke; Stream und Box bleiben auf 100 %. Unter 100 % hilft er,
  wenn ein UKW-Sender bei vollem Pegel übersteuert.
- **Pro Box:** eigener Name (z. B. „Radiostream 87.5"), *When Idle* =
  Standard, Lautstärke-Sperre an, AVRCP aus, MPD-Port wie oben.

### Fork-Versionen

| Version | Datum | Inhalt |
|---------|-------|--------|
| cc.1 | 31.10./01.11. | Fixes für #315 (Adapter-Reindex), #316 (MPD nach Reconnect, Self-Heal), #317 (Auto-Reconnect nach Force-Reconnect), #318 (Streams auf fremdem Sink), #319 (Discovery vs. Wiedergabe); MPD-Stream-Lautstärke 100 % |
| cc.2 | 01.11. | Dokumentation der Fixes |
| cc.3 | 01.11. | MPD-Repeat für Live-Streams, schmalere D-Bus-Signal-Abos |
| cc.4 | 01.11. | Wiederholte Wiedergabe nach Stream-Fehler (Internetausfall) |
| cc.5 | 02.11. | Sink-Zustände running/idle werden erkannt, keine minütliche Discovery mehr |
| cc.6 | 02.11. | Lautstärke-Sperre pro Box |
| cc.7 | 02.11. | Lautstärke-Sperre für alle Boxen in den App Settings |
| cc.8 | 02.11. | Keine zeitgesteuerten `pactl`-Abfragen mehr; Diagnose-Endpunkt für PulseAudio-Logs |
| cc.9 | 02.11. | Gap-Monitor: Stille vor Bluetooth erkennen |
| cc.10 | 02.11. | Gap-Monitor: Stockungen am Bluetooth-Ausgang erkennen |
| cc.11 | 03.11. | Bitraten-Erholung zur Laufzeit einstellbar – **zurückgenommen**, siehe 3. |
| cc.12 | 03.11. | Rücknahme von cc.11; Bitraten-Erholung nur noch lesend anzeigen |
| cc.13 | 06.11. | 44,1 kHz bevorzugen: 48-kHz-Verbindungen, die eine Box selbst aufbaut, werden neu geöffnet |
| cc.14 | 06.11. | Nach dem Neuöffnen das A2DP-Profil der Karte aktivieren (sonst fehlte der Sink) |
| cc.15 | 07.11. | Eigene Anzeigenamen pro Box (*Name* in den Geräte-Einstellungen); aiohttp 3.14.4 (wie scyto#320) |
| cc.16 | 07.11. | Lautstärke-Sperre mit einstellbarem Wert für alle Boxen (*Locked volume*, 10–100 %), statt fest 100 % |
| cc.17 | 10.11. | Härtung: PulseAudio-Verbindung wird überwacht und neu aufgebaut (Neustart des Audio-Dienstes, PulseAudio beim Start noch nicht da); fehlt der eingestellte Adapter beim Start, wird auf ihn gewartet statt auf einen fremden auszuweichen; `pactl` mit Zeitlimit; MPD-Log-Leser und MPD-Wächter überstehen Fehler |

### Basis und übernommene Arbeit aus anderen Forks

| Quelle | Was | Wie übernommen |
|--------|-----|----------------|
| [scyto/ha-bluetooth-audio-manager](https://github.com/scyto/ha-bluetooth-audio-manager), Branch `dev` | Original-Add-on, Stand 2.1.0 plus UI-Escaping-Fix | Basis dieses Branches |
| [slawa19/ha-bluetooth-audio-manager](https://github.com/slawa19/ha-bluetooth-audio-manager), Branch `fix/normalize-mpd-stream-volume`, Commit [`0a5e806`](https://github.com/slawa19/ha-bluetooth-audio-manager/commit/0a5e806cc7f978c91a354e10d01c70ced5d9e9c7) (Slawa Gorobets, 18.07.2026) | „fix: normalize MPD PulseAudio stream volume" – jeder neue MPD-Stream wird in PulseAudio auf 100 % gesetzt (ergänzt scyto#285) | Unverändert per Cherry-Pick als `5e73193`, Autor bleibt Slawa Gorobets; seit cc.1 |
| [Cayouche1989/ha-bluetooth-audio-manager](https://github.com/Cayouche1989/ha-bluetooth-audio-manager), Branch `cayouche/reconnect-2.1.1`, Commit [`2c38ea0`](https://github.com/Cayouche1989/ha-bluetooth-audio-manager/commit/2c38ea08619c045e380ab11fddc51a52a329e82e) (23.08.2026) | „Fix auto-reconnect after speaker availability" | Nur der Teil für fehlgeschlagene explizite Verbindungen, neu umgesetzt in `fc313d0` (Hinweis im Commit); der Discovery-gesteuerte Teil nicht. Zusammen mit `84ad826` deckt das beide Vorschläge aus scyto#317 ab; seit cc.1 |

Alles Übrige im Branch ist eigene Arbeit (Fixes für scyto#315–#319 und die
Erweiterungen cc.2–cc.17).

Bei scyto eingereicht (09.11.2026), nur `src/` und `tests/`:
[#324](https://github.com/scyto/ha-bluetooth-audio-manager/pull/324) mit den Fixes für
#315–#319 und [#325](https://github.com/scyto/ha-bluetooth-audio-manager/pull/325) mit den
Erweiterungen (Lautstärke-Sperre, Anzeigenamen, 44,1 kHz, Live-Radio, Diagnose; baut auf #324 auf).
Die Härtung aus cc.17 ist dort noch nicht eingereicht.

## 3. PulseAudio: Aussetzer-Fix (custom.pa)

**Symptom:** Mit drei gleichzeitigen Streams alle 50–70 Sekunden ein kurzer
Aussetzer.

**Ursache (gemessen mit dem Gap-Monitor, cc.9/cc.10):**

- Vor Bluetooth fehlte nie Audio – MPD, Stream und PulseAudio-Mischung sind
  unschuldig.
- Am Bluetooth-Ausgang stockten mit drei Streams auf dem Realtek-Stick alle
  drei Boxen laufend (97.0 ~9/min, 105.9 ~15/min, 87.5 ~20/min, bis 125 ms).
  Mit einem oder zwei Streams (jede Kombination) gab es keine Aussetzer.
- Mechanismus in `module-bluez5-device`: Kommt der Adapter nicht hinterher,
  verwirft PulseAudio Audio (= hörbarer Aussetzer) und senkt den SBC-Bitpool
  um 5. Danach hebt es ihn alle `output_rate_refresh_interval_ms` (Standard
  500 ms) um 1 an und läuft so sofort wieder in die nächste Überlast.
- Der Intel AX210 wurde erneut getestet: Er verbindet drei Boxen, trägt aber
  keine drei Streams (Stockungen bis 2,6 s, Abbrüche).

**Fix:** Bitraten-Erholung auf einmal pro Stunde. Die Datei `/data/custom.pa`
im Audio-Plugin wird bei jedem PulseAudio-Start geladen:

```
unload-module module-bluetooth-discover
load-module module-bluetooth-discover output_rate_refresh_interval_ms=3600000
```

- **Anlegen:** In der App *Advanced SSH & Web Terminal* kurz den Schutzmodus
  ausschalten, dann
  `docker exec hassio_audio sh -c 'printf "%s\n" "unload-module module-bluetooth-discover" "load-module module-bluetooth-discover output_rate_refresh_interval_ms=3600000" > /data/custom.pa'`,
  Schutzmodus wieder an, `ha audio restart`, danach das Add-on neu starten.
- **Prüfen:** `GET /api/diagnostics/pulse-bluetooth` muss
  `output_rate_refresh_interval_ms: 3600000` zeigen.
- **Rückgängig:** `docker exec hassio_audio rm /data/custom.pa`, dann
  `ha audio restart`.
- **Nicht zur Laufzeit neu laden:** Das Entladen des Bluetooth-Moduls bei
  verbundenen Boxen hat PulseAudio auf HAOS abstürzen lassen (cc.11).

**Ergebnis:** Mit 10 Minuten Intervall in 20 Minuten nur noch zwei Stockungen
≥60 ms (beide in den ersten 3 Minuten) statt rund 44 pro Minute, Hörtest ohne
Aussetzer. Ein einzelner kurzer Aussetzer beim Hochstufen führte zur
Festlegung auf 60 Minuten (aktiv seit 06.11.2026 22:17). Nach jedem
Neustart oder Neuverbinden beginnt PulseAudio wieder mit voller Bitrate;
anfangs sind daher 1–2 kurze Aussetzer möglich.

### 44,1 statt 48 kHz

Wer eine A2DP-Verbindung aufbaut, bestimmt das Format. Verbindet das Add-on,
wählt PulseAudio 44,1 kHz. Verbindet sich eine Box nach einem Stromzyklus
selbst, wählt die ES-BT17 48 kHz – bei Bitpool 53 sind das 357 statt 328 kbit/s
(~9 % mehr Funkzeit) plus Resampling. cc.13/cc.14 öffnen solche Verbindungen
neu (*Prefer 44.1 kHz Bluetooth audio*, höchstens zwei Versuche pro Box in
10 Minuten). Für UKW würden 32 kHz reichen, lassen sich mit HAOS-PulseAudio
aber nicht erzwingen; der Bitpool ist der entsprechende Hebel.

## 4. Home-Assistant-Seite

### Zentrale Helfer

- `input_text.radiostream_address_map`, `..._port_map`, `..._dose_switch_map`,
  `..._schalter_map`, `..._aktiv_map`, `..._mpd_entry_map` – JSON-Maps pro Box,
  einzige Quelle für MACs, Ports, Steckdosen, Schalter und MPD-Config-Entries.
- `input_boolean.radiostream_<p>_aktiv` – soll die Box spielen.
- `input_boolean.radiostream_ausfall_gemeldet_<p>` – für diese Box wurde ein
  Ausfall gemeldet (nur dann gibt es eine Entwarnung).
- `input_boolean.radiostream_lautstarke_fest_100` – Lautstärke-Sperre aller Boxen.
- `input_number.radiostream_lautstarke_alle_boxen` – Wert, auf dem die Sperre die
  Boxen hält (10–100 %, Standard 100).
- `input_boolean.radiostream_power_schaltet_steckdosen` – ob „Aus" auch die
  Steckdose schaltet.
- `input_select.radiosender_<p>`, `input_select.radiostream_preset_1..10`,
  `input_select.radiostream_<p>_steckdose`.
- `input_text.letzter_sender_<p>` / `letzter_preset_<n>` – gemerkte Auswahl
  (robust gegen veraltete Werte nach einem Neustart).
- `input_number.radiostream_<p>_letzte_position` – Stall-Erkennung des Watchdogs.
- `input_text.radiostream_letzter_start` – Mixing-Schutz (zuletzt gestarteter
  Player + Zeit).
- `input_datetime.radiostream_letzte_automatische_voll_reparatur` – Sperrzeit
  der Voll-Reparatur.

### Automationen

| Automation | Auslöser | Aufgabe |
|------------|----------|---------|
| **Radiostream permanent** | HA-Start, alle 5 Min, Senderwechsel, Aktiv-Schalter an, Rückkehr eines Players (20 s stabil), Player hört von selbst auf zu spielen (20 s) | Spielt den gewählten Sender. Watchdog startet neu, wenn ein aktiver Player nicht spielt, seine Position steht oder ein falscher Sender läuft. Senderwechsel, Aktivierung, Rückkehr und Stopp betreffen nur die eine Box; Rückkehr und Stopp nur, wenn sie aktiv ist. Zwischen Starts verschiedener Boxen 3 s Abstand (Mixing-Schutz). Modus `queued`. |
| **Radiostream stoppen** | Aktiv-Schalter aus | `media_stop` am Player. |
| **Bug-Watch** (Player unavailable) | Player 5/10/20/30 Min `unavailable` **oder** 15/20/30/40 Min erreichbar, aber stumm (`binary_sensor.radiostream_<p>_spielt_nicht`) | Eskalationskette, siehe unten. Nur für aktive Boxen mit Strom. |
| **Wieder verfügbar** | Player kommt aus `unavailable` zurück (20 s) oder „spielt nicht" geht aus (Player spielt 90 s durchgehend) | Entwarnung mit Ausfalldauer, ersetzt die Ausfallmeldung (gleicher Tag). Nur wenn vorher eine Meldung verschickt wurde. |
| **Nach HA-Start prüfen** | 3 Min nach HA-Start | Box seit dem Start weg: Diagnose, bei getrennter Bluetooth-Verbindung einmal Steckdosen-Zyklus. Holt verpasste Entwarnungen nach. |
| **Lautstärke-Sperre an Add-on übertragen** | Schalter `lautstarke_fest_100`, Wert `lautstarke_alle_boxen`, HA-Start | Gibt den Sperr-Wert (10–100 %) als `volume_lock_level` ans Add-on und setzt `volume_lock` für alle Boxen per REST (bei reiner Wert-Änderung nur den Wert). |
| **Sender-Auswahl persistieren** | Änderung eines Sender-/Preset-Selects | Schreibt die Auswahl in `letzter_sender_*` / `letzter_preset_*`. |
| **Senderlisten synchronisieren** | HA-Start, Änderung von `sensor.radiostream_senderliste` | Aktualisiert die Optionen aller 13 Selects und stellt die gemerkte Auswahl wieder her. |

### Eskalationskette (Bug-Watch)

| Stufe | Nach | Aktion |
|-------|------|--------|
| 1 diagnose | 5 Min | `script.radiostream_reparieren_ultralight`: prüft per API, ob Bluetooth gesund ist; lädt ggf. nur die MPD-Integration neu oder macht einen Force-Reconnect. |
| 2 steckdosen_zyklus | 10 Min | Nur die betroffene Steckdose 30 s aus, danach 60 s warten und Nachdiagnose. Stört die anderen Boxen nicht. |
| 3 addon_neustart | 20 Min | `script.radiostream_reparieren`: Steckdose aus, Add-on-Neustart, Steckdose an, MPD sicherstellen. Betrifft kurz alle Boxen, höchstens alle 30 Min. |
| 4 manuell_pruefen | 30 Min | Nur Meldung „bitte manuell prüfen". |

Die 5/10 Minuten sind bewusst länger als früher, damit die Selbstheilung des
Add-ons (Auto-Reconnect, #316-Self-Heal) zuerst greift. Alle Meldungen einer Box
laufen über `script.benachrichtigung_alle_geraete` mit Tag `radiostream_<p>` und
ersetzen sich gegenseitig auf dem Handy.

**Zweiter Einstieg „spielt nicht" (seit 11.11.2026).** Bis dahin eskalierte nur
`unavailable`. Eine Box, deren Player erreichbar ist, aber nicht spielt (Zustand
*aus* oder *pausiert*, z. B. wenn MPD keinen Ton ausgeben kann), blieb stumm, ohne
dass etwas reparierte oder meldete – „Radiostream permanent" startete sie nur immer
wieder neu. Jetzt läuft dafür dieselbe Leiter mit denselben Schritten, zehn Minuten
später: Diagnose nach 15, Steckdosen-Zyklus nach 20, Voll-Reparatur nach 30 Minuten,
Meldung „bitte manuell prüfen" nach 40.

- Erkannt wird das über drei Template-Helfer
  `binary_sensor.radiostream_<p>_spielt_nicht`: an, wenn die Box aktiv ist, ihre
  Steckdose an ist und der Player nicht `playing` meldet. Aus geht der Helfer erst,
  wenn der Player 90 s durchgehend spielt. Die kurzen Startversuche, die im
  Fehlerfall alle halbe Minute kommen, setzen die Zeit deshalb nicht zurück (ein
  einfaches „seit 15 Minuten aus" würde so nie erreicht).
- Der Einstieg entfällt, solange der Player seit mindestens 5 Minuten durchgehend
  `unavailable` ist (dann läuft bereits die Leiter für Ausfälle) und solange
  `binary_sensor.internet` aus ist oder erst seit weniger als 5 Minuten wieder an:
  ohne Internet kann kein Stream spielen, eine Reparatur würde nichts beheben.
- Die Helfer heißen in der Oberfläche „Radiostream <p> Wiedergabe" und zeigen
  *OK* oder *Problem* (oben in der Ansicht *Reparatur*, mit Zeitpunkt der
  letzten Änderung). Im Verlauf sieht man auch, wann eine Box stumm war – der
  Zustand der MPD-Player selbst wird nicht aufgezeichnet.

### Skripte

| Skript | Aufgabe |
|--------|---------|
| `radiostream_reparieren_ultralight` („Diagnose") | Stufe 1, auch per Button. |
| `radiostream_reparieren_light` („BT-Reconnect") | Force-Reconnect einer Box über das Add-on. |
| `radiostream_steckdose_zyklieren` | Steckdose einer Box 30 s aus und wieder an. |
| `radiostream_steckdosen_alle_zyklieren` | Alle eingeschalteten Steckdosen 30 s aus, dann nacheinander mit 20 s Abstand wieder an; ohne Add-on-Neustart (ab 11.11.2026, Button in Stufe 2). Daneben gibt es den Gruppenschalter `switch.radiostream_steckdosen_alle` für alle drei Steckdosen. |
| `radiostream_reparieren` („Voll-Reparatur") | Steckdose(n) aus, Add-on-Neustart, Steckdose(n) an, MPD-Integrationen neu laden, MPD sicherstellen. |
| `radiostream_mpd_sicherstellen` | Startet einen fehlenden MPD-Dienst einer verbundenen Box. |
| `radiostream_notfall_forget_pair` | Box entfernen, neu pairen, MPD zuweisen. |
| `radiostream_power_toggle` | An/Aus pro Box (Steckdose und Aktiv-Schalter). |
| `radiostream_preset_abspielen` | Preset auf eine Box legen. |

Konvention: Ein Skript ruft ein anderes immer mit `script.turn_on` +
`target.entity_id` + `data.variables` auf, nie über die Kurzform
`script.<name>`.

### REST-Befehle

`rest_command.bt_audio_*` (z. B. `get_devices`, `get_state`, `scan`,
`set_volume_lock`) stehen in einer YAML-Datei, die von der
`configuration.yaml` eingebunden wird, und sprechen die REST-API des Add-ons
an. `bt_audio_scan` wird derzeit von nichts aufgerufen, bleibt aber für den
Bedarfsfall stehen.

### Dashboard `radio-streams`

Ansichten *Radiostreams* (Bedienung), *Reparatur* (Diagnose, BT-Reconnect,
Steckdosen-Zyklus, Voll- und Notfall-Reparatur, Tabelle Frequenz/MAC/Port),
*Presets*, *Radio*, *Receiver*.

## 5. Aufgeräumt am 06.11.2026

Mit dem gepatchten Add-on waren diese Teile überflüssig oder störend:

| Entfernt | Grund |
|----------|-------|
| Bug-Watch Stufe 4 „HA-Neustart" (ersetzt durch eine Meldung) | Ein HA-Neustart startet weder Add-on noch Bluetooth oder PulseAudio neu; lief seit 23.09. nie. |
| Auslöser „reconnect" in *Radiostream permanent* (startete bei jeder Rückkehr **alle** Boxen neu) | Das Add-on schiebt fehlgeleitete Streams selbst zurück (#318). Ersetzt durch den schlanken Auslöser „Rückkehr", der nur die zurückgekehrte Box prüft. |
| Automation „hci-Index und Signalstärke überwachen" | Der Adapter ist per MAC gewählt, ein neuer hci-Index ist egal (#315). |
| Automation „Sink-Check" | Das Problem (Stream auf fremdem Sink) löst das Add-on (#318); der Watchdog erkennt falsche Sender. Die Sink-Abfrage selbst verursachte früher Aussetzer. |
| Skript „Signalstärke messen" + drei Signal-Helfer + Dashboard-Spalte | Messen braucht einen 30-s-Scan auf demselben Chip, der die Streams trägt (fror am 26.09. alle drei ein). Die Aussetzer waren kein Signalproblem. |
| Helfer letzter hci-Index, letzter automatischer HA-Neustart, letzter Gesamt-Neustart | Wurden nur von den entfernten Teilen benutzt. |
| Altes Add-on `d4261985` | Rückweg nicht mehr nötig; zwei Bluetooth-Manager dürfen nie gleichzeitig laufen. |

Wiederherstellen lässt sich alles über ein HA-Backup von vor dem 06.11.2026.

## 6. Falls die Aussetzer zurückkommen

- Zweiter USB-Bluetooth-Stick für eine Box (z. B. 97.0); der Realtek trägt
  dann nur noch zwei Streams, was im Test aussetzerfrei war.
- Das Add-on verwaltet nur einen Adapter. Dafür eine zweite Instanz dieses
  Add-ons mit eigenem Slug und Namen bauen, mit eigenem Adapter und
  dem gleichen MPD-Port für die umgezogene Box. Anzupassen sind u. a. der
  HFP-Null-Handler (darf nur einmal registriert sein) und die HA-Skripte und
  REST-Befehle für diese Box.
- Nicht den Intel AX210 dafür nehmen (gehört HA; trägt keine drei Streams).

## 7. Bekannte Grenzen (Stand 11.11.2026)

Beobachtet oder aus dem Aufbau abgeleitet; „möglich" heißt: denkbar, aber
nicht nachgewiesen.

**UKW-Boxen (ES-BT17)**

- **Klang verschlechtert sich, Stromreset hilft.** Am 07.11.2026 war der
  UKW-Klang schlecht und nach einem Stromreset der Boxen wieder in Ordnung.
  Die Ursache liegt also in der Box (Zustand des Senders); welche, ist
  unbekannt. Home Assistant merkt davon nichts: Es sieht nur Bluetooth und
  MPD, nicht, was die Box auf UKW sendet. Abhilfe: Steckdose kurz aus
  (Skript *Steckdosen-Zyklus*). Wird der Klang regelmäßig nach einiger Zeit
  schlechter, wäre ein nächtlicher Zyklus pro Box möglich.
  Am 10.11.2026 erneut, wieder behoben durch Stromreset aller drei Boxen.
  Beide Male kam der Stromreset 2–4 Minuten nach einem Update des Add-ons
  (07.11. cc.15, 10.11. cc.17). Verdacht, nicht nachgewiesen: Beim Start des
  Add-ons beginnen alle drei Streams in derselben Sekunde, der Stick kommt
  kurz nicht nach und PulseAudio senkt bei jedem Überlauf die
  Bluetooth-Bitrate (SBC-Bitpool) um eine Stufe; mit `custom.pa` steigt sie
  nur um eine Stufe pro Stunde wieder. Nach einem Stromreset verbinden sich
  die Boxen einzeln neu und starten mit voller Bitrate. Kann auch Zufall
  sein (nach einem Update wird genauer hingehört).
- **Möglich: Übersteuerung bei vollem Pegel.** Kleine UKW-Sender verzerren
  oft bei vollem Eingangspegel; Radio BOB ist laut gemastert. Gegenmittel ist
  der Sperr-Wert unter 100 % (cc.16, Regler *Lautstärke alle Boxen*). Am
  07.11. war es nicht die Ursache (Stromreset genügte).
- **Pre-Emphasis unbekannt.** In Europa gelten 50 µs, viele solche Geräte
  nutzen 75 µs (zu heller Klang); bei der ES-BT17 nicht einstellbar.
- **Möglich: Mischprodukte.** Drei Sender auf 1–1,5 m Abstand können
  rechnerisch Störungen auf etwa 88,1, 96,4 und 106,5 MHz erzeugen. Bei der
  geringen Sendeleistung meist unhörbar; sonst hilft mehr Abstand.
- **Keine Pairing-Taste.** Neu verbinden geht nur per Stromzyklus. Danach
  baut die Box die Verbindung selbst mit 48 kHz auf; das Add-on öffnet sie
  neu, damit 44,1 kHz laufen (MPD pausiert dabei einige Sekunden). So
  beobachtet am 10.11.2026 nach einem Stromreset aller drei Boxen von Hand:
  nach 40–70 s spielten alle drei wieder, 105.9 kam mit 48 kHz und lief nach
  dem Neuöffnen mit 44,1 kHz.

**Bluetooth und PulseAudio**

- **Drei Streams auf einem Realtek-Stick nur mit custom.pa** (Abschnitt 3).
  Nach einer Überlast läuft die SBC-Bitrate niedriger und erholt sich nur in
  60-Minuten-Schritten (bis zu ~5 h); nach jedem Neustart oder Neuverbinden
  sind anfangs 1–2 kurze Aussetzer möglich. Hinter UKW ist die niedrigere
  Bitrate praktisch nicht hörbar.
- **custom.pa nur beim Start von PulseAudio.** Das Bluetooth-Modul zur
  Laufzeit neu zu laden hat PulseAudio abstürzen lassen (cc.11).
- **Ein Adapter pro Add-on-Instanz** (Abschnitt 6).
- **Fehlt der eingestellte Adapter beim Start, wartet das Add-on auf ihn**
  (seit cc.17; Statuszeile in der Oberfläche, Warnung im Log, alle 5 Minuten
  wiederholt). Es weicht nicht mehr auf den Intel-Adapter aus. Ohne den
  Realtek-Stick gibt es also keinen Ton, bis er wieder da ist oder in den
  App Settings ein anderer Adapter gewählt wird (wirkt dann sofort).
- **Neustart des Audio-Dienstes (PulseAudio).** Seit cc.17 verbindet sich das
  Add-on von selbst neu (innerhalb von ~10–15 s nach Rückkehr) und richtet
  die Boxen wieder ein; die Wiedergabe startet danach „Radiostream
  permanent". Vorher half nur ein Neustart des Add-ons. Live getestet ist
  das noch nicht (ein Test unterbricht alle drei Sender für etwa eine Minute).
  Bleibt eine Box danach trotzdem stumm, meldet und repariert das seit dem
  11.11.2026 der Bug-Watch (Einstieg „spielt nicht", Abschnitt 4).
- **Signalstärke nur mit Scan.** BlueZ liefert die Signalstärke nur während
  eines Scans, und der stört auf demselben Chip alle laufenden Streams. Im
  Betrieb gibt es deshalb keine Messung mehr.
- **Keine PulseAudio-Logs.** Das Audio-Plugin von HAOS schreibt nicht ins
  Journal; Aussetzer lassen sich nur mit dem Gap-Monitor des Add-ons messen.

**Add-on**

- **Nach einem Neustart oder Update des Add-ons spielt MPD nicht von selbst
  weiter.** Die Player gehen dabei teils direkt von *spielt* auf *aus*, ohne
  *nicht verfügbar* zu sein. Wieder gestartet werden sie von „Radiostream
  permanent" (Auslöser *Rückkehr* und *Stopp*, nach ~20–30 s).
- **Anzeigenamen:** Der MPD-Ausgabename übernimmt einen geänderten Namen erst
  beim nächsten Start von MPD. *Clear all devices* löscht die Namen.
- **Sperr-Wert:** Ein Wert für alle gesperrten Boxen, kein Wert pro Box. Er
  wirkt auf die MPD-Lautstärke (digital, vor Bluetooth); Stream und Box
  bleiben auf 100 %, die Lautstärketasten der Box werden zurückgesetzt.

**Home Assistant**

- **Stopp am MPD-Player wird rückgängig gemacht.** Ist der Aktiv-Schalter an,
  startet „Radiostream permanent" einen gestoppten Player nach 20 s neu.
  Absichtlich aus geht eine Box nur über den Aktiv-Schalter bzw. Power.
- **REST-Befehl `bt_audio_put_settings`:** Die Automation übergibt das JSON
  als Text-Vorlage. Home Assistant wandelt es dabei in ein Objekt um, gibt
  aber beim Einsetzen wieder den Originaltext aus – funktioniert (getestet
  am 07.11.2026), hängt aber an diesem Verhalten von HA.
- **„Spielt nicht" heißt: der Player meldet nicht `playing`.** Meldet MPD
  *spielt*, obwohl nichts ankommt (Position steht), greift weiter nur der
  5-Minuten-Watchdog von „Radiostream permanent" mit einem Neustart des Streams;
  eine Eskalation gibt es dafür nicht. Fällt nur der Sender aus (Internet da,
  Stream nicht), laufen die Stufen einmal ins Leere. Der neue Einstieg ist mit
  nachgestellten Auslösern geprüft, aber noch nicht in einem echten Fall
  gelaufen (dafür müsste eine Box 15 Minuten stumm bleiben).
- **Keine Stufe für „Box braucht Pairing-Modus".** Die Eskalationskette endet
  mit einer Meldung; bei der ES-BT17 entspricht das dem Steckdosen-Zyklus,
  der schon Stufe 2 ist.
