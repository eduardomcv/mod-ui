#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import shutil
import tempfile
import unittest

from mod.pedalboard_sidecars import copy_sidecars

CONFIG = "hardware:\n  version: 3.0\n"


class TestCopySidecars(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "Old.pedalboard")
        self.dst = os.path.join(self.tmp, "New.pedalboard")
        os.mkdir(self.src)
        os.mkdir(self.dst)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_config(self, bundle):
        with open(os.path.join(bundle, "config.yml"), "w") as fh:
            fh.write(CONFIG)

    def test_config_is_copied(self):
        self.write_config(self.src)
        self.assertEqual(copy_sidecars(self.src, self.dst), ["config.yml"])
        with open(os.path.join(self.dst, "config.yml")) as fh:
            self.assertEqual(fh.read(), CONFIG)

    def test_source_without_config(self):
        self.assertEqual(copy_sidecars(self.src, self.dst), [])
        self.assertEqual(os.listdir(self.dst), [])

    def test_untitled_board_has_no_source(self):
        # Host.pedalboard_path is "" for an untitled board and after a default load.
        self.assertEqual(copy_sidecars("", self.dst), [])
        self.assertEqual(copy_sidecars(None, self.dst), [])

    def test_deleted_source_bundle(self):
        self.assertEqual(copy_sidecars(os.path.join(self.tmp, "Gone.pedalboard"), self.dst), [])

    def test_same_bundle_is_left_alone(self):
        self.write_config(self.src)
        self.assertEqual(copy_sidecars(self.src, self.src), [])

    def test_config_directory_is_not_a_file(self):
        os.mkdir(os.path.join(self.src, "config.yml"))
        self.assertEqual(copy_sidecars(self.src, self.dst), [])

    def test_failed_copy_does_not_raise(self):
        self.write_config(self.src)
        missing = os.path.join(self.tmp, "Missing.pedalboard")
        with self.assertLogs(level="ERROR"):
            self.assertEqual(copy_sidecars(self.src, missing), [])

    def test_mod_ui_files_are_not_copied(self):
        self.write_config(self.src)
        with open(os.path.join(self.src, "manifest.ttl"), "w") as fh:
            fh.write("old")
        copy_sidecars(self.src, self.dst)
        self.assertEqual(os.listdir(self.dst), ["config.yml"])


if __name__ == "__main__":
    unittest.main()
