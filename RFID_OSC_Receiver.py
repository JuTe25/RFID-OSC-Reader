#!/usr/bin/env python3
"""
OSC RFID Receiver for Arduino + Ethernet Shield
Empfängt RFID-Daten (UID, Vorname, Nachname) vom Arduino
"""

import sys
from pythonosc import dispatcher, osc_server
from pythonosc.osc_server import ThreadingOSCUDPServer
import threading
from datetime import datetime

# ============= Configuration =============
LISTEN_IP = "0.0.0.0"           # Höre auf allen Interfaces
LISTEN_PORT = 8000              # Muss mit Arduino Port übereinstimmen
OSC_ADDRESS = "/rfid"           # OSC Address Pattern vom Arduino

# ============= Global Variables =============
running = True
card_data = []

# ============= OSC Message Handler =============
def rfid_handler(address, *args):
    """
    Handler für eingehende OSC Messages
    WICHTIG: *args wird als Tuple übergeben!
    
    Args:
      address: OSC Address (/rfid)
      *args: Tuple mit (uid, firstName, lastName)
    """
    print(f"\nDebug - Address: {address}")
    print(f"Debug - Args type: {type(args)}")
    print(f"Debug - Args: {args}")
    print(f"Debug - Args length: {len(args)}")
    
    if len(args) >= 3:
        uid = args[0]
        first_name = args[1]
        last_name = args[2]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*60)
        print(f"[{timestamp}] RFID Card Detected!")
        print("="*60)
        print(f"UID:       {uid}")
        print(f"Vorname:   {first_name}")
        print(f"Nachname:  {last_name}")
        print("="*60)
        
        # Speichere Daten für weitere Verarbeitung
        card_entry = {
            'timestamp': timestamp,
            'uid': uid,
            'firstName': first_name,
            'lastName': last_name
        }
        card_data.append(card_entry)
        
        # Rufe Callback-Funktion auf (optional)
        on_card_detected(card_entry)
    else:
        print(f"⚠ Warning: Expected 3 arguments, got {len(args)}")
        print(f"  Args: {args}")


def on_card_detected(card_info):
    """
    Callback-Funktion, wird aufgerufen wenn Karte erkannt wird
    """
    print(f"\n→ Processing: {card_info['firstName']} {card_info['lastName']} ({card_info['uid']})")


def setup_osc_server():
    """
    Initialisiert und startet den OSC Server
    """
    print("="*60)
    print("OSC RFID Receiver - Arduino Ethernet Shield")
    print("="*60)
    print(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
    print(f"OSC Address: {OSC_ADDRESS}")
    print("Waiting for RFID cards...\n")
    
    # Erstelle Dispatcher
    disp = dispatcher.Dispatcher()
    disp.map(OSC_ADDRESS, rfid_handler)
    
    # Erstelle Server
    server = ThreadingOSCUDPServer((LISTEN_IP, LISTEN_PORT), disp)
    
    # Starte Server in eigenem Thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return server, server_thread


def display_statistics():
    """
    Zeigt Statistiken der empfangenen Karten
    """
    if card_data:
        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Total Cards Read: {len(card_data)}")
        print("\nCard Log:")
        for i, card in enumerate(card_data, 1):
            print(f"{i}. [{card['timestamp']}] {card['firstName']} {card['lastName']} - UID: {card['uid']}")
        print("="*60 + "\n")
    else:
        print("\n⚠ No cards read yet.\n")


def main():
    """
    Hauptfunktion
    """
    global running
    
    try:
        # Starte OSC Server
        server, server_thread = setup_osc_server()
        
        # Warte auf Benutzereingaben
        print("Press ENTER to show statistics")
        print("Type 'quit' to exit\n")
        
        while running:
            try:
                user_input = input().strip().lower()
                
                if user_input == 'quit' or user_input == 'exit':
                    running = False
                    print("\nShutting down...")
                    break
                elif user_input == '' or user_input == 'stats':
                    display_statistics()
                elif user_input == 'clear':
                    card_data.clear()
                    print("Card history cleared.\n")
                else:
                    print("Commands: [ENTER] stats, 'clear', 'quit'\n")
                    
            except KeyboardInterrupt:
                running = False
                print("\nInterrupted by user")
                break
        
        # Zeige finale Statistiken
        display_statistics()
        
    except OSError as e:
        print(f"Error: {e}")
        print(f"Could not bind to {LISTEN_IP}:{LISTEN_PORT}")
        print("Check if the port is already in use or if you have the right permissions.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
