# PawPal+

## 📸 Demo

<a href="/course_images/ai110/demo_screenshot.png" target="_blank"><img src='/course_images/ai110/demo_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>



A Streamlit app that helps busy pet owners stay consistent with daily pet care. PawPal+ generates a prioritised daily schedule across multiple pets, detects time conflicts, and automatically reschedules recurring tasks — all explained in plain language.

---

## Challenge Extensions

Five extension challenges were implemented using AI-assisted Agent Mode planning:

| Challenge | Feature | Key method |
|---|---|---|
| C1 | Next available slot finder | `Scheduler.find_next_slot()` |
| C2 | JSON persistence (auto-save/load) | `Owner.save_to_json()` / `Owner.load_from_json()` |
| C3 | Emoji priority & category indicators | `PRIORITY_EMOJI`, `CATEGORY_EMOJI`, `Task.to_dict()` |
| C4 | Professional CLI tables | `tabulate` in `main.py` |
| C5 | Multi-model prompt comparison | Documented in `reflection.md` |

**Agent Mode approach for C1 & C2:** The agent was given the full `pawpal_system.py` as context and asked to (1) design a gap-scanning algorithm that returns the earliest free slot given a duration, and (2) add round-trip JSON serialisation without breaking existing `to_dict()` display logic. The key architectural decision — keeping a separate `to_json_dict()` for serialisation and `to_dict()` for display — was a human judgment call after reviewing the agent's initial suggestion to overload a single method.

---

## Features

### Multi-pet management
Register multiple pets (dogs, cats, or other) under a single owner profile. Each pet maintains its own independent task list, and the scheduler works across all pets simultaneously.

### Priority-based scheduling
Tasks are ranked **high / medium / low**. The scheduler fills the owner's daily time budget in priority order, greedily assigning the most important tasks first. Tasks that would exceed the remaining budget are moved to a "Skipped" list with an explanation.

### Sort by start time
Once a plan is built, `sort_by_time()` reorders the schedule chronologically by each task's assigned `start_time` (HH:MM format), so the output reads like a real daily timeline. Tasks with no assigned time appear at the end.

### Conflict detection
`find_conflicts()` checks every pair of scheduled tasks that have a `start_time` and flags any whose time windows overlap using the standard interval-overlap test (`start_a < end_b AND start_b < end_a`). Conflicts are surfaced as warnings in the UI — the app never crashes or silently drops a task.

### Recurring tasks
Tasks can be set to repeat **daily** or **weekly**. When a recurring task is marked complete via `complete_task()`, the system automatically calculates the next due date using Python's `timedelta` and adds the new occurrence to the pet's task list — no manual rescheduling needed.

### Task filtering
`filter_tasks()` lets you slice the full task list by pet name, completion status, or both. Useful for quickly checking what still needs to be done for a specific pet.

### Plain-language plan explanation
`explain_plan()` produces a readable summary of every scheduled and skipped task, including the reason a task was skipped (insufficient time remaining).

---

## Project structure

```
pawpal_system.py   — all backend logic (Task, Pet, Owner, Scheduler classes)
app.py             — Streamlit UI that wires the logic to the browser
main.py            — CLI demo script for verifying logic in the terminal
tests/
  test_pawpal.py   — 14 automated tests covering core behaviours
uml_final.png      — final class diagram (rendered from uml_final.mmd)
uml_final.mmd      — Mermaid source for the class diagram
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

## Run the CLI demo

```bash
python main.py
```

---

## Testing PawPal+

```bash
python -m pytest
```

The suite in `tests/test_pawpal.py` covers 14 test cases:

| Area | What is verified |
|---|---|
| Task completion | `mark_complete()` sets `completed = True` |
| Pet task management | `add_task()` increments the task count |
| Sorting | `sort_by_time()` returns chronological order; untimed tasks sort last |
| Recurrence | Daily/weekly tasks produce a next occurrence with the correct due date; one-time tasks return `None` |
| Conflict detection | Overlapping windows are flagged; non-overlapping and untimed tasks are not |
| Edge cases | Empty pet → empty plan; over-budget task → `skipped_tasks`; calling `build_plan()` twice produces the same result |

**Confidence: ★★★★☆** — backend logic is fully tested. The Streamlit UI layer is verified manually in the browser.

---

## Architecture

The system uses four classes. See `uml_final.png` for the full diagram.

| Class | Responsibility |
|---|---|
| `Task` | Holds all data for one care activity (title, duration, priority, category, start time, frequency, due date) |
| `Pet` | Owns a list of tasks; manages adding, removing, and sorting them by priority |
| `Owner` | Holds the daily time budget and a list of pets; provides a flat view of all tasks across pets |
| `Scheduler` | Reads from `Owner` to build, sort, filter, and explain the daily plan; detects conflicts and handles recurring completions |
