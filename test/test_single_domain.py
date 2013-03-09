
import httplib2
import wsgi_intercept

from wsgi_intercept import httplib2_intercept

from tiddlyweb.model.user import User
from tiddlyweb.model.tiddler import Tiddler

from test.fixtures import make_test_env, make_fake_space, get_auth

import pdb

def setup_module(module):
    make_test_env(module)
    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('0.0.0.0', 8080, app_fn)
    wsgi_intercept.add_wsgi_intercept('om.0.0.0.0', 8080, app_fn)
    make_fake_space(module.store, 'om')
    user = User('om')
    user.set_password('moo')
    module.store.put(user)
    

def teardown_module(module):
    import os

def test_root_redirect():
    tiddler = Tiddler('Solar', 'om_public')
    store.put(tiddler)
    http = httplib2.Http()

    response, content = http.request('http://0.0.0.0:8080/',
            method='GET')

    cookie = get_auth('om', 'moo')
    response, content = http.request('http://0.0.0.0:8080/',
            headers = {'Cookie': 'tiddlyweb_user="%s"' % cookie},
            method='GET')

    response, content = http.request('http://0.0.0.0:8080/space/om/bags/om_public/tiddlers/Solar',
            headers = {'Cookie': 'tiddlyweb_user="%s"' % cookie},
            method='GET')
