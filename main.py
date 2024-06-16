from typing import List, Iterable

import argparse
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
TEMPLATE_DIR = PATH_PROJECT.joinpath('templates')
TEMPLATE_OUTPUT_LESSFILTER = '.lessfilter'
TEMPLATE_OUTPUT_README = 'README.md'
TEMPLATE_LESSFILTER = f'template{TEMPLATE_OUTPUT_LESSFILTER}.sh'
TEMPLATE_README = f'template.{TEMPLATE_OUTPUT_README}'
INDENT = 4
INDENT_DOUBLE = INDENT * 2
MAX_COL_SIZE = 80

# for each of the following, if a specific lexer is not found, `sh` is used
misc_shell_filenames = [
    ".profile",

    # bash
    "bash.bashrc",
    ".bashrc",
    ".bash_aliases",
    ".bash_completion",
    ".bash_environment",
    ".bash_history",
    ".bash_login",
    ".bash_logout",
    ".bash_profile",

    # zsh
    "zlogin",
    "zlogout",
    "zprofile",
    "zshrc",
    ".zlogin",
    ".zlogout",
    ".zprofile",
    ".zshrc",
    ".zshenv",

    # csh
    "csh.cshrc",
    "csh.login",
    "csh.logout",
    ".cshdirs",
    ".cshrc",

    # tcsh
    ".tcshrc",

    # ksh
    "ksh.kshrc"
    ".kshrc",
]
recognized_filenames = {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate_readme', action='store_true')
    args = parser.parse_args()

    print("Fetching Pygments version number from homepage...", end='')
    version = fetch_version()
    print(f'v{version}')
    print('Fetching lexers from documentation page...')
    fetch_lexers()
    print(f'  Supported filenames:\n  {recognized_filenames}')

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    render_template(env, version)
    if args.generate_readme:
        render_readme(env, version)
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
                if filename != 'None' and '\\' not in filename:
                    filename_values = recognized_filenames.setdefault(name, [])
                    filename_values.append(filename)
                    # specific lexer exists; no need to use the `sh` lexer
                    try:
                        misc_shell_filenames.remove(filename)
                    except ValueError:
                        pass
        else:
            raise Exception(f'Aborted due to an unrecognized "{name}" lexer description format: {description}')

def render_readme(env: Environment, version: str):
    template = env.get_template(TEMPLATE_README)
    template_vars = {
        'pygments_version': version
    }
    output = template.render(**template_vars)
    output_path = PATH_PROJECT.joinpath(TEMPLATE_OUTPUT_README)
    with output_path.open(mode='w', encoding='utf-8', newline='\n') as f:
        f.write(output)


def render_template(env: Environment, version: str):    
    template = env.get_template(TEMPLATE_LESSFILTER)
    template_vars = {
        'pygments_version': version,
        'misc_shell_filenames': to_bar_separated_string(chain(misc_shell_filenames),
                                                        INDENT_DOUBLE),
        'recognized_filenames': to_bar_separated_string(chain.from_iterable(recognized_filenames.values()),
                                                        INDENT_DOUBLE)
    }
    output = template.render(**template_vars)
    output_path = PATH_PROJECT.joinpath(TEMPLATE_OUTPUT_LESSFILTER)
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
