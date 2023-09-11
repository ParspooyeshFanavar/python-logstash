import json
import logging
import socket
import typing
from datetime import datetime

from .datagram import DatagramClient

if typing.TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)

class LogstashClient(DatagramClient):
    MAX_DATA_SIZE = 65507
    
    def __init__(
        self,
        host,
        port,
        message_type='log',
        tags=None,
        fqdn=False,
    ):
        self.tags = tags or []
        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()
        self.message_type = message_type
        DatagramClient.__init__(self, host=host, port=port)

    def sendDict(self, message: "dict[str, Any]"):
        message["@timestamp"] = self._currentTimestamp()
        message["@version"] = "1"
        message["source"] = "logstash"
        if "tags" not in message:
            message["tags"] = self.tags
        if "type" not in message:
            message["type"] = self.message_type
        msg_json = json.dumps(message, default=str).encode("utf-8")
        if len(msg_json) > self.MAX_DATA_SIZE:
            print(f"---------- LogstashClient: sendDict: skipped sending message with length {len(msg_json)}")
            return
        try:
            self.send(msg_json)
        except Exception as e:
            print(f"---------- LogstashClient: sendDict: exception trying to send {e}")


    def _currentTimestamp(self):
        dt = datetime.utcnow().replace(tzinfo=None)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + \
            ".%03d" % (dt.microsecond / 1000) + "Z"
