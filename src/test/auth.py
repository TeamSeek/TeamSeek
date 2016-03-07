from types import ListType
import os
import json
import testCommon

cookieFile = 'tmp_auth_cookies_test.txt'
url = 'localhost:8080'

class Test:
    def __init__(self):
        if os.path.isfile(cookieFile):
            os.remove(cookieFile)
        status = testCommon.login(cookieFile, 'navargas', url)
        assert status == 303 # Login should redirect to homepage
    def get_returns_warnings(self):
        result = testCommon.curl(url + '/api/projects/', read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(result)
        assert obj['error'] == 'Not enough data' # Should return correct warning
    def get_project_list(self):
        result = testCommon.curl(url + '/api/projects/?action=my_projects',
            read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(result)
        assert type(obj) == ListType # Returned object should be an array
    def __deinit__(self):
        os.remove(cookieFile)
        assert not os.path.isfile(cookieFile) # cookieFile was removed
