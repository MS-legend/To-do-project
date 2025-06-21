# app/routes.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app import db
from app.forms import LoginForm, RegistrationForm, TaskForm
from app.models import User, Task
from sqlalchemy import or_, desc, asc # Убедись, что asc и desc импортированы

bp = Blueprint('main', __name__)

# --- Маршруты Аутентификации ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        is_safe_next = False
        if next_page:
            parsed_next = urlparse(next_page)
            if parsed_next.netloc == '' and parsed_next.scheme == '':
                is_safe_next = True
        if is_safe_next:
            return redirect(next_page)
        else:
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('main.index'))
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
    # Получаем параметры из URL
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'created_desc') 
    filter_by_status = request.args.get('filter', 'all')

    # Базовый запрос для задач текущего пользователя
    query = Task.query.filter_by(user_id=current_user.id)

    # Применение фильтра по статусу
    if filter_by_status == 'active':
        query = query.filter_by(done=False)
    elif filter_by_status == 'done':
        query = query.filter_by(done=True)

    # Применение поиска, если есть поисковый запрос
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term),
                Task.category.ilike(search_term)
            )
        )

    # Применение сортировки
    if sort_by == 'created_asc':
        query = query.order_by(Task.created_at.asc())
    elif sort_by == 'created_desc': 
        query = query.order_by(Task.created_at.desc())
    elif sort_by == 'due_date_asc':
        query = query.order_by(Task.due_date.asc().nullslast())
    elif sort_by == 'due_date_desc':
        query = query.order_by(Task.due_date.desc().nullsfirst())
    elif sort_by == 'status_done_first': # Сначала выполненные
        query = query.order_by(Task.done.desc(), Task.created_at.desc())
    elif sort_by == 'status_pending_first': # Сначала активные (невыполненные)
        query = query.order_by(Task.done.asc(), Task.created_at.desc())
    # Если sort_by не указан или не соответствует, сортировка по умолчанию 'created_desc' 
    # уже применится, так как это значение по умолчанию для переменной sort_by.

    tasks = query.all()
    
    return render_template('index.html', 
                           title='Мои Задачи', 
                           tasks=tasks, 
                           current_filter=filter_by_status,
                           current_sort=sort_by,
                           search_query=search_query)

@bp.route('/task/add', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data if form.category.data.strip() else 'Общее',
            due_date=form.due_date.data if form.due_date.data else None,
            author=current_user
        )
        db.session.add(task)
        db.session.commit()
        flash('Задача успешно добавлена!', 'success')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        if not form.category.data:
             form.category.data = 'Общее'
    return render_template('create_task.html', title='Добавить Задачу', form=form, legend='Новая задача')

@bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        flash('У вас нет прав на редактирование этой задачи.', 'danger')
        return redirect(url_for('main.index'))

    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.category = form.category.data if form.category.data.strip() else 'Общее'
        task.due_date = form.due_date.data if form.due_date.data else None
        db.session.commit()
        flash('Задача успешно обновлена!', 'success')
        return redirect(url_for('main.index'))
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
    # Сохраняем параметры при редиректе
    return redirect(url_for('main.index', 
                            filter=request.args.get('filter', 'all'), 
                            sort=request.args.get('sort', 'created_desc'),
                            search=request.args.get('search', '')))


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
    # Сохраняем параметры при редиректе
    return redirect(url_for('main.index', 
                            filter=request.args.get('filter', 'all'), 
                            sort=request.args.get('sort', 'created_desc'),
                            search=request.args.get('search', '')))