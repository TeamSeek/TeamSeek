import os
import time
import json
import pystache

NO_CACHE = 'NO_CACHE' in os.environ

def pagePath(pageName):
    """ Return the path for template pages """
    # welcome --> views/welcome.html
    return os.path.join('views', pageName + '.html')

# Storage for cached pages
STORAGE = {}

class Page:
    pageName = ""
    fileData = ""
    template = ""
    lastUpdated = 0
    def __init__(self, pageName):
        """ Read data from filesystem """
        self.pageName = pageName
        self.updateFileData()
        self.template = pystache.parse(unicode(self.fileData, 'utf-8'))
    def updateFileData(self):
        """ Read data from template pages """
        with open(pagePath(self.pageName)) as f:
            self.fileData = f.read()
        self.lastUpdated = time.time()
    def render(self, renderParam):
        """ Render {{ mustache }} blocks """
        if 'initial_data' not in renderParam:
            renderParam['initial_data'] = json.dumps({});
        return pystache.render(self.template, renderParam)
    def fresh(self):
        """ Return True if cached data is fresh """
        if NO_CACHE:
            return False
        return os.path.getmtime(pagePath(self.pageName))<=self.lastUpdated

class PageCache:
    def removeOldItems(self):
        """ Purge old items from cache """
        pass
    def getRaw(self, pageName):
        """ Raw html document """
        return self.get(pageName).fileData
    def getTemplate(self, pageName):
        """ Pystache template """
        return self.get(pageName).template
    def get(self, pageName):
        """ Page object """
        if pageName not in STORAGE:
            STORAGE[pageName] = Page(pageName)
        if not STORAGE[pageName].fresh():
            # If the page has been updated, reload it into memory
            STORAGE[pageName].updateFileData()
        return STORAGE[pageName]
