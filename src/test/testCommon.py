import json
import pycurl
import urllib
import cStringIO

def curl(url, POST="", PUT="", write_cookie_file="", read_cookie_file="",
         cookie_string="", status=False, verbose=False, redir=False):
  buf = cStringIO.StringIO()
  c = pycurl.Curl()
  c.setopt(c.URL, url)
  if POST:
    c.setopt(c.POSTFIELDS, POST)
  if PUT:
    c.setopt(c.POSTFIELDS, POST)
  if write_cookie_file:
    c.setopt(c.COOKIEJAR, write_cookie_file)
  if read_cookie_file:
    c.setopt(c.COOKIEFILE, read_cookie_file)
  if cookie_string:
    c.setopt(c.COOKIE, cookie_string)
  c.setopt(c.CONNECTTIMEOUT, 5)
  c.setopt(c.TIMEOUT, 8)
  if verbose:
    c.setopt(c.VERBOSE, True)
  if redir:
    c.setopt(c.FOLLOWLOCATION, True)
  c.setopt(c.WRITEFUNCTION, buf.write)
  c.perform()
  result = buf.getvalue()
  statusCode = c.getinfo(pycurl.HTTP_CODE)
  if status:
    return statusCode
  buf.close()
  return result

def jsonToDict(result):
    try:
        obj = json.loads(result)
    except ValueError:
        obj = None 
    assert obj != None # JSON should be valid
    return obj

def login(cookieFile, username, url='localhost:8080'):
    statusCode = curl(url + '/api/auth/debug?user=navargas',
                      write_cookie_file=cookieFile,
                      status=True)
    return statusCode
