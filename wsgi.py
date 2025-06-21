from app import create_app
import os # Для загрузки переменных окружения, если они нужны на этом уровне

# Можно загрузить .env здесь, если Render не делает это автоматически для wsgi файла,
# но обычно переменные окружения задаются в UI Render.
# from dotenv import load_dotenv
# load_dotenv()

app = create_app()

# Строка ниже не обязательна для Gunicorn, но может быть полезна для других серверов или тестов
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000)) # Render может предоставлять переменную PORT
#     app.run(host='0.0.0.0', port=port)