# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the infos classes used to stored information about instruments.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


from ecpy.instruments.infos import (DriverInfos, InstrumentModelInfos,
                                    SeriesInfos, ManufacturerInfos,
                                    ManufacturerHolder, ProfileInfos)


def test_driver():
    """Test that the driver validation does work.

    """
    class FalsePlugin(object):
        """Lighter than using the real plugin.

        """
        pass
    p = FalsePlugin()
    p.starters = {'starter': None}
    p.connections = {'c1': {}, 'c2': {}, 'c3': {}}
    p.settings = {'s1': {}, 's2': {}, 's3': {}}

    # Test that when we know everything validation does work
    d = DriverInfos(starter='starter', connections={'c1': {}, 'c2': {}},
                    settings={'s2': {}, 's3': {}})
    assert d.validate(p)[0] and d.valid

    # Test validation failing because of starter
    p.starters.clear()
    assert not d.validate(p)[0] and not d.valid

    # Test validation failing because of one missing connection
    p.starters = {'starter': None}
    d.connections['c4'] = {}
    assert not d.validate(p)[0] and not d.valid

    # Test validation failing because of one missing settings
    del d.connections['c4']
    d.settings['s4'] = {}
    assert not d.validate(p)[0] and not d.valid


def create_driver_infos(id, manufacturer='M', serie='S', model='m',
                        kind='Other', architecture='a',
                        connections={'c1': {'d': 1}},
                        settings={'s1': {'s': 1}}):
    return DriverInfos(id=id, connections=connections, settings=settings,
                       infos=dict(manufacturer=manufacturer, serie=serie,
                                  model=model, kind=kind,
                                  architecture=architecture)
                       )


def test_model_update():
    """Test updating an instrument model infos using a list of drivers infos.

    """
    d = [create_driver_infos('1'),
         create_driver_infos('2', connections={'c1': {'d2': 2}, 'c2': {}}),
         create_driver_infos('3', settings={'s1': {'w': 2}, 's2': {}})
         ]
    i = InstrumentModelInfos()
    i.update(d)
    assert i.connections == {'c1': {'d': 1, 'd2': 2}, 'c2': {}}
    assert i.settings == {'s1': {'s': 1, 'w': 2}, 's2': {}}

    i.update([d[2]], removed=True)
    assert i.settings == {'s1': {'s': 1}}

    i.update([d[1]], removed=True)
    assert i.connections == {'c1': {'d': 1}}


def test_model_find_matching_drivers():
    """Test filtering the drivers based on connections and settings infos.

    """
    d = [create_driver_infos('1'),
         create_driver_infos('2', connections={'c1': {'d2': 2}, 'c2': {}}),
         create_driver_infos('3', settings={'s1': {'w': 2}, 's2': {}})
         ]
    i = InstrumentModelInfos()
    i.update(d)

    c_filtered = i.find_matching_drivers('c2')
    assert len(c_filtered) == 1 and c_filtered[0].id == '2'

    s_filtered = i.find_matching_drivers('c1', 's2')
    assert len(s_filtered) == 1 and s_filtered[0].id == '3'

    assert i.find_matching_drivers('c1') == d


def test_series():
    """Test updating the information of a serie from a list of drivers.

    """
    d = [create_driver_infos(str(i), model=m)
         for i, m in enumerate(('m1', 'm2', 'm2'))]
    s = SeriesInfos()
    s.update_models(d)

    assert len(s.instruments) == 2
    i1 = s.instruments[0]
    assert (i1.manufacturer == 'M' and i1.serie == 'S' and i1.model == 'm1' and
            i1.kind == 'Other' and
            i1.connections and i1.settings and len(i1.drivers) == 1)

    i2 = s.instruments[1]
    assert (i2.manufacturer == 'M' and i2.serie == 'S' and i2.model == 'm2' and
            i2.kind == 'Other' and
            i2.connections and i2.settings and len(i2.drivers) == 2)

    # Test filtering
    i1.kind = 'Lock-in'
    s.kind = 'Lock-in'
    assert len(s.instruments) == 1 and s.instruments[0] is i1

    # Test adding more connections/settings
    d2 = [create_driver_infos('a', model='m1', connections={'c2': {}}),
          create_driver_infos('b', model='m2', settings={'s2': {}})]
    s.update_models(d2)
    s.kind = 'All'
    assert 'c2' in s.instruments[0].connections
    assert 's2' in s.instruments[1].settings

    # Test removing drivers
    s.update_models(d2, removed=True)
    assert 'c2' not in s.instruments[0].connections
    assert 's2' not in s.instruments[1].settings

    s.update_models([d[0]], removed=True)
    assert len(s.instruments) == 1 and s.instruments[0] is i2


def test_manufaturer_using_series():
    """Test the capabilities of the manufacturer infos.

    """
    d = [create_driver_infos(m+s, model=m, serie=s,
                             kind='Lock-in' if m == 'm1' else 'Other')
         for s in ('s', 's2', '')
         for m in ('m1', 'm2', 'm2')
         ]
    m = ManufacturerInfos()
    m.update_series_and_models(d)

    assert len(m.instruments) == 4  # Two series and two models with no serie
    s_names = ['s', 's2']
    for s_or_m in m.instruments:
        if isinstance(s_or_m, SeriesInfos):
            assert s_or_m.name in s_names
            s_names.remove(s_or_m.name)

    # Filtering by kind
    m.kind = 'Lock-in'
    assert len(m.instruments) == 3
    for s_or_m in m.instruments:
        if isinstance(s_or_m, SeriesInfos):
            assert len(s_or_m.instruments) == 1

    m.kind = 'All'
    # Remove some drivers and hence update the series
    m.update_series_and_models(d[:2], removed=True)
    assert len(m.instruments) == 4
    for s_or_m in m.instruments:
        if isinstance(s_or_m, SeriesInfos) and s_or_m.name == 's':
            assert len(s_or_m.instruments) == 1

    # Remove a full serie
    m.update_series_and_models(d[:3], removed=True)
    assert len(m.instruments) == 3


def test_manufaturer_not_using_series():
    """Test the capabilities of the manufacturer infos.

    """
    d = [create_driver_infos(m+s, model=m, serie=s,
                             kind='Lock-in' if m == 'm1' else 'Other')
         for s in ('s', 's2', '')
         for m in ('m1', 'm2', 'm2')
         ]
    m = ManufacturerInfos()
    m.update_series_and_models(d)
    m.use_series = False

    assert len(m.instruments) == 6

    # Filtering by kind
    m.kind = 'Lock-in'
    assert len(m.instruments) == 3

    m.kind = 'All'
    # Remove some drivers and hence update the series
    m.update_series_and_models(d[:2], removed=True)
    assert len(m.instruments) == 5

    # Remove a full serie
    m.update_series_and_models(d[:3], removed=True)
    assert len(m.instruments) == 4


def test_holder_update_manufacturer():
    """
    """
    pass


def test_holder_filter():
    """
    """
    pass


def test_profile_members():
    """
    """
    pass


def test_profile_write():
    """
    """
    pass


def test_profile_clone():
    """
    """
    pass


def test_profile_get_connection():
    """
    """
    pass


def test_profile_get_settings():
    """
    """
    pass
