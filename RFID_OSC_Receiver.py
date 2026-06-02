#!/usr/bin/env python3
"""
OSC RFID Receiver für Museum-Spiel
Empfängt Chip ID (Figur) und Standort ID vom Arduino
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
      *args: Tuple mit (uid, chipID, locationID)
    """
    print(f"\nDebug - Address: {address}")
    print(f"Debug - Args type: {type(args)}")
    print(f"Debug - Args: {args}")
    print(f"Debug - Args length: {len(args)}")
    
    if len(args) >= 3:
        uid = args[0]
        chip_id = args[1]
        location_id = args[2]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*60)
        print(f"[{timestamp}] Figure Detected!")
        print("="*60)
        print(f"UID:           {uid}")
        print(f"Figure ID:     {chip_id}")
        print(f"Location ID:   {location_id}")
        print("="*60)
        
        # Speichere Daten für weitere Verarbeitung
        card_entry = {
            'timestamp': timestamp,
            'uid': uid,
            'chipID': chip_id,
            'locationID': location_id
        }
        card_data.append(card_entry)
        
        # Rufe Callback-Funktion auf (optional)
        on_card_detected(card_entry)
    else:
        print(f"⚠ Warning: Expected 3 arguments, got {len(args)}")
        print(f"  Args: {args}")


def on_card_detected(card_info):
    """
    Callback-Funktion, wird aufgerufen wenn Figur erkannt wird
    """
    print(f"\n→ Processing: Figure {card_info['chipID']} at Location {card_info['locationID']} ({card_info['uid']})")


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
