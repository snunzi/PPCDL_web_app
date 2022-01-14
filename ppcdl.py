from app import create_app, db
from app.models import User, Task, Run

app = create_app()

@app.shell_context_processor
def make_shell_context():
	return {'db' : db, 'User': User, 'Notification': Notification, 'Task': Task, 'Run': Run}
