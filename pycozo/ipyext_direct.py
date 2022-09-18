from pycozo.ext_impl import CozoMagics


def auto_cozo_mode(lines):
    if lines:
        if lines[0].strip() == '%%py':
            del lines[0]
        elif not (lines[0].startswith('%') or lines[0].startswith('!')):
            lines.insert(0, '%%cozo')
    return lines


def load_ipython_extension(ipython):
    ipython.input_transformers_cleanup.append(auto_cozo_mode)
    ipython.register_magics(CozoMagics(ipython))
