from types import ListType
import os
import json
import testCommon

cookieFile = 'tmp_projects_cookies_test.txt'
url = 'localhost:8080'

class Test:
    def __init__(self):
        testCommon.login(cookieFile, 'navargas', url)
    def my_projects_returns_array(self):
        result = testCommon.curl(url + '/api/projects/?action=my_projects&user=navargas',
            read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(result)
        assert type(obj) == ListType # Returned object should be an array
    def returns_not_enough_data_without_title(self):
        data = testCommon.curl(url + '/api/projects/', PUT="action=new_project",
            read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(data)
        assert obj['error'] == 'Not enough data'
    def __deinit__(self):
        os.remove(cookieFile)
        assert not os.path.isfile(cookieFile) # cookieFile was removed
