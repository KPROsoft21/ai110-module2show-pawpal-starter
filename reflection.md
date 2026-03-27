# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial design uses four classes arranged in a simple hierarchy: `Owner` has a `Pet`, the `Pet` owns a collection of `Task` objects, and a `Scheduler` reads from both `Owner` and `Pet` to produce the daily plan.

- **`Task`** — represents one pet care activity. It holds the title, duration in minutes, priority level (low/medium/high), category (walk/feeding/medication/grooming/enrichment), and a completed flag. Its responsibility is purely to describe a unit of work; it has no scheduling logic.

- **`Pet`** — represents the animal being cared for. It holds the pet's name and species, and owns the list of tasks. It is responsible for managing that list (adding, removing, and sorting tasks by priority) so that nothing outside the class needs to manipulate the list directly.

- **`Owner`** — holds context about the person providing care: their name, how many minutes they have available today, and any preferences (such as preferred walk time). Its responsibility is to be the single source of the time budget that the scheduler will respect.

- **`Scheduler`** — the core planning engine. It takes a `Pet` and an `Owner`, reads the task list and the available time, and produces a prioritized daily schedule. It is responsible for deciding which tasks fit, in what order, and for generating a plain-language explanation of those decisions.

**b. Design changes**

Yes, four changes were made during implementation:

1. **`Scheduler` stores a reference to `Owner` instead of copying `available_minutes`.** The original skeleton did `self.available_minutes = owner.available_minutes`, which snapshots the value at construction time. If `Owner.set_availability()` is called later — for example, when the user updates their schedule in the UI — the `Scheduler` would silently use a stale budget. Storing `self.owner = owner` and reading `self.owner.available_minutes` inside `build_plan()` ensures the scheduler always uses the current value.

2. **`build_plan()` resets `scheduled_tasks` and `skipped_tasks` at the start of each call.** Because these lists are initialized in `__init__`, calling `build_plan()` more than once would append to them rather than replace them, producing doubled or corrupted results. Resetting them at the top of the method makes each call produce a clean, independent plan.

3. **Added a `PRIORITY_ORDER` module-level constant** (`{"high": 3, "medium": 2, "low": 1}`). The `get_tasks_by_priority()` method on `Pet` and any sorting inside `Scheduler` both need to rank priority levels numerically. Without a shared constant, both places would need the same magic strings independently, which is fragile. A single constant at the top of the file gives both classes one place to reference.

4. **`Owner` was expanded to manage multiple pets, and `Scheduler` was updated to work across all of them.** The original UML modelled a one-to-one relationship between Owner and Pet, but the real scenario calls for managing all of a household's pets together. `Owner` now holds a `pets` list with `add_pet()` and `remove_pet()` methods, plus `get_all_tasks()` which flattens every pet's tasks into a single list of `(pet_name, task)` pairs. `Scheduler` was simplified to take only an `Owner` (instead of a separate `Pet` and `Owner`), and `build_plan()` now sorts and schedules tasks globally across all pets by priority.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints: **available time** (the owner's daily minute budget) and **task priority** (high / medium / low). Priority determines the order tasks are evaluated; available time determines whether each task fits.

Time was chosen as the hard constraint because it is a real physical limit — you cannot schedule more minutes than exist in a day. Priority was chosen as the ranking signal because the owner already assigns it when creating a task, so it directly encodes their intent without requiring the scheduler to infer importance.

**b. Tradeoffs**

The scheduler uses a **greedy priority-first algorithm**: it sorts all tasks from high to low priority and fills the time budget one task at a time, skipping any task whose duration exceeds the remaining minutes. It never backtracks.

This means a large high-priority task can consume most of the budget and cause several smaller medium-priority tasks to be skipped, even though those smaller tasks would have fit together in the same time slot if the large task had been placed differently. A more optimal approach — such as a knapsack algorithm — would consider all combinations and find the selection that maximises total value within the budget, but it is significantly more complex to implement and explain.

The greedy approach is a reasonable tradeoff here because: pet care tasks are rarely interchangeable (a walk is not a substitute for medication), the priority field already encodes the owner's intent about what matters most, and for the small task lists typical in a household app the greedy result is usually good enough. Optimality matters more when tasks are fungible and budgets are tight — neither is consistently true in this scenario.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

The suite covers 14 cases across six areas: task completion status, pet task management, sort order correctness (including the edge case of tasks with no start time), daily and weekly recurrence (verifying the exact due date and that the next occurrence is added to the pet), conflict detection (overlapping, non-overlapping, and untimed tasks), and scheduler edge cases (empty pet, task exceeding the budget, and idempotent `build_plan()` calls).

These tests matter because the scheduler's greedy logic, time arithmetic, and interval-overlap test are all easy to get subtly wrong — especially the recurring task due-date calculation and the double-call reset behaviour. Automated tests catch regressions immediately if any of that logic changes.

**b. Confidence**

★★★★☆ — confident in the backend logic. The scheduling, sorting, recurrence, and conflict detection all have direct test coverage and pass cleanly. The main untested area is the Streamlit UI layer: session state persistence, form submissions, and the display of results are only verified manually in the browser. If more time were available, the next tests to add would be: removing a pet mid-session and verifying its tasks disappear from the plan, marking a weekly task complete multiple times in a row, and testing conflict detection when more than two tasks overlap simultaneously.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
