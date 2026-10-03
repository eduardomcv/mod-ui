#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import shutil
import tempfile
import unittest

from mod import mobile_spa

IMMUTABLE_JS = "_app/immutable/entry/start.abc123.js"


def write(root, rel, text):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    return path


class TestResolveRequest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "dist")
        write(self.root, "index.html", "<!doctype html>")
        write(self.root, IMMUTABLE_JS, "export {}")
        write(self.root, "_app/version.json", '{"version":"1"}')
        write(self.root, "icon.svg", "<svg/>")
        self.secret = write(self.tmp, "secret.txt", "secret")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def resolve(self, url_path):
        return mobile_spa.resolve_request(self.root, url_path)

    def test_root_gives_index(self):
        self.assertEqual(self.resolve(""), "index.html")
        self.assertEqual(self.resolve("./"), "index.html")

    def test_existing_files_are_served(self):
        self.assertEqual(self.resolve("index.html"), "index.html")
        self.assertEqual(self.resolve(IMMUTABLE_JS), IMMUTABLE_JS)
        self.assertEqual(self.resolve("_app/version.json"), "_app/version.json")
        self.assertEqual(self.resolve("icon.svg"), "icon.svg")

    def test_repeated_slashes_collapse(self):
        self.assertEqual(self.resolve("_app//immutable/entry/start.abc123.js"), IMMUTABLE_JS)

    def test_deep_link_gives_index(self):
        self.assertEqual(self.resolve("boards"), "index.html")
        self.assertEqual(self.resolve("boards/live/"), "index.html")
        self.assertEqual(self.resolve("settings/wifi"), "index.html")

    def test_missing_file_with_extension_is_404(self):
        self.assertIsNone(self.resolve("missing.js"))
        self.assertIsNone(self.resolve("boards/cover.png"))
        self.assertIsNone(self.resolve("favicon.ico"))

    def test_missing_file_below_app_is_404(self):
        self.assertIsNone(self.resolve("_app/immutable/entry/gone.js"))
        self.assertIsNone(self.resolve("_app/immutable/chunks/gone"))
        self.assertIsNone(self.resolve("_app"))
        self.assertIsNone(self.resolve("_app/"))

    def test_directory_is_not_a_file(self):
        self.assertIsNone(self.resolve("_app/immutable"))

    def test_parent_segment_is_404(self):
        self.assertIsNone(self.resolve("../secret.txt"))
        self.assertIsNone(self.resolve("_app/../../secret.txt"))
        self.assertIsNone(self.resolve("boards/../index.html"))

    def test_absolute_path_stays_below_root(self):
        self.assertIsNone(self.resolve(self.secret))
        self.assertEqual(self.resolve("/etc/passwd"), "index.html")

    def test_symlink_out_of_root_is_404(self):
        os.symlink(self.secret, os.path.join(self.root, "link.txt"))
        self.assertIsNone(self.resolve("link.txt"))

    def test_nul_byte_is_404(self):
        self.assertIsNone(self.resolve("index.html\x00.js"))

    def test_missing_root_is_404(self):
        missing = os.path.join(self.tmp, "not-installed")
        self.assertIsNone(mobile_spa.resolve_request(missing, ""))
        self.assertIsNone(mobile_spa.resolve_request(missing, "boards"))
        self.assertIsNone(mobile_spa.resolve_request("", ""))
        self.assertIsNone(mobile_spa.resolve_request(None, ""))

    def test_root_without_index_is_404(self):
        empty = os.path.join(self.tmp, "empty")
        os.mkdir(empty)
        self.assertIsNone(mobile_spa.resolve_request(empty, ""))
        self.assertIsNone(mobile_spa.resolve_request(empty, "boards"))


class TestCacheControl(unittest.TestCase):
    def test_immutable_files_are_kept_a_year(self):
        self.assertEqual(mobile_spa.cache_control(IMMUTABLE_JS), "max-age=31536000, immutable")

    def test_every_other_file_is_checked(self):
        for path in ("index.html", "_app/version.json", "icon.svg", "_app/immutablex/a.js"):
            self.assertEqual(mobile_spa.cache_control(path), "no-cache", path)


class TestEtag(unittest.TestCase):
    def test_format(self):
        self.assertEqual(mobile_spa.etag(255, 16), '"ff-10"')

    def test_changes_with_mtime_and_size(self):
        self.assertNotEqual(mobile_spa.etag(1, 10), mobile_spa.etag(2, 10))
        self.assertNotEqual(mobile_spa.etag(1, 10), mobile_spa.etag(1, 11))


if __name__ == "__main__":
    unittest.main()
