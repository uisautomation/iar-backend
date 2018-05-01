import logging


LOG = logging.getLogger(__name__)


class LogHttp400Errors:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 400:
            LOG.warn('400 response from following request:')
            LOG.warn('%r', request)
            LOG.warn('Response was:')
            LOG.warn('%r', response)
            LOG.warn('Response body was:')
            LOG.warn('%r', response.content)

        return response
