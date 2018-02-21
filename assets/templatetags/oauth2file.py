from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
from urllib.parse import urlsplit, urlunsplit


register = template.Library()


@register.simple_tag
def oauth2file(scheme, host, static_file):
    """This custom tag always generates a FQDN for the specified static file"""
    oauth2fileurl = urlsplit(static(static_file))
    if oauth2fileurl.scheme == '' and oauth2fileurl.netloc == '':
        return urlunsplit((str(scheme), str(host), oauth2fileurl.path, oauth2fileurl.query,
                           oauth2fileurl.fragment))
    return static(static_file)
