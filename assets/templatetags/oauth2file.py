from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
from urllib.parse import urlparse, urljoin


register = template.Library()


@register.simple_tag
def oauth2file(scheme, host):
    oauth2fileurl = urlparse(static('iarbackend/oauth2-redirect.html'))
    if oauth2fileurl.scheme == '' and oauth2fileurl.netloc == '':
        return urljoin(str(scheme)+str(host), static('iarbackend/oauth2-redirect.html'))
    return static('iarbackend/oauth2-redirect.html')
