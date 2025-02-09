"""Utils for formatting output in Jupyter notebooks"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/04_format.ipynb.

# %% auto 0
__all__ = ['init_pygments', 'code_pygments', 'code_markdown']

# %% ../nbs/api/04_format.ipynb 3
from fastcore.all import *
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from IPython.display import display_html, display_markdown

# %% ../nbs/api/04_format.ipynb 4
def init_pygments():
    "Call this at the beginning of the notebook"
    display_html(f"<style>{HtmlFormatter().get_style_defs()}</style>", raw=True)

# %% ../nbs/api/04_format.ipynb 5
def code_pygments(c: str,
         language: str):
    "Display code with syntax highlighting"
    lexer = get_lexer_by_name(language)
    display_html(highlight(c, lexer, HtmlFormatter()), raw=True)

# %% ../nbs/api/04_format.ipynb 6
def code_markdown(c: str, lang: str):
    display_markdown(f"""```{lang}
{c}
```""", raw = True)
