import makeWASocket, {useMultiFileAuthState, DisconnectReason} from "@whiskeysockets/baileys";
import { WebSocketServer } from "ws";
import pino from 'pino';
import QRCode from 'qrcode-terminal';




/** INITIALISATION DES VARIABLES GLOBALES */
let pythonClient = null;
let sock = null;

/** INITIALISATION DU WEBSOCKET WA AVEC BAILEYS */
async function connectToWA() {
    const {state, saveCreds} = await useMultiFileAuthState('auth_info_baileys');

    sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        logger: pino({level : 'silent'}),
    })

    /** Gérer les connnections */
    sock.ev.on('connection.update', (update) => {
        const {connection, lastDisconnect, qr} = update;

        if(qr && pythonClient) {
            pythonClient.send(JSON.stringify({
                type: "QR",
                data: qr
            }))
        }

        // Vérifier l'état de la connexion
        if (connection === 'open' && pythonClient) {
            console.log(`[+] Link to WA established...`);
            console.log(`[+] Trying to send the connexion status to the python app`)
            pythonClient.send(JSON.stringify({
                type: 'STATUS',
                data: 'CONNECTED'
            }))
        } else if (connection === 'close') {
            const need_to_reconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;

            if(need_to_reconnect) {
                console.log(`[+] Trying to reconnect...`)
                connectToWA();
            }
        }
    })

    /** Sauvegarde automatique des creds */
    sock.ev.on('creds.update',saveCreds);

    sock.ev.on('messages.upsert', async (m) => {
            if (m.type === 'notify') {
                for (const msg of m.messages) {
                    if (!msg.key.fromMe) {
                        const jID = msg.key.remoteJid;
                        const name = msg.pushName;
                        const text = msg.message?.conversation || msg.message.extendedTextMessage;

                        if (text && pythonClient) {
                            const messageObject = {
                                event: 'NEW_MESSAGE',
                                sender_name : name,
                                sender_id : jID,
                                text: text,
                                date : msg.messageTimestamp,
                            };
                            const messagePayload = JSON.stringify(messageObject);
                            pythonClient.send(messagePayload);
                        }
                    }
                }
            }
    })
}

/** INITIALISATION DU WEBSOCKET POUR PYTHON ET NODE */
function create_ws() {
    const wss = new WebSocketServer({port:8088});
    console.log(`[+] The node server is listenning on port : 8088`)

    /** Manage inbound connexion */
    wss.on('connection', async (ws) => {
        console.log(`[+] Python client connected successfully...`);
        pythonClient = ws
        connectToWA();

        // On message
        ws.on('message', async (message) => {
            try {
                const parsed_message = JSON.parse(message); 
                
                if (parsed_message.action === 'SEND_MESSAGE' && parsed_message.to && parsed_message.text) {
                    await sock.sendMessage(parsed_message.to, {text:parsed_message.text})
                    console.log(`[+] Message sent to : ${parsed_message.to}`);
                }
            } catch (error) {
                console.error(`[!] An error occured : ${error}`);
            }
        });

        // On close
        ws.on('close', () => {
            console.log(`[-] Python client disconnected successfully...`);
            pythonClient = null;
        });

    });
}


create_ws();


