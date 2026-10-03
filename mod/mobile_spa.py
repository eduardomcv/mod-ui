#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
The rules that serve pistomp-chain, the phone UI, at /m/.

The app is a SvelteKit static build. A file under _app/immutable/ carries a hash
in its name and never changes under that name, so the browser may keep it for a
year. Every other file, index.html above all, names those files, so the browser
must ask again each time. A route of the app has no file of its own, and the
server answers it with index.html.

This module does not import tornado, so its tests run without it.
"""

import os

INDEX = "index.html"
APP_DIR = "_app"
IMMUTABLE_PREFIX = "_app/immutable/"
IMMUTABLE_CACHE_CONTROL = "max-age=31536000, immutable"
REVALIDATE_CACHE_CONTROL = "no-cache"


def resolve_request(root, url_path):
    """Gives the path, relative to root, of the file that answers url_path.

    Gives None for a 404: no root, a path that leaves root, a missing file below
    _app/, or a missing file whose name has an extension.
    """
    if not root or not os.path.isdir(root) or "\x00" in url_path:
        return None

    segments = [s for s in url_path.split("/") if s not in ("", ".")]
    if ".." in segments:
        return None
    rel = "/".join(segments)

    # realpath, not abspath: a symlink in the build must not lead out of root.
    root_real = os.path.realpath(root)

    def inside_root(path):
        return path == root_real or path.startswith(root_real + os.sep)

    target = os.path.realpath(os.path.join(root_real, rel))
    if not inside_root(target):
        return None
    if rel and os.path.isfile(target):
        return rel

    # A missing asset stays 404. index.html in its place would be cached as
    # that asset, and an immutable one for a year.
    if segments and (segments[0] == APP_DIR or "." in segments[-1]):
        return None
    index = os.path.realpath(os.path.join(root_real, INDEX))
    if inside_root(index) and os.path.isfile(index):
        return INDEX
    return None


def cache_control(rel_path):
    """Gives the Cache-Control value for the file that resolve_request chose."""
    if rel_path.startswith(IMMUTABLE_PREFIX):
        return IMMUTABLE_CACHE_CONTROL
    return REVALIDATE_CACHE_CONTROL


def etag(mtime_ns, size):
    """Gives an ETag that changes when a file is replaced.

    The ETag of tornado hashes a file once and keeps that hash for the life of
    the process, so a build copied onto a running device would keep the old
    ETag and the browser would get 304 for the old index.html.
    """
    return '"%x-%x"' % (mtime_ns, size)


def client_config(sample_rate, default_pedalboard, favorites, version):
    """Gives the values that index.html gets as template variables."""
    return {
        'sampleRate': sample_rate,
        'defaultPedalboard': default_pedalboard,
        'favorites': list(favorites),
        'version': version,
    }
