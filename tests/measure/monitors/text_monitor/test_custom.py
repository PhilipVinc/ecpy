# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the widget used to create/edit a custom entry.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from ecpy.measure.monitors.text_monitor.entry import MonitoredEntry
from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.measure.monitors.text_monitor.custom_entry_edition\
        import EntryDialog

pytest_plugins = str('ecpy.testing.measure.monitors.text_monitor.fixtures'),


@pytest.fixture
def monitor(text_monitor_workbench):
    """Bare text monitor as created by the plugin.

    """
    p = text_monitor_workbench.get_plugin('ecpy.measure.monitors.text_monitor')
    m = p.create_monitor(False)
    m.handle_database_change(('added', 'root/test', 0))
    m.handle_database_change(('added', 'root/simp/test', 0))
    m.handle_database_change(('added', 'root/comp/test', 0))
    return m


def test_creating_new_custom_entry(monitor, dialog_sleep):
    """Test creating an  entry using the dialog.

    """
    d = EntryDialog(monitor=monitor)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    w = d.central_widget().widgets()
    w[1].text = 'test'
    process_app_events()
    sleep(dialog_sleep)

    w[5].text = '{root/test}, {simp/test}, {comp/test}'
    process_app_events()
    sleep(dialog_sleep)

    b = d.builder
    for e in ('root/test', 'simp/test', 'comp/test'):
        assert e in b.map_entries
    b.add_entry(0, 'after')
    assert b.used_entries
    process_app_events()
    sleep(dialog_sleep)

    b.used_entries[0].entry = 'root/test'
    process_app_events()
    sleep(dialog_sleep)

    b.add_entry(0, 'after')
    assert not b.used_entries[-1].entry
    process_app_events()
    sleep(dialog_sleep)

    b.used_entries[-1].entry = 'simp/test'
    process_app_events()
    sleep(dialog_sleep)

    b.add_entry(0, 'before')
    assert not b.used_entries[0].entry
    process_app_events()
    sleep(dialog_sleep)

    b.used_entries[0].entry = 'comp/test'
    process_app_events()
    sleep(dialog_sleep)

    w[-2].clicked = True
    process_app_events()

    assert d.entry
    e = d.entry
    assert e.name == 'test'
    assert (sorted(e.depend_on) ==
            sorted(('root/test', 'root/simp/test', 'root/comp/test')))

    d.close()
    process_app_events()


def test_editing_cusom_entry(monitor, dialog_sleep):
    """Test that we can edit an existing monitored entry.

    """
    e = MonitoredEntry(name='test', path='test',
                       depend_on=['root/test', 'root/simp/test',
                                  'root/comp/test'],
                       formatting=('{root/test}, {root/simp/test}, '
                                   '{root/comp/test}')
                       )

    # Test cancelling after editon.
    d = EntryDialog(monitor=monitor, entry=e)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    w = d.central_widget().widgets()
    assert w[1].text == 'test'
    w[1].text = 'dummy'
    process_app_events()
    sleep(dialog_sleep)

    w[-1].clicked = True
    process_app_events()
    assert d.entry.name == 'test'

    # Test doing some actuel editions
    d = EntryDialog(monitor=monitor, entry=e)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    w = d.central_widget().widgets()
    w[1].text = 'test2'
    process_app_events()
    sleep(dialog_sleep)

    w[5].text = '{simp/test}, {comp/test}'
    process_app_events()
    sleep(dialog_sleep)

    b = d.builder
    assert b.used_entries[0].entry == 'root/test'
    b.remove_entry(0)
    process_app_events()
    sleep(dialog_sleep)

    w[-2].clicked = True
    process_app_events()

    e = d.entry
    assert e.name == 'test2'
    assert (sorted(e.depend_on) ==
            sorted(('root/simp/test', 'root/comp/test')))
