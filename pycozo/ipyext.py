from pycozo.ext_impl import CozoMagics


def load_ipython_extension(ipython):
    ipython.register_magics(CozoMagics(ipython))
