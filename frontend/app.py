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

    def do_chats(self, arg):
        """Affiche la liste des discussions récentes. Usage: chats"""
        print("[*] Récupération des discussions...")
        # Plus tard, on demandera la liste au backend via WebSocket
        print("1. +33612345678 (Sacha)")
        print("2. +33698765432 (Maman)")

    def do_read(self, arg):
        """Lit l'historique d'une discussion. Usage: read <numéro_ou_JID>"""
        if not arg:
            print("[-] Erreur: Spécifiez un numéro. Exemple: read 1")
            return
        print(f"[*] Lecture des derniers messages de la discussion {arg}...")
        # Simulation
        print("[Sacha]: Salut, t'es là ?")
        print("[Moi]: Ouaip, en plein dev.")

    def do_send(self, arg):
        """Envoie un message. Usage: send <numéro> <votre message>"""
        parts = arg.split(" ", 1)
        if len(parts) < 2:
            print("[-] Erreur: Syntaxe incorrecte. Exemple: send 1 Salut ça va ?")
            return
        
        target, text = parts[0], parts[1]
        print(f"[*] Envoi du message à [{target}]...")

        if self.ws:
            payload = {
                "action": "send_message",
                "to": "1234567890@s.whatsapp.net",  # Géré dynamiquement plus tard
                "text": text
            }
            # On utilise la boucle réseau d'arrière-plan pour envoyer de manière thread-safe
            asyncio.run_coroutine_threadsafe(self.ws.send(json.dumps(payload)), self.loop)
            print("[+] Message envoyé avec succès.")
        else:
            print("[-] Erreur: Le backend est hors-ligne.")

    def do_exit(self, arg):
        """Quitte proprement l'application. Usage: exit"""
        print("[*] Fermeture de wterminal...")
        return True  # Retourner True arrête la boucle cmd.Cmd

    # Alias pour quitter
    do_quit = do_exit


if __name__ == '__main__':
    try:
        wterminal().cmdloop()
    except KeyboardInterrupt:
        print("\n[*] Interruption détectée. Fermeture.")