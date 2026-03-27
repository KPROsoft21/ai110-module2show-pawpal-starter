from pawpal_system import Task, Pet


def test_mark_complete_changes_task_status():
    """Calling mark_complete() should set completed to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high", category="walk")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", category="feeding"))

    assert len(pet.tasks) == 1
