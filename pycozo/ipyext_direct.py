#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.

from pycozo.ext_impl import CozoMagics


def _auto_cozo_mode(lines):
    if lines:
        if lines[0].strip() == '%%py':
            del lines[0]
        elif not (lines[0].startswith('%') or lines[0].startswith('!')):
            lines.insert(0, '%%cozo')
    return lines


def load_ipython_extension(ipython):
    ipython.input_transformers_cleanup.append(_auto_cozo_mode)
    ipython.register_magics(CozoMagics(ipython))
