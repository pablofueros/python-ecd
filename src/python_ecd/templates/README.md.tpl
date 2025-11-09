# 🧩 Everybody Codes Solutions

My solutions to the [Everybody Codes](https://everybody.codes/) puzzles — powered by **[`python-ecd`](https://github.com/pablofueros/python-ecd)** ⚙️

> A lightweight CLI tool to fetch, test, and submit Everybody Codes challenges with ease.

---

## 📂 Project Structure

Each quest is stored under `events/<year>/quest_<id>/` and contains:

| File / Folder | Description |
|----------------|-------------|
| `solution.py` | Your Python solution with `part_1`, `part_2`, and `part_3` functions. |
| `input/` | Puzzle inputs (`input_p1.txt`, `input_p2.txt`, …) fetched automatically. |
| `test/` | Optional test files (`test_p1.txt`, …) for local validation. |

---

## ✅ Completed Quests

| Event | Quest | Part 1 | Part 2 | Part 3 |
|------|--------|--------|--------|--------|

---

## 🚀 Usage

Note that **[`python-ecd`](https://github.com/pablofueros/python-ecd)** must be installed.

```bash
# Initialize your workspace
ecd init

# Fetch a puzzle input ()
ecd pull 3  # Quest 3 of the current year

# Run your test cases
ecd test 3 --part 1

# Execute your actual input
ecd run 3 --part 1

# Submit your answer
ecd push 3 --part 1
