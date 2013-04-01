"""
Set up the routes and WSGI Middleware used by TiddlySpace.
"""

from tiddlyweb.web.negotiate import Negotiate

from tiddlywebplugins.prettyerror import PrettyHTTPExceptor
from tiddlywebplugins.utils import replace_handler

from tiddlywebplugins.tiddlyspace.controlview import (ControlView,
        DropPrivs, AllowOrigin)
from tiddlywebplugins.csrf import CSRFProtector
from tiddlywebplugins.tiddlyspace.serversettings import ServerSettings
from tiddlywebplugins.tiddlyspace.handler import (home, friendly_uri,
        get_identities, get_space_tiddlers)
from tiddlywebplugins.tiddlyspace.profiles import add_profile_routes
from tiddlywebplugins.tiddlyspace.repudiator import RepudiatorController
from tiddlywebplugins.tiddlyspace.safemode import safe_mode
from tiddlywebplugins.tiddlyspace.spaces import add_spaces_routes
from tiddlywebplugins.tiddlyspace.singledomain import (ConvertSingleDomain,
	OutputSingleDomain)

def establish_www(config):
    """
    Set up the routes and WSGI Middleware used by TiddlySpace.
    """
    replace_handler(config['selector'], '/', dict(GET=home))
    config['selector'].add('/_safe', GET=safe_mode, POST=safe_mode)
    add_spaces_routes(config['selector'])
    add_profile_routes(config['selector'])
    config['selector'].add('/users/{username}/identities',
            GET=get_identities)
    config['selector'].add('/tiddlers[.{format}]', GET=get_space_tiddlers)
    config['selector'].add('/{tiddler_name:segment}', GET=friendly_uri)

    if ConvertSingleDomain not in config['server_request_filters']:
        config['server_request_filters'].insert(
                config['server_request_filters'].
                index(Negotiate) + 1, ConvertSingleDomain)

    if ControlView not in config['server_request_filters']:
        config['server_request_filters'].insert(
                config['server_request_filters'].
                index(ConvertSingleDomain) + 1, ControlView)

    if DropPrivs not in config['server_request_filters']:
        config['server_request_filters'].insert(
                config['server_request_filters'].
                index(ControlView) + 1, DropPrivs)

    if CSRFProtector not in config['server_request_filters']:
        config['server_request_filters'].append(CSRFProtector)

    if ServerSettings not in config['server_request_filters']:
        config['server_request_filters'].append(ServerSettings)

    if AllowOrigin not in config['server_response_filters']:
        config['server_response_filters'].insert(
                config['server_response_filters'].
                index(PrettyHTTPExceptor) + 1, AllowOrigin)

    if RepudiatorController not in config['server_response_filters']:
        config['server_response_filters'].insert(
                config['server_response_filters'].
                index(PrettyHTTPExceptor) + 1, RepudiatorController)

    if OutputSingleDomain not in config['server_response_filters']:
        config['server_response_filters'].insert(
                config['server_response_filters'].
                index(AllowOrigin) + 1, OutputSingleDomain)

