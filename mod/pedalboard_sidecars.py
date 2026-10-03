#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2012-2023 MOD Audio UG
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Files that pi-stomp keeps in a pedalboard bundle and mod-ui does not write.

Host.save writes a new bundle from memory on Save-As, so a file that only
pi-stomp writes is lost unless it is copied from the old bundle.

This module does not import tornado, so its tests run without it.
"""

import logging
import os
import shutil

SIDECAR_FILES = ("config.yml",)


def copy_sidecars(src_bundle, dst_bundle):
    """Copies each sidecar file of src_bundle into dst_bundle.

    Gives the names it copied. A file that cannot be copied is logged and
    skipped: the save must not fail for it.
    """
    copied = []
    if not src_bundle or not os.path.isdir(src_bundle):
        return copied
    if os.path.realpath(src_bundle) == os.path.realpath(dst_bundle):
        return copied

    for name in SIDECAR_FILES:
        src = os.path.join(src_bundle, name)
        if not os.path.isfile(src):
            continue
        try:
            shutil.copyfile(src, os.path.join(dst_bundle, name))
        except OSError:
            logging.exception("could not copy %s to %s", src, dst_bundle)
            continue
        copied.append(name)

    return copied
