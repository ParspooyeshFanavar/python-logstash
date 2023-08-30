import logging
import socket
import traceback
from datetime import datetime
import sys

try:
    import json
except ImportError:
    import simplejson as json


class LogstashFormatterBase(logging.Formatter):

    def __init__(self, message_type, tags=None, fqdn=False):
        self.message_type = message_type
        self.tags = tags if tags is not None else []

        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()

    def get_extra_fields(self, record):
        # The list contains all the attributes listed in
        # http://docs.python.org/library/logging.html#logrecord-attributes
        skip_list = (
            "args", "asctime", "created", "exc_info", "exc_text", "filename",
            "funcName", "id", "levelname", "levelno", "lineno", "module",
            "msecs", "msecs", "message", "msg", "name", "pathname", "process",
            "processName", "relativeCreated", "thread", "threadName", "extra",
            "auth_token", "password", "stack_info",
            "request", "host", "response",
        )

        if sys.version_info < (3, 0):
            easy_types = (
                basestring,  # noqa: F821
                bool,
                dict,
                float,
                int,
                long,  # noqa: F821
                list,
                type(None),
            )
        else:
            easy_types = (str, bool, dict, float, int, list, type(None))

        fields = {}

        for key, value in record.__dict__.items():
            if key not in skip_list:
                if isinstance(value, easy_types):
                    fields[key] = value
                else:
                    fields[key] = repr(value)

        return fields

    def get_debug_fields(self, record):
        fields = {
            "stack_trace": self.format_exception(record.exc_info),
            "lineno": record.lineno,
            "process": record.process,
            "thread_name": record.threadName,
        }

        # funcName was added in 2.5
        if not getattr(record, "funcName", None):
            fields["funcName"] = record.funcName

        # processName was added in 2.6
        if not getattr(record, "processName", None):
            fields["processName"] = record.processName

        return fields

    @classmethod
    def format_source(cls, message_type, host, path):
        return f"{message_type}://{host}/{path}"

    @classmethod
    def format_timestamp(cls, timestamp: int):
        tstamp = datetime.utcfromtimestamp(timestamp)
        return tstamp.strftime("%Y-%m-%dT%H:%M:%S") + \
            ".%03d" % (tstamp.microsecond / 1000) + "Z"

    @classmethod
    def format_exception(cls, exc_info):
        return "".join(traceback.format_exception(*exc_info)) if exc_info else ""

    @classmethod
    def serialize(cls, message):
        if sys.version_info < (3, 0):
            return json.dumps(message)
        else:
            return bytes(json.dumps(message, default=str), "utf-8")

class LogstashFormatterVersion0(LogstashFormatterBase):
    version = 0

    def format(self, record):
        # Create message dict
        message = {
            "@timestamp": self.format_timestamp(record.created),
            "@message": record.getMessage(),
            "@source": self.format_source(
                self.message_type,
                self.host,
                record.pathname,
            ),
            "@source_host": self.host,
            "@source_path": record.pathname,
            "@tags": self.tags,
            "@type": self.message_type,
            "@fields": {
                "levelname": record.levelname,
                "logger": record.name,
            },
        }

        # Add extra fields
        message["@fields"].update(self.get_extra_fields(record))

        # If exception, add debug info
        if record.exc_info:
            message["@fields"].update(self.get_debug_fields(record))

        return self.serialize(message)


class LogstashFormatterVersion1(LogstashFormatterBase):

    def format(self, record):
        # Create message dict
        message = {
            "@timestamp": self.format_timestamp(record.created),
            "@version": "1",
            "message": record.getMessage(),
            "host": {
                "name": self.host,
            },
            "path": record.pathname,
            "tags": self.tags,
            "type": self.message_type,
            "source": "logstash",
            "action": "LOG",

            # Extra Fields
            "level": record.levelname,
            "logger_name": record.name,
        }

        # Add extra fields
        try:
            extra = json.dumps(self.get_extra_fields(record))
        except Exception as e:
            print(e)
        else:
            message["extra"] = extra

        # If exception, add debug info
        if record.exc_info:
            message["debug"] = json.dumps(self.get_debug_fields(record))

        return self.serialize(message)
