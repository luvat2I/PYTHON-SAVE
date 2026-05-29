import sys
from proton import Message
from proton.utils import BlockingConnection, BlockingSender, BlockingReceiver

# Configuration
HOST = "ydgluva24q"
PORT = 8081
USERNAME = "xdev-jms-user"
PASSWORD = "xl4Jee%40ChangeIt1"  # mot de passe URL-encodé si vous l'incluez dans l'URL; 
                                # vous pouvez aussi construire l'URL sans encodage et proton acceptera user:pass séparés
ADDRESS = "jms.queue.XOSTIndexEventProcessQueue"  # destination passée au sender/receiver
WS_SCHEME = "amqp+ws"  # ou "amqp+wss" si TLS


# Payload binaire
PAYLOAD = {
  "objectDescriptors": {
    "id": "XFRAMEWORK-EVENT-BUSINESSOPERATION--001-PAC0005",
    "objectReference": {
      "objectKind": {
        "softwareCode": "XFRAMEWORK-EVENT",
        "objectType": "BusinessOperation",
        "objectSubType": ""
      },
      "objectId": "PAC0005"
    },
    "objectSource": {
      "uri": "",
      "objectSourceKind": {
        "type": "XFRAMEWORK-EVENT",
        "name": "001"
      }
    },
    "objectDescription": {
      "audit": {
        "creationUser": "001-svc-usr",
        "creationDateTime": {"year":2026,"month":5,"dayOfMonth":18,"hourOfDay":8,"minute":16,"second":24},
        "modificationUser": "001-svc-usr",
        "modificationDateTime": {"year":2026,"month":5,"dayOfMonth":18,"hourOfDay":8,"minute":16,"second":24}
      },
      "creationUserFullName":"001-svc-usr",
      "modificationUserFullName":"001-svc-usr",
      "objectFilterDate":{"year":2026,"month":5,"dayOfMonth":18,"hourOfDay":8,"minute":16,"second":24}
    },
    "objectKeyValues":["#EVENT_CATEGORY#BATCH"],
    "objectSecurityClasses":[[],[],[],[],[],[],[],[]],
    "objectSecurityBusinessObjects":[[],[]],
    "objectAttributes": "{\"status\":\"Échoué\",\"statusDescription_fr\":\"Échoué\",\"statusDescription_de\":\"Échoué\",\"statusDescription_it\":\"Échoué\",\"statusDescription_en\":\"Échoué\",\"server\":\"YDGLUVA24Q\",\"environment\":\"001\",\"softwareCode\":\"PAC-DESIGNER\",\"softwareDescription_fr\":\"PAC DESIGNER\",\"softwareDescription_de\":\"PAC DESIGNER\",\"softwareDescription_it\":\"PAC DESIGNER\",\"softwareDescription_en\":\"PAC DESIGNER\",\"groupId\":\"0000000000000000\",\"objectType\":\"Déploiement\",\"objectTypeDescription_fr\":\"Déploiement\",\"objectTypeDescription_de\":\"Déploiement\",\"objectTypeDescription_it\":\"Déploiement\",\"objectTypeDescription_en\":\"Déploiement\",\"objectSubType\":\"xframework-saas-function-create\",\"objectSubTypeDescription_fr\":\"xframework-saas-function-create\",\"objectSubTypeDescription_de\":\"xframework-saas-function-create\",\"objectSubTypeDescription_it\":\"xframework-saas-function-create\",\"objectSubTypeDescription_en\":\"xframework-saas-function-create\",\"type\":\"MAJ PAC\",\"typeDescription_fr\":\"MAJ PAC\",\"typeDescription_de\":\"MAJ PAC\",\"typeDescription_it\":\"MAJ PAC\",\"typeDescription_en\":\"MAJ PAC\",\"category\":\"BATCH\",\"categoryDescription_fr\":\"BATCH\",\"categoryDescription_de\":\"BATCH\",\"categoryDescription_it\":\"BATCH\",\"categoryDescription_en\":\"BATCH\",\"source\":\"XECM\",\"message\":\"Déploiement PAC via application PAC designer\",\"severity\":\"0\",\"severityDescription_fr\":\"0\",\"severityDescription_de\":\"0\",\"severityDescription_it\":\"0\",\"severityDescription_en\":\"0\",\"userName\":\"001-svc-usr\",\"userFullName\":\"001-svc-usr\",\"timestamp\":{\"year\":2026,\"month\":5,\"dayOfMonth\":18,\"hourOfDay\":8,\"minute\":16,\"second\":24},\"DateTime\":{\"year\":2026,\"month\":5,\"dayOfMonth\":18,\"hourOfDay\":8,\"minute\":16,\"second\":24},\"createDate_ddmmyyyy_dot\":\"18.05.2026\",\"createDate_ddmmyyyy_slash\":\"18/05/2026\",\"createDate_ddmmyyyy_dash\":\"18-05-2026\",\"createDate_mmddjyyyy_slash\":\"05/18/2026\",\"formattedEvent_fr\":\"\\u003cdiv class\\u003d\\u0027event-message\\u0027\\u003eDéploiement PAC via application PAC designer\\u003cdiv class\\u003d\\u0027message-content\\u0027\\u003ePAC-DESIGNER - Déploiement - MAJ PAC\\u003c/div\\u003e\\u003c/div\\u003e\",\"formattedEvent_de\":\"\\u003cdiv class\\u003d\\u0027event-message\\u0027\\u003eDéploiement PAC via application PAC designer\\u003cdiv class\\u003d\\u0027message-content\\u0027\\u003ePAC-DESIGNER - Déploiement - MAJ PAC\\u003c/div\\u003e\\u003c/div\\u003e\",\"formattedEvent_it\":\"\\u003cdiv class\\u003d\\u0027event-message\\u0027\\u003eDéploiement PAC via application PAC designer\\u003cdiv class\\u003d\\u0027message-content\\u0027\\u003ePAC-DESIGNER - Déploiement - MAJ PAC\\u003c/div\\u003e\\u003c/div\\u003e\",\"formattedEvent_en\":\"\\u003cdiv class\\u003d\\u0027event-message\\u0027\\u003eDéploiement PAC via application PAC designer\\u003cdiv class\\u003d\\u0027message-content\\u0027\\u003ePAC-DESIGNER - Déploiement - MAJ PAC\\u003c/div\\u003e\\u003c/div\\u003e\"}",
    "objectSecurityUserNameList": [],
    "score": 17.329885,
    "childrenVisibility": True
  }
}

def build_url():
    # Construire une URL de connexion sans chemin de queue
    # Exemple : amqp+ws://user:pass@host:port
    return f"{WS_SCHEME}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}"

def send_and_receive():
    url = build_url()
    print(url)
    try:
        print("1")
        conn = BlockingConnection(url)
        print("2")
    except Exception as e:
        print("Erreur de connexion (vérifiez support amqp+ws et reachability):", e)
        sys.exit(1)
    print("3")
    try:
        sender = BlockingSender(conn, address=ADDRESS)
        receiver = BlockingReceiver(conn, address=ADDRESS, timeout=10)
        print("3")
        # Envoyer un message AMQP avec body binaire
        msg = Message(body=PAYLOAD)
        sender.send(msg)
        print("Payload bytes envoyé:", PAYLOAD)

        # Recevoir
        incoming = receiver.receive(timeout=10)
        if incoming is None:
            print("Timeout: aucun message reçu en 10s")
        else:
            body = incoming.message.body
            print("Message reçu (type):", type(body), "value:", body)
            receiver.accept(incoming)
    finally:
        try:
            sender.close()
        except Exception:
            pass
        try:
            receiver.close()
        except Exception:
            pass
        conn.close()

if __name__ == "__main__":
    send_and_receive()