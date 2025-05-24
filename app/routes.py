# app/routes.py
from flask import Blueprint, render_template, flash, redirect, url_for, request # Добавь Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app import db # Это остается, db инициализируется до импорта routes в __init__.py
from app.forms import LoginForm, RegistrationForm, TaskForm
from app.models import User, Task
# НЕ НУЖНО: from flask import current_app
# НЕ НУЖНО: def get_app(): ...

# Создаем экземпляр Blueprint
# Первый аргумент - имя блюпринта (обычно совпадает с именем модуля)
# Второй аргумент - __name__ (помогает Flask найти шаблоны и статику)
# Можно также указать url_prefix, если все маршруты блюпринта должны иметь общий префикс
bp = Blueprint('main', __name__) # Назовем его 'main'

# --- Маршруты Аутентификации ---
# Теперь используем @bp.route вместо @get_app().route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # current_user доступен здесь, т.к. Flask-Login его предоставляет
        return redirect(url_for('main.index')) # Обрати внимание: 'main.index' - имя блюпринта.имя_функции
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        # Важно: в условии для next_page, если next_page пустой, urlparse вызовет ошибку
        is_safe_next = False
        if next_page:
            parsed_next = urlparse(next_page)
            if parsed_next.netloc == '' and parsed_next.scheme == '':
                is_safe_next = True
        
        if is_safe_next:
            return redirect(next_page) # Редирект на next_page
        else:
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('main.index')) # Редирект на index если next_page не безопасен
    return render_template('login.html', title='Вход', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы успешно зарегистрированы!', 'success')
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('register.html', title='Регистрация', form=form)

# --- Маршруты для Задач (CRUD) ---
@bp.route('/')
@bp.route('/index')
@login_required
def index():
    filter_by = request.args.get('filter', 'all')
    query = Task.query.filter_by(user_id=current_user.id)
    if filter_by == 'active':
        query = query.filter_by(done=False)
    elif filter_by == 'done':
        query = query.filter_by(done=True)
    tasks = query.order_by(Task.created_at.desc()).all()
    return render_template('index.html', title='Мои Задачи', tasks=tasks, current_filter=filter_by)

@bp.route('/task/add', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data if form.due_date.data else None,
            author=current_user
        )
        db.session.add(task)
        db.session.commit()
        flash('Задача успешно добавлена!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_task.html', title='Добавить Задачу', form=form, legend='Новая задача')

@bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        flash('У вас нет прав на редактирование этой задачи.', 'danger')
        return redirect(url_for('main.index'))
    form = TaskForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.due_date = form.due_date.data if form.due_date.data else None
        db.session.commit()
        flash('Задача успешно обновлена!', 'success')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.title.data = task.title
        form.description.data = task.description
        form.due_date.data = task.due_date
    return render_template('create_task.html', title='Редактировать Задачу', form=form, legend=f'Редактирование: {task.title}')

@bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        flash('У вас нет прав на удаление этой задачи.', 'danger')
        return redirect(url_for('main.index'))
    db.session.delete(task)
    db.session.commit()
    flash('Задача удалена.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        flash('У вас нет прав на изменение этой задачи.', 'danger')
        return redirect(url_for('main.index'))
    task.done = not task.done
    db.session.commit()
    status = "выполнена" if task.done else "активна"
    flash(f'Задача "{task.title}" отмечена как {status}.', 'info')
    return redirect(url_for('main.index', filter=request.args.get('filter', 'all')))