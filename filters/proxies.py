import os
import urlparse


def proxies_from_env(ret):
    for env in ['http_proxy', 'https_proxy', 'no_proxy']:
        if env in os.environ:
            ret[env] = os.environ[env]
    return ret

def host_from_url(ret):
    parsed = urlparse.urlparse(ret)
    return parsed.netloc.split(":")[0]

class FilterModule(object):
    """
    Specific filters
    """

    def filters(self):
        return {
            'proxies_from_env': proxies_from_env,
            'host_from_url': host_from_url
        }
