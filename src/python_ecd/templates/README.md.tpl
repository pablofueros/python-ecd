# 🧩 Everybody Codes Solutions

Solutions to the [Everybody Codes](https://everybody.codes/) puzzles — powered by **[`python-ecd`](https://github.com/pablofueros/python-ecd)** ⚙️

> A lightweight CLI tool to fetch, test, and submit Everybody Codes challenges with ease.

---

## 📂 Project Structure

Each quest is stored under `events/<year>/quest_<id>/` and contains:

| File / Folder | Description |
|----------------|-------------|
| `solution.py` | Your Python solution with `part_1`, `part_2`, and `part_3` functions. |
| `input/` | Puzzle inputs (`input_p1.txt`, …) fetched automatically. |
| `test/` | Optional test files (`test_p1.txt`, …) for local validation. |

---

## 🚀 Usage

Note that **[`python-ecd`](https://github.com/pablofueros/python-ecd)** must be installed.

```bash
# Configure your session token using a hidden prompt
ecd set-token

# Initialize your workspace
ecd init everybody-codes-solutions

# Fetch the available puzzle input
ecd pull <QUEST_NUMBER>

# Run your test cases for a given part
ecd test <QUEST_NUMBER> --part=<N>

# Execute your actual input for a given part
ecd run <QUEST_NUMBER> --part=<N>

# Submit your answer for a given part
ecd push <QUEST_NUMBER> --part=<N>
```

For more info check the project [README](https://github.com/pablofueros/python-ecd/blob/main/README.md)
