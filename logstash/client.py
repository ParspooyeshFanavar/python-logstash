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
    def __init__(self, host, port, tags=None, fqdn=False):
        self.tags = tags
        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()
        DatagramClient.__init__(self, host=host, port=port)

    def sendDict(self, message: "dict[str, Any]"):
        logger.info(f"--- LogstashClient: sendDict: {message}")
        self.send(json.dumps(message, default=str).encode("utf-8"))

    @classmethod
    def format_datetime(cls, dt: datetime):
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (dt.microsecond / 1000) + "Z"

    def sendDjangoRequest(self, req, **kwargs):
        from ipware import get_client_ip
        # kwargs can have "pk"
        remote_ip, _is_routable = get_client_ip(req)
        host = req.get_host()
        host_parts = host.split(":")
        host_ip = host_parts[0]
        host_dict = {
            "ip": host_ip,
        }
        if len(host_parts) > 1:
            host_dict["port"] = host_parts[1]

        # keys should not start with '@' except timestamp and version
        message = {
            '@timestamp': self.format_datetime(datetime.now()),
            '@version': '1',
            "message": f"{req.method} {req.path}",
            'host': host_dict,
            "path": req.path,
            'tags': self.tags,
            'type': "logstash",
            'level': "INFO",
            'logger_name': "django.requests",
            # extra fields:
            "username": req.user.username,
            "remote_ip": remote_ip,
            "method": req.method,
            # "request": req.__dict__,
        }
        for key, value in kwargs.items():
            # map "pk" to "object_id" ?
            message[key] = value

        self.sendDict(message)
