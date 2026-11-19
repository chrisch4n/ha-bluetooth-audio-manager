# Home-Assistant-Konfiguration „Radiostream" (Export, Stand 13.11.2026)

Anonymisierter Export der Home-Assistant-Teile, mit denen drei Internetradio-Streams
über dieses Add-on dauerhaft an drei Bluetooth-UKW-Sender (ES-BT17) gehen. Was das
System macht und warum es so gebaut ist, steht in
[`../chrischan-radiostream.md`](../chrischan-radiostream.md).

Alle Dateien sind unverändert aus Home Assistant übernommen; nur persönliche Daten
sind ersetzt (siehe unten). Die langen `description`-Texte der Automationen und
Skripte enthalten die Änderungshistorie und sind bewusst drin geblieben.

## Inhalt

| Datei | In HA | Inhalt |
|-------|-------|--------|
| [`automations.yaml`](automations.yaml) | `automations.yaml` (UI-Automationen) | Die 10 Radiostream-Automationen |
| [`scripts.yaml`](scripts.yaml) | `scripts.yaml` (UI-Skripte) | Die 10 Radiostream-Skripte + `benachrichtigung_alle_geraete` |
| [`dashboard-radio-streams.yaml`](dashboard-radio-streams.yaml) | Dashboard `radio-streams` (Rohkonfiguration) | Ansichten Receiver (Bedienung, Seite MEMORY für die Presets) und Reparatur (oben: „Wiedergabe" je Box, OK/Problem) |
| [`packages/radiostream.yaml`](packages/radiostream.yaml) | Paket in `configuration_yaml/packages/` (seit 18.11.2026; `configuration.yaml` lädt den Ordner mit `homeassistant: packages: !include_dir_named configuration_yaml/packages/`) | Alles YAML-Seitige des Radiostreams in einer Datei: Universal-Media-Player `media_player.radiostream_<p>_sender`, `sensor.radiostream_bt_signal` (command_line), `rest_command.bt_audio_*` für die REST-API des Add-ons und `sensor.radiostream_senderliste` (Sendername → Stream-URL). Die Recorder-Ausschlüsse bleiben in der zentralen `recorder.yaml`. |

`<p>` steht für die Box: `87_5`, `105_9` oder `97_0`.

## Platzhalter

| Platzhalter | Bedeutung |
|-------------|-----------|
| `<MAC_87_5>`, `<MAC_105_9>`, `<MAC_97_0>` | Bluetooth-Adresse der jeweiligen Box |
| `notify.mobile_app_geraet_1..3` | Benachrichtigungsdienste der drei Handys/Tablets (Companion-App) |

Die Adresse des Add-ons in den REST-Befehlen
(`http://1b3a7c56-bluetooth-audio-manager:8099`) und der Slug in
`script.radiostream_reparieren` (`1b3a7c56_bluetooth_audio_manager`) hängen vom
Repository ab, aus dem das Add-on installiert ist; bei einer anderen Installation
anpassen (siehe [`../api.md`](../api.md)).

## Voraussetzungen

**Add-on und Geräte**

- Dieses Add-on (Branch `chrischan`), die drei Boxen gepairt, pro Box MPD aktiv
  (Ports 6600 / 6601 / 6602 für 87.5 / 105.9 / 97.0).
- Pro Box eine schaltbare Steckdose: `switch.dose_bt_87_5`, `switch.dose_bt_105_9`,
  `switch.dose_bt_97_0`.
- Pro Box eine MPD-Integration (Host = Add-on, Port wie oben), die Player heißen
  `media_player.musik_radiostream_<p>`.
- Companion-App auf den Geräten, die Meldungen bekommen sollen.
- `binary_sensor.internet` (Ping-Integration auf eine Adresse im Internet): ohne
  Internet eskaliert der Bug-Watch eine stumme, aber erreichbare Box nicht.
- Für das Dashboard: card-mod bzw. UIX; die Ansicht *Receiver* nutzt die eigene Karte
  `custom:radiostream-receiver-card`, die nicht in diesem Export liegt. Sie liest seit 19.11.2026 die
  Template-Selects `select.radiosender_<p>` / `select.radiostream_preset_<n>` und schaltet über `select.*`;
  ihre Seite MEMORY zeigt seitdem auch ON AIR je Speicherplatz und die drei Boxen mit Senderwahl.
  Am 19.11.2026 entfernt: die Ansichten „Radio“ (Röhrenradio-Karte `custom:radiostream-radio-card`),
  „Presets“ (zuletzt `custom:radiostream-preset-card`) und „Radiostreams“ (Basic-Player mit Preset-Tasten);
  Bedienung und Preset-Belegung laufen über den Receiver.

**Helfer (UI → Einstellungen → Helfer)**

| Helfer | Typ | Inhalt |
|--------|-----|--------|
| `input_text.radiostream_address_map` | Text | `{"97_0":"<MAC_97_0>","105_9":"<MAC_105_9>","87_5":"<MAC_87_5>"}` |
| `input_text.radiostream_port_map` | Text | `{"87_5": 6600, "105_9": 6601, "97_0": 6602}` |
| `input_text.radiostream_stick_map` | Text | `{"97_0": "Logilink alt", "105_9": "Logilink alt", "87_5": "Logilink neu"}` (Bluetooth-Stick je Box, für die Statustabelle und den Stick-Reset; seit 18.11.2026) |
| `input_text.radiostream_stick_mac_map` | Text | `{"Logilink alt": "<MAC_STICK_ALT>", "Logilink neu": "<MAC_STICK_NEU>"}` (Adapter-MAC je Stick-Name, für `radiostream_stick_zuruecksetzen`; seit 18.11.2026) |
| `sensor.radiostream_bt_signal` | command_line (`packages/radiostream.yaml`, Skript `cli/bt_link_quality.py` → `/config/cli/`) | Verbindungsqualität je Box ohne Scan, alle 2 Min; Attribute `87_5`/`97_0`/`105_9` mit `rssi`, `tx`, `tx_max`, `adapter` (seit 18.11.2026) |
| `input_text.radiostream_dose_switch_map` | Text | `{"97_0":"switch.dose_bt_97_0","105_9":"switch.dose_bt_105_9","87_5":"switch.dose_bt_87_5"}` |
| `input_text.radiostream_schalter_map` | Text | `{"97_0":"switch.97_0_schalter","105_9":"switch.105_9_schalter","87_5":"switch.87_5_schalter"}` |
| `input_text.radiostream_aktiv_map` | Text | `{"97_0":"input_boolean.radiostream_97_0_aktiv", …}` |
| `input_text.radiostream_mpd_entry_map` | Text | `{"97_0":"<config_entry_id der MPD-Integration>", …}` |
| `input_text.radiostream_letzter_start` | Text | leer (wird von „Radiostream permanent" geschrieben) |
| `input_text.letzter_sender_<p>`, `input_text.letzter_preset_1..10` | Text (max. 60) | Wert der Template-Selects (Senderwahl, Presets) |
| `input_boolean.radiostream_<p>_aktiv` | Schalter | soll die Box spielen |
| `input_boolean.radiostream_ausfall_gemeldet_<p>` | Schalter | Merker für die Entwarnung |
| `input_boolean.radiostream_lautstarke_fest_100` | Schalter | Lautstärke-Sperre aller Boxen („Radiostream Lautstärke fest") |
| `input_number.radiostream_lautstarke_alle_boxen` | Zahl (10–100 %, Schieberegler) | Wert, auf dem die Sperre die Boxen hält (Add-on-Einstellung `volume_lock_level`, ab cc.16) |
| `input_boolean.radiostream_power_schaltet_steckdosen` | Schalter | „Aus" schaltet auch die Steckdose |
| `select.radiosender_<p>`, `select.radiostream_preset_1..10` | Template-Select im Paket `packages/radiostream.yaml` (seit 18.11.2026) | Senderwahl je Box und die 10 Presets. Optionen immer aus `sensor.radiostream_senderliste`, der Wert steht in `input_text.letzter_sender_<p>` / `letzter_preset_<n>` (eine Auswahl schreibt dorthin, beim Neustart wird er sicher wiederhergestellt). Ersetzen die früheren `input_select`-Helfer, deren gespeicherte Optionsliste veraltete: nach einem Neustart sprang eine Auswahl, deren Sender dort fehlte, auf den ersten Eintrag (am 18.11.2026: 97.0 bis zu 80 s „Queen"). |
| `input_select.radiostream_<p>_steckdose` | Dropdown | Optionen: die drei `switch.dose_bt_*` |
| `input_number.radiostream_<p>_letzte_position` | Zahl | Stall-Erkennung (muss −1 und die Spielzeit in Sekunden aufnehmen können) |
| `input_datetime.radiostream_letzte_automatische_voll_reparatur` | Datum + Zeit | Sperrzeit der Voll-Reparatur |
| `binary_sensor.radiostream_<p>_spielt_nicht` (Anzeigename „Radiostream <p> Wiedergabe": *OK* / *Problem*) | Template-Binärsensor (Helfer), Geräteklasse *Problem*, **Ausschaltverzögerung 1:30 min** | `{{ is_state('input_boolean.radiostream_<p>_aktiv', 'on') and is_state('switch.dose_bt_<p>', 'on') and not is_state('media_player.musik_radiostream_<p>', 'playing') }}` – an, solange die Box spielen soll, es aber nicht tut; geht erst aus, wenn der Player 90 s durchgehend spielt (ab 11.11.2026) |
| `switch.radiostream_steckdosen_alle` | Gruppe (Schalter), „Alle Mitglieder" an | Die drei `switch.dose_bt_*`; an, wenn alle drei an sind; Schalten wirkt auf alle drei (ab 11.11.2026) |
| `sensor.radiostream_boxen_ohne_verbindung` | Template-Sensor (Helfer) | Anzahl der Boxen, die aktiv sind, deren Steckdose an ist und deren Player `unavailable` ist (aus `input_text.radiostream_aktiv_map` und `input_text.radiostream_dose_switch_map`); Anzeige im Dashboard; bis 18.11.2026 Auslöser des Stick-Resets (ab 2 für 4 Min) |
| `sensor.radiostream_sticks_ohne_verbindung` | Template-Sensor (Helfer) | Sticks, an denen alle aktiven Boxen mit eingeschalteter Steckdose `unavailable` sind, kommagetrennt (z. B. `Logilink neu`), sonst `keine` (aus `input_text.radiostream_stick_map`, `…_aktiv_map`, `…_dose_switch_map`); für 4 Min ≠ `keine` startet die Automatik „Stick-Reset je Stick“ (seit 18.11.2026) |
| `switch.<p>_schalter` | Template-Schalter (Helfer) | leitet an die in `input_select.radiostream_<p>_steckdose` gewählte Steckdose weiter |

## Einspielen

1. Add-on installieren, Boxen pairen, MPD je Box aktivieren.
2. `packages/radiostream.yaml` als Paket einbinden (z. B. nach
   `configuration_yaml/packages/` legen und in `configuration.yaml`
   `homeassistant: packages: !include_dir_named configuration_yaml/packages/`
   eintragen), `cli/bt_link_quality.py` nach `/config/cli/` legen.
   Konfiguration prüfen, Home Assistant neu starten.
3. Die drei MPD-Integrationen einrichten und ihre Config-Entry-IDs in
   `input_text.radiostream_mpd_entry_map` eintragen.
4. Helfer anlegen (Tabelle oben), Platzhalter durch die echten Werte ersetzen.
5. `scripts.yaml` und danach `automations.yaml` übernehmen (Inhalte an die
   eigenen Dateien anhängen oder einzeln im UI-Editor über „In YAML bearbeiten"
   einfügen), dann Skripte und Automationen neu laden.
6. Dashboard anlegen und `dashboard-radio-streams.yaml` im
   Rohkonfigurations-Editor einfügen.

## Hinweise

- Ein Skript ruft ein anderes immer mit `script.turn_on` + `target.entity_id` +
  `data.variables` auf, nie mit der Kurzform `script.<name>` (die war in dieser
  Installation unzuverlässig).
- Die Bluetooth-Seite (PulseAudio-Einstellung gegen Aussetzer mit drei Boxen,
  44,1 kHz) ist im Add-on bzw. in `/data/custom.pa` des Audio-Plugins geregelt,
  nicht hier – siehe [`../chrischan-radiostream.md`](../chrischan-radiostream.md#3-pulseaudio-aussetzer-fix-custompa).
- Entfernte Teile (Signalstärke-Messung, Sink-Check, hci-Überwachung,
  automatischer HA-Neustart) sind in diesem Export nicht mehr enthalten; warum,
  steht im Setup-Dokument unter „Aufgeräumt am 06.11.2026".
