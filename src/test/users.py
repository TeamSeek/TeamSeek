from types import ListType
import os
import json
import testCommon

cookieFile = 'tmp_projects_cookies_test.txt'
url = 'localhost:8080'

class Test:
    def __init__(self):
        testCommon.login(cookieFile, 'navargas', url)
    def feed_returns_array(self):
        result = testCommon.curl(url + '/api/feed/',
            read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(result)
        assert type(obj) == ListType # Returned object should be an array
    def feed_array_is_non_empty(self):
        result = testCommon.curl(url + '/api/feed/',
            read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(result)
        assert len(obj) > 0 # User navargas should have a multi-item feed
    def feed_items_in_correct_format(self):
        result = testCommon.curl(url + '/api/feed/',
            read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(result)
        for item in obj:
            assert 'git_link' in item # Item present in feed object
            assert 'last_edit' in item # Item present in feed object
            assert 'owner' in item # Item present in feed object
            assert 'posted_date' in item # Item present in feed object
            assert 'project_members' in item # Item present in feed object
            assert 'short_desc' in item # Item present in feed object
            assert 'title' in item # Item present in feed object
            assert 'update' in item # Item present in feed object
    def project_members_is_array(self):
        result = testCommon.curl(url + '/api/feed/',
            read_cookie_file=cookieFile)
        obj = testCommon.jsonToDict(result)
        for item in obj:
            assert type(item['project_members']) == ListType
    def __deinit__(self):
        os.remove(cookieFile)
        assert not os.path.isfile(cookieFile) # cookieFile was removed
