# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the instrument task.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


from ecpy.tasks.tasks.base_tasks import RootTask
from ecpy.tasks.tasks.instr_task import (InstrumentTask, PROFILE_DEPENDENCY_ID,
                                         DRIVER_DEPENDENCY_ID)

p_id = PROFILE_DEPENDENCY_ID
d_id = DRIVER_DEPENDENCY_ID


class FalseStarter(object):
    """False instrument starter used for testing.

    """

    def __init__(self, should_pass=True):
        self.should_pass = should_pass

    def check_infos(self, driver_cls, connection, settings):
        return self.should_pass, 'Message'

    def initialize(self, driver_cls, connection, settings):
        return object()


class TestInstrumentTask(object):
    """Test the instrument task.

    """

    def setup(self):
        r = RootTask()
        r.run_time = {d_id: {'d': (object, FalseStarter())},
                      p_id: {'p': {'connections': {'c': {}, 'c2': {}},
                                   'settings': {'s': {}}}}}
        self.task = InstrumentTask(name='Dummy',
                                   selected_instrument=('p', 'd', 'c', 's'))
        r.add_child_task(0, self.task)
        self.err_path = 'root/Dummy-instrument'

    def test_instr_task_check_handling_missing_instrument(self):
        """Test handling an incorrect selected instrument during the checks.

        """
        self.task.selected_instrument = ()
        res, tb = self.task.check()
        assert not res
        assert self.err_path in tb
        assert 'No instrument' in tb[self.err_path]

    def test_instr_task_check_handling_missing_driver(self):
        """Test handling a missing driver from the run_time.

        """
        del self.task.root.run_time[d_id]['d']
        res, tb = self.task.check()
        assert not res
        assert self.err_path in tb
        assert 'specified driver' in tb[self.err_path]

    def test_instr_task_check_handling_no_profile(self):
        """Test handling the absence of profile.

        """
        del self.task.root.run_time[p_id]['p']
        res, tb = self.task.check()
        assert res
        assert not tb

    def test_instr_task_check_handling_no_connection(self):
        """Test handling the absence of the requested connection.

        """
        del self.task.root.run_time[p_id]['p']['connections']['c']
        res, tb = self.task.check()
        assert not res
        assert self.err_path in tb
        assert ' connection' in tb[self.err_path]

    def test_instr_task_check_handling_no_settings(self):
        """Test handling the absence of the requested settings.

        """
        del self.task.root.run_time[p_id]['p']['settings']['s']
        res, tb = self.task.check()
        assert not res
        assert self.err_path in tb
        assert ' settings' in tb[self.err_path]

    def test_instr_task_check_skip_starter(self):
        """Test running the check when we are not asked to check the connection

        """
        res, tb = self.task.check()
        assert res

    def test_instr_task_check_starter_pass(self):
        """Test running the check when we are asked to check the connection

        """
        res, tb = self.task.check(test_instr=True)
        assert res

    def test_instr_task_check_starter_fail(self):
        """Test running the check when we are asked to check the connection
        and the check fail.

        """
        self.task.root.run_time[d_id]['d'][1].should_pass = False
        res, tb = self.task.check(test_instr=True)
        assert not res
        assert self.err_path in tb
        assert 'Message' in tb[self.err_path]

    def test_instr_task_start_driver1(self):
        """Test starting a driver.

        """
        self.task.start_driver()
        d = self.task.driver
        self.task.start_driver()
        assert d is self.task.driver

    def test_instr_task_start_driver2(self):
        """Test starting a driver with same profile but different connection.

        """
        self.task.start_driver()
        d = self.task.driver
        self.task.selected_instrument = ('p', 'd', 'c2', 's')
        self.task.start_driver()
        assert d is not self.task.driver
