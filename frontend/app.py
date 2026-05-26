#!/usr/bin/env python3

import asyncio
import cmd
import threading
import websockets
import json


class wterminal(cmd.Cmd):
    intro = "Welcome do WTERMINAL : Tape 'Helps' or '?' for more information."
    prompt = 'wterminal >_'

    def __init__(self):
        super().__init__()
        self.ws = None
        self.loop = asyncio.new_event_loop()

        # Lancer le websockets dans un thread séparé en tâche de fond
        # Pour ne pas bloquer l'interpreteur de commande.

        self.net_thread = threading.Thread(target=self.start_network_loop,daemon=True)
        self.net_thread.start()

    def start_network_loop(self):
        """ Pour démarrer une boucle asynchrone pour le réseau """
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.listen_to_backend())

    async def listen_to_backend(self):
        uri = 'ws://localhost:8080'
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.ws = websocket
                    print("\n[+] Connected to the W backend.")
                    print(self.pro , end="", flush=True)

                    async for message in websocket:
                        data  = json.loads(message)
                        if data.get("type") == "new_message":
                            sender = data.get("from")
                            text = data.get("text")

                            print(f"\n[New message] {sender} : {text}")
                            print(self.prompt, end="", flush=True)

            except Exception:
                self.ws = None
                await asyncio.sleep(3)
