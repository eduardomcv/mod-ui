#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest

from mod.ws_messages import format_add_message, format_snapshots_changed

# The format before the instance number was added, at all three call sites.
LEGACY_ADD = "add %s %s %.1f %.1f %d %s %d"


class TestFormatAddMessage(unittest.TestCase):
    def test_golden(self):
        msg = format_add_message("/graph/DS1", "http://example.org/ds1", 200, 150.5,
                                 False, "0_0_1_0", "", 3)
        self.assertEqual(msg, "add /graph/DS1 http://example.org/ds1 200.0 150.5 0 0_0_1_0 0 3")

    def test_flags_are_integers(self):
        msg = format_add_message("/graph/DS1", "urn:x", 0, 0, True, "1_2_3_4", "modapp", 12)
        self.assertEqual(msg.split(" ")[5:], ["1", "1_2_3_4", "1", "12"])

    def test_desktop_reads_the_legacy_seven_fields(self):
        # host.js:353 does data.split(" ", 7), which drops every field after the 7th.
        legacy = LEGACY_ADD % ("/graph/DS1", "urn:x", 10.0, 20.0, 1, "1_2_3_4", 0)
        msg = format_add_message("/graph/DS1", "urn:x", 10.0, 20.0, True, "1_2_3_4", "", 7)
        self.assertEqual(msg.split(" ")[:8], legacy.split(" "))
        self.assertEqual(msg.split(" ")[8:], ["7"])

    def test_pistomp_parser_shape(self):
        # pi-stomp modalapi/ws_protocol.py: raw.split(" ", 2), then rest.split(),
        # reading uri, x, y and bypassed from parts[0..3].
        msg = format_add_message("/graph/DS1", "urn:x", 10.0, 20.0, True, "1_2_3_4", "", 7)
        cmd, instance, rest = msg.split(" ", 2)
        parts = rest.split()
        self.assertEqual((cmd, instance, parts[0]), ("add", "/graph/DS1", "urn:x"))
        self.assertEqual((float(parts[1]), float(parts[2]), int(parts[3])), (10.0, 20.0, 1))
        self.assertEqual(int(parts[6]), 7)


class TestFormatSnapshotsChanged(unittest.TestCase):
    def test_golden(self):
        self.assertEqual(format_snapshots_changed(2), "pedal_snapshots_changed 2")

    def test_no_current_snapshot(self):
        self.assertEqual(format_snapshots_changed(-1), "pedal_snapshots_changed -1")

    def test_is_not_read_as_a_snapshot_load(self):
        # host.js:188 and pi-stomp both match the first token exactly.
        self.assertNotEqual(format_snapshots_changed(0).split(" ", 1)[0], "pedal_snapshot")


if __name__ == "__main__":
    unittest.main()
