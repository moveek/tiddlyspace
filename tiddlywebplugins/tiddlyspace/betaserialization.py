"""
extend TiddlyWiki serialization to optionally use beta release

activated via "twrelease=beta" URL parameter
"""

from tiddlywebwiki.serialization import Serialization as WikiSerialization
from tiddlywebplugins.tiddlyspace.web import determine_space


class Serialization(WikiSerialization):

    def _get_wiki(self):
        release = self.environ.get('tiddlyweb.query', {}).get(
                'twrelease', [False])[0]
        if release == 'beta':
            return _read_file(
                    self.environ['tiddlyweb.config']['base_tiddlywiki_beta'])
        else:
            return WikiSerialization._get_wiki(self) # XXX: inelegant?

    def _tiddler_as_div(self, tiddler):
        http_host = self.environ['HTTP_HOST']
        space = determine_space(self.environ, http_host) 
        if space:
            _, self.environ['HTTP_HOST'] = http_host.split('.', 1)
        return WikiSerialization._tiddler_as_div(self, tiddler)


def _read_file(path):
    f = open(path)
    contents = f.read()
    f.close()
    return unicode(contents, 'utf-8')
