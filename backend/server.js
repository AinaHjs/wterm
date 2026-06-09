import makeWASocket, {useMultiFileAuthState, DisconnectReason} from "@whiskeysockets/baileys";
import { WebSocketServer } from "ws";
import pino from 'pino';
import QRCode from 'qrcode-terminal';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from "url";


/** INITIALISATION DES VARIABLES GLOBALES */
let pythonClient = null;
let sock = null;

const __filename = fileURLToPath(import.meta.url)
const ROOT_DIR = path.dirname(__filename);

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

        // Check connection state
        if (connection === 'open' && pythonClient) {
            console.log(`[+] Connection to whatsapp established...`);
            console.log(`[+] Trying to send the connexion status to wterminal.`)
            pythonClient.send(JSON.stringify({
                type: 'STATUS',
                data: 'CONNECTED'
            }))
    
        // Check logout reason and try to reconnect if there was an error.
        } else if (connection === 'close') {
            const need_to_reconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;

            if(need_to_reconnect) {
                console.log(`[+] Trying to reconnect whatsapp.`)
                connectToWA();
            }
        }
    })

    // Automatically save creds
    sock.ev.on('creds.update',saveCreds);

    // Listen on messages.upsert from whatsapp.
    sock.ev.on('messages.upsert', async (m) => {
        // For all messages on the websocket
        for (const msg of m.messages){
            // Is the type of this message a 'notify' ?
            if (m.type === 'notify'){
                // Is the message from me?
                if (!msg.key.fromMe){
                    const jID = msg.key.remoteJid;
                    const defaultName = msg.pushName || "Unknown";
                    const text = msg.message?.conversation || msg.message?.extendedTextMessage;
                    const msgDate = msg.messageTimestamp;
                    // Is the sender on my contact list?
                    let isOnMyContact = false;
                    let senderContactName = "Unknown";
                    try{
                        const contactsFilePath = path.join(ROOT_DIR,'frontend','contacts.json');
                        const contactData = await fs.readFile(contactsFilePath, "utf-8");
                        const contacts = JSON.parse(contactData);
                        // Look for remoteJID inside the contacts.json
                        for (const [contactName, contactJid] in Object.entries(contacts)){
                            if (contactJid === jID){
                                isOnMyContact = true;
                                senderContactName = contactName;
                                break;
                            }
                        }
                    } catch (error){
                        console.log(`[!] Contact error : ${error}`);
                    } 

                    // If sender is on my contact list
                    if (isOnMyContact){
                        // Is there a python client connected to the websocket
                        if(pythonClient){
                            const newMsgFilePath = path.join(ROOT_DIR, "frontend", "Messages", `${senderContactName.toLowerCase()}.txt`);
                            const newMessageModel = `${msgDate}-${senderContactName}-${text}.`
                            const messagePayload = {
                                event: 'NEW_MESSAGE',
                                sender_name : defaultName,
                                sender_id : jID,
                                text: text,
                                date : msgDate,
                            };
                            // Try to write the message on dedicated file and alert the wterminal user
                            try{
                                // Write the message on dedicated file
                                fs.appendFile(newMsgFilePath, newMessageModel, "utf8")
                                // Alert user
                                pythonClient.send(JSON.stringify(messagePayload));
                            } catch(error){
                                console.log(`[!] Message processing error : ${error}`);
                            }
                        } else if (!pythonClient) {
                            const newMsgListFilePath = path.join(ROOT_DIR, "Frontend", "Messages", "newMessageList.txt");

                        }
                    }
                }
            }

        }

                    // Write new message on user_message_file and list_new_message_file
                    const newMsgFilePath = path.join(ROOT_DIR, "Frontend", "Messages", `${senderContactName.toLowerCase()}.txt`);
                    const newMsgListFilePath = path.join(ROOT_DIR, "Frontend", "Messages", "newMessageList.txt");
                    const newMessageModel = `${msgDate}-${senderContactName}-${text}.`

                    try {
                        await fs.appendFile(newMsgListFilePath, `[${msgDate}] : New message from ${senderContactName} \n>>> ${text}.`)
                    } catch (err) {
                        console.log(`[!] Error writing message file : ${err}`)
                    }
                }
            }
        }
    })
}

/** INITIALISATION DU WEBSOCKET POUR PYTHON ET NODE */
function create_ws() {
    const wss = new WebSocketServer({port:8088});
    console.log(`[+] The backend server is listenning on port : 8088`)

    // Manage inbound connection
    wss.on('connection', async (ws) => {
        console.log(`[+] Wterminal client connected successfully...`);
        pythonClient = ws

        // Send status if you are connected to whatsapp
        if (sock && sock.user) {
            ws.send(JSON.stringify({type: 'STATUS', data: 'CONNECTED'}));
        }

        // When wterminal client send message via websocket
        ws.on('message', async (wsMessage) => {
            try {
                const data = JSON.parse(wsMessage); 
    
                if (data.action === 'SEND_MESSAGE' && data.to && data.text) {
                    if (sock){
                        await sock.sendMessage(data.to, {text:data.text});
                        console.log(`[+] Message sent to : ${data.to}`);
                    }
                } else {
                    console.log("[!] Whatsapp socket not initialized yet.");
                }
            } catch (err) {
                console.error(`[!] Socket error : ${err}`);
            }
        });

        // When wterminal client is disconnected
        ws.on('close', () => {
            console.log(`[-] Wterminal client disconnected successfully...`);
            pythonClient = null;
        });

    });
}


create_ws();
connectToWA();


