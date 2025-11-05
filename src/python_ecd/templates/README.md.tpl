# 🧩 Everybody Codes Solutions

My solutions to the [Everybody Codes](https://everybody.codes/) puzzles (managed by the [python-ecd](https://github.com/pablofueros/python-ecd) library).

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

| Year | Quest | Part 1 | Part 2 | Part 3 |
|------|--------|--------|--------|--------|
| yyyy | n | ✅ | ⬜ | ⬜ |

---

## 🚀 Usage

```bash
# Initialize your workspace
ecd init

# Fetch a puzzle input ()
ecd get 3  # Quest 3 of the current year

# Run your test cases
ecd test 3 --part 1

# Execute your actual input
ecd run 3 --part 1
