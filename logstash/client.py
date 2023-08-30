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
        self.send(
            json.dumps(message, default=str).encode("utf-8"),
        )

    def _currentTimestamp(self):
        dt = datetime.utcnow().replace(tzinfo=None)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + \
            ".%03d" % (dt.microsecond / 1000) + "Z"
