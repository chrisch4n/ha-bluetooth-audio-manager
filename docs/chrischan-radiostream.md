# Radiostream-Setup mit diesem Fork (Stand 14.11.2026)

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

| Box | Frequenz | MPD-Port | Steckdose | Bluetooth-Stick (seit 18.11.2026) |
|-----|----------|----------|-----------|-----------------------------------|
| ES-BT17 | 87.5 MHz | 6600 | `switch.dose_bt_87_5` | Logilink neu |
| ES-BT17 | 105.9 MHz | 6601 | `switch.dose_bt_105_9` | Logilink alt (Hauptadapter) |
| ES-BT17 | 97.0 MHz | 6602 | `switch.dose_bt_97_0` | Logilink alt (Hauptadapter) |

- **Host:** Home Assistant OS auf einem Fujitsu Futro S740, PulseAudio 17 im
  Audio-Plugin (`hassio_audio`).
- **Boxen:** ES-BT17 empfangen Bluetooth (A2DP, SBC) und senden auf UKW. Sie
  haben keine Pairing-Taste – gepairt bzw. neu verbunden wird per Stromzyklus
  über ihre Zigbee-Steckdose.
- **Bluetooth-Adapter:**
  - Zwei Realtek-RTL8761B-USB-Sticks (Logilink), ausschließlich für dieses
    Add-on: „Logilink alt" (USB 2.0, mit Verlängerungskabel) ist der
    Hauptadapter, in den App Settings per MAC fest eingestellt; „Logilink
    neu" (seit 18.11.2026) trägt 87.5 über die Box-Einstellung *Bluetooth
    adapter* (Abschnitt 6). Beide sind in der HA-Bluetooth-Integration
    ignoriert (Doppelzugriff HA + Add-on führte früher zu Kernel-Abstürzen).
    Am 24.11.2026 umgesteckt, „Logilink neu" per Verlängerung näher an 87.5:
    Signal 87.5 von etwa −22 auf −2 bis −4 dB, 105.9 von −17 auf −5 bis −9,
    97.0 von −3 auf −8 bis −10 (`sensor.radiostream_<p>_signal`).
  - Intel AX210 (intern) – gehört HA, passives Scannen.
- **Streams:** RADIO BOB! über die MPD-Instanzen des Add-ons. In HA gibt es pro
  Box zwei Player: `media_player.musik_radiostream_<p>` (MPD-Integration, wird
  von Automationen/Skripten gesteuert) und `media_player.radiostream_<p>_sender`
  (Universal-Media-Player-Wrapper aus YAML, fürs Dashboard).

## 2. Add-on

- Installiert als lokal gebautes Add-on `1b3a7c56_bluetooth_audio_manager`
  aus diesem Branch, Version `2.1.0-cc.23`. Das ursprüngliche scyto-Add-on
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
| cc.18 | 13.11. | Stick zurücksetzen per API (`POST /api/adapter/reset`): *soft* schaltet den Adapter über BlueZ aus und wieder ein und verbindet die Boxen danach einzeln im Abstand von 20 s; *usb* setzt den USB-Stick zurück wie Abziehen und Einstecken (Firmware wird neu geladen), danach startet das Add-on neu. Dafür USB-Zugriff (`usb: true`) |
| cc.19 | 13.11. | Boxen verbinden sich auch beim Start des Add-ons einzeln im Abstand von 20 s (nur die, die nicht schon verbunden sind); ein MPD-Stream, den PulseAudio auf eine andere Box geschoben hatte, wird nach dem Zurückschieben neu geöffnet – am 13.11. blieb 97.0 danach stumm, obwohl HA *spielt* zeigte |
| cc.20 | 14.11. | Diagnose: `GET /api/diagnostics/pulse-bluetooth` zeigt pro Box, wie weit PulseAudio die SBC-Bitrate abgesenkt hat (SBC-Frames pro Bluetooth-Paket, aus der festen Latenz des Sinks: 7 = volle Qualität, 15 = Bitpool ≤ ~22) |
| cc.21 | 14.11. | Mehrere Bluetooth-Adapter in einer Instanz: Einstellung *Bluetooth adapter* pro Box, Koppeln auf einem bestimmten Adapter (`POST /api/pair` mit `adapter`, sperrt die Box währenddessen am alten Adapter und löscht dort danach die Kopplung), Scan und Stick-Reset pro Adapter, Überwachung jedes Adapters |
| cc.22 | 15.11. | Eigene Namen für Bluetooth-Adapter (Stift-Knopf in *Bluetooth Adapters*, `PUT /api/adapters/<MAC>/name`), angezeigt in der Adapterliste, den Box-Einstellungen und auf den Gerätekarten |
| cc.23 | 15.11. | Adapter-Namen werden in einem eigenen Dialog der App vergeben statt im Eingabefenster des Browsers |
| cc.24 | 18.11. | Hauptadapter-Wechsel abgesichert: Knopf heißt *Make main*, der Dialog nennt die Boxen, die entkoppelt werden, und verlangt eine Bestätigung; die API verlangt `confirm_unpair` (Anzahl der Boxen) |
| cc.25 | 18.11. | 48-kHz-Box wird komplett neu verbunden statt nur den Stream neu zu öffnen; eine nicht antwortende Box wird höchstens alle 120 s gesucht, solange am selben Stick gestreamt wird (`POST /api/connect` → 409 mit `retry_in`); laufender Sender wird nach Add-on-Neustart oder Box-Abbruch vom Add-on selbst fortgesetzt (bis 30 Min); `GET /api/diagnostics/link-quality` (im Add-on nicht nutzbar, s. Abschnitt 7) |
| cc.26 | 18.11. | Signalstärke-Abfrage hört auf, wenn Bluetooth-Sockets im Add-on nicht verfügbar sind; Doku |
| cc.27 | 18.11. | Fußzeile der Oberfläche nennt alle Sticks, die das Add-on nutzt (Hauptadapter zuerst); `/api/info` liefert dafür `adapter_labels` |
| cc.28 | 18.11. | Fortsetzen nach Neustart robuster: Der laufende Sender wird alle 30 s notiert; ist ein MPD beim Beenden schon weg (das Stopp-Signal des Containers erreicht MPD und Add-on gleichzeitig), bleibt die Notiz erhalten. Beim cc.27-Neustart hatte das gefehlt, die Sender startete erst „Radiostream permanent“ |
| cc.29 | 18.11. | Kleine Korrekturen aus der Durchsicht: Klappt das Neuverbinden einer 48-kHz-Box nicht sofort, wird der Sender notiert und beim Wiederverbinden fortgesetzt (vorher wartete er auf HA); ein Fehler beim Fortsetzen erscheint als solcher im Log statt als „MPD start failed“. |
| cc.30 | 21.11. | Hängt eine spielende Box 5 Minuten (Einstellung *Reconnect after minutes at the lowest bitrate*, 0 = aus) auf der untersten SBC-Bitrate, verbindet das Add-on sie neu; der Sender läuft danach weiter. Höchstens einmal je Box in 30 Minuten. Anlass: 87.5 hing am 21.11. mit zwei Stockungen pro Sekunde auf der untersten Stufe, ein Neuverbinden machte sie sofort sauber. |
| cc.31 | 23.11. | Nach einem Verbindungsabbruch setzt das Add-on den Sender selbst fort, sobald die Box zurück ist (MPD pausiert sich beim Abriss; bisher löschte das die Sender-Notiz, und erst HA startete den Sender 24 s später). Jeder MPD-Stream wird an die Senke seiner Box gebunden (bevorzugte Senke über module-stream-restore): vorher folgte der Stream auf der Standard-Senke jedem Wechsel der Standardausgabe – bei jedem Neuverbinden von 87.5 sprang der 97.0-Stream kurz hinüber (ca. 3 s Stille auf 97.0). Das Log nennt den BlueZ-Abbruchgrund (`Timeout` = Funk weg, `Remote` = Box hat getrennt); `pulse-bluetooth` zeigt `default_sink` und `mpd_streams`. |
| cc.32 | 24.11. | Ein Fehler beim Neuverbinden beendet die Wiederholungen nicht mehr (bisher: `InterfaceNotFoundError`, wenn der Stick der Box noch nicht zurück war → 87.5 blieb am 24.11. nach dem Umstecken 5½ Min still, bis HA den Stick zurücksetzte). Taucht ein zusätzlicher Stick wieder auf, starten die Verbindungsversuche seiner Boxen sofort neu. |

### Basis und übernommene Arbeit aus anderen Forks

| Quelle | Was | Wie übernommen |
|--------|-----|----------------|
| [scyto/ha-bluetooth-audio-manager](https://github.com/scyto/ha-bluetooth-audio-manager), Branch `dev` | Original-Add-on, Stand 2.1.0 plus UI-Escaping-Fix | Basis dieses Branches |
| [slawa19/ha-bluetooth-audio-manager](https://github.com/slawa19/ha-bluetooth-audio-manager), Branch `fix/normalize-mpd-stream-volume`, Commit [`0a5e806`](https://github.com/slawa19/ha-bluetooth-audio-manager/commit/0a5e806cc7f978c91a354e10d01c70ced5d9e9c7) (Slawa Gorobets, 18.07.2026) | „fix: normalize MPD PulseAudio stream volume" – jeder neue MPD-Stream wird in PulseAudio auf 100 % gesetzt (ergänzt scyto#285) | Unverändert per Cherry-Pick als `5e73193`, Autor bleibt Slawa Gorobets; seit cc.1 |
| [Cayouche1989/ha-bluetooth-audio-manager](https://github.com/Cayouche1989/ha-bluetooth-audio-manager), Branch `cayouche/reconnect-2.1.1`, Commit [`2c38ea0`](https://github.com/Cayouche1989/ha-bluetooth-audio-manager/commit/2c38ea08619c045e380ab11fddc51a52a329e82e) (23.08.2026) | „Fix auto-reconnect after speaker availability" | Nur der Teil für fehlgeschlagene explizite Verbindungen, neu umgesetzt in `fc313d0` (Hinweis im Commit); der Discovery-gesteuerte Teil nicht. Zusammen mit `84ad826` deckt das beide Vorschläge aus scyto#317 ab; seit cc.1 |

Alles Übrige im Branch ist eigene Arbeit (Fixes für scyto#315–#319 und die
Erweiterungen cc.2–cc.23).

Bei scyto eingereicht (09.11.2026), nur `src/` und `tests/`: #324 mit den Fixes für
#315–#319 und #325 mit den Erweiterungen (Lautstärke-Sperre, Anzeigenamen, 44,1 kHz,
Live-Radio, Diagnose; baut auf #324 auf). GitHub schloss beide am 18.11.2026, als das
Umschreiben der Fork-Historie (echte MAC-Adressen entfernt) die Branches kurz von `dev`
trennte; sie ließen sich nicht wieder öffnen. Gleicher Inhalt neu eingereicht als
[#327](https://github.com/scyto/ha-bluetooth-audio-manager/pull/327) (Fixes) und [#328](https://github.com/scyto/ha-bluetooth-audio-manager/pull/328) (Erweiterungen, baut auf #327 auf).
Am 18.11.2026 folgte [#326](https://github.com/scyto/ha-bluetooth-audio-manager/pull/326)
(baut auf #328 auf) mit cc.17–cc.28: Härtung, Stick-Reset, mehrere Adapter, Adapter-Namen,
geschütztes „Make main", 48-kHz-Neuverbindung, Paging-Drossel, Fortsetzen nach Neustart,
SBC-Diagnose – samt DOCS.md, `usb: true` und AppArmor-Regeln für beide App-Ordner; die
Signalmessung fehlt dort (im Add-on nicht nutzbar).

## 3. PulseAudio: Aussetzer-Fix (custom.pa)

> **Stand 18.11.2026: `custom.pa` ist entfernt**, PulseAudio läuft wieder mit
> der Standard-Erholung (500 ms). Grund: Mit zwei Sticks (Abschnitt 6) trägt
> kein Stick mehr drei Streams, und die lange Erholung hatte die Bitrate nach
> jeder Überlast stundenlang unten gehalten (UKW-Rauschen, siehe unten).
> Aktiv war bis zuletzt der 60-Minuten-Wert (`3600000`); der am 14.11.
> beschlossene 30-Minuten-Wert wurde nie eingespielt.
> Messung danach (Gap-Monitor, je 10 Min): 14:49–14:59 105.9 und 97.0 auf
> „Logilink alt" **0** Stockungen, 87.5 allein auf „Logilink neu" 179
> Stockungen (60–200 ms, etwa alle 3 s = 5 Stufen runter, 2,5 s wieder hoch),
> alle in den ersten 8 Minuten nach dem Verbinden; 15:02–15:10 alle drei
> **0**. Der Rest dieses Abschnitts beschreibt die Lage mit einem Stick.
> Bei Bedarf wieder anlegen wie unten beschrieben, dann mit kurzem Wert
> (z. B. `60000`).

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

**Fix:** Bitraten-Erholung seltener – zuerst einmal pro Stunde, seit dem 14.11.2026 alle 30 Minuten (siehe unten). Die Datei `/data/custom.pa`
im Audio-Plugin wird bei jedem PulseAudio-Start geladen:

```
unload-module module-bluetooth-discover
load-module module-bluetooth-discover output_rate_refresh_interval_ms=1800000
```

- **Anlegen:** In der App *Advanced SSH & Web Terminal* kurz den Schutzmodus
  ausschalten, dann
  `docker exec hassio_audio sh -c 'printf "%s\n" "unload-module module-bluetooth-discover" "load-module module-bluetooth-discover output_rate_refresh_interval_ms=1800000" > /data/custom.pa'`,
  Schutzmodus wieder an, `ha audio restart`, danach das Add-on neu starten.
- **Prüfen:** `GET /api/diagnostics/pulse-bluetooth` muss
  `output_rate_refresh_interval_ms: 1800000` zeigen (bis 14.11.2026: 3600000).
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

**Nebenwirkung, erkannt am 14.11.2026: Rauschen auf UKW.** Jede Überlast
senkt den Bitpool um 5, die Erholung holt nur 1 Stufe pro Intervall auf –
mit 60 Minuten wirkt eine einzige Absenkung 5 Stunden nach. Die ES-BT17
erlauben Bitpool 2 bis 53; nach einigen Überlasten (gehäuft in den ersten
Minuten nach jedem Neuverbinden) war die Bitrate so weit unten, dass alle drei
Sender auf UKW stark rauschten – Bluetooth lieferte dabei lückenlos. Beweis:
97.0 nur per Bluetooth neu verbunden (Box blieb an) klang sofort sauber.
Messung danach (cc.20, `GET /api/diagnostics/pulse-bluetooth`): in der ersten
Stunde 6 Überlasten, alle in den ersten 15 Minuten, 5 davon auf 87.5 –
87.5 fiel von Bitpool 53 auf ≈ 33, 105.9 auf ≈ 48, 97.0 blieb voll.
Entscheidung vom 14.11.2026 deshalb: **Erholung alle 30 Minuten** (`1800000`): eine
Absenkung ist nach ~2,5 Stunden aufgeholt; dafür ab und zu ein sehr kurzer
Aussetzer, wenn eine Box wieder an ihre Grenze kommt.

Die Diagnose zeigt pro Box `sbc_frames_per_packet` (aus der festen Latenz des
Sinks, 25 ms + ein Bluetooth-Paket): 7 = volle Qualität (Bitpool 53),
8 ≈ 48, 9 ≈ 38–43, 11 ≈ 33, 12 ≈ 28, 14 ≈ 23, 15 = Bitpool 22 oder weniger.

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
  `..._aktiv_map`, `..._stick_map`, `..._stick_mac_map` –
  JSON-Maps pro Box bzw. Stick, einzige Quelle für MACs, Ports, Steckdosen
  und die Stick-Zuordnung. Die Config-Entry-ID der MPD-Integration holen die
  Skripte seit 25.11.2026 per `config_entry_id('media_player.musik_radiostream_<p>')`;
  die frühere `..._mpd_entry_map` hatte noch die IDs von vor der Neuanlage der
  MPD-Integrationen Ende Oktober (Neuladen brach mit UnknownEntry ab) und ist gelöscht. (Bis 21.11.2026 gab es zusätzlich
  `..._schalter_map` mit drei Template-Schaltern `switch.<p>_schalter` und den
  Auswahlhelfern `input_select.radiostream_<p>_steckdose` – ein Umweg zur selben
  Steckdose, entfernt; `radiostream_power_toggle` nutzt `dose_switch_map`.)
- `input_boolean.radiostream_<p>_aktiv` – soll die Box spielen.
- `input_boolean.radiostream_ausfall_gemeldet_<p>` – für diese Box wurde ein
  Ausfall gemeldet (nur dann gibt es eine Entwarnung).
- `input_boolean.radiostream_lautstarke_fest_100` – Lautstärke-Sperre aller Boxen.
- `input_number.radiostream_lautstarke_alle_boxen` – Wert, auf dem die Sperre die
  Boxen hält (10–100 %, Standard 100).
- `input_boolean.radiostream_power_schaltet_steckdosen` – ob „Aus" auch die
  Steckdose schaltet.
- `select.radiosender_<p>`, `select.radiostream_preset_1..10` – Template-Selects
  im Paket `radiostream.yaml` (seit 18.11.2026, vorher `input_select`-Helfer):
  Optionen immer aus der Senderliste, Wert in `input_text.letzter_sender_<p>` /
  `letzter_preset_<n>`. Die alten `input_select`-Helfer sind seit 21.11.2026 gelöscht.
- `input_number.radiostream_<p>_letzte_position` – Stall-Erkennung des Watchdogs.
- `input_text.radiostream_letzter_start` – Mixing-Schutz (zuletzt gestarteter
  Player + Zeit).
- `input_datetime.radiostream_letzte_automatische_voll_reparatur` – Sperrzeit
  der Voll-Reparatur.

### Automationen

Die `description` jeder Automation und jedes Skripts nennt seit 21.11.2026 nur noch den
Zweck; die frühere Änderungsgeschichte steht in [`chrischan-ha/historie.md`](chrischan-ha/historie.md).
Boxenlisten in Vorlagen kommen aus `input_text.radiostream_address_map` (bzw.
`dose_switch_map`), nur Auslöser und Entitäten je Box sind fest eingetragen.
*Radiostream permanent* und die Bitrate-Absicherung behalten 30 statt 5 Traces, weil ihre
regelmäßigen Prüfungen sonst echte Läufe verdrängen.

| Automation | Auslöser | Aufgabe |
|------------|----------|---------|
| **Radiostream permanent** | HA-Start, alle 5 Min, Senderwechsel, Aktiv-Schalter an, Rückkehr eines Players (20 s stabil), Player hört von selbst auf zu spielen (20 s) | Spielt den gewählten Sender. Watchdog startet neu, wenn ein aktiver Player nicht spielt, seine Position steht oder ein falscher Sender läuft. Senderwechsel, Aktivierung, Rückkehr und Stopp betreffen nur die eine Box; Rückkehr und Stopp nur, wenn sie aktiv ist. Zwischen Starts verschiedener Boxen 3 s Abstand (Mixing-Schutz). Modus `queued`. |
| **Radiostream stoppen** | Aktiv-Schalter aus | `media_stop` am Player. |
| **Bug-Watch** (Player unavailable) | Player 3/5/20/30 Min `unavailable` **oder** 15/20/30/40 Min erreichbar, aber stumm (`binary_sensor.radiostream_<p>_spielt_nicht`) | Eskalationskette, siehe unten. Nur für aktive Boxen mit Strom. |
| **Wieder verfügbar** | Player kommt aus `unavailable` zurück (20 s) oder „spielt nicht" geht aus (Player spielt 90 s durchgehend) | Entwarnung mit Ausfalldauer, ersetzt die Ausfallmeldung (gleicher Tag). Nur wenn vorher eine Meldung verschickt wurde. |
| **Nach HA-Start prüfen** | 3 Min nach HA-Start | Box seit dem Start weg: Diagnose, bei getrennter Bluetooth-Verbindung einmal Steckdosen-Zyklus. Holt verpasste Entwarnungen nach. |
| **Lautstärke-Sperre an Add-on übertragen** | Schalter `lautstarke_fest_100`, Wert `lautstarke_alle_boxen`, HA-Start | Gibt den Sperr-Wert (10–100 %) als `volume_lock_level` ans Add-on und setzt `volume_lock` für alle Boxen per REST (bei reiner Wert-Änderung nur den Wert). |
| **Bitrate unten: BT-Reconnect** (seit 21.11.2026, Absicherung) | `binary_sensor.radiostream_<p>_bitrate_unten` seit 40 Min an; zusätzlich alle 15 Min eine Prüfung, falls der Sensor schon ohne Wechsel an war | Normalerweise verbindet das Add-on (ab cc.30) eine Box nach 5 Min auf der untersten Bitrate selbst neu. Hängt sie trotzdem 40 Min unten: `rest_command.bt_audio_force_reconnect` nur für diese Box, 30 s später `radiostream_mpd_sicherstellen`, Push nur an das eigene Handy (Tag `radiostream_bitrate`). Nicht während Voll-Reparatur, Stick-Reset oder Zyklus aller Boxen; höchstens einmal in 30 Min; 30 Traces. |
| **Stick-Reset je Stick** (Entity `automation.radiostream_stick_reset_bei_mehrfachausfall`) | `sensor.radiostream_sticks_ohne_verbindung` nennt seit 4 Min einen oder mehrere Sticks (alle aktiven Boxen mit Strom an diesem Stick: Player `unavailable`) | Startet `radiostream_stick_zuruecksetzen` mit Stufe *auto* nur für den genannten Stick (bei mehreren für alle). Nicht während Voll-Reparatur, Zyklus aller Boxen oder eines laufenden Stick-Resets; höchstens einmal in 30 Min (ab 13.11.2026, je Stick seit 18.11.2026; vorher: zwei Boxen ohne Verbindung). |

Am 21.11.2026 gelöscht: *Sender-Auswahl persistieren* und *Senderlisten
synchronisieren* (seit 18.11. aus; die Template-Selects schreiben ihre Auswahl selbst
in `letzter_sender_*` / `letzter_preset_*` und holen die Optionen direkt aus der
Senderliste – `input_select.set_options` wurde nie gespeichert, deshalb veralteten die
alten Listen) sowie der *nächtliche Steckdosen-Zyklus* (13.–14.11.2026, aus: Das
Rauschen kam von der abgesenkten Bitrate, nicht von den Boxen).

### Eskalationskette (Bug-Watch)

| Stufe | Nach | Aktion |
|-------|------|--------|
| 1 diagnose | 3 Min | `script.radiostream_reparieren_ultralight`: prüft per API, ob Bluetooth gesund ist; lädt ggf. nur die MPD-Integration neu oder macht einen Force-Reconnect. Push nur ans eigene Handy (seit 23.11.2026), ab Stufe 2 an alle Geräte. |
| 2 steckdosen_zyklus | 5 Min | Nur die betroffene Steckdose 30 s aus, danach 60 s warten und Nachdiagnose. Stört die anderen Boxen nicht. |
| 3 addon_neustart | 20 Min | `script.radiostream_reparieren`: Steckdose aus, Add-on-Neustart, Steckdose an, MPD sicherstellen. Betrifft kurz alle Boxen, höchstens alle 30 Min. |
| 4 manuell_pruefen | 30 Min | Nur Meldung „bitte manuell prüfen". |

**Stick zuerst (seit 13.11.2026, je Stick seit 18.11.2026).** Fehlen alle
Boxen eines Sticks seit 4 Minuten, liegt es eher am Realtek-Stick als an den
Boxen: Dann setzt „Stick-Reset je Stick" diesen Stick zurück (erst sanft, bei
Bedarf per USB, siehe Skripte). Am Stick „Logilink neu" hängt nur 87.5, dort
reicht also eine Box; am „Logilink alt" müssen 105.9 und 97.0 beide fehlen. Stufe 2 wartet, solange der Stick-Reset läuft, und entfällt für
Boxen, die danach wieder da sind.

Diagnose nach 3 und Steckdosen-Zyklus nach 5 Minuten (bis 11.11.2026: 5 und
10): Die Selbstheilung des Add-ons (Auto-Reconnect nach 10 s, 32 s, 63 s,
130 s; #316-Self-Heal) greift zuerst. Nimmt eine ES-BT17 danach keine
Verbindung mehr an – so nach dem Absturz des Realtek-Sticks am 11.11. –, hilft
nur der Stromzyklus, und der kommt jetzt nach 5 statt 10 Minuten. Alle Meldungen einer Box
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
| `radiostream_steckdosen_alle_zyklieren` | Alle eingeschalteten Boxen nacheinander zurücksetzen: jede 30 s stromlos, dann wieder an, 90 s später die nächste (dauert etwa 6 Minuten, nie mehr als ein Sender still); ohne Add-on-Neustart. Button in Stufe 2 (lief vom 13. bis 14.11.2026 auch jede Nacht um 04:30). Bis 13.11.2026 gingen alle gleichzeitig aus und mit 20 s Abstand wieder an – dabei kamen die Boxen fast gleichzeitig zurück, und der Realtek-Stick geriet zweimal durcheinander. Daneben gibt es den Gruppenschalter `switch.radiostream_steckdosen_alle` für alle drei Steckdosen. |
| `radiostream_stick_zuruecksetzen` | Bluetooth-Stick zurücksetzen, ohne ihn abzuziehen (`rest_command.bt_audio_adapter_reset`, Add-on ab cc.18). Feld *sticks*: `alle` (Standard, Button) oder Stick-Namen aus `input_text.radiostream_stick_mac_map`, kommagetrennt – bei genau einem Namen nur dieser Stick (seit 18.11.2026). Stufe *auto*: erst sanft (Adapter über BlueZ aus/an, Boxen verbinden sich einzeln), ist ein Ziel-Stick nach gut 2 Minuten weiter ganz ohne Verbindung, folgt der USB-Reset (wie Abziehen und Einstecken: Firmware wird neu geladen; beim Hauptadapter startet das Add-on neu). *sanft* / *usb* nur die jeweilige Stufe. Ergebnis als Push (Tag `radiostream_stick`). Button „Stick zurücksetzen" in der Ansicht *Reparatur*; läuft automatisch je Stick. Live getestet am 13.11.2026: sanft ~1 Min Pause, USB ~40 s (die Boxen verbanden sich danach von selbst). |
| `radiostream_reparieren` („Voll-Reparatur") | Steckdose(n) aus, Add-on-Neustart, Steckdose(n) an, MPD-Integrationen neu laden, MPD sicherstellen. |
| `radiostream_mpd_sicherstellen` | Startet einen fehlenden MPD-Dienst einer verbundenen Box. |
| `radiostream_notfall_forget_pair` | Box entfernen, neu pairen, MPD zuweisen. Feld `player` (87_5/97_0/105_9) statt `address`/`mpd_port` – MAC und Port kommen dann aus den zentralen Maps (seit 19.11.2026). Koppelt am Stick der Box (`input_text.radiostream_stick_map` → `radiostream_stick_mac_map`, `rest_command.bt_audio_pair_device` mit `adapter`, Timeout 60 s); vorher landete eine vergessene Box immer am Hauptadapter. |
| `radiostream_power_toggle` | An/Aus pro Box (Steckdose und Aktiv-Schalter); Steckdose aus `dose_switch_map` (seit 21.11.2026 direkt). |
| `radiostream_aussetzer_diagnose` (seit 21.11.2026) | Gap-Monitor des Add-ons für einige Minuten (Feld `minuten`, Standard 10), Ergebnis als Push nur an das eigene Handy (Tag `radiostream_diagnose`): je Box Stockungen am Bluetooth-Ausgang und Stille im Stream, dazu wie oft mehrere Boxen gleichzeitig stockten (Stick/USB). Button in *Reparatur → Status*. |
| `radiostream_preset_abspielen` | Preset auf eine Box legen. |

Konvention: Ein Skript ruft ein anderes immer mit `script.turn_on` +
`target.entity_id` + `data.variables` auf, nie über die Kurzform
`script.<name>`.

### REST-Befehle

`rest_command.bt_audio_*` (z. B. `get_devices`, `get_state`, `scan`,
`set_volume_lock`) stehen seit 18.11.2026 im Paket
`configuration_yaml/packages/radiostream.yaml` (zusammen mit den Universal-Playern,
dem Signal-Sensor und der Senderliste; Export in `chrischan-ha/packages/`) und
sprechen die REST-API des Add-ons an. `bt_audio_scan` wird derzeit von nichts aufgerufen, bleibt aber für den
Bedarfsfall stehen.
`bt_audio_adapter_reset` (seit 13.11.2026) setzt Bluetooth-Sticks zurück
(`mode` *soft* oder *usb*, optional `adapter` = MAC eines Sticks, sonst alle;
siehe `radiostream_stick_zuruecksetzen`). `bt_audio_put_settings` nimmt
`payload` als Text oder Objekt (Objekte gehen per `to_json` raus).
`bt_audio_set_adapter` (Hauptadapter wechseln) nimmt seit 21.11.2026 optional
`confirm_unpair` – das Add-on verlangt es seit cc.24 bei `clean: true`; den Wert
(Anzahl der Boxen) liefert `bt_audio_set_adapter_impact`. Neu am 21.11.2026:
`bt_audio_pulse_bluetooth` (Bitrate je Box, für den Bitrate-Wächter) und
`bt_audio_gap_monitor_start` / `_status` (Aussetzer-Diagnose).

### Bitrate-Wächter

`binary_sensor.radiostream_<p>_bitrate_unten` (Paket `radiostream.yaml`, seit
21.11.2026): Trigger-Template, das alle 5 Minuten `GET /api/diagnostics/pulse-bluetooth`
abfragt. *An* heißt: Die Box hängt auf der untersten SBC-Stufe (15 Frames pro Paket
statt 5–7) – der UKW-Sender rauscht. Attribut `sbc_frames_per_packet`. Am 21.11.2026
mit dem Gap-Monitor geprüft: fünf Abfragen in drei Minuten, auf den gesunden Boxen
keine einzige Stockung. Die Automation *Bitrate unten: BT-Reconnect* verbindet eine
betroffene Box nach 40 Minuten neu – als Absicherung, denn ab cc.30 verbindet das Add-on
selbst eine spielende Box neu, die 5 Minuten auf der untersten Stufe hängt (Einstellung
*Reconnect after minutes at the lowest bitrate*). Kacheln „Bitrate“ in *Reparatur → Status*.

Die Signalstärke (`sensor.radiostream_bt_signal`) bleibt beim Skript in HA Core (seit
21.11.2026 meldet es eine verbundene, aber nicht lesbare Box als „Lesefehler: …“ statt als
nicht verbunden; die Statustabelle zeigt das an):
`GET /api/diagnostics/link-quality` des Add-ons scheitert hier mit „Address family not
supported“, das Add-on läuft ohne Host-Netzwerk.

### Dashboard `radio-streams`

Ansichten *Receiver* (Bedienung im Stil eines RS-970-Receivers; Seite MEMORY: Preset-Belegung,
ON AIR je Speicherplatz, die drei Boxen mit Senderwahl) und *Reparatur* (Diagnose, BT-Reconnect,
Steckdosen-Zyklus, Bluetooth-Stick zurücksetzen und „Boxen ohne Verbindung",
Voll- und Notfall-Reparatur, Tabelle Frequenz/MAC/Port). Die Ansichten *Radiostreams*,
*Presets* und *Radio* wurden am 19.11.2026 entfernt.

*Reparatur* am 19.11.2026 neu aufgebaut (erst als Kopie, dann ersetzt; Pfad unverändert
`/radio-streams/reparatur`): vier Abschnitte Status · Reparatur in Stufen ·
Bluetooth-Sticks · Steckdosen & Einstellungen.
Die Knöpfe sind Kacheln des jeweiligen Skripts – ein farbiges Symbol heißt „läuft gerade“.
Stick-Reset je Stick (*Logilink alt*, *Logilink neu*, *Beide*) mit Schalter für den
automatischen Reset, „Sticks ohne Verbindung“ im Status, Notfall-Koppeln über das Feld
`player` statt Templates, Bestätigungstexte auf dem aktuellen Stand (kein Hinweis auf den
abgeschalteten Nachtzyklus, keine Kopplungstaste an der ES-BT17).

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

## 6. Zweiter Bluetooth-Stick (bestellt 14.11., in Betrieb seit 18.11.2026)

Drei Streams auf einem Realtek-Stick überlasten ihn ab und zu, und jede
Überlast senkt die SBC-Bitrate für lange Zeit (Abschnitt 3). Mit zwei Streams
pro Stick gab es im Test keine Überlast. Deshalb kommt ein zweiter, gleicher
Stick (RTL8761B) dazu, und **87.5** zieht um – 87.5 hatte am 14.11. fünf der
sechs Überlasten.

Seit cc.21 kann eine Add-on-Instanz mehrere Adapter: Jede Box hat die
Einstellung *Bluetooth adapter* (leer = Hauptadapter, also der bisherige
Realtek). Keine zweite Instanz, keine Änderung an MPD-Ports, Skripten oder
REST-Befehlen nötig.

**Umzug von 87.5, wenn der Stick da ist**

1. Stick einstecken – nicht direkt neben den ersten Stick und nicht neben
   einen blauen USB-3-Anschluss (stört 2,4 GHz); am besten an ein kurzes
   Verlängerungskabel.
2. Home Assistant → Einstellungen → Geräte & Dienste → **Bluetooth**: Der neue
   Adapter wird als „entdeckt" angeboten → **Ignorieren**. Sonst nutzt HA ihn
   für BLE, und das Add-on lehnt ihn ab.
3. Add-on-Oberfläche → *Settings → Bluetooth Adapters*: Der neue Stick steht
   in der Liste (MAC notieren). **Nicht** auf *Make main* (bis cc.23:
   *Select*) drücken – das würde den Hauptadapter wechseln und alle
   Kopplungen samt Einstellungen löschen (passiert am 18.11.2026, siehe
   unten). Mit dem Stift-Knopf beiden Sticks Namen geben (hier „Logilink alt"
   und „Logilink neu").
4. Bei 87.5 *Settings* öffnen → *Bluetooth adapter* = neuer Stick → **Pair on
   this adapter**. Das Add-on sperrt 87.5 am Realtek (die Box wird getrennt und
   kann sich dort nicht neu verbinden) und sucht sie 40 s lang am neuen Stick.
   Falls sie nicht gefunden wird: Box in den Kopplungsmodus bringen (Taste
   bzw. wie beim Notfall-Neukoppeln) und erneut drücken. Schlägt es fehl, wird
   die Sperre am Realtek wieder aufgehoben; 87.5 verbindet sich dann wieder
   dort.
5. Nach dem Koppeln verbindet sich 87.5 über den neuen Stick, die Kopplung am
   Realtek wird gelöscht, MPD läuft weiter auf Port 6600. „Radiostream
   permanent" startet die Wiedergabe.
6. Prüfen: `GET /api/diagnostics/pulse-bluetooth` – alle drei sollten auf
   Dauer bei 7 SBC-Frames pro Paket bleiben (volle Bitrate).

Per API statt Oberfläche: `PUT /api/devices/<MAC_87_5>/settings
{"adapter": "<MAC neuer Stick>"}` und `POST /api/pair {"address": "<MAC_87_5>",
"adapter": "<MAC neuer Stick>"}`.

**Was danach anders ist**

- *Stick zurücksetzen*: Der Button setzt beide Sticks zurück, die Automatik
  nur den Stick, an dem alle Boxen fehlen (seit 18.11.2026).
- Fehlt ein Stick, startet das Add-on trotzdem (nur der Hauptadapter wird
  abgewartet); die Box am fehlenden Stick bleibt aus, bis er wieder da ist.
- Die 30-Minuten-Sperre der Automatik gilt für beide Sticks gemeinsam: Fällt
  kurz nach einem Reset der andere Stick aus, greift dort zuerst der Bug-Watch.
- Nicht den Intel AX210 dafür nehmen (gehört HA; trägt keine drei Streams).

**Umzug am 18.11.2026 (erledigt)**

- Der neue Stick meldete sich als `hci1`, der alte rutschte auf `hci2`. Das
  Add-on startete sich deswegen neu und blieb – Adapter per MAC gespeichert –
  richtig beim alten Stick.
- 14:20 wurde beim neuen Stick *Select* gedrückt: alle drei Boxen entkoppelt,
  ihre Einstellungen und Anzeigenamen gelöscht, Hauptadapter = neuer Stick.
  Wiederherstellung per API: Hauptadapter zurück auf den alten Stick
  (`POST /api/set-adapter`, ohne `clean`), Scan, 105.9 und 97.0 am alten
  Stick gekoppelt, 87.5 mit `adapter` am neuen; Einstellungen neu gesetzt
  (MPD 6600/6601/6602, `volume_lock`, AVRCP aus, Namen „87.5"/„105.9"/„97.0").
  Die Werte standen im Add-on-Log („custom settings" beim Start). Daraus
  entstand cc.24.
- Während die Boxen ohne Verbindung waren, löste „Stick-Reset bei
  Mehrfachausfall" erst einen Soft-, dann einen USB-Reset aus; harmlos.
- Danach lief **97.0 zu schnell** (≈ 1,09-fach = 48/44,1): Die Box hatte den
  Stream selbst mit 48 kHz aufgebaut, das Add-on ihn auf 44,1 kHz neu
  geöffnet, die Box spielte weiter mit 48 kHz. Ein Neuverbinden vom Add-on aus
  (`POST /api/force-reconnect`) behob es. Das Add-on erkennt diesen Zustand
  nicht – bei „zu schnell/zu hoch" die Box neu verbinden.
- Nach dem Neukoppeln zeigt die Diagnose 5 statt 7 SBC-Frames pro Paket
  (nicht auf der untersten Stufe, bei allen drei gleich). Vermutlich kleinere
  Bluetooth-Pakete nach dem Neukoppeln; die Zuordnung Frames → Bitpool oben
  gilt dann nicht. Noch nicht geklärt.
- Dashboard „Radiostreams" → Reparatur → Einstellungen & Status: Spalte
  „Stick" (fest eingetragen).
- 14:47 `custom.pa` entfernt (Abschnitt 3), 14:48 cc.24 eingespielt; alle
  drei Boxen verbanden vom Add-on aus direkt mit 44,1 kHz.
- 15:11 Steckdosen von 105.9 und 87.5 getauscht (Boxen umgesteckt). Danach
  Namen in Zigbee2MQTT getauscht (`bridge/request/device/rename`, ohne
  `homeassistant_rename`) und die Entity-IDs in HA über eine Zwischen-ID
  (`switch.dose_bt_tmp`, samt `_last_seen`/`_linkquality`): `switch.dose_bt_87_5`
  ist wieder die Dose der Box 87.5. Skripte, Automationen und
  `input_text.radiostream_dose_switch_map` brauchten keine Änderung; der
  Verlauf der beiden Entity-IDs mischt ab dem Tausch die zwei Dosen.
- 105.9 kam nach dem Umstecken nicht wieder (`br-connection-page-timeout`),
  erst nach dem Steckdosen-Zyklus (Stufe 2, von der Bug-Watch ausgelöst,
  15:16) um 15:18:52. **Währenddessen fiel 97.0 auf die unterste Bitrate**
  (15 Frames, `at_lowest_step: true`) und rauschte: Die wiederholten
  Verbindungsversuche zu 105.9 laufen über denselben Stick. Neuverbinden von
  97.0 um 15:19 stellte die volle Bitrate her. Ob 97.0 sich nach dem Ende der
  Verbindungsversuche mit 500 ms Erholung auch von selbst erholt hätte, ist
  offen. Eine automatische Rettung (Box neu verbinden, wenn sie auf der
  untersten Stufe hängen bleibt) ist zurückgestellt: Die Bitrate lässt sich
  nur über `pactl list sinks` ablesen, und ein regelmäßiger `pactl`-Aufruf
  hat früher selbst gestottert (cc.8).

## 7. Bekannte Grenzen (Stand 18.11.2026)

Beobachtet oder aus dem Aufbau abgeleitet; „möglich" heißt: denkbar, aber
nicht nachgewiesen.

**UKW-Boxen (ES-BT17)**

- **Klang verschlechtert sich, Stromreset hilft – Ursache war Bluetooth.**
  Am 07.11., 10.11., 11.11., 13.11. und 14.11.2026 klangen alle drei Sender
  verrauscht bzw. unsauber; ein Stromreset der Boxen half jedes Mal. Bis zum
  13.11. habe ich das dem UKW-Teil der Boxen zugeschrieben – falsch. Ursache
  ist der abgesenkte SBC-Bitpool (Abschnitt 3): Ein Stromreset half nur, weil
  die Box danach neu verbindet und mit voller Bitrate startet. Am 14.11.
  nachgewiesen (Neuverbinden nur per Bluetooth genügte). Seit 18.11. zwei
  Sticks und Standard-Erholung (500 ms) statt `custom.pa`; der nächtliche
  Zyklus ist abgeschaltet. Home Assistant sieht die Bitrate nicht;
  `GET /api/diagnostics/pulse-bluetooth` zeigt sie (cc.20).
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

- **Drei Streams auf einem Realtek-Stick nur mit custom.pa** (Abschnitt 3),
  mit der Nebenwirkung stundenlang niedriger Bitrate nach jeder Überlast.
  Seit 18.11.2026 deshalb zwei Sticks (2 + 1 Streams) ohne `custom.pa`. In den
  ersten Minuten nach dem Verbinden kann eine Box mit schwächerer Funkstrecke
  (bisher 87.5) kurz stocken, danach lief es sauber.
- **Ist eine Box nicht erreichbar, leidet die andere am selben Stick.** Jeder
  vergebliche Verbindungsversuch belegt den Stick ~5 s; am 18.11. fiel 97.0
  so auf die unterste Bitrate (UKW-Rauschen), während 105.9 fehlte. Seit
  cc.25 wird eine Box nach einem „page timeout" höchstens alle 120 s gesucht,
  solange eine andere Box am selben Stick streamt (gilt auch für
  `POST /api/connect` aus HA: Antwort 409 mit `retry_in`;
  `POST /api/force-reconnect` ist ausgenommen). Ist die Bitrate trotzdem
  unten: verrauschte Box neu verbinden (`POST /api/force-reconnect`).
- **Box lief zu schnell (≈ 1,09-fach)** – bis cc.24. Hatte eine Box den
  Stream selbst mit 48 kHz aufgebaut, öffnete das Add-on nur den Stream auf
  44,1 kHz neu, und die Box konnte bei 48 kHz bleiben (18.11.2026, 97.0). Seit
  cc.25 verbindet das Add-on die Box komplett neu; damit kam bisher jedes Mal
  sauber 44,1 kHz.
- **Der Realtek-Stick kann abstürzen.** Am 11.11.2026 um 18:20 meldete der
  Kernel `Bluetooth: hci1: RTL: hw err, trigger devcoredump (51)`: Die
  Firmware des Sticks setzte sich selbst zurück, alle drei Verbindungen fielen
  gleichzeitig weg. Schon gut zehn Minuten vorher stockte die Übertragung
  (erst nur 105.9 etwa einmal pro Sekunde, dann 87.5 und 97.0 im Gleichtakt
  alle halbe Sekunde), am Radio war es unsauber, fiepte und rauschte zuletzt
  nur noch. Vorausgegangen waren ein Internetausfall (17:09–17:46, viele
  Stream-Neustarts) und Verbindungsversuche zu einer nicht antwortenden Box.
  Die Ursache im Chip ist unbekannt (Realtek dokumentiert den Code nicht);
  Doppelzugriff durch HA, Prozessorlast und USB-Fehler waren es nicht. Nach
  dem Absturz liefen 97.0 und 105.9 sofort wieder sauber; 87.5 und vorher
  105.9 nahmen bis zu einem Steckdosen-Zyklus keine Verbindung mehr an. Die
  Messung dafür ist der Gap-Monitor des Add-ons
  (`POST /api/diagnostics/gap-monitor`).
  Am 13.11.2026 kippte der Stick erneut – diesmal direkt nach einem
  Steckdosen-Zyklus aller Boxen, als sich alle drei fast gleichzeitig neu
  verbanden: `link tx timeout, killing stalled connection`, Pakete für
  unbekannte Verbindungen, doppelte Verbindungsmeldungen. Erst Abziehen und
  Wiedereinstecken des Sticks (Firmware wird neu geladen, das Add-on startet
  sich danach selbst neu) half. Auch am 11.11. kam der Absturz beim
  gleichzeitigen Neuverbinden. Seitdem setzt der Zyklus die Boxen
  nacheinander mit 90 s Abstand zurück.
  **Seit dem 13.11.2026 lässt sich der Stick ohne Abziehen zurücksetzen**
  (Add-on cc.18, Skript `radiostream_stick_zuruecksetzen`, Button in der
  Ansicht *Reparatur*, automatisch bei zwei oder mehr Boxen ohne Verbindung
  nach 4 Minuten). Der USB-Reset lädt die Firmware nachweislich neu (Kernel:
  `loading rtl_bt/rtl8761bu_fw.bin`, wie beim Wiedereinstecken); nur die
  Stromversorgung bleibt, ein Fehler, den nur Stromlos-Sein behebt, bleibt also.
  Live-Test am 13.11.: Beim sanften Reset kamen 97.0 und 105.9 einzeln zurück,
  87.5 nahm keine Verbindung an („page timeout") und kam erst mit dem
  Steckdosen-Zyklus des Bug-Watch wieder – wie nach dem Absturz am 11.11. Beim
  USB-Reset verbanden sich alle drei Boxen von selbst innerhalb von Sekunden,
  also wieder gleichzeitig; das gestaffelte Neuverbinden des Add-ons greift nur
  für Boxen, die das nicht tun.
- **Stumme Box nach Umleitung durch PulseAudio.** Verbindet sich eine Box neu,
  schiebt PulseAudio laufende Streams der anderen Boxen kurz auf die neue Box;
  das Add-on schiebt sie sofort zurück. Am 13.11.2026 kam danach auf 97.0 nur
  noch digitale Stille an (Gap-Monitor: „silence before Bluetooth"), obwohl HA
  *spielt* zeigte – der Bug-Watch merkt das nicht. Stop/Play behob es. Seit
  cc.19 öffnet das Add-on einen zurückgeschobenen Stream 2 s später selbst neu
  (kurzer Aussetzer nur auf diesem Sender).
- **custom.pa nur beim Start von PulseAudio.** Das Bluetooth-Modul zur
  Laufzeit neu zu laden hat PulseAudio abstürzen lassen (cc.11).
- **Mehrere Adapter erst ab cc.21** (Abschnitt 6); vorher ein Adapter pro Add-on-Instanz.
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
  eines Scans, und der stört auf demselben Chip alle laufenden Streams. Die
  Abfrage einer bestehenden Verbindung ohne Scan (Kernel-Schnittstelle
  „Get Connection Information", cc.25) scheitert im Add-on: Bluetooth-Sockets
  gibt es nur im Netzwerk-Namespace des Hosts (`EAFNOSUPPORT`), und
  Host-Netzwerk würde die Adresse `1b3a7c56-bluetooth-audio-manager:8099`
  der REST-Befehle und MPD-Integrationen brechen. **Gelöst über HA Core**
  (läuft im Host-Netzwerk): Skript `/config/cli/bt_link_quality.py` und
  `command_line`-Sensor `sensor.radiostream_bt_signal` (alle 2 Min, Export in
  `chrischan-ha/`), Spalte „Signal" in *Reparatur → Einstellungen & Status*.
  `rssi` ist bei Bluetooth Classic kein dBm-Wert, sondern der Abstand zum
  Idealbereich des Sticks (0 = gut, negativ = schwächer); `tx`/`tx_max` melden
  die Realtek-Sticks nicht (0/0). Erste Werte 18.11.2026 16:01: 87.5 −24 dB
  (Logilink neu), 105.9 −18 dB, 97.0 −2 dB (beide Logilink alt) – 87.5 hat die
  schwächste Strecke, passend zu ihren Stockungen nach dem Verbinden.
  Bewertung in der Tabelle (Faustregel, kein Standard): gut bis −5 dB, mäßig
  bis −15, schwach bis −25, darunter kritisch. Bei einer Untergrenze des
  Idealbereichs von typisch −56 dBm entspricht −22 dB etwa −78 dBm, rund
  10 dB über der Empfindlichkeit; Schwankungen von 2–4 dB sind normal.
- **Keine PulseAudio-Logs.** Das Audio-Plugin von HAOS schreibt nicht ins
  Journal; Aussetzer lassen sich nur mit dem Gap-Monitor des Add-ons messen.

**Add-on**

- **Fortsetzen nach Neustart (seit cc.25).** MPD kann im Add-on-Container
  keine eigene Zustandsdatei schreiben (MPD 0.24 braucht dafür
  `CAP_DAC_READ_SEARCH`), jeder neue MPD startet mit leerer Warteschlange.
  Das Add-on merkt sich deshalb beim Beenden eines MPD (Add-on-Neustart oder
  -Update, Box-Abbruch) den laufenden Sender in `/data/playback_resume.json`
  und startet ihn wieder, sobald der MPD dieser Box läuft (höchstens 30 Min
  alt; nicht nach Stopp, Vergessen oder MPD aus). Seit cc.28 notiert das
  Add-on den laufenden Sender zusätzlich alle 30 s, weil ein MPD beim
  Container-Stopp schon beendet sein kann, bevor das Add-on nachsieht.
  Vorher übernahm das „Radiostream permanent" nach ~20–30 s; es bleibt als
  Rückfallebene.
- **Anzeigenamen:** Der MPD-Ausgabename übernimmt einen geänderten Namen erst
  beim nächsten Start von MPD. *Clear all devices* löscht die Namen.
- **Sperr-Wert:** Ein Wert für alle gesperrten Boxen, kein Wert pro Box. Er
  wirkt auf die MPD-Lautstärke (digital, vor Bluetooth); Stream und Box
  bleiben auf 100 %, die Lautstärketasten der Box werden zurückgesetzt.

**Home Assistant**

- **Stopp am MPD-Player wird rückgängig gemacht.** Ist der Aktiv-Schalter an,
  startet „Radiostream permanent" einen gestoppten Player nach 20 s neu.
  Absichtlich aus geht eine Box nur über den Aktiv-Schalter bzw. Power.
- **REST-Befehl `bt_audio_put_settings`:** seit 18.11.2026 robust – die
  Vorlage `{{ payload if payload is string else (payload | to_json) }}` macht
  aus einem Objekt JSON und reicht fertigen JSON-Text durch (beides
  getestet). Vorher hing es daran, dass HA beim Einsetzen den Originaltext
  ausgab.
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
