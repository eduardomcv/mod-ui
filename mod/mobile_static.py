#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

from tornado import web

from mod.mobile_spa import cache_control, etag, resolve_request


class MobileStaticFileHandler(web.StaticFileHandler):
    """
    Serves pistomp-chain at /m/. mod/mobile_spa.py holds the rules.

    This is not a TimelessStaticFileHandler. That class gives every file, and
    every 404, a cache of one year and no ETag, and index.html must be checked
    on each visit.
    """
    @classmethod
    def urls(cls, root):
        return [
            (r"/m", web.RedirectHandler, {"url": "/m/", "permanent": False}),
            (r"/m/(.*)", cls, {"path": root}),
        ]

    def parse_url_path(self, url_path):
        path = resolve_request(self.root, url_path)
        if path is None:
            raise web.HTTPError(404)
        return path

    def compute_etag(self):
        st = os.stat(self.absolute_path)
        return etag(st.st_mtime_ns, st.st_size)

    def get_cache_time(self, path, modified, mime_type):
        # The default gives ?v= a cache of ten years, Expires included.
        return 0

    def set_extra_headers(self, path):
        self.set_header("Cache-Control", cache_control(path))
