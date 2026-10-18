# 🧩 Everybody Codes Solutions

Solutions to the [Everybody Codes](https://everybody.codes/) puzzles — powered by **[`python-ecd`](https://github.com/pablofueros/python-ecd)** ⚙️

> A lightweight CLI tool to fetch, test, and submit Everybody Codes challenges with ease.

---

## 📂 Project Structure

Event quests are stored under `events/<year>/quest_<id>/`; story quests use
`stories/<story>/quest_<id>/`. Each quest contains:

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
ecd token set

# Initialize your workspace
ecd init everybody-codes-solutions

# Fetch an event or story puzzle input
ecd pull <QUEST_NUMBER> --year <EVENT_YEAR>
ecd pull <QUEST_NUMBER> --story <STORY_NUMBER>

# Run your test cases for a given part
ecd test <QUEST_NUMBER> --year <EVENT_YEAR> --part=<N>

# Execute your actual input for a given part
ecd run <QUEST_NUMBER> --year <EVENT_YEAR> --part=<N>

# Submit your answer for a given part
ecd push <QUEST_NUMBER> --year <EVENT_YEAR> --part=<N>
```

Use exactly one of `--year` or `--story` with `pull`, `test`, `run`, and `push`.

For more info check the project [README](https://github.com/pablofueros/python-ecd/blob/main/README.md)
