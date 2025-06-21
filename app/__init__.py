# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

# Инициализируем расширения без привязки к приложению сразу
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
# Указываем view для перенаправления, если пользователь не авторизован и пытается
# получить доступ к защищенной странице
login_manager.login_view = 'main.login'# Сообщение, которое будет показано пользователю
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
login_manager.login_message_category = "info" # Категория для flash-сообщений

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Загрузка конфигурации
    # Сначала из config.py по умолчанию (если он есть в папке app)
    # app.config.from_object('config.Config') # Если бы был app/config.py

    # Затем из instance/config.py (если он существует) - переопределит значения
    # Это позволяет хранить секретные ключи вне основного кода
    app_root = os.path.dirname(os.path.abspath(__file__))
    instance_config_path = os.path.join(app_root, '..', 'instance', 'config.py')
    if os.path.exists(instance_config_path):
        app.config.from_pyfile(instance_config_path)
    else:
        # Устанавливаем значения по умолчанию, если instance/config.py не найден
        # (лучше чтобы он был, но для простоты запуска)
        app.config.setdefault('SECRET_KEY', 'dev_secret_key_default') # Только для разработки!
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + os.path.join(app_root, '..', 'todo_dev.db'))
        app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
        print("WARNING: instance/config.py not found. Using default development settings.")


    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Регистрация моделей и маршрутов
    # Важно импортировать модели *после* инициализации db,
    # а маршруты *после* создания app и login_manager
    from app import routes, models
    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)

    return app