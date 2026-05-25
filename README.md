# # WhatsApp Terminal Edition

---

# Un client WhatsApp léger en ligne de commande pour serveur Linux

---

Il utilise une architecture Client/Serveur séparant la gestion du protocole WhatsApp (via Baileys) et l'interface utilisateur textuelle (TUI).

# # Architecture

**\* Backend : ** Node.js avec `@whiskeysockets/baileys` qui tourne en arrière-plan.
**\* Frontend : ** Interface TUI (Terminal User Interface) connectée via WebSockets.

# # Installation & Lancement

1. Cloner le dépôt.
2. Configurer le backend : `cd backend && npm install`.
3. Lancer le serveur et scanner le QR Code : `node index.js`.
4. Lancer l'interface dans un autre terminal.
