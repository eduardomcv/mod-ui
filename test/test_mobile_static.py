#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Serves a fake pistomp-chain build through MobileStaticFileHandler.

CI installs no Python package, so these tests are skipped there. Run them with
tornado 4.3, the version on the device, which needs Python 3.9:

    uv run --no-project --python 3.9 --with 'tornado==4.3' \\
        python -B -m unittest discover -s test -p 'test_mobile_static.py' -v
"""

import os
import shutil
import tempfile
import unittest

try:
    from tornado.testing import AsyncHTTPTestCase
    from tornado.web import Application
    HAVE_TORNADO = True
except ImportError:
    AsyncHTTPTestCase = unittest.TestCase
    HAVE_TORNADO = False

if HAVE_TORNADO:
    from mod.mobile_static import MobileStaticFileHandler

INDEX = "<!doctype html><title>chain</title>"
IMMUTABLE_JS = "_app/immutable/entry/start.abc123.js"


def write(root, rel, text):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    return path


@unittest.skipUnless(HAVE_TORNADO, "tornado is not installed")
class TestMobileStaticFileHandler(AsyncHTTPTestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "dist")
        write(self.root, "index.html", INDEX)
        write(self.root, IMMUTABLE_JS, "export {}")
        write(self.root, "_app/version.json", '{"version":"1"}')
        write(self.tmp, "secret.txt", "secret")
        AsyncHTTPTestCase.setUp(self)

    def tearDown(self):
        AsyncHTTPTestCase.tearDown(self)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def get_app(self):
        return Application(MobileStaticFileHandler.urls(self.root))

    def test_bare_prefix_redirects(self):
        resp = self.fetch("/m", follow_redirects=False)
        self.assertEqual(resp.code, 302)
        self.assertEqual(resp.headers["Location"], "/m/")

    def test_root_serves_index(self):
        resp = self.fetch("/m/")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body.decode(), INDEX)
        self.assertEqual(resp.headers["Cache-Control"], "no-cache")
        self.assertIn("Etag", resp.headers)

    def test_head_has_no_body(self):
        resp = self.fetch("/m/", method="HEAD")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b"")
        self.assertEqual(resp.headers["Cache-Control"], "no-cache")

    def test_deep_link_serves_index(self):
        resp = self.fetch("/m/boards/live")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body.decode(), INDEX)
        self.assertEqual(resp.headers["Cache-Control"], "no-cache")

    def test_immutable_asset_is_kept_a_year(self):
        resp = self.fetch("/m/" + IMMUTABLE_JS)
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.headers["Cache-Control"], "max-age=31536000, immutable")
        self.assertIn("javascript", resp.headers["Content-Type"])

    def test_version_file_is_checked(self):
        resp = self.fetch("/m/_app/version.json")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.headers["Cache-Control"], "no-cache")

    def test_missing_asset_is_404_and_not_cached(self):
        for path in ("/m/_app/immutable/entry/gone.js", "/m/_app/immutable/chunks/gone", "/m/missing.css"):
            resp = self.fetch(path)
            self.assertEqual(resp.code, 404, path)
            self.assertNotIn("max-age", resp.headers.get("Cache-Control", ""), path)
            self.assertNotIn("Expires", resp.headers, path)

    def test_unchanged_file_gives_304(self):
        first = self.fetch("/m/")
        resp = self.fetch("/m/", headers={"If-None-Match": first.headers["Etag"]})
        self.assertEqual(resp.code, 304)

    def test_replaced_file_gives_200(self):
        first = self.fetch("/m/")
        path = write(self.root, "index.html", INDEX + "<p>new build</p>")
        st = os.stat(path)
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))
        resp = self.fetch("/m/", headers={"If-None-Match": first.headers["Etag"]})
        self.assertEqual(resp.code, 200)
        self.assertIn("new build", resp.body.decode())

    def test_unchanged_file_gives_304_with_both_validators(self):
        first = self.fetch("/m/")
        resp = self.fetch("/m/", headers={
            "If-None-Match": first.headers["Etag"],
            "If-Modified-Since": first.headers["Last-Modified"],
        })
        self.assertEqual(resp.code, 304)

    def test_replaced_file_with_same_mtime_gives_200(self):
        first = self.fetch("/m/")
        path = os.path.join(self.root, "index.html")
        mtime_ns = os.stat(path).st_mtime_ns
        write(self.root, "index.html", INDEX + "<p>new build</p>")
        os.utime(path, ns=(mtime_ns, mtime_ns))
        resp = self.fetch("/m/", headers={
            "If-None-Match": first.headers["Etag"],
            "If-Modified-Since": first.headers["Last-Modified"],
        })
        self.assertEqual(resp.code, 200)
        self.assertIn("new build", resp.body.decode())

    def test_replaced_file_with_older_mtime_gives_200(self):
        first = self.fetch("/m/")
        path = os.path.join(self.root, "index.html")
        mtime_ns = os.stat(path).st_mtime_ns
        write(self.root, "index.html", INDEX + "<p>older build</p>")
        os.utime(path, ns=(mtime_ns - 3600 * 10**9, mtime_ns - 3600 * 10**9))
        resp = self.fetch("/m/", headers={
            "If-None-Match": first.headers["Etag"],
            "If-Modified-Since": first.headers["Last-Modified"],
        })
        self.assertEqual(resp.code, 200)
        self.assertIn("older build", resp.body.decode())

    def test_version_query_adds_no_long_cache(self):
        resp = self.fetch("/m/?v=1")
        self.assertEqual(resp.headers["Cache-Control"], "no-cache")
        self.assertNotIn("Expires", resp.headers)

    def test_traversal_is_404(self):
        for path in ("/m/../secret.txt", "/m/%2e%2e/secret.txt", "/m/_app/%2e%2e/%2e%2e/secret.txt"):
            resp = self.fetch(path)
            self.assertEqual(resp.code, 404, path)
            self.assertNotIn(b"secret", resp.body, path)


@unittest.skipUnless(HAVE_TORNADO, "tornado is not installed")
class TestMobileStaticFileHandlerWithoutBuild(AsyncHTTPTestCase):
    def get_app(self):
        return Application(MobileStaticFileHandler.urls("/nonexistent/pistomp-chain/"))

    def test_everything_is_404(self):
        for path in ("/m/", "/m/boards", "/m/" + IMMUTABLE_JS):
            self.assertEqual(self.fetch(path).code, 404, path)


if __name__ == "__main__":
    unittest.main()
