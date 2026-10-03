#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
WebSocket messages that mod-ui sends from more than one place.

This module does not import tornado, so its tests run without it.
"""


def format_add_message(instance, uri, x, y, bypassed, sversion, build_env, instance_id):
    # instance_id goes last: host.js:353 reads 7 fields and drops the rest.
    return "add %s %s %.1f %.1f %d %s %d %d" % (instance, uri, x, y,
                                                int(bypassed),
                                                sversion,
                                                int(bool(build_env)),
                                                instance_id)


def format_snapshots_changed(current_idx):
    return "pedal_snapshots_changed %d" % current_idx
