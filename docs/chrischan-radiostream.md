# Radiostream-Setup mit diesem Fork (Stand 06.11.2026)

Dieses Dokument beschreibt die Installation, für die der Branch `chrischan`
gepflegt wird: drei Internetradio-Streams, die rund um die Uhr über Bluetooth
an drei UKW-Sender gehen. Die Funktionen des Add-ons selbst stehen in
[`bluetooth_audio_manager/DOCS.md`](../bluetooth_audio_manager/DOCS.md); hier
geht es um Hardware, PulseAudio, die Home-Assistant-Seite und die Entscheidungen
dahinter.

MAC-Adressen, Config-Entry-IDs und Gerätenamen der Handys stehen bewusst nicht
hier (öffentliches Repository) – sie liegen in den HA-Helfern
(`input_text.radiostream_address_map` usw.).

Die Automationen und Skripte selbst liegen als anonymisierter Export aus
`automations.yaml` / `scripts.yaml` unter
[`docs/chrischan-ha/`](chrischan-ha/) (Box-MACs → `<MAC_87_5>` usw.,
Mobilgeräte → `geraet_1..3`).

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
  aus diesem Branch, Version `2.1.0-cc.14`. Das ursprüngliche scyto-Add-on
  (`d4261985`) wurde am 06.11.2026 deinstalliert; sein Repository ist noch
  eingetragen, falls ein Rückweg nötig ist.
- **App Settings:** Adapter = Realtek-MAC, Auto-Reconnect an,
  *Prefer 44.1 kHz Bluetooth audio* an. Die Lautstärke-Sperre setzt HA
  (Abschnitt 5).
- **Pro Box:** *When Idle* = Standard, Lautstärke-Sperre an, AVRCP aus,
  MPD-Port wie oben.

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
| **Radiostream permanent** | HA-Start, alle 5 Min, Senderwechsel, Aktiv-Schalter an, Rückkehr eines Players (20 s stabil) | Spielt den gewählten Sender. Watchdog startet neu, wenn ein aktiver Player nicht spielt, seine Position steht oder ein falscher Sender läuft. Senderwechsel, Aktivierung und Rückkehr betreffen nur die eine Box. Zwischen Starts verschiedener Boxen 3 s Abstand (Mixing-Schutz). Modus `queued`. |
| **Radiostream stoppen** | Aktiv-Schalter aus | `media_stop` am Player. |
| **Bug-Watch** (Player unavailable) | Player 5/10/20/30 Min `unavailable` | Eskalationskette, siehe unten. Nur für aktive Boxen mit Strom. |
| **Wieder verfügbar** | Player kommt aus `unavailable` zurück (20 s) | Entwarnung mit Ausfalldauer, ersetzt die Ausfallmeldung (gleicher Tag). |
| **Nach HA-Start prüfen** | 3 Min nach HA-Start | Box seit dem Start weg: Diagnose, bei getrennter Bluetooth-Verbindung einmal Steckdosen-Zyklus. Holt verpasste Entwarnungen nach. |
| **Lautstärke-Sperre an Add-on übertragen** | Schalter `lautstarke_fest_100`, HA-Start | Setzt `volume_lock` für alle Boxen per REST. |
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

### Skripte

| Skript | Aufgabe |
|--------|---------|
| `radiostream_reparieren_ultralight` („Diagnose") | Stufe 1, auch per Button. |
| `radiostream_reparieren_light` („BT-Reconnect") | Force-Reconnect einer Box über das Add-on. |
| `radiostream_steckdose_zyklieren` | Steckdose einer Box 30 s aus und wieder an. |
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
