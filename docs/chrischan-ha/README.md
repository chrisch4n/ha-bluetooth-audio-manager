# Home-Assistant-Konfiguration „Radiostream" (Export, Stand 06.11.2026)

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
| [`automations.yaml`](automations.yaml) | `automations.yaml` (UI-Automationen) | Die 8 Radiostream-Automationen |
| [`scripts.yaml`](scripts.yaml) | `scripts.yaml` (UI-Skripte) | Die 8 Radiostream-Skripte + `benachrichtigung_alle_geraete` |
| [`dashboard-radio-streams.yaml`](dashboard-radio-streams.yaml) | Dashboard `radio-streams` (Rohkonfiguration) | Ansichten Radiostreams, Reparatur, Presets, Radio, Receiver |
| [`configuration_yaml/rest_command.yaml`](configuration_yaml/rest_command.yaml) | `rest_command: !include …` | `rest_command.bt_audio_*` für die REST-API des Add-ons |
| [`configuration_yaml/media_player.yaml`](configuration_yaml/media_player.yaml) | `media_player: !include …` | Universal-Media-Player `media_player.radiostream_<p>_sender` |
| [`configuration_yaml/template_radiostream_senderliste.yaml`](configuration_yaml/template_radiostream_senderliste.yaml) | Ausschnitt aus `template: !include …` | `sensor.radiostream_senderliste` (Sendername → Stream-URL) |

`<p>` steht für die Box: `87_5`, `105_9` oder `97_0`.

## Platzhalter

| Platzhalter | Bedeutung |
|-------------|-----------|
| `<MAC_87_5>`, `<MAC_105_9>`, `<MAC_97_0>` | Bluetooth-Adresse der jeweiligen Box |
| `notify.mobile_app_geraet_1..3` | Benachrichtigungsdienste der drei Handys/Tablets (Companion-App) |

Die Adresse des Add-ons in `rest_command.yaml`
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
- Für das Dashboard: card-mod bzw. UIX.

**Helfer (UI → Einstellungen → Helfer)**

| Helfer | Typ | Inhalt |
|--------|-----|--------|
| `input_text.radiostream_address_map` | Text | `{"97_0":"<MAC_97_0>","105_9":"<MAC_105_9>","87_5":"<MAC_87_5>"}` |
| `input_text.radiostream_port_map` | Text | `{"87_5": 6600, "105_9": 6601, "97_0": 6602}` |
| `input_text.radiostream_dose_switch_map` | Text | `{"97_0":"switch.dose_bt_97_0","105_9":"switch.dose_bt_105_9","87_5":"switch.dose_bt_87_5"}` |
| `input_text.radiostream_schalter_map` | Text | `{"97_0":"switch.97_0_schalter","105_9":"switch.105_9_schalter","87_5":"switch.87_5_schalter"}` |
| `input_text.radiostream_aktiv_map` | Text | `{"97_0":"input_boolean.radiostream_97_0_aktiv", …}` |
| `input_text.radiostream_mpd_entry_map` | Text | `{"97_0":"<config_entry_id der MPD-Integration>", …}` |
| `input_text.radiostream_letzter_start` | Text | leer (wird von „Radiostream permanent" geschrieben) |
| `input_text.letzter_sender_<p>`, `input_text.letzter_preset_1..10` | Text | leer (gemerkte Auswahl) |
| `input_boolean.radiostream_<p>_aktiv` | Schalter | soll die Box spielen |
| `input_boolean.radiostream_ausfall_gemeldet_<p>` | Schalter | Merker für die Entwarnung |
| `input_boolean.radiostream_lautstarke_fest_100` | Schalter | Lautstärke-Sperre aller Boxen |
| `input_boolean.radiostream_power_schaltet_steckdosen` | Schalter | „Aus" schaltet auch die Steckdose |
| `input_select.radiosender_<p>` | Dropdown | Sender je Box (Optionen setzt die Automation „Senderlisten synchronisieren") |
| `input_select.radiostream_preset_1..10` | Dropdown | Presets (ebenso) |
| `input_select.radiostream_<p>_steckdose` | Dropdown | Optionen: die drei `switch.dose_bt_*` |
| `input_number.radiostream_<p>_letzte_position` | Zahl | Stall-Erkennung (muss −1 und die Spielzeit in Sekunden aufnehmen können) |
| `input_datetime.radiostream_letzte_automatische_voll_reparatur` | Datum + Zeit | Sperrzeit der Voll-Reparatur |
| `switch.<p>_schalter` | Template-Schalter (Helfer) | leitet an die in `input_select.radiostream_<p>_steckdose` gewählte Steckdose weiter |

## Einspielen

1. Add-on installieren, Boxen pairen, MPD je Box aktivieren.
2. Die Dateien aus `configuration_yaml/` in den Konfigurationsordner legen und in
   `configuration.yaml` einbinden (`rest_command:`, `media_player:`; den
   Senderlisten-Sensor in die eigene `template:`-Konfiguration übernehmen).
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
