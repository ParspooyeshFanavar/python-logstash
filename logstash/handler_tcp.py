from logging.handlers import DatagramHandler

from . import formatter


# Derive from object to force a new-style class and thus allow super() to work
# on Python 2.6
class TCPLogstashHandler(DatagramHandler):
    """Python logging handler for Logstash. Sends events over TCP.
    :param host: The host of the logstash server.
    :param port: The port of the logstash server (default 5959).
    :param message_type: The type of the message (default logstash).
    :param fqdn: Indicates whether to show fully qualified domain name
                 or not (default False).
    :param version: version of logstash event schema (default is 0).
    :param tags: list of tags for a logger (default is None).
    """

    def __init__(
        self,
        host,
        port=5959,
        message_type='log',
        tags=None,
        fqdn=False,
        version=1,
    ):
        DatagramHandler.__init__(self, host, port)
        if version == 1:
            self.formatter = formatter.LogstashFormatterVersion1(
                message_type=message_type,
                tags=tags,
                fqdn=fqdn,
            )
        else:
            self.formatter = formatter.LogstashFormatterVersion0(
                message_type=message_type,
                tags=tags,
                fqdn=fqdn,
            )

    def makePickle(self, record):
        return self.formatter.format(record) + b'\n'
