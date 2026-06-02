# RFID-OSC-Reader
Code für ein interaktives Spiel im Wetterau Museum, bei dem RFID-Figuren auf verschiedene Standorte gestellt werden.
Die Erarbeitung geschieht im Rahmen des Moduls "Anwendungen von Medientechnologien" für das Wetterau Museum in Friedberg.

### System-Übersicht:
- **Writer**: Programm zum Beschreiben von NFC-Tags mit Figur-IDs
- **Sender**: Arduino an jedem Spielstandort, liest Figur-ID und sendet mit Standort-ID
- **Receiver**: Empfängt Figur-ID und Standort-ID per OSC

### RFID-Datenstruktur:
- **UID**: Eindeutige Kartennummer (Hardware-ID)
- **Chip ID**: Figur-ID (auf dem NFC-Tag gespeichert, Block 1-2) - wer/was auf dem Chip ist
- **Location ID**: Standort-ID (hardcoded im Arduino) - wo sich der Sensor befindet

### Aktuell offene Aufgaben:
- Content erstellen
- 3D Modelle erstellen & drucken
- Tisch konzipieren
- Tisch bauen
- Kuppel organisieren
- OSC Nachrichten an Medienserver schicken
- OSC Nachrichten mit Content verbinden
- TouchDesigner oder Pixera?
- Projektoren auf Kuppel mappen mit Edge Blending
