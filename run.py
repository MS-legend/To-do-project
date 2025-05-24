# run.py
from app import create_app, db # Импортируем create_app и db из пакета app
from app.models import User, Task # Убедитесь, что модели импортированы для migrate и shell_context
from dotenv import load_dotenv # Для загрузки .env файла
import os

# Загрузка переменных окружения из .env файла (если он есть)
load_dotenv()

app = create_app() # Создаем экземпляр приложения с помощью нашей фабрики

# Это нужно, чтобы Flask-Migrate и Flask-SQLAlchemy знали о ваших моделях
# при выполнении команд flask db ...
# А также для удобства работы в `flask shell`
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task}

if __name__ == '__main__':
    # Для запуска через python run.py, Flask Development Server
    # В продакшене используйте Gunicorn или другой WSGI сервер
    # Режим debug берется из переменной окружения FLASK_DEBUG
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')