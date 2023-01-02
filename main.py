from typing import List, Iterable

import re
import requests
from lxml import html
from lxml.html import HtmlElement
from lxml.cssselect import CSSSelector
from pathlib import Path
from jinja2 import FileSystemLoader, Environment
from itertools import chain

URL_HOMEPAGE = 'https://pygments.org/'
URL_LEXERS = 'https://pygments.org/docs/lexers/'
SELECT_LEXERS = CSSSelector('.py.class')
SELECT_LEXER_DESCRIPTION = CSSSelector('.field-list')
SELECT_LEXER_NAME = CSSSelector('.sig-name')
SELECT_HOMEPAGE_VERSION = CSSSelector('.sphinxsidebarwrapper b')
REGEXP_FILENAMES = re.compile(r'.*?Filenames:\s+?(.+?)$', re.MULTILINE | re.DOTALL)
PATH_PROJECT = Path(__file__).parent
TEMPLATE_LESSFILTER = 'template.lessfilter.sh'
TEMPLATE_OUTPUT = '.lessfilter'
INDENT = 4
INDENT_DOUBLE = INDENT * 2
INDENT_QUADRUPLE = INDENT * 4
MAX_COL_SIZE = 80

# any known shell filenames that don't have specific lexers will use the `sh` lexer
misc_shell_filenames = [".bashrc", "bash.bashrc", ".bash_aliases", ".bash_environment", ".bash_profile", ".bash_login",
                        ".bash_logout", ".profile", ".zprofile", ".zshrc", ".zlogin", ".zlogout", "zprofile", "zshrc",
                        "zlogin", "zlogout", ".cshrc", ".cshdirs", "csh.cshrc", "csh.login", "csh.logout", ".tcshrc",
                        ".kshrc", "ksh.kshrc"]
recognized_filenames = {}
recognized_extensions = {}


def main():
    print("Fetching Pygments version number from homepage...", end='')
    version = fetch_version()
    print(f'v{version}')
    print('Fetching lexers from documentation page...')
    fetch_lexers()
    print(f'  Supported filenames:\n  {recognized_filenames}')
    print(f'  Supported extensions:\n  {recognized_extensions}')
    render_template(version)
    print(f'Done.')


def fetch_version() -> str:
    page = requests.get(URL_HOMEPAGE)
    doc: HtmlElement = html.fromstring(page.content)
    version: List[HtmlElement] = SELECT_HOMEPAGE_VERSION(doc)
    if len(version) != 1:
        raise Exception('Unable to find Pygments version number.')
    return version[0].text_content()


def fetch_lexers():
    page = requests.get(URL_LEXERS)
    doc: HtmlElement = html.fromstring(page.content)
    lexers: List[HtmlElement] = SELECT_LEXERS(doc)
    for lexer in lexers:
        name = next(iter(SELECT_LEXER_NAME(lexer)), None)
        name = name.text_content() if name is not None else 'None'
        description = next(iter(SELECT_LEXER_DESCRIPTION(lexer)), None)
        description = description.text_content() if description is not None else 'None'
        m = REGEXP_FILENAMES.match(description)
        if m is not None and len(m.groups()) == 1:
            filenames: List[str] = m.group(1).split(',')
            for filename in filenames:
                filename = filename.strip()
                if '\\' not in filename:
                    if filename.startswith(r'*.'):
                        ext_values = recognized_extensions.setdefault(name, [])
                        ext_values.append(filename[1:])
                    elif filename != 'None':
                        filename_values = recognized_filenames.setdefault(name, [])
                        filename_values.append(filename)
                        # specific lexer exists; no need to use the `sh` lexer
                        try:
                            misc_shell_filenames.remove(filename)
                        except ValueError:
                            pass
        else:
            raise Exception(f'Aborted due to an unrecognized "{name}" lexer description format: {description}')


def render_template(version: str):
    env = Environment(loader=FileSystemLoader(PATH_PROJECT))
    template = env.get_template(TEMPLATE_LESSFILTER)
    template_vars = {
        'pygments_version': version,
        'misc_shell_filenames': to_bar_separated_string(chain(misc_shell_filenames),
                                                        INDENT_DOUBLE),
        'recognized_filenames': to_bar_separated_string(chain.from_iterable(recognized_filenames.values()),
                                                        INDENT_DOUBLE),
        'recognized_extensions': to_bar_separated_string(chain.from_iterable(recognized_extensions.values()),
                                                         INDENT_QUADRUPLE)
    }
    output = template.render(**template_vars)
    output_path = PATH_PROJECT.joinpath(TEMPLATE_OUTPUT)
    with output_path.open(mode='w', encoding='utf-8', newline='\n') as f:
        f.write(output)
    output_path.chmod(0o755)


def to_bar_separated_string(values: Iterable[str], indent: int):
    # remove duplicates and sort lexicographically
    values = sorted(set(values))
    # first line already indented in template
    result = ''
    line_len = indent
    for i in range(0, len(values)):
        value = values[i]
        value_len = len(value)
        if i > 0:
            result += '|'
            line_len += 1
        if line_len + value_len + 2 >= MAX_COL_SIZE:
            result += '\\\n' + (' ' * indent)
            line_len = indent
        result += value
        line_len += value_len
    return result


if __name__ == '__main__':
    main()
