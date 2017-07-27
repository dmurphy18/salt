# -*- coding: utf-8 -*-
'''
A module for testing the logic of states and highstates

Saltcheck provides unittest like functionality requiring only the knowledge of salt module execution and yaml.

In order to run state and highstate saltcheck tests a sub-folder of a state must be creaed and named "saltcheck-tests".

Tests for a state should be created in files ending in *.tst and placed in the saltcheck-tests folder.

Multiple tests can be created in a file.
Multiple *.tst files can be created in the saltcheck-tests folder.
The "id" of a test works in the same manner as in salt state files.
They should be unique and descriptive.

Example file system layout:
/srv/salt/apache/
                 init.sls
                 config.sls
                 saltcheck-tests/
                                 pkg_and_mods.tst
                                 config.tst


Saltcheck Test Syntax:

Unique-ID:
  module_and_function: 
  args:
  kwargs:
  assertion:
  expected-return: 


Example test 1:

echo-test-hello:
  module_and_function: test.echo
  args:
    - "hello"
  kwargs:
  assertion: assertEqual
  expected-return:  'hello'

 
:codeauthor:    William Cannon <william.cannon@gmail.com>
:maturity:      new
'''
from __future__ import absolute_import
import logging
import os
import time
import yaml
try:
    # import salt.utils
    import salt.client
    import salt.exceptions
except ImportError:
    pass

log = logging.getLogger(__name__)

__virtualname__ = 'saltcheck'


def __virtual__():
    '''
    Check dependencies - may be useful in future
    '''
    return __virtualname__


def update_master_cache():
    '''
    Updates the master cache onto the minion - transfers all salt-check-tests
    Should be done one time before running tests, and if tests are updated
    Can be automated by setting "auto_update_master_cache: True" in minion config

    CLI Example:
        salt '*' saltcheck.update_master_cache
    '''
    __salt__['cp.cache_master']()
    return True


def run_test(**kwargs):
    '''
    Execute one saltcheck test and return result

    :param keyword arg test:
    CLI Example::
        salt '*' saltcheck.run_test
            test='{"module_and_function": "test.echo",
                   "assertion": "assertEqual",
                   "expected-return": "This works!",
                   "args":["This works!"] }'
    '''
    # salt converts the string to a dictionary auto-magically
    scheck = SaltCheck()
    test = kwargs.get('test', None)
    if test and isinstance(test, dict):
        return scheck.run_test(test)
    else:
        return "Test must be a dictionary"


def run_state_tests(state):
    '''
    Execute all tests for a salt state and return results
    Nested states will also be tested

    :param str state: the name of a user defined state

    CLI Example::
      salt '*' saltcheck.run_state_tests postfix
    '''
    scheck = SaltCheck()
    paths = scheck.get_state_search_path_list()
    stl = StateTestLoader(search_paths=paths)
    results = {}
    sls_list = _get_state_sls(state)
    for state_name in sls_list:
        mypath = stl.convert_sls_to_path(state_name)
        stl.add_test_files_for_sls(mypath)
        stl.load_test_suite()
        results_dict = {}
        for key, value in stl.test_dict.items():
            result = scheck.run_test(value)
            results_dict[key] = result
        results[state_name] = results_dict
    passed = 0
    failed = 0
    missing_tests = 0
    for state in results:
        if len(results[state].items()) == 0:
            missing_tests = missing_tests + 1
        else:
            for dummy, val in results[state].items():
                log.info("dummy={}, val={}".format(dummy, val))
                if val.startswith('Pass'):
                    passed = passed + 1
                if val.startswith('Fail'):
                    failed = failed + 1
    out_list = []
    for key, value in results.items():
        out_list.append({key: value})
    out_list.sort()
    out_list.append({"TEST RESULTS": {'Passed': passed, 'Failed': failed, 'Missing Tests': missing_tests}})
    return out_list


def run_highstate_tests():
    '''
    Execute all tests for a salt highstate and return results

    CLI Example::
      salt '*' saltcheck.run_highstate_tests
    '''
    scheck = SaltCheck()
    paths = scheck.get_state_search_path_list()
    stl = StateTestLoader(search_paths=paths)
    results = {}
    sls_list = _get_top_states()
    for state_name in sls_list:
        mypath = stl.convert_sls_to_path(state_name)
        stl.add_test_files_for_sls(mypath)
        stl.load_test_suite()
        results_dict = {}
        for key, value in stl.test_dict.items():
            result = scheck.run_test(value)
            results_dict[key] = result
        results[state_name] = results_dict
    passed = 0
    failed = 0
    missing_tests = 0
    for state in results:
        if len(results[state].items()) == 0:
            missing_tests = missing_tests + 1
        else:
            for dummy, val in results[state].items():
                log.info("dummy={}, val={}".format(dummy, val))
                if val.startswith('Pass'):
                    passed = passed + 1
                if val.startswith('Fail'):
                    failed = failed + 1
    out_list = []
    for key, value in results.items():
        out_list.append({key: value})
    out_list.sort()
    out_list.append({"TEST RESULTS": {'Passed': passed, 'Failed': failed, 'Missing Tests': missing_tests}})
    return out_list


def _is_valid_module(module):
    '''return a list of all modules available on minion'''
    modules = __salt__['sys.list_modules']()
    return bool(module in modules)


def _get_auto_update_cache_value():
    '''return the config value of auto_update_master_cache'''
    __salt__['config.get']('auto_update_master_cache')
    return True


def _is_valid_function(module_name, function):
    '''Determine if a function is valid for a module'''
    try:
        functions = __salt__['sys.list_functions'](module_name)
    except salt.exceptions.SaltException:
        functions = ["unable to look up functions"]
    return "{0}.{1}".format(module_name, function) in functions


def _get_top_states():
    ''' equivalent to a salt cli: salt web state.show_top'''
    alt_states = []
    try:
        returned = __salt__['state.show_top']()
        for i in returned['base']:
            alt_states.append(i)
    except Exception:
        raise
    # log.info("top states: {}".format(alt_states))
    return alt_states


def _get_state_sls(state):
    ''' equivalent to a salt cli: salt web state.show_low_sls STATE'''
    sls_list_state = []
    try:
        returned = __salt__['state.show_low_sls'](state)
        for i in returned:
            if i['__sls__'] not in sls_list_state:
                sls_list_state.append(i['__sls__'])
    except Exception:
        raise
    return sls_list_state


class SaltCheck(object):
    '''
    This class implements the saltcheck
    '''

    def __init__(self):
        # self.sls_list_top = []
        self.sls_list_state = []
        self.modules = []
        self.results_dict = {}
        self.results_dict_summary = {}
        self.assertions_list = '''assertEqual assertNotEqual
                                  assertTrue assertFalse
                                  assertIn assertGreater
                                  assertGreaterEqual
                                  assertLess assertLessEqual'''.split()
        self.auto_update_master_cache = _get_auto_update_cache_value
        # self.salt_lc = salt.client.Caller(mopts=__opts__)
        self.salt_lc = salt.client.Caller()
        if self.auto_update_master_cache:
            update_master_cache()

    def __is_valid_test(self, test_dict):
        '''Determine if a test contains:
             a test name,
             a valid module and function,
             a valid assertion,
             an expected return value'''
        tots = 0  # need total of >= 6 to be a valid test
        m_and_f = test_dict.get('module_and_function', None)
        assertion = test_dict.get('assertion', None)
        expected_return = test_dict.get('expected-return', None)
        if m_and_f:
            tots += 1
            module, function = m_and_f.split('.')
            if _is_valid_module(module):
                tots += 1
            if _is_valid_function(module, function):
                tots += 1
        if assertion:
            tots += 1
            if assertion in self.assertions_list:
                tots += 1
        if expected_return:
            tots += 1
        return tots >= 6

    def call_salt_command(self,
                          fun,
                          args=None,
                          kwargs=None):
        '''Generic call of salt Caller command'''
        value = False
        try:
            if args and kwargs:
                value = self.salt_lc.cmd(fun, *args, **kwargs)
            elif args and not kwargs:
                value = self.salt_lc.cmd(fun, *args)
            elif not args and kwargs:
                value = self.salt_lc.cmd(fun, **kwargs)
            else:
                value = self.salt_lc.cmd(fun)
        except salt.exceptions.SaltException:
            raise
        except Exception:
            raise
        return value

    def run_test(self, test_dict):
        '''Run a single saltcheck test'''
        if self.__is_valid_test(test_dict):
            mod_and_func = test_dict['module_and_function']
            args = test_dict.get('args', None)
            assertion = test_dict['assertion']
            expected_return = test_dict['expected-return']
            kwargs = test_dict.get('kwargs', None)
            actual_return = self.call_salt_command(mod_and_func, args, kwargs)
            if assertion != "assertIn":
                expected_return = self.cast_expected_to_returned_type(expected_return, actual_return)
            if assertion == "assertEqual":
                value = self.__assert_equal(expected_return, actual_return)
            elif assertion == "assertNotEqual":
                value = self.__assert_not_equal(expected_return, actual_return)
            elif assertion == "assertTrue":
                value = self.__assert_true(expected_return)
            elif assertion == "assertFalse":
                value = self.__assert_false(expected_return)
            elif assertion == "assertIn":
                value = self.__assert_in(expected_return, actual_return)
            elif assertion == "assertNotIn":
                value = self.__assert_not_in(expected_return, actual_return)
            elif assertion == "assertGreater":
                value = self.__assert_greater(expected_return, actual_return)
            elif assertion == "assertGreaterEqual":
                value = self.__assert_greater_equal(expected_return, actual_return)
            elif assertion == "assertLess":
                value = self.__assert_less(expected_return, actual_return)
            elif assertion == "assertLessEqual":
                value = self.__assert_less_equal(expected_return, actual_return)
            else:
                value = "Fail"
        else:
            return "Fail"
        return value

    @staticmethod
    def cast_expected_to_returned_type(expected, returned):
        '''
        Determine the type of variable returned
        Cast the expected to the type of variable returned
        '''
        ret_type = type(returned)
        new_expected = expected
        if expected == "False" and ret_type == bool:
            expected = False
        try:
            new_expected = ret_type(expected)
        except ValueError:
            log.info("Unable to cast expected into type of returned")
            log.info("returned = {}".format(returned))
            log.info("type of returned = {}".format(type(returned)))
            log.info("expected = {}".format(expected))
            log.info("type of expected = {}".format(type(expected)))
        return new_expected

    @staticmethod
    def __assert_equal(expected, returned):
        '''
        Test if two objects are equal
        '''
        result = "Pass"

        try:
            assert (expected == returned), "{0} is not equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_not_equal(expected, returned):
        '''
        Test if two objects are not equal
        '''
        result = "Pass"
        try:
            assert (expected != returned), "{0} is equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_true(returned):
        '''
        Test if an boolean is True
        '''
        result = "Pass"
        try:
            assert (returned is True), "{0} not True".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_false(returned):
        '''
        Test if an boolean is False
        '''
        result = "Pass"
        if isinstance(returned, str):
            try:
                returned = bool(returned)
            except ValueError:
                raise
        try:
            assert (returned is False), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = "Pass"
        try:
            assert (expected in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_not_in(expected, returned):
        '''
        Test if a value is not in the list of returned values
        '''
        result = "Pass"
        try:
            assert (expected not in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_greater(expected, returned):
        '''
        Test if a value is greater than the returned value
        '''
        result = "Pass"
        try:
            assert (expected > returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_greater_equal(expected, returned):
        '''
        Test if a value is greater than or equal to the returned value
        '''
        result = "Pass"
        try:
            assert (expected >= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_less(expected, returned):
        '''
        Test if a value is less than the returned value
        '''
        result = "Pass"
        try:
            assert (expected < returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_less_equal(expected, returned):
        '''
        Test if a value is less than or equal to the returned value
        '''
        result = "Pass"
        try:
            assert (expected <= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def get_state_search_path_list():
        '''For the state file system, return a
           list of paths to search for states'''
        # state cache should be updated before running this method
        search_list = []
        cachedir = __opts__.get('cachedir', None)
        environment = __opts__['environment']
        if environment:
            path = cachedir + os.sep + "files" + os.sep + environment
            search_list.append(path)
        path = cachedir + os.sep + "files" + os.sep + "base"
        search_list.append(path)
        return search_list


class StateTestLoader(object):
    '''
    Class loads in test files for a state
    e.g.  state_dir/saltcheck-tests/[1.tst, 2.tst, 3.tst]
    '''

    def __init__(self, search_paths):
        self.search_paths = search_paths
        self.path_type = None
        self.test_files = []  # list of file paths
        self.test_dict = {}

    def load_test_suite(self):
        '''load tests either from one file, or a set of files'''
        self.test_dict = {}
        for myfile in self.test_files:
            self.load_file(myfile)
        self.test_files = []

    def load_file(self, filepath):
        '''
        loads in one test file
        '''
        try:
            # with salt.utils.files.fopen(filepath, 'r') as myfile:
            with open(filepath, 'r') as myfile:
                contents_yaml = yaml.load(myfile)
                for key, value in contents_yaml.items():
                    self.test_dict[key] = value
        except:
            raise
        return

    def gather_files(self, filepath):
        '''gather files for a test suite'''
        self.test_files = []
        log.info("gather_files: {}".format(time.time()))
        filepath = filepath + os.sep + 'saltcheck-tests'
        rootdir = filepath
        # for dirname, subdirlist, filelist in os.walk(rootdir):
        for dirname, dummy, filelist in os.walk(rootdir):
            for fname in filelist:
                if fname.endswith('.tst'):
                    start_path = dirname + os.sep + fname
                    full_path = os.path.abspath(start_path)
                    self.test_files.append(full_path)
        return

    @staticmethod
    def convert_sls_to_paths(sls_list):
        '''Converting sls to paths'''
        new_sls_list = []
        for sls in sls_list:
            sls = sls.replace(".", os.sep)
            new_sls_list.append(sls)
        return new_sls_list

    @staticmethod
    def convert_sls_to_path(sls):
        '''Converting sls to paths'''
        sls = sls.replace(".", os.sep)
        return sls

    def add_test_files_for_sls(self, sls_path):
        '''Adding test files'''
        for path in self.search_paths:
            full_path = path + os.sep + sls_path
            rootdir = full_path
            if os.path.isdir(full_path):
                log.info("searching path= {}".format(full_path))
                # for dirname, subdirlist, filelist in os.walk(rootdir, topdown=True):
                for dirname, subdirlist, dummy in os.walk(rootdir, topdown=True):
                    if "saltcheck-tests" in subdirlist:
                        self.gather_files(dirname)
                        log.info("test_files list: {}".format(self.test_files))
                        log.info("found subdir match in = {}".format(dirname))
                    else:
                        log.info("did not find subdir match in = {}".format(dirname))
                    del subdirlist[:]
            else:
                log.info("path is not a directory= {}".format(full_path))
        return
