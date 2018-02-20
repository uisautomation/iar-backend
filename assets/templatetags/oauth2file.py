from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
from urllib.parse import urlparse, urljoin


register = template.Library()


@register.simple_tag
def oauth2file(scheme, host, static_file):
    """This custom tag always generates a FQDN for the specified static file"""
    oauth2fileurl = urlparse(static(static_file))
    if oauth2fileurl.scheme == '' and oauth2fileurl.netloc == '':
        return urljoin(str(scheme)+"://"+str(host), static(static_file))
    return static(static_file)
