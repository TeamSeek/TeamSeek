#!/usr/bin/env python
from types import FunctionType
import os
import imp
import sys
import glob
import traceback

"""                     ##########
                        # all.py #
                        ##########

Run all tests in directory. Files should contain a "Test" class. The
"Test" class can optionally contain '__init__' and '__deinit__'
functions which are run before and after the other functions.

Functions are considered "failed" if a contained assertion fails.
"""

# Build array of all filenames in current directory
thisFile = os.path.realpath(__file__)
cwd = os.path.dirname(thisFile)
allFiles = glob.glob(os.path.join(cwd, '*.py'))
allFiles.remove(thisFile) # remove ./all.py

testModules = []
for pathName in allFiles:
    fileName = '.'.join(os.path.basename(pathName).split('.')[:-1])
    try:
        testModule = imp.load_source(fileName, pathName)
        t = testModule.Test()
        testModules.append(testModule)
    except AttributeError:
        pass

print '(Loaded {0} out of {1} files)'.format(len(testModules), len(allFiles))

testsPassed = 0
totalTests = 0

for test in testModules:
    namelen = len(test.__name__)
    print '\n' + '#' * (namelen + 4)
    print '# {0} #'.format(test.__name__)
    print '#' * (namelen + 4)
    tests = [func[0] for func in test.Test.__dict__.items() if type(func[1]) == FunctionType]
    if '__init__' in tests: tests.remove('__init__')
    if '__deinit__' in tests: tests.remove('__deinit__')
    tObj = test.Test()
    success = 0
    for testName in tests:
        testFunc = getattr(tObj, testName)
        print ' * Running {0}'.format(testName)
        try:
            testFunc()
            success += 1
        except AssertionError as e:
            error = traceback.extract_tb(sys.exc_info()[2])[1]
            print '!! Error @ `{0}` on line {1}'.format(error[3], error[1])
            pass
    try:
        tObj.__deinit__()
    except AttributeError:
        # Not all tests need a deconstructor
        pass
    print ' Successfully ran {0}/{1} tests'.format(success, len(tests))
    testsPassed += success
    totalTests += len(tests)

print '\nSummary'
print '\t {0} tests run'.format(totalTests)
print '\t {0} tests passed'.format(testsPassed)
if testsPassed != totalTests:
    print 'There were errors'
