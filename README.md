<div align="center">

<img src="https://raw.githubusercontent.com/pablofueros/python-ecd/main/assets/banner.png" alt="python-ecd logo" width="600"/>

---

### **✨ A Python CLI tool for managing Everybody Codes puzzles ✨**

[![Code Quality](https://github.com/pablofueros/python-ecd/actions/workflows/code-quality.yml/badge.svg)](https://github.com/pablofueros/python-ecd/actions/workflows/code-quality.yml)
[![Coverage](https://codecov.io/gh/pablofueros/python-ecd/graph/badge.svg?branch=main)](https://codecov.io/gh/pablofueros/python-ecd)
[![PyPI Latest Release](https://img.shields.io/pypi/v/python-ecd.svg)](https://pypi.org/project/python-ecd/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/python-ecd.svg)](https://pypistats.org/packages/python-ecd)
[![Python](https://img.shields.io/pypi/pyversions/python-ecd.svg)](https://pypi.org/project/python-ecd/)
[![License](https://img.shields.io/pypi/l/python-ecd.svg)](LICENSE)

---

</div>

## 💛 Acknowledgements

This tool relies on the [Everybody Codes Data](https://github.com/wimglenn/everybody-codes-data) library. Shout out to [@wimglenn](https://github.com/wimglenn)!

## 📋 Features

- Initialize workspace for [Everybody Codes](https://everybody.codes) puzzles
- Keep event and story solutions in separate directory trees
- Download puzzle inputs automatically
- Configure authentication without exposing session tokens in shell history
- Run solutions with both test and real input data
- Submit solutions and check if they are correct

## 📦 Installation

The package can be installed using [uv](https://docs.astral.sh/uv/#installation), which is recommended for better dependency management and faster installations:

```bash
# Install it as a system tool
uv tool install python-ecd

# Otherwise use:
uvx python-ecd
```

The tool requires Python 3.13 or newer and is available as both `python-ecd` and
`ecd`.


## 💻 Usage

### Initialize a Workspace

Create a new workspace for your puzzles solutions:

It can be done in the current directory:

```bash
ecd init
```

Or in a specified path:

```bash
ecd init everybody-codes-solutions
```

Note that if the directory does not exist, it will be created.

Options:
- `--force`, `-f`: Overwrite existing files

### Set Session Token

Copy the session token from the **Session Cookie** section of your
[Everybody Codes profile](https://everybody.codes/profile), then store it using
an interactive hidden prompt:

```bash
ecd token set
```

The token is stored at `~/.config/ecd/token`, with access restricted to the
current user on POSIX systems. For temporary use or CI, set the `ECD_TOKEN`
environment variable instead; it takes precedence over the file.

Inspect or validate the active authentication without revealing the token:

```bash
ecd token status  # Local source and file permissions
ecd token check   # Remote validation against Everybody Codes
ecd token remove  # Remove the stored file after confirmation
```

### Download Puzzle Input

Download the input for all available parts. Select exactly one event or story:

```bash
ecd pull <QUEST_NUMBER> --year <EVENT_YEAR>
ecd pull <QUEST_NUMBER> --story <STORY_NUMBER>
```

Options:
- `--year`, `-y`: Event year
- `--story`, `-s`: Story number
- `--force`, `-f`: Overwrite existing files

Exactly one of `--year` or `--story` is required. Event quests are stored under
`events/<year>/quest_<id>/`; story quests use `stories/<story>/quest_<id>/`.
This command creates the necessary directories and files if they do not exist.

### Test Solutions

Run your solution using test data:

```bash
ecd test <QUEST_NUMBER> --year <EVENT_YEAR> [OPTIONS]
# or: ecd test <QUEST_NUMBER> --story <STORY_NUMBER> [OPTIONS]
```

Options:
- `--year`, `-y`: Event year (mutually exclusive with `--story`)
- `--story`, `-s`: Story number (mutually exclusive with `--year`)
- `--part`, `-p`: Part number to test (default: 1)

### Run Solutions

Execute your solution for a specific puzzle:

```bash
ecd run <QUEST_NUMBER> --year <EVENT_YEAR> [OPTIONS]
# or: ecd run <QUEST_NUMBER> --story <STORY_NUMBER> [OPTIONS]
```

Options:
- `--year`, `-y`: Event year (mutually exclusive with `--story`)
- `--story`, `-s`: Story number (mutually exclusive with `--year`)
- `--part`, `-p`: Part number to execute (default: 1)

### Submit Solutions

Submit your solution for a specific puzzle:

```bash
ecd push <QUEST_NUMBER> --year <EVENT_YEAR> [OPTIONS]
# or: ecd push <QUEST_NUMBER> --story <STORY_NUMBER> [OPTIONS]
```

Options:
- `--year`, `-y`: Event year (mutually exclusive with `--story`)
- `--story`, `-s`: Story number (mutually exclusive with `--year`)
- `--part`, `-p`: Part number to submit (default: 1)

Note that next available part (if exists) will be pulled automatically if the result is correct.

### Display Version

Show the current version of the tool:

```bash
ecd --version
```

## ©️ License

This project is licensed under the terms of the MIT license.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development

Install the locked environment and Git hooks, then run the same checks as CI:

```bash
make install
make format
make lint
make test
```

`make format` fixes lint issues where possible and formats the code.

Contributions target `develop`. Releases are prepared automatically from
Conventional Commits after `develop` is merged into `main`; publishing uses a
protected `pypi` environment and PyPI Trusted Publishing.
