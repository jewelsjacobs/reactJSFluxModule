import requests

from logging import Handler


class LogglyHandler(Handler):
    def __init__(self, token, tags=None):
        """Logging handler for Loggly

        :param token: str
        :param tags: list or tuple
        :return:
        """
        super(LogglyHandler, self).__init__()

        if tags:
            if not isinstance(tags, (list, tuple)):
                raise TypeError("Keyword argument 'tags' must be a list or tuple.")
            tag_str = 'tag/{}/'.format(','.join(tags))
        else:
            tag_str = ''

        self.url = 'https://logs-01.loggly.com/inputs/{}/{}'.format(token, tag_str)

    def emit(self, record):
        """Emit log record

        :param record: str
        :return:
        """
        requests.post(self.url, data=self.format(record), headers={'content-type': 'text/plain'}, timeout=10)
