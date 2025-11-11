<div align="center">

<img src="https://raw.githubusercontent.com/pablofueros/python-ecd/main/assets/banner.png" alt="python-ecd logo" width="600"/>

---

### **✨ A Python CLI tool for managing Everybody Codes puzzles ✨**

[![Code Quality](https://github.com/pablofueros/python-ecd/actions/workflows/code-quality.yaml/badge.svg)](https://github.com/pablofueros/python-ecd/actions/workflows/code-quality.yaml)
[![Release](https://github.com/pablofueros/python-ecd/actions/workflows/release.yaml/badge.svg)](https://github.com/pablofueros/python-ecd/actions/workflows/release.yaml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/python-ecd.svg)](https://pypi.org/project/python-ecd/)
[![PyPI Downloads](https://static.pepy.tech/badge/python-ecd)](https://pepy.tech/projects/python-ecd)
![versions](https://img.shields.io/pypi/pyversions/python-ecd.svg)

---

</div>

## 💛 Acknowledgements

This tool relies on the [Everybody Codes Data](https://github.com/wimglenn/everybody-codes-data) library. Shout out to [@wimglenn](https://github.com/wimglenn)!

## 📋 Features

- Initialize workspace for [Everybody Codes](https://everybody.codes) puzzles
- Download puzzle inputs automatically
- Manage session tokens securely
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

The tool will be available as both 'python-ecd' and 'ecd'


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

Configure your [session token](https://github.com/wimglenn/everybody-codes-data?tab=readme-ov-file#auth) for accessing puzzle inputs:

```bash
ecd set-token <TOKEN>
```

Note that is not necessary if you set it during initialization.

### Download Puzzle Input

Download the input for all available part

```bash
ecd pull <QUEST_NUMBER> [OPTIONS]
```

Options:
- `--year`, `-y`: Event year (default: actual)
- `--force`, `-f`: Overwrite existing files

This command will create the necessary dirs and files if they do not exist.

### Test Solutions

Run your solution using test data:

```bash
ecd test <QUEST_NUMBER> [OPTIONS]
```

Options:
- `--year`: Event year (default: actual)
- `--part`: Part number to test (default: 1)

### Run Solutions

Execute your solution for a specific puzzle:

```bash
ecd run <QUEST_NUMBER> [OPTIONS]
```

Options:
- `--year`: Event year (default: actual)
- `--part`: Part number to execute (default: 1)

### Submit Solutions

Submit your solution for a specific puzzle:

```bash
ecd push <QUEST_NUMBER> [OPTIONS]
```

Options:
- `--year`: Event year (default: actual)
- `--part`: Part number to test (default: 1)

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