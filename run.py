# run.py
from app import create_app, db
from app.models import User, Task
from dotenv import load_dotenv
import os

load_dotenv()
app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task, 'Tag': Tag, 'Category': Category}

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')