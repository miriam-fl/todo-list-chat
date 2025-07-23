# todo_service.py
# Global array to store tasks

tasks = []

def get_tasks():
    """Return all tasks."""
    return tasks


def add_task(task):
    """Add a new task (expects a dict with at least 'id' and 'content')."""
    tasks.append(task)
    return task


def update_task(task_id, new_task):
    """Update an existing task by id."""
    for i, t in enumerate(tasks):
        if t.get('id') == task_id:
            tasks[i].update(new_task)
            return tasks[i]
    return None


def delete_task(task_id):
    """Delete a task by id."""
    global tasks
    for i, t in enumerate(tasks):
        if t.get('id') == task_id:
            removed = tasks.pop(i)
            return removed
    return None
