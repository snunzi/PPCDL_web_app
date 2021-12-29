from app import create_app, db
from app.models import User, Assembly, Task

app = create_app()

@app.shell_context_processor
def make_shell_context():
	return {'db' : db, 'User': User, 'Assembly': Assembly, 'Notification': Notification, 'Task': Task}
