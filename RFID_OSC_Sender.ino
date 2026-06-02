/*
 * Initial Author: ryand1011 (https://github.com/ryand1011)
 * Modified: OSC Ethernet Integration
 *
 * Reads data from MFRC522 RFID reader and sends via OSC over Ethernet Shield
 * FIXED: Pin conflicts resolved!
 */

#include <SPI.h>
#include <MFRC522.h>
#include <Ethernet.h>
#include <EthernetUdp.h>
#include <OSCMessage.h>

// ============= RFID Pin Configuration (FIXED!) =============
// WICHTIG: Nicht Pin 10 verwenden! (Ethernet Shield braucht Pin 10)
#define RST_PIN         9           // MFRC522 Reset pin
#define SS_PIN          8           // MFRC522 SS (SDA) pin - CHANGED FROM 10 TO 8!

MFRC522 mfrc522(SS_PIN, RST_PIN);

// ============= Ethernet Configuration =============
byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};
IPAddress ip(192, 168, 1, 177);
unsigned int localPort = 8888;

EthernetUDP Udp;

// ============= OSC Target Configuration =============
IPAddress outIp(192, 168, 1, 42);
int outPort = 8000;

// ============= Device Configuration =============
const String LOCATION_ID = "LOCATION_01";  // Feste Standort-ID (Arduino an diesem Standort)

// ============= Timing =============
unsigned long lastCardRead = 0;
const unsigned long cardReadDelay = 1000;

//*****************************************************************************************//
void setup() {
  Serial.begin(9600);
  
  // Setze Pin 10 als Output (für Ethernet Shield)
  pinMode(10, OUTPUT);
  digitalWrite(10, HIGH);  // Deselect Ethernet initially
  
  // Setze Pin 8 als Output (für MFRC522)
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);   // Deselect MFRC522 initially
  
  delay(100);
  
  Serial.println(F("\n\n=== Arduino RFID-OSC Sender ==="));
  Serial.println(F("Initializing Ethernet with static IP..."));
  
  // Ethernet initialisieren mit einer festen IP-Adresse (kein DHCP)
  Ethernet.begin(mac, ip);
  
  Serial.print(F("Ethernet OK - IP: "));
  Serial.println(Ethernet.localIP());
  
  // UDP initialisieren
  Udp.begin(localPort);
  Serial.print(F("UDP Port: "));
  Serial.println(localPort);
  
  // RFID initialisieren
  Serial.println(F("Initializing SPI..."));
  SPI.begin();
  
  Serial.println(F("Initializing MFRC522..."));
  mfrc522.PCD_Init();
  
  // Prüfe MFRC522 Version
  byte version = mfrc522.PCD_ReadRegister(MFRC522::VersionReg);
  Serial.print(F("MFRC522 Version: 0x"));
  Serial.println(version, HEX);
  
  if (version == 0x00 || version == 0xFF) {
    Serial.println(F("ERROR: MFRC522 not found! Check wiring."));
    while (true);  // Stop here
  }
  
  Serial.print(F("OSC Target: "));
  Serial.print(outIp);
  Serial.print(F(":"));
  Serial.println(outPort);
  
  Serial.println(F("\n=== Ready! Scan a card... ===\n"));
}

//*****************************************************************************************//
void loop() {
  // Ethernet Verbindung prüfen
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println(F("Ethernet link is OFF"));
    delay(1000);
    return;
  }

  // Prüfe, ob neue Karte vorhanden ist
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  Serial.println(F("Card detected!"));

  // Wähle eine der Karten
  if (!mfrc522.PICC_ReadCardSerial()) {
    Serial.println(F("Failed to read card serial"));
    return;
  }

  // Debouncing
  unsigned long now = millis();
  if (now - lastCardRead < cardReadDelay) {
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    return;
  }
  lastCardRead = now;

  Serial.println(F("\n**Card Detected:**"));
  
  // Karten-Details
  mfrc522.PICC_DumpDetailsToSerial(&(mfrc522.uid));

  // ============= Daten lesen =============
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;
  
  byte buffer[18];
  byte block;
  byte len = 18;
  MFRC522::StatusCode status;
  
  String chipID = "";

  // --- GET CHIP ID / FIGURE ID (Block 1) ---
  block = 1;
  status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, 1, &key, &(mfrc522.uid));
  if (status == MFRC522::STATUS_OK) {
    status = mfrc522.MIFARE_Read(block, buffer, &len);
    if (status == MFRC522::STATUS_OK) {
      for (uint8_t i = 0; i < 16; i++) {
        if (buffer[i] != 32 && buffer[i] != 0) {
          chipID += (char)buffer[i];
        }
      }
      Serial.print(F("Chip ID (Figure): "));
      Serial.println(chipID);
    } else {
      Serial.print(F("Read error: "));
      Serial.println(mfrc522.GetStatusCodeName(status));
    }
  } else {
    Serial.print(F("Auth error: "));
    Serial.println(mfrc522.GetStatusCodeName(status));
  }

  // --- USE FIXED LOCATION ID ---
  Serial.print(F("Location ID (Station): "));
  Serial.println(LOCATION_ID);

  // --- GET UID ---
  String UID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    UID += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
    UID += String(mfrc522.uid.uidByte[i], HEX);
  }
  Serial.print(F("UID: "));
  Serial.println(UID);

  // ============= OSC Message versenden =============
  sendOSCMessage(chipID, LOCATION_ID, UID);

  Serial.println(F("**End Reading**\n"));

  // Cleanup
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  delay(1000);
}

//*****************************************************************************************//
void sendOSCMessage(String chipID, String locationID, String uid) {
  
  Serial.println(F("Sending OSC Message..."));
  
  // Erstelle OSC Message
  OSCMessage msg("/rfid");
  msg.add(uid.c_str());
  msg.add(chipID.c_str());
  msg.add(locationID.c_str());

  // Versende via UDP
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp);
  Udp.endPacket();
  msg.empty();

  Serial.println(F("✓ OSC Message sent!"));
  Serial.print(F("  Address: /rfid"));
  Serial.print(F(" | Args: "));
  Serial.print(uid);
  Serial.print(F(", "));
  Serial.print(chipID);
  Serial.print(F(", "));
  Serial.println(locationID);
}

//*****************************************************************************************//
