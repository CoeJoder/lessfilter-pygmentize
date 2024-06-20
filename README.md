# Syntax highlighter for `less`
Adds syntax highlighting to everyone's favorite terminal pager, `less`.
![screenshot](screenshot.png)

## Installation
These instructions assume an Ubuntu-based distro; modify as needed.

### 1. Install `pygmentize` & `awk`
[Pygments](https://pygments.org/) provides `pygmentize`.  Your system may already have an outdated version of Pygments installed.  If so, leave that alone and install the latest Pygments locally, giving it priority in your `$PATH`.  [Pipx](https://pipx.pypa.io/stable/) can facilitate these two tasks.

You'll also need `awk`:
```shell
# install pipx if needed
sudo apt install pipx

# add pipx-installed binaries to `$PATH` if not already
pipx ensurepath

# install Pygments and GNU awk
pipx install Pygments
sudo apt install gawk
```

### 2. Install `lesspipe` (optional, recommended)
Most Linux distros already have `lesspipe` enabled, but you can check for certain by running:
```shell
echo $LESSOPEN
```
If you don't see `lesspipe` or `lessfile` in the output, install [lesspipe](https://github.com/wofr06/lesspipe).

### 3. Configure Environment Variables
Add the following to `~/.bashrc`:
```shell
# sets LESSOPEN and LESSCLOSE variables
eval "$(SHELL=/bin/sh lesspipe)"

# interpret color characters
export LESS='-R'

# more styles available, see: `pygmentize -L styles`
export PYGMENTIZE_STYLE='paraiso-dark'

# optional
alias ls='ls --color=always'
alias grep='grep --color=always'
```
If you opted out of `lesspipe` in the previous step, replace the above `eval` statement with:
```shell
export LESSOPEN='|~/.lessfilter %s'
```

### 4. Generate `~/.lessfilter` (optional)
This repo contains a pre-generated [.lessfilter](.lessfilter) which is currently at version `2.18.0` and is updated occasionally.  You could use that and skip to the next step, even if its version lags behind that of Pygments (any unsupported file types would fallback to plain-text).

You could also generate a `.lessfilter` yourself by running [main.py](main.py), which scrapes the Pygments lexer documentation website and produces a `.lessfilter` in this directory which corresponds to the latest published version:
```shell
git clone https://github.com/CoeJoder/lessfilter-pygmentize.git
cd lessfilter-pygmentize/
pipenv install
pipenv run python main.py >/dev/null
```

### 5. Copy `.lessfilter` to `$HOME` and make it executable
```shell
# if you performed step 4, do this:
cp .lessfilter ~

# otherwise, do this:
wget -P ~ https://github.com/CoeJoder/lessfilter-pygmentize/raw/master/.lessfilter

# now make it executable
chmod +x ~/.lessfilter
```

That's it.  Test it out by running `less ~/.lessfilter`.