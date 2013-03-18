"""
This is a server request filter and server response filter 
pair that enables a single domain URI scheme to
work with tiddlyspace's existing subdomain based logic.
The logic for spaces, ControlView, DropPrivs, etc.

ConvertSingleDomain is a server request filter that performs
a simple task. It takes requests of the form:

    http://host.com/space/spacename

and changes them to:
 
    http://spacename.host.com/

SingleDomainOutput is a server response filter that 
converts uris in the response to their equivalent single domain 
form--the reverse of what the above request filter does.

It is a little messier because it actually needs to 
dip into the response and alter uris if they are "space links," 
meaning they are absolute uris for a space or something in a space.

The requests that have responses containing space links are
requests to:

* /: If an user is authenticated, a request for the frontpage will
result in a redirect to the user's own space. The uri in the redirect
needs to be converted to single domain form.

* /spaces: This request returns a list of dictionaries, one for each 
existing space. The space uri in each dict needs to be converted
to single domain form.

* Requests for a tiddler:

bags/{bag_name}/tiddlers/{tiddler_name}
recipes/{recipe_name}/tiddlers/{tiddler_name}

Requests for a tiddler return the tiddler content along with a 
space link that opens the tiddler in its home space when clicked.
The space link needs to be converted to single domain form.

* The final case is when the request is for a tiddlywiki. The
wiki serializer sets each tiddler's server.host field, so the 
server.host of each tiddler needs to converted to single domain
form. For now, instead of doing that here in the response filter,
it's being done by modifiying environ['HTTP_HOST'] in 
tiddlywebplugins.tiddyspace.betaserialization. This was it's done
in one step, rather needing to modify each tiddler div in the output.

"""

import re
import simplejson
from tiddlywebplugins.tiddlyspace.web import determine_space

import pdb

class ConvertSingleDomain(object):
    """
    WSGI middleware that transforms incoming requests with
    a single domain URI scheme to the subdomain URI scheme
    used by tiddlyspace.
    """ 
    
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        req_uri = environ.get('PATH_INFO', '')

        if (req_uri.startswith('/space/')):
            self._update_environ(environ, req_uri)

        return self.application(environ, start_response)

    def _update_environ(self, environ, req_uri):
        http_host = environ['HTTP_HOST']
        server_name = environ['SERVER_NAME']

        space = self._determine_space(req_uri)
        
        environ['HTTP_HOST'] = ''.join([space, '.', http_host])
        environ['SERVER_NAME'] = ''.join([space, '.', server_name])
        environ['PATH_INFO'] = self._remove_space_from_path(space, req_uri)

    def _determine_space(self, req_uri):
        return req_uri.split('/')[2]

    def _remove_space_from_path(self, space, req_uri):
        return req_uri.split('/', 2)[2].replace(space, '', 1)

class OutputSingleDomain(object):
    """
    WSGI middleware that modifies links to resources
    in a space so they are in single domain form.
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        req_entity = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')

        if req_entity == '/' and 'HTTP_COOKIE' in environ and 'tiddlyweb_user' in environ['HTTP_COOKIE']:
            return self._handle_root_response(environ, start_response)

        if re.search('/spaces$', req_entity):
            return self._handle_spaces_response(environ, start_response)
                
        if req_entity.find('/tiddlers/') != -1:
            return (self._handle_space_link(environ, output) for 
                    output in self.application(environ, start_response))

        return self.application(environ, start_response)

    def _handle_root_response(self, environ, start_response):
        def replacement_start_response(status, headers, exc_info=None):
            if '302' in status:
                redirect_uri = headers[0][1]
                space = self._has_space(environ, redirect_uri)
                if space:
                    headers[0] = ('Location', self._reformat_link_uri(redirect_uri, space))

            return start_response(status, headers, exc_info)

        return self.application(environ, replacement_start_response)
                            
    def _handle_spaces_response(self, environ, start_response):
        output = self.application(environ, start_response)
        #spaces = simplejson.loads(output)
        spaces = simplejson.loads("".join([str(c) for c in output]))
        for space_dict in spaces:
            space = self._has_space(environ, space_dict['uri'])
            if space:
                space_dict['uri'] = self._reformat_link_uri(space_dict['uri'], space)

        return simplejson.dumps(spaces)

    def _handle_space_link(self, environ, output):
        try:
            space_link = re.search('<a href="(.*)".*title="space link">', output).group(1)
            space = self._has_space(environ, space_link)
            if space:
                new_link = self._reformat_link_uri(space_link, space)
                output = output.replace(space_link, new_link)
        except (TypeError, AttributeError, IndexError):
            pass

        return output

    def _reformat_link_uri(self, link, space):
        split_link = link.rstrip('/').split('/')
        _, host_without_subdomain = split_link[2].split('.', 1)
        split_link[2] = host_without_subdomain
        split_link.insert(3, space)
        split_link.insert(3, 'space')
        new_link = '/'.join(split_link)
        return new_link

    def _has_space(self, environ, link):
        try:
            http_host = re.search('http://([a-zA-Z0-9.:-]*)', link).group(1)
            return determine_space(environ, http_host)
        except:
            pass

        return None
