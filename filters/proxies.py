import os


def proxies_from_env(ret):
    for env in ['http_proxy', 'https_proxy', 'no_proxy']:
        if env in os.environ:
            ret[env] = os.environ[env]
    return ret


class FilterModule(object):
    """
    Specific filters
    """

    def filters(self):
        return {
            'proxies_from_env': proxies_from_env
        }
