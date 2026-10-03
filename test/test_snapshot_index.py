#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest

from mod import snapshot_index_after_remove


class TestSnapshotIndexAfterRemove(unittest.TestCase):
    def test_earlier_snapshot_removed(self):
        self.assertEqual(snapshot_index_after_remove(3, 1), 2)

    def test_later_snapshot_removed(self):
        self.assertEqual(snapshot_index_after_remove(1, 3), 1)

    def test_current_snapshot_removed(self):
        self.assertEqual(snapshot_index_after_remove(2, 2), -1)
        self.assertEqual(snapshot_index_after_remove(0, 0), -1)

    def test_no_current_snapshot(self):
        self.assertEqual(snapshot_index_after_remove(-1, 0), -1)


if __name__ == "__main__":
    unittest.main()
