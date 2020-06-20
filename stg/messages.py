
# Message types:
ADDRESS_REQUEST = "ADDRESS_REQUEST"
ADDRESS_RESPONSE = "ADDRESS_RESPONSE"
PATTERN = "PATTERN"
SIGNAL = "SIGNAL"
REPORT = "REPORT"


# Signal types:
SIGNAL_START = "START"
SIGNAL_READY = "READY"
SIGNAL_SUCCESS = "SUCCESS"


def createMessage(recipients, typ, payload):
    return {"recipients": recipients,
               "payload": payload,
                  "type": typ}
