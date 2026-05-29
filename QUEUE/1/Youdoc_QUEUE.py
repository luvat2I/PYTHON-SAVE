import uuid
import json
from proton import Message
from proton.reactor import Container
from proton.handlers import MessagingHandler
from urllib.parse import urlparse, urlunparse

def build_payload(object_id):
    return {
      "objectDescriptors": {
        "id": f"XFRAMEWORK-EVENT-BUSINESSOPERATION--001-{object_id}",
        "objectReference": {"objectKind":{"softwareCode":"XFRAMEWORK-EVENT","objectType":"BusinessOperation","objectSubType":""},"objectId": object_id},
        "objectSource": {"uri": "", "objectSourceKind": {"type":"XFRAMEWORK-EVENT","name":"001"}},
        "objectDescription": {"audit":{
            "creationUser":"001-svc-usr",
            "creationDateTime":{"year":2026,"month":5,"dayOfMonth":18,"hourOfDay":8,"minute":16,"second":24},
            "modificationUser":"001-svc-usr",
            "modificationDateTime":{"year":2026,"month":5,"dayOfMonth":18,"hourOfDay":8,"minute":16,"second":24}
          },
          "creationUserFullName":"001-svc-usr",
          "modificationUserFullName":"001-svc-usr",
          "objectFilterDate":{"year":2026,"month":5,"dayOfMonth":18,"hourOfDay":8,"minute":16,"second":24}
        },
        "objectKeyValues":["#EVENT_CATEGORY#BATCH"],
        "objectSecurityClasses":[[],[],[],[],[],[],[],[]],
        "objectSecurityBusinessObjects":[[],[]],
        "objectAttributes": "{\"status\":\"Échoué\",\"environment\":\"001\",\"server\":\"YDGLUVA24Q\"}",
        "objectSecurityUserNameList": [],
        "score": 17.329885,
        "childrenVisibility": True
      }
    }

class SendHandler(MessagingHandler):
    def __init__(self, url, address, payload_bytes, username=None, password=None):
        super().__init__()
        self.url = url
        self.address = address
        self.payload = payload_bytes
        self.corr_id = str(uuid.uuid4())
        self.username = username
        self.password = password

    def on_start(self, event):
        # create sender using URL without credentials; attach creds at connection.open via SASL if needed
        # proton supports passing username/password in URL: amqp://user:pass@host:5672
        event.container.create_sender(self.url + "/" + self.address)

    def on_sendable(self, event):
        msg = Message(body=self.payload, properties={'environment':'001'})
        msg.correlation_id = self.corr_id
        event.sender.send(msg)
        print("Envoyé correlation_id=", self.corr_id)
        event.sender.close()
        event.connection.close()

if __name__ == "__main__":
    # paramètres à modifier
    broker_url = "amqp://ydgluva24q:8281"      # ou inclure user:pass => amqp://user:pass@host:5672
    username = "xdev-jms-user"
    password = "xl4Jee@ChangeIt1"
    queue_name = "jms.queue.XOSTIndexEventProcessQueue"
    object_id = "PAC9999"
    print(broker_url)
    # si proton ne transmet pas automatiquement les creds depuis la partie user:pass de l'URL,
    # construisez l'URL avec les identifiants :
    parsed = urlparse(broker_url)
    if username and password:
        netloc = f"{username}:{password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        broker_url_with_auth = urlunparse((parsed.scheme, netloc, parsed.path or "", "", "", ""))
    else:
        broker_url_with_auth = broker_url
    print(broker_url_with_auth)
    payload_bytes = json.dumps(build_payload(object_id), ensure_ascii=False).encode('utf-8')
    print(")
    print(payload_bytes)
    #Container(SendHandler(broker_url_with_auth, queue_name, payload_bytes, username, password)).run()
    
    