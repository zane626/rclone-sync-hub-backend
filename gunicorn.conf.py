def on_starting():
    from app.tasks.task_manager.manager import initialize_the_project
    initialize_the_project()
