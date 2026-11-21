# Änderungsgeschichte der Radiostream-Automationen und -Skripte

Bis 21.11.2026 stand die Geschichte jeder Automation und jedes Skripts in ihrer
`description` in Home Assistant. Dort steht seitdem nur noch ein kurzer Zweck; der
vollständige Text vom 21.11.2026 ist hier gesichert (unverändert, anonymisiert wie die
übrigen Exporte). Neuere Änderungen: [`../chrischan-radiostream.md`](../chrischan-radiostream.md).

## Automationen

### Radiostream Player unavailable (BT Audio Manager Bug-Watch)

`automations.yaml id 1786256754488`

AKTUELLER STAND (11.11.2026): Meldet, wenn einer der drei Radiostream-Player laenger als 3 Minuten
unavailable ist ODER erreichbar ist, aber seit 15 Minuten nicht spielt
(binary_sensor.radiostream_<p>_spielt_nicht; Stufen dann nach 15/20/30/40 Min statt 3/5/20/30), und
eskaliert in 4 Stufen - nur fuer Boxen, die laut radiostream_aktiv_map aktiv und laut
radiostream_dose_switch_map mit Strom versorgt sind: 1 'diagnose' (3 Min,
script.radiostream_reparieren_ultralight), 2 'steckdosen_zyklus' (5 Min, nur die betroffene
Steckdose, danach Nachdiagnose), 3 'addon_neustart' (20 Min, script.radiostream_reparieren inkl.
Add-on-Neustart, hoechstens alle 30 Min), 4 'manuell_pruefen' (30 Min, nur Meldung 'bitte manuell
pruefen'). Alle Meldungen einer Box laufen ueber script.benachrichtigung_alle_geraete mit tag
radiostream_<player> und ersetzen sich gegenseitig; die Entwarnung kommt von
automation.radiostream_player_wieder_verfugbar_benachrichtigung_loschen. HISTORIE: VEREINFACHUNG
12.09.2026: die vorherige eigenstaendige 'leicht'-Stufe (10 Min, reiner BT-Force-Reconnect) wurde
ENTFERNT, da seit der Ultralight-Erweiterung vom 12.09.2026 funktional redundant -
Ultralight/Diagnose deckt den BT-Force-Reconnect-Fall bereits als internen Fallback mit ab (siehe
script.radiostream_reparieren_ultralight), acht Minuten frueher. Dadurch verkuerzt sich die maximale
Zeit bis zum HA-Neustart von 40 auf 30 Minuten ohne Abdeckungsverlust. Bekannte Grenze: keine der 4
Stufen deckt den Fall ab, dass eine Box manuell in den Kopplungsmodus versetzt werden muss
(T65-Vorfall 23.08.) - das bleibt manuell. Push-Benachrichtigung geht gezielt an die drei aktiven
Geraete statt per notify.notify an alle. continue_on_error bleibt zur Sicherheit auf den Notify-
Schritten. Aeltere Fixes (24.08./11.09./12.09.2026) betrafen Schema-Fehler bei notify.send_message,
falsche Servicenamen mit 's', und unzuverlaessige Kurzform-Script-Aufrufe - alle behoben, Details im
Projekt-Dokumentationsfile. ZEITANPASSUNG 19.09.2026 (Claude, auf Wunsch des Nutzers): Wartezeit bis
steckdosen_zyklus von 10 auf 5 Minuten gesenkt, da die diagnose-Stufe seit ihrer Erweiterung am
19.09.2026 deutlich gruendlicher ist (deckt 4 von 5 Fehlermodi in einem ~30s-Durchlauf ab) - reine
Zeitersparnis bei echten Ausfaellen, kein Abdeckungsverlust.

[21.09.2026: Push- und persistent_notification-Nachrichten um 'Stufe X/4:'-Praefix ergaenzt
(diagnose=1, steckdosen_zyklus=2, addon_neustart=3, ha_neustart=4), damit auf einen Blick erkennbar
ist, wie weit die Eskalation fortgeschritten ist. Ausserdem Script-Aliase umbenannt (Entity-IDs
unveraendert): radiostream_reparieren_ultralight -> 'Radiostream Diagnose',
radiostream_reparieren_light -> 'Radiostream BT-Reconnect', radiostream_reparieren -> 'Radiostream
Voll-Reparatur' - 'ultralight' klang nach minimal, ist aber die ausgefeilteste Stufe.

[23.09.2026: (a) Neue Bedingung - greift nur, wenn die Box laut radiostream_aktiv_map aktiv UND laut
radiostream_dose_switch_map mit Strom versorgt ist; absichtlich ausgeschaltete Boxen werden nicht
mehr 'repariert' oder wieder eingeschaltet. (b) Sperrzeiten: automatische Voll-Reparatur hoechstens
alle 30 Min (input_datetime.radiostream_letzte_automatische_voll_reparatur), automatischer HA-
Neustart hoechstens alle 3 Std (input_datetime.radiostream_letzter_automatischer_ha_neustart) -
statt Wiederholung gibt es dann eine Push-Nachricht 'bitte manuell pruefen'. Verhindert
Endlosschleifen bei nicht automatisch loesbaren Faellen.]

[25.09.2026 Nachdiagnose in Stufe 2: nach dem Steckdosen-Zyklus wird auf dessen Ende gewartet, dann
60s, und falls der Player dann noch unavailable ist, laeuft die Diagnose erneut. Anlass: 87.5 war
nach dem Zyklus wieder per Bluetooth verbunden, aber das Add-on startete den MPD-Dienst nicht mit
(bekannter Add-on-Bug, eigenes GitHub-Issue) - Stufe 1 war zu frueh gelaufen (Box damals noch
unerreichbar), sodass erst die Voll-Reparatur nach 20 Min gegriffen haette.]

[25.09.2026 Push umgebaut: statt notify.send_message (kein tag moeglich) jetzt
notify.mobile_app_<geraet> mit data.tag 'radiostream_<player>' an die drei aktiven Geraete.
Meldungen derselben Box ersetzen sich auf dem Handy gegenseitig (eine Meldung pro Box, von Stufe zu
Stufe aktualisiert). Zusaetzlich wird input_boolean.radiostream_ausfall_gemeldet_<player> gesetzt -
die Entwarnungs-Automation schickt nur bei gesetztem Merker ein 'wieder da', das die Ausfall-Meldung
ersetzt.]

[02.10.2026: Push-Meldungen laufen jetzt ueber script.benachrichtigung_alle_geraete (gleiche drei
Geraete, gleicher Tag). 1 Bloecke umgestellt.]

[01.11.2026 Testphase gepatchtes Add-on 1b3a7c56 (Claude): Stufe 1 von 2 auf 5 Min, Stufe 2 von 5
auf 10 Min verlaengert, damit die Selbstheilung des Add-ons zuerst greift. Nach erfolgreichem Test
pruefen, ob die Stufen ausgeduennt werden koennen.]

[06.11.2026 Claude, auf Wunsch des Nutzers: Stufe 4 'ha_neustart' ersetzt durch 'manuell_pruefen' -
nach 30 Min nur noch Push + persistente Meldung 'bitte manuell pruefen', KEIN homeassistant.restart
mehr. Grund: ein HA-Neustart startet weder das Add-on noch Bluetooth/PulseAudio neu, kann also
nichts beheben, was Stufe 3 nicht geschafft hat; er lief seit 23.09. auch nie. Helfer
input_datetime.radiostream_letzter_automatischer_ha_neustart entfernt. Die Testphasen-Zeiten (Stufe
1 nach 5 Min, Stufe 2 nach 10 Min) gelten jetzt dauerhaft, damit die Selbstheilung des gepatchten
Add-ons zuerst greift.]

[06.11.2026 Claude: Stand-Zusammenfassung vorangestellt; Meldung 'Eskalation gesperrt' in Stufe 3
von notify.send_message auf script.benachrichtigung_alle_geraete mit tag umgestellt.]

[11.11.2026 Claude, auf Wunsch des Nutzers (Haertung): zweiter Einstieg in dieselbe Stufenleiter -
eine aktive Box mit eingeschalteter Steckdose, deren Player erreichbar ist, aber nicht spielt.
Bisher blieb das unbemerkt, weil nur 'unavailable' eskalierte (z.B. PulseAudio neu gestartet: Player
'off' statt 'unavailable'). Erkennung ueber die Template-Helfer
binary_sensor.radiostream_<p>_spielt_nicht (an = aktiv UND Steckdose an UND Player nicht 'playing';
geht erst aus, wenn der Player 90 s durchgehend spielt - kurze Startversuche setzen die Zeit also
nicht zurueck). Stufen: 15 Min Diagnose, 20 Min Steckdosen-Zyklus, 30 Min Voll-Reparatur (gleiche
30-Min-Sperre), 40 Min 'bitte manuell pruefen'. Dieser Einstieg entfaellt, wenn (a) der Player seit
mindestens 5 Min durchgehend unavailable ist - dann laeuft bereits die Leiter fuer Ausfaelle -, oder
(b) binary_sensor.internet aus ist bzw. erst seit weniger als 5 Min wieder an: ohne Internet kann
kein Stream spielen, eine Reparatur wuerde nichts beheben. Dafuer Variablen
p/player/spielt_nicht/box_name/stoerung eingefuehrt; alle Schritte nutzen sie statt
trigger.entity_id. Entwarnung: neuer Ausloeser 'spielt_wieder' in
automation.radiostream_player_wieder_verfugbar_benachrichtigung_loschen.]

[11.11.2026 abends Claude, auf Wunsch des Nutzers: fuer 'unavailable' Diagnose von 5 auf 3 Min und
Steckdosen-Zyklus von 10 auf 5 Min vorgezogen. Anlass: Firmware-Absturz des Realtek-Sticks 18:20
(RTL hw err, alle drei Verbindungen gleichzeitig weg); 87.5 und vorher 105.9 nahmen danach keine
Verbindung mehr an, bis ihre Steckdose kurz aus war - die ES-BT17 verbindet sich nur nach einem
Stromzyklus neu. Die Selbstheilung des Add-ons (Reconnect nach 10 s, 32 s, 63 s, 130 s) hat bis 3
Min trotzdem Vorrang. Stufen 3/4 (20/30 Min) und der Einstieg 'spielt nicht' (15/20/30/40 Min)
unveraendert.]

[13.11.2026 Claude, auf Wunsch des Nutzers: Stufe 2 (Steckdosen-Zyklus) wartet, solange
script.radiostream_stick_zuruecksetzen laeuft (neu:
automation.radiostream_stick_reset_bei_mehrfachausfall startet es, wenn 2+ Boxen seit 4 Min ohne
Verbindung sind), und entfaellt, wenn die Box danach wieder da ist. Grund: Der Realtek-Stick hing am
11.11. und 13.11.; ein Steckdosen-Zyklus hilft dann nicht und stoert das einzelne Neuverbinden nach
dem Stick-Reset.]

### Radiostream Player wieder verfügbar (Benachrichtigung löschen)

`automations.yaml id 1786706796964`

Entwarnung nach einem gemeldeten Ausfall (neu aufgebaut 25.09.2026). Ausloeser: ein Player kommt aus
'unavailable' in IRGENDEINEN anderen Zustand zurueck und bleibt dort 20s stabil (vorher nur direkt
unavailable->playing, verpasste z.B. unavailable->off->playing nach einem Reload). Bedingung: der
Merker input_boolean.radiostream_ausfall_gemeldet_<player> ist gesetzt, d.h. der Watchdog hat fuer
diese Box wirklich eine Ausfall-Meldung verschickt (die alte Bedingung pruefte eine
persistent_notification-Entity, die es in aktuellen HA-Versionen nicht mehr gibt - sie war seit
20.09.2026 immer falsch, daher kam nie eine Entwarnung). Aktion: Merker zuruecksetzen,
persistent_notification loeschen, Push 'wieder da' mit derselben Markierung (tag
radiostream_<player>) an die drei Geraete - ersetzt auf dem Handy die Ausfall-Meldung inkl.
Ausfalldauer. Kurze Aussetzer ohne vorherige Ausfall-Meldung loesen nichts aus.

[02.10.2026: Push-Meldungen laufen jetzt ueber script.benachrichtigung_alle_geraete (gleiche drei
Geraete, gleicher Tag).]

[11.11.2026 Claude, auf Wunsch des Nutzers (Haertung): zweiter Ausloeser 'spielt_wieder'
(binary_sensor.radiostream_<p>_spielt_nicht geht von an auf aus) fuer Stoerungen, bei denen der
Player erreichbar war, aber nicht spielte - dafuer gab es bisher weder Meldung noch Entwarnung. Die
Dauer ist dann die Zeit, die der Helfer an war. Box-Kuerzel wird jetzt per Regex aus der Entity-ID
gelesen (passt fuer Player und Helfer); die ID der persistenten Meldung bleibt
radiostream_ausfall_musik_radiostream_<p>.]

### Radiostream permanent (97.0/105.9/87.5)

`automations.yaml id 1787286971104`

Konsolidierte Version der drei ehemals separaten '..._permanent'-Automationen (97.0, 105.9, 87.5).
Spielt pro Player den gewaehlten Sender dauerhaft via MPD, sofern
input_boolean.radiostream_<player>_aktiv an ist. Startet beim HA-Neustart, bei Senderwechsel sofort,
bei Reaktivierung des Aktiv-Schalters sofort, und prueft alle 5 Minuten per Watchdog je Player (nur
falls aktiv), inkl. Stall-Erkennung ueber media_position. Seit 31.08.2026 als repeat: for_each ueber
die 3 Player-Suffixe implementiert statt 3 kopierter Codebloecke - identisches Verhalten, deutlich
kompakter und leichter erweiterbar.

[20.09.2026: 3s-Pause nach jedem play_media-Aufruf ergaenzt - verhindert die am selben Tag entdeckte
Race Condition im Add-on, die auftrat wenn mehrere Player im selben Automationslauf (z.B. bei
ha_start oder Watchdog) nahezu gleichzeitig gestartet wurden und dadurch alle Streams auf einem
einzigen Audio-Sink landeten (Mixing-Bug) statt auf ihren jeweils eigenen.]

[23.09.2026: Stall-Pruefung um Falscher-Sender-Erkennung erweitert - vergleicht media_content_id mit
der URL des in input_select.radiosender_<n> gewaehlten Senders (aus sensor.radiostream_senderliste).
Bei Abweichung wird der richtige Sender neu gestartet. Keine zusaetzliche BT-Aktivitaet, reiner
Vergleich. Bewusste Folge: manuell ueber den HA-Mediaplayer gestartete fremde Inhalte werden
innerhalb von 5 Min auf den gewaehlten Sender zurueckgesetzt (Presets sind nicht betroffen, sie
schreiben in die Senderauswahl).]

[23.09.2026 Traegheits-Fix: (a) Modus 'single' -> 'queued' (max 10). Im single-Modus wurden
Preset-/Senderwechsel waehrend eines laufenden Durchgangs verworfen (Trace: failed_single, mehrere
105.9-Presets verschluckt). (b) Ein Senderwechsel bzw. eine Reaktivierung bearbeitet jetzt nur noch
den betroffenen Player statt alle drei - vorher lief jeder Wechsel durch alle drei Player inkl.
moeglicher Neustarts mit je 3s Pause. Die Gesamtpruefung aller aktiven Player bleibt fuer HA-Start,
5-Min-Watchdog und manuelles automation.trigger erhalten. Die 3s-Pause nach jedem Start bleibt als
Mindestabstand gegen Mixing bestehen; durch queued greift sie auch zwischen schnell
aufeinanderfolgenden Tipps auf verschiedene Player.]

[23.09.2026 Zapp-Fix: Die feste 3s-Pause nach JEDEM Start ist ersetzt durch einen gezielten Mixing-
Schutz: gewartet wird nur, wenn innerhalb der letzten 3s ein ANDERER Player gestartet wurde, und nur
die Restzeit (gemerkt in input_text.radiostream_letzter_start als 'player|zeitstempel'). Schnelles
Durchzappen innerhalb eines Players laeuft damit ohne Wartezeit. Zusaetzlich werden ueberholte Tipps
uebersprungen: stimmt die aktuelle Senderauswahl beim Abarbeiten nicht mehr mit dem Tipp ueberein,
wird dieser Zwischenschritt nicht mehr abgespielt.]

[23.09.2026: max_exceeded: silent ergaenzt (nur Log-Warnung bei >10 gleichzeitig wartenden Laeufen
unterdrueckt). Einen Vorschlag 'queued mit max: 2' bewusst NICHT uebernommen: beim schnellen Zappen
wuerde ein dritter Tipp still verworfen - oft genau der letzte, also der gewollte Sender. Die Logik
zum Ueberspringen ueberholter Tipps setzt voraus, dass der letzte Tipp in der Warteschlange
ankommt.]

[24.09.2026 Umzugs-Schutz: Neuer Ausloeser 'reconnect' (ein Player meldet sich nach unavailable
zurueck, 20s stabil). Dann werden ALLE aktiven Player gestaffelt neu gestartet, auch wenn sie laut
HA gesund wirken. Hintergrund: PulseAudio zieht beim Neuverbinden eines BT-Lautsprechers laufende
Streams auf den neuen Sink um (am 24.09. beobachtet: 105.9 spielte nach Steckdosen-Reset den Stream
von 97.0, obwohl HA fuer 105.9 den richtigen Sender meldete). Das erklaert rueckblickend fast alle
Mixing-Faelle. Entprellung: liegt der letzte Gesamt-Neustart (reconnect oder ha_start,
input_datetime.radiostream_letzter_gesamt_neustart) weniger als 60s zurueck, wird der Lauf beendet -
mehrere Rueckmeldungen z.B. nach einer Voll-Reparatur ergeben so nur einen Neustart.]

[01.11.2026 Testphase gepatchtes Add-on 1b3a7c56 (Claude): Ausloeser reconnect deaktiviert (nicht
geloescht), siehe Notiz am Ausloeser.]

[06.11.2026 Claude, auf Wunsch des Nutzers: Ausloeser 'reconnect' samt Entprellung (Helfer
input_datetime.radiostream_letzter_gesamt_neustart) endgueltig entfernt - das gepatchte Add-on
schiebt fehlgeleitete MPD-Streams selbst auf ihre Box zurueck (#318); die Falscher-Sender-Erkennung
im 5-Min-Watchdog bleibt als Netz.]

[06.11.2026 Claude, auf Wunsch des Nutzers: schlanker Ersatz fuer 'reconnect' - neue Ausloeser
'zurueck_<player>' (Player kommt aus unavailable zurueck, 20 s stabil). Bearbeitet wird nur dieser
eine Player und nur, wenn er aktiv ist: laeuft er nicht, steht er oder spielt den falschen Sender,
wird er neu gestartet. Die anderen Boxen bleiben unberuehrt. Vorher spielte eine zurueckgekehrte Box
erst beim naechsten 5-Min-Watchdog wieder.]

[07.11.2026 Claude, auf Wunsch des Nutzers: zusaetzliche Ausloeser 'gestoppt_<player>' (Player geht
von playing auf off/idle/paused und bleibt 20 s so). Fall: nach einem Add-on-Update sprangen 105.9
und 97.0 direkt von playing auf off, ohne unavailable zu sein - 'zurueck' griff nicht, erst der
5-Min-Watchdog startete sie neu. Behandelt wie 'zurueck': nur dieser Player, nur wenn er aktiv ist;
ein absichtlicher Stopp ueber den Aktiv-Schalter bleibt deshalb aus. Ein Stopp direkt am MPD-Player
bei aktivem Schalter wird nach 20 s rueckgaengig gemacht (vorher spaetestens nach 5 Min durch den
Watchdog).]

[18.11.2026 Claude, auf Wunsch des Nutzers: Senderwahl kommt aus den Template-Selects
select.radiosender_<player> (Paket radiostream.yaml) statt aus input_select.radiosender_<player> -
deren gespeicherte Optionsliste veraltete und liess die Auswahl beim Neustart auf den ersten Sender
springen. Ausloeser sender_gewechselt_* mit not_from unknown/unavailable.]

### Radiostream Player nach HA-Start prüfen

`automations.yaml id 1790922426090`

Schliesst eine Luecke des Watchdogs
(automation.radiostream_player_unavailable_bt_audio_manager_bug_watch) und der Entwarnung
(automation.radiostream_player_wieder_verfugbar_benachrichtigung_loschen): beide haengen an einem
Zustandswechsel des Players. Ist eine Box schon beim HA-Start 'unavailable' (z.B. nach einem HA-
Neustart; den automatischen HA-Neustart als Watchdog-Stufe 4 gibt es seit 06.11.2026 nicht mehr),
gibt es keinen Wechsel und die Reparaturkette startet nie; kommt eine Box waehrend des Neustarts
zurueck, bleibt die Entwarnung aus und der Ausfall-Merker steht dauerhaft an. Diese Automation
prueft 3 Minuten nach dem HA-Start jeden Player einmal: (a) seit dem Start durchgehend unavailable,
aktiv und Steckdose an -> Merker setzen, Push an die drei Geraete, EINMAL die Diagnose
(script.radiostream_reparieren_ultralight) - bewusst keine weitere Eskalation (kein Steckdosen-
Zyklus, kein Add-on- oder HA-Neustart), damit keine Schleife entsteht; (b) Merker noch an, Player
aber wieder da -> Entwarnung nachholen. Player, die erst nach dem Start ausfallen oder
zurueckkommen, bleiben beim Watchdog bzw. der normalen Entwarnung (Abgrenzung ueber last_changed).
Die Player werden nacheinander bearbeitet, damit keine gleichzeitigen Bluetooth-Aktionen entstehen.
Eingerichtet 02.10.2026.

[06.10.2026 ERGAENZUNG auf Wunsch des Nutzers: Bleibt eine Box nach der Diagnose unavailable UND
meldet das Add-on sie als per Bluetooth getrennt (rest_command.bt_audio_get_devices,
connected=false), folgt genau EINMAL pro HA-Start der Steckdosen-Zyklus
(script.radiostream_steckdose_zyklieren) mit 60 s Wartezeit und Nachdiagnose - wie Stufe 2 des
Watchdogs. Anlass: Nach dem Host-Neustart am 06.10.2026 antwortete 105.9 nicht mehr (br-connection-
page-timeout) und kam erst nach Aus-/Einschalten von Hand und einem Connect zurueck. Ist die Box per
Bluetooth verbunden, der Player aber trotzdem unavailable (z.B. MPD-Integration erreicht das Add-on
nicht), gibt es KEINEN Zyklus - ein Stromreset hilft dann nicht. Weiterhin bewusst kein Add-on- und
kein HA-Neustart von hier aus, damit keine Schleife entsteht. Damit ist die fruehere Aussage 'kein
Steckdosen-Zyklus' in dieser Beschreibung ueberholt.]

## Skripte

### Radiostream Notfall: Forget + Pair + MPD zuweisen

`script.radiostream_notfall_forget_pair`

Manueller Nothelfer fuer eine haengende Bluetooth-Audio-Box: vergisst das Geraet, scannt neu, pairt
es erneut und setzt danach mpd_enabled/mpd_port ueber die Add-on-API. Nur manuell aufrufen (z.B.
ueber Entwicklertools > Aktionen), keine automatische Ausloesung. Nutzt die rest_command-
Definitionen bt_audio_forget_device/bt_audio_scan/bt_audio_pair_device/bt_audio_set_mpd.

[25.09.2026 Ueberarbeitet: (1) set_mpd uebergibt jetzt mpd_enabled: true - fehlte bisher, sodass ein
frisch gekoppeltes Geraet ohne MPD-Dienst (stumm) blieb. (2) Nach dem Scan bis zu 3
Kopplungsversuche mit Erfolgskontrolle per get_devices statt eines einzelnen Versuchs mit fester
Wartezeit. (3) Fuer bereits gemappte Boxen am Ende script.radiostream_mpd_sicherstellen. Hinweis:
Wird die Box trotzdem nicht gefunden, muss sie in den Kopplungsmodus versetzt werden.]

[19.11.2026 Claude, auf Wunsch des Nutzers: optionales Feld player (87_5/97_0/105_9) - MAC und MPD-
Port kommen dann aus input_text.radiostream_address_map / _port_map. Grund: Dashboard-Knoepfe
uebergaben Templates als Variablen, die beim Skriptaufruf nicht ausgewertet werden. address/mpd_port
gehen weiterhin.]

[19.11.2026 Claude, auf Wunsch des Nutzers: koppelt am Stick der Box
(input_text.radiostream_stick_map -> radiostream_stick_mac_map, rest_command.bt_audio_pair_device
mit adapter). Grund: Nach dem Forget kennt das Add-on die Stick-Zuordnung nicht mehr und koppelte
sonst am Hauptadapter. Box ohne Eintrag: Hauptadapter wie bisher.]

### Radiostream Power umschalten

`script.radiostream_power_toggle`

action=on: schaltet IMMER beides ein - Steckdose (switch_map) UND Stream-Start (aktiv_map) -
unabhaengig vom Modus-Flag, seit 08.09.2026 (Claude), damit z.B. der Dashboard-Tile-Tap nach einem
vorherigen Pause zuverlaessig auch die Box wieder mit Strom versorgt statt nur MPD zu starten.
action=off: verhaelt sich weiterhin je nach input_boolean.radiostream_power_schaltet_steckdosen -
entweder Steckdose aus (Schalter-Variante, kappt Strom = Pause-Verhalten) oder nur
input_boolean.radiostream_<player>_aktiv aus (Stream-Modus). switch_map und aktiv_map zentral aus
input_text.radiostream_schalter_map bzw. input_text.radiostream_aktiv_map (JSON).

[21.09.2026 Fix: 8s Pause zwischen Steckdose-an und Stream-Start ergaenzt (action=on) - vorher kein
Delay, wodurch der erste Play-Versuch oft fehlschlug, bevor die Box überhaupt gebootet/reconnected
war.

[25.09.2026: Nach action=on wird script.radiostream_mpd_sicherstellen aufgerufen - faengt den Fall
ab, dass das Add-on nach dem verzoegerten Neuverbinden den MPD-Dienst nicht mitstartet.]

[21.11.2026 Claude, auf Wunsch des Nutzers: switch_map kommt aus
input_text.radiostream_dose_switch_map und schaltet die Steckdose direkt - der Umweg ueber
input_text.radiostream_schalter_map, die Template-Schalter switch.<player>_schalter und die
Auswahlhelfer input_select.radiostream_<player>_steckdose ist entfernt.]

### Radiostream Steckdosen alle zyklieren

`script.radiostream_steckdosen_alle_zyklieren`

Setzt alle eingeschalteten Radiostream-Boxen nacheinander per Steckdose zurueck (97.0, 105.9, 87.5):
jede Box 30 s stromlos, dann wieder an, dann 90 s Pause, bevor die naechste dran ist. Es ist also
nie mehr als eine Box gleichzeitig still, und die Boxen verbinden sich einzeln neu. Dauer bei drei
Boxen etwa 6 Minuten. Bewusst ausgeschaltete Steckdosen bleiben aus. Ohne Add-on-Neustart; die
Wiedergabe startet 'Radiostream permanent' (Ausloeser Rueckkehr). Gedacht gegen verrauschten UKW-
Klang, der nach 1-3 Tagen Dauerbetrieb auf allen Boxen auftritt (07.11., 10.11., 11.11.,
13.11.2026), und laeuft dafuer auch jede Nacht
(automation.radiostream_nachtlicher_steckdosen_zyklus).

[11.11.2026 angelegt von Claude auf Wunsch des Nutzers: alle gemeinsam 30 s aus, dann mit 20 s
Abstand wieder an.]

[13.11.2026 Claude, auf Wunsch des Nutzers: umgebaut auf nacheinander mit 90 s Abstand. Grund: Die
Boxen brauchen 40-70 s zum Hochfahren und Verbinden; mit 20 s Abstand kamen alle drei fast
gleichzeitig zurueck, und genau dabei geriet der Realtek-Stick zweimal durcheinander (11.11. 18:20
Firmware-Absturz, 13.11. 07:02 'link tx timeout', half nur Abziehen des Sticks). 90 s Abstand bleibt
ausserdem unter der Bug-Watch-Diagnose (3 Min unavailable).]

### Radiostream Diagnose

`script.radiostream_reparieren_ultralight`

Schnellste, unaufdringlichste Reparaturstufe (Stand 19.09.2026, jetzt inkl. Audio-Sink-Check).
Prueft per GET /api/devices ob Bluetooth gesund ist (connected+has_transport) UND per GET
/api/audio/sinks ob der PulseAudio-Sink tatsaechlich 'running' ist (das ist das Feld, das die Add-
on-App als STREAMING/idle anzeigt - deckt jetzt auch den frueher nicht automatisch erkennbaren
Audio-Routing-Bug ab, live bestaetigt am 19.09.2026: BT+HA meldeten 'gesund'/'playing', aber der
Sink war 'idle' und es kam nachweislich kein Ton). Falls BT NICHT gesund: direkte Delegation an
script.radiostream_reparieren_light (BT-Reparatur mit eigener Retry-Schleife). Falls BT gesund, aber
Player nicht 'playing' ODER Sink nicht 'running': kombinierter Fix - MPD-Daemon per
rest_command.bt_audio_set_mpd aus/an (behebt toten Daemon, nie gestarteten Daemon nach verzoegertem
Reconnect, UND den Audio-Routing-Bug) + homeassistant.reload_config_entry (behebt haengende HA-MPD-
Integration). Danach 3s-Check; falls Player weiterhin unavailable, bis zu 3 Retries via
reparieren_light im 6s-Abstand (deckt pausierten Reconnect-Scheduler ab). Schutzbedingung: laeuft
nur, wenn NICHT (Player playing UND Sink running) - ein bereits vollstaendig gesunder Stream wird
nicht angetastet. Deckt damit jetzt 5 von 5 bekannten Fehlermodi ab (nur der harte BT-Stack-Haenger
und Adapter-Reindex brauchen weiterhin steckdosen_zyklus bzw. addon_neustart).

[19.09.2026 v3, Doppelpruefung ergaenzt: Bevor tatsaechlich repariert wird, erfolgt nach 2s eine
zweite Abfrage von /api/devices und /api/audio/sinks - nur wenn der Fehlerzustand dort bestaetigt
wird, laufen die eigentlichen Reparaturaktionen (MPD-Toggle/Reload/Delegation). Grund: eigene
automatische Pruefungen sind nicht neutral - sie koennen selbst zur Instabilitaet beitragen (siehe
Diskussion 19.09.2026: die stuendliche RSSI-Scan-Automation kann A2DP-Verbindungen kurz stoeren, was
ohne Zweitpruefung faelschlich als echter Ausfall interpretiert und unnoetig 'repariert' werden
koennte).

[19.09.2026 v4, Race-Fix: Modus von 'parallel' auf 'queued' (max 5) umgestellt - verhindert, dass
zwei Ausloeser (z.B. Watchdog-diagnose-Stufe UND periodischer Sink-Check) gleichzeitig fuer
DENSELBEN Player laufen und sich beim MPD-Toggle gegenseitig ins Gehege kommen (z.B. ein Lauf
schaltet MPD gerade aus, waehrend der andere wieder an schaltet). Kosten: max. ~25s Wartezeit falls
wirklich zwei Ausloeser gleichzeitig feuern - vernachlaessigbar gegenueber den Minuten-Zeitskalen
des restlichen Systems.]

[20.09.2026: Beide get_devices+get_sinks-Aufrufpaare (Erst- und Zweitpruefung) auf den kombinierten
rest_command.bt_audio_get_state (GET /api/state) umgestellt - halbiert die Anzahl der REST-Calls pro
Lauf, keine funktionale Aenderung.]

[20.09.2026 KRITISCHER FIX: Bei der get_state-Umstellung blieben an beiden Pruefpunkten (Erst- und
Zweitpruefung) alte devices_result/sinks_result-Variablen-Schritte liegen, die device/sink sofort
wieder auf none zurücksetzten (diese Variablen existierten seit der Umstellung nicht mehr). Folge:
bt_healthy/sink_healthy waren IMMER false, die Schutzbedingung griff nie, das Script nahm bei JEDEM
Lauf den Reparaturzweig, und device.mpd_port schlug fehl (device=none) - das erzeugte die real
beobachteten 'Failed to update settings: Expecting value' Fehler alle ~5 Min fuer alle 3 Geraete.
Beide verwaisten Schritte entfernt - device/sink werden jetzt nur noch korrekt aus state_result
berechnet. [Nachbesserung: bei der ersten Fix-Runde wurde versehentlich der KORREKTE state_result-
Schritt geloescht statt des fehlerhaften devices_result-Schritts (Index-Verschiebung falsch
berechnet) - jetzt per Inhaltspruefung (enthaelt 'devices_result') gezielt korrigiert, statt per
Index.] [Endgueltig korrigiert: fehlenden device/sink-Berechnungsschritt (aus state_result) in der
Zweitpruefung wieder eingefuegt, der durch die vorherigen zwei fehlerhaften Korrekturversuche
versehentlich ganz entfernt worden war.]

[21.09.2026: Alias von 'Radiostream reparieren (Ultralight)' auf 'Radiostream Diagnose' geaendert -
'ultralight' klang nach minimal, ist aber inzwischen die ausgefeilteste Stufe (Sink-Check,
Doppelpruefung, intelligente Connect/Force-Logik, Retries). Entity-ID/Storage-Key bewusst
UNVERAENDERT gelassen (reine Kosmetik, kein Risiko wie bei der fruaeheren 's'-Umbenennungshistorie).

[23.09.2026 KRITISCHER LOGIK-FIX: Die if/then/else-Bedingung fuer 'BT gesund -> MPD-Toggle, BT nicht
gesund -> delegieren' war VERTAUSCHT (if bt_healthy delegierte faelschlich an BT-Reconnect, else
machte MPD-Toggle bei nicht-gesundem BT) - jetzt korrigiert auf 'if not bt_healthy -> delegieren,
else -> MPD-Toggle+Reload', wie urspruenglich dokumentiert und beabsichtigt. Gefunden bei einer
angeforderten vollstaendigen Logik-Audit aller Stufen.

[23.09.2026 KORREKTUR DES VORHERIGEN FIXES: der Fix von vorhin hatte Bedingung UND Zweige
gleichzeitig invertiert und war damit wirkungslos - der Block ist jetzt eindeutig neu aufgebaut:
'not bt_healthy' -> BT-Reconnect (mit Warten auf dessen Ende), sonst MPD-Toggle+Reload. Ausserdem:
Wartezeit nach Reparatur 3s -> 10s, und nach jedem BT-Reconnect-Aufruf (Delegation und Retries) wird
per wait_template auf dessen Ende gewartet statt blind weiterzulaufen.]

[25.09.2026: Jeder Retry ruft nach BT-Reconnect zusaetzlich script.radiostream_mpd_sicherstellen auf
(mit Warten auf dessen Ende). Vorher blieb die Diagnose haengen, wenn die Box per Bluetooth
zurueckkam, der MPD-Dienst aber fehlte (am 25.09. bei 87.5): BT-Reconnect sah eine gesunde
Verbindung und tat nichts, einen MPD-Neustart gab es nur im ersten Zweig.]

[06.10.2026: Sink-Abfrage nur noch, wenn der Player 'playing' meldet. Vor jeder der beiden
Pruefungen wird der Player-Zustand gemerkt (mit_sinks): bei 'playing' wie bisher bt_audio_get_state
(inkl. Sinks), sonst nur bt_audio_get_devices - kein Stocken auf den gesunden Boxen, waehrend eine
Box ausgefallen ist. Hintergrund: die Sink-Daten gehen nur in die Entscheidung ein, wenn der Player
'playing' ist; fuer die Wahl BT-Reconnect vs. MPD-Toggle zaehlt allein der Bluetooth-Status, und
get_devices liefert connected/has_transport/mpd_port ebenfalls (live geprueft). Doppelpruefung
unveraendert. Einzige Verhaltensaenderung: wird der Player genau waehrend einer Abfrage ohne Sink-
Daten von selbst 'playing' und ist Bluetooth gesund, wird nicht eingegriffen (vorher entschied in
diesem Moment der Sink-Zustand).]

[08.10.2026: device/sink-Vorlagen in beiden Pruefungen um '| default(none)' ergaenzt. Ohne Sink-
Daten (get_devices-Pfad) lieferte '| first' auf einer leeren Liste bei jedem Lauf die Log-Warnung
'No first item, sequence was empty'. Ergebnis der Pruefung unveraendert: fehlender Sink bzw.
fehlendes Geraet gilt weiter als nicht gesund.]

### Radiostream Voll-Reparatur

`script.radiostream_reparieren`

Schaltet die Bluetooth-Steckdose(n) kurz aus, startet waehrend sie noch aus sind das Bluetooth Audio
Manager (stabil) neu, und schaltet die Steckdose(n) danach wieder ein. Feld 'player' optional: leer
= alle drei (87.5/97.0/105.9) nacheinander mit 20s Abstand - fuer Totalausfaelle; gesetzt
(97_0/105_9/87_5) = nur die eine betroffene Steckdose. Der Add-on-Neustart selbst betrifft immer
alle drei gemeinsam (laesst sich nicht trennen). Laedt am Ende die drei MPD-Config-Entries einzeln
(nicht als Liste) parallel neu. [Neu angelegt 12.09.2026 von Claude nach Registrierungs-Bug post-
Neustart, Config identisch zur Vorversion: Steckdosen-Zuordnung zentral aus
input_text.radiostream_dose_switch_map (JSON).]

[20.09.2026: abschliessendes reload_config_entry von parallel auf sequenziell (3s Abstand)
umgestellt, vorsorglich gegen dieselbe Race-Condition-Klasse wie beim Mixing-Bug.]

[21.09.2026 Konsistenz-Fix: die 3 reload_config_entry-Aufrufe nutzten bisher wortwoertlich
eingetragene entry_ids statt radiostream_mpd_entry_map - jetzt per entry_map[player]-Template aus
der zentralen Map bezogen, analog zu switch_map. Verhindert eine kuenftige Divergenz zwischen Map
und Script, z.B. beim geplanten FM02-Tausch.

[21.09.2026: Alias von 'Radiostream reparieren' auf 'Radiostream Voll-Reparatur' geaendert -
Symmetrie zur Dashboard-Sektion 'Volle Reparatur' und klare Abgrenzung zu Diagnose/BT-Reconnect.
Entity-ID/Storage-Key bewusst UNVERAENDERT gelassen.

[22.09.2026: beide Steckdosen-Aus-Dauern (Einzelplayer- und Alle-Drei-Zweig) von 15 auf 30 Sekunden
verdoppelt - analog zum selben Fix in radiostream_steckdose_zyklieren, ausgelöst durch einen
hartnaeckigen 87.5-Ausfall am 22.09.]

[25.09.2026: (a) Alle-drei-Zweig schaltet am Ende nur die Steckdosen wieder ein, die vorher an waren
(vorher_an) - bewusst ausgeschaltete Boxen bleiben aus. (b) Abschliessend wird fuer jede betroffene
Box script.radiostream_mpd_sicherstellen aufgerufen, da das Add-on nach verzoegertem Reconnect den
MPD-Dienst oft nicht mitstartet (#316).]

[13.10.2026: Storage-Key von 'radiostreams_reparieren' auf 'radiostream_reparieren' angeglichen
(jetzt identisch mit der Entity-ID script.radiostream_reparieren) - Watchman konnte das Script
vorher keiner Entitaet zuordnen. Inhalt unveraendert, veralteter Registry-Name 'Radiostream
reparieren' entfaellt, angezeigt wird der Alias.]

[01.11.2026 (Claude): Add-on-Neustart auf das gepatchte Add-on 1b3a7c56_bluetooth_audio_manager
(Chrischan-Fork) umgestellt; das alte d4261985 ist gestoppt und bleibt als Rueckweg installiert.]

[06.11.2026 (Claude): das alte Add-on d4261985 wurde deinstalliert; die Neustart-Schritte zeigen
ausschliesslich auf 1b3a7c56_bluetooth_audio_manager.]

### Radiostream BT-Reconnect

`script.radiostream_reparieren_light`

Leichte Variante von script.radiostream_reparieren. UEBERARBEITET 21.09.2026: prueft jetzt erst den
tatsaechlichen Verbindungsstatus (rest_command.bt_audio_get_state) und waehlt je Geraet die mildere
Aktion: ist das Geraet laut Add-on bereits getrennt (connected=false), wird nur ein normaler
rest_command.bt_audio_connect versucht (kein unnoetiger Force-Disconnect eines ohnehin schon
getrennten Geraets). NUR wenn das Geraet sich faelschlich noch fuer verbunden haelt (connected=true,
aber offensichtlich nicht richtig funktionierend - deshalb wurde dieses Script ueberhaupt
aufgerufen), wird der haertere rest_command.bt_audio_force_reconnect als letztes Mittel eingesetzt.
Grund: force_reconnect erzwingt einen Disconnect+Reconnect-Zyklus - bei einem bereits getrennten
Geraet ist der Disconnect-Teil unnoetig scharf und kann einen laufenden natuerlichen Reconnect-
Versuch des Add-ons stoeren, statt ihm Zeit zu geben. Feld 'player' optional: leer = alle drei
Geraete nacheinander (5s Abstand), gesetzt = nur das eine Geraet. continue_on_error je Geraet, damit
ein einzelner BT-Fehler andere nicht blockiert. MAC-Adressen zentral aus
input_text.radiostream_address_map (JSON).

[21.09.2026: Alias von 'Radiostream reparieren (Light)' auf 'Radiostream BT-Reconnect' geaendert -
beschreibt praeziser was es tut (Connect/Force-Reconnect). Entity-ID/Storage-Key bewusst
UNVERAENDERT gelassen.

[23.09.2026 Race-Fix: Modus von 'single' auf 'queued' (max 5) umgestellt - bei 'single' konnte ein
Retry-Aufruf aus der Retry-Schleife von radiostream_reparieren_ultralight (3s nach dem ersten
Delegations-Aufruf) still verworfen werden, falls der erste Lauf noch nicht fertig war. 'queued'
stellt sicher, dass jeder angeforderte Lauf irgendwann tatsaechlich ausgefuehrt wird, statt
geraeuschlos zu verpuffen. Gefunden bei der vollstaendigen Logik-Audit vom 23.09.2026.

[23.09.2026 GESUNDHEITS-SCHUTZ: Entscheidung jetzt dreistufig statt zweistufig - (1)
verbunden+Transport = gesund -> nichts tun (nur Logbuch), (2) verbunden ohne Transport = halbtot ->
force_reconnect, (3) getrennt/unbekannt -> connect. Vorher loeste jede bestehende Verbindung einen
Force-Reconnect aus, auch eine voellig gesunde - live passiert beim Testaufruf am 23.09.2026
(87.5+105.9 getrennt) und theoretisch auch bei jedem Diagnose-Retry kurz nach einem erfolgreichen
Reload.]

[23.09.2026: Abfrage von bt_audio_get_state auf bt_audio_get_devices umgestellt. Das Script braucht
nur die Bluetooth-Daten; das Auslesen der PulseAudio-Sinks (Teil von get_state) verursacht
nachweislich ein hoerbares Stocken (gezielter A/B-Test: get_devices unauffaellig, get_sinks
stockt).]

[13.10.2026: Storage-Key von 'radiostreams_reparieren_light' auf 'radiostream_reparieren_light'
angeglichen (jetzt identisch mit der Entity-ID script.radiostream_reparieren_light). Inhalt
unveraendert, veralteter Registry-Name 'Radiostream reparieren (Light)' entfaellt, angezeigt wird
der Alias.]
