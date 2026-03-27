# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Smarter Scheduling

The `Scheduler` class goes beyond a simple task list with four additional capabilities:

- **Sort by time** — `sort_by_time()` orders the scheduled plan by each task's `start_time` (HH:MM), so the output reads like a real daily timeline. Tasks with no assigned time appear at the end.
- **Filter tasks** — `filter_tasks(pet_name, completed)` lets you slice the full task list by pet, by completion status, or both. Pass `None` to skip either filter.
- **Recurring tasks** — Tasks can be set to `frequency="daily"` or `frequency="weekly"`. When `complete_task()` is called, it marks the current occurrence done and automatically adds the next occurrence (calculated with `timedelta`) to the pet's task list.
- **Conflict detection** — `find_conflicts()` checks every pair of scheduled tasks with a `start_time` and returns any whose time windows overlap. It uses `itertools.combinations` to test all pairs and the standard interval-overlap test (`start_a < end_b AND start_b < end_a`). Conflicts are reported as warnings — the scheduler never crashes.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
