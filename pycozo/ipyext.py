#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.

from pycozo.ext_impl import CozoMagics


def load_ipython_extension(ipython):
    ipython.register_magics(CozoMagics(ipython))
