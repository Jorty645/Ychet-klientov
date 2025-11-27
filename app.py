# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime  # Убедитесь, что этот импорт есть

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-123'

def get_db():
    """Подключение к базе данных"""
    conn = sqlite3.connect('clients.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_db()
    
    # Создаем таблицы
    conn.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            email TEXT,
            phone TEXT,
            registration_date DATE DEFAULT CURRENT_DATE,
            address TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            order_date DATE DEFAULT CURRENT_DATE,
            order_number TEXT UNIQUE,
            description TEXT,
            total_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Новый',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')
    
    # Добавляем тестовые данные, если их нет
    count = conn.execute('SELECT COUNT(*) as count FROM clients').fetchone()['count']
    if count == 0:
        test_data = [
            ('Иванов', 'Иван', 'Иванович', 'ivanov@test.ru', '+79991234567', 'Москва', 'Постоянный клиент'),
            ('Петрова', 'Мария', 'Сергеевна', 'petrova@test.ru', '+79992345678', 'СПб', 'Новый клиент'),
            ('Сидоров', 'Алексей', 'Петрович', 'sidorov@test.ru', '+79993456789', 'Екатеринбург', 'VIP клиент')
        ]
        
        for data in test_data:
            conn.execute(
                'INSERT INTO clients (last_name, first_name, middle_name, email, phone, address, notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
                data
            )
        
        # Тестовые заказы
        orders_data = [
            (1, '2024-01-15', 'ORD-001', 'Разработка сайта', 50000, 'Завершен'),
            (1, '2024-02-20', 'ORD-002', 'Техническая поддержка', 15000, 'В работе'),
            (2, '2024-03-01', 'ORD-003', 'Дизайн логотипа', 25000, 'Завершен')
        ]
        
        for order in orders_data:
            conn.execute(
                'INSERT INTO orders (client_id, order_date, order_number, description, total_amount, status) VALUES (?, ?, ?, ?, ?, ?)',
                order
            )
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

# Маршруты для клиентов
@app.route('/')
def index():
    """Главная страница"""
    conn = get_db()
    
    stats = conn.execute('''
        SELECT 
            (SELECT COUNT(*) FROM clients) as total_clients,
            (SELECT COUNT(*) FROM orders) as total_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders) as total_revenue
    ''').fetchone()
    
    conn.close()
    return render_template('index.html', stats=stats)

@app.route('/clients')
def clients():
    """Страница клиентов"""
    search = request.args.get('search', '')
    conn = get_db()
    
    if search:
        clients_data = conn.execute(
            'SELECT * FROM clients WHERE last_name LIKE ? OR first_name LIKE ? OR email LIKE ? ORDER BY created_at DESC',
            (f'%{search}%', f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        clients_data = conn.execute('SELECT * FROM clients ORDER BY created_at DESC').fetchall()
    
    conn.close()
    return render_template('clients.html', clients=clients_data, search=search)

@app.route('/clients/add', methods=['GET', 'POST'])
def add_client():
    """Добавление клиента"""
    if request.method == 'POST':
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        notes = request.form.get('notes', '')
        
        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO clients (last_name, first_name, middle_name, email, phone, address, notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (last_name, first_name, middle_name, email, phone, address, notes)
            )
            conn.commit()
            flash('Клиент успешно добавлен!', 'success')
        except Exception as e:
            flash(f'Ошибка при добавлении клиента: {e}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('clients'))
    
    return render_template('add_client.html')

@app.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    """Редактирование клиента"""
    conn = get_db()
    
    if request.method == 'POST':
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        registration_date = request.form.get('registration_date', '')
        address = request.form.get('address', '')
        notes = request.form.get('notes', '')
        
        try:
            conn.execute('''
                UPDATE clients SET 
                last_name=?, first_name=?, middle_name=?, email=?, phone=?, 
                registration_date=?, address=?, notes=?
                WHERE id=?
            ''', (last_name, first_name, middle_name, email, phone, registration_date, address, notes, client_id))
            conn.commit()
            flash('Данные клиента успешно обновлены!', 'success')
        except Exception as e:
            flash(f'Ошибка при обновлении клиента: {e}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('clients'))
    
    # GET запрос - показываем форму редактирования
    client = conn.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
    conn.close()
    
    if not client:
        flash('Клиент не найден!', 'error')
        return redirect(url_for('clients'))
    
    return render_template('edit_client.html', client=client)

@app.route('/clients/delete/<int:client_id>')
def delete_client(client_id):
    """Удаление клиента"""
    conn = get_db()
    try:
        # Сначала удаляем связанные заказы
        conn.execute('DELETE FROM orders WHERE client_id = ?', (client_id,))
        # Затем удаляем клиента
        conn.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        conn.commit()
        flash('Клиент и его заказы успешно удалены!', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении клиента: {e}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('clients'))

# Маршруты для заказов
@app.route('/orders')
def orders():
    """Страница заказов"""
    conn = get_db()
    orders_data = conn.execute('''
        SELECT o.*, c.last_name, c.first_name, c.middle_name
        FROM orders o 
        LEFT JOIN clients c ON o.client_id = c.id 
        ORDER BY o.created_at DESC
    ''').fetchall()
    
    conn.close()
    return render_template('orders.html', orders=orders_data)

@app.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    """Добавление заказа"""
    conn = get_db()
    
    if request.method == 'POST':
        client_id = request.form['client_id']
        order_date = request.form.get('order_date', datetime.now().strftime('%Y-%m-%d'))
        order_number = request.form['order_number']
        description = request.form.get('description', '')
        total_amount = request.form.get('total_amount', 0)
        status = request.form.get('status', 'Новый')
        
        try:
            conn.execute(
                'INSERT INTO orders (client_id, order_date, order_number, description, total_amount, status) VALUES (?, ?, ?, ?, ?, ?)',
                (client_id, order_date, order_number, description, total_amount, status)
            )
            conn.commit()
            flash('Заказ успешно добавлен!', 'success')
        except Exception as e:
            flash(f'Ошибка при добавлении заказа: {e}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('orders'))
    
    # GET запрос - показываем форму добавления
    clients_data = conn.execute('SELECT id, last_name, first_name, middle_name FROM clients ORDER BY last_name, first_name').fetchall()
    conn.close()
    
    # Передаем текущую дату в шаблон
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_order.html', clients=clients_data, current_date=current_date)

@app.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    """Редактирование заказа"""
    conn = get_db()
    
    if request.method == 'POST':
        client_id = request.form['client_id']
        order_date = request.form.get('order_date', '')
        order_number = request.form['order_number']
        description = request.form.get('description', '')
        total_amount = request.form.get('total_amount', 0)
        status = request.form.get('status', 'Новый')
        
        try:
            conn.execute('''
                UPDATE orders SET 
                client_id=?, order_date=?, order_number=?, description=?, total_amount=?, status=?
                WHERE id=?
            ''', (client_id, order_date, order_number, description, total_amount, status, order_id))
            conn.commit()
            flash('Заказ успешно обновлен!', 'success')
        except Exception as e:
            flash(f'Ошибка при обновлении заказа: {e}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('orders'))
    
    # GET запрос - показываем форму редактирования
    order = conn.execute('''
        SELECT o.*, c.last_name, c.first_name, c.middle_name
        FROM orders o 
        LEFT JOIN clients c ON o.client_id = c.id 
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    
    clients_data = conn.execute('SELECT id, last_name, first_name, middle_name FROM clients ORDER BY last_name, first_name').fetchall()
    conn.close()
    
    if not order:
        flash('Заказ не найден!', 'error')
        return redirect(url_for('orders'))
    
    return render_template('edit_order.html', order=order, clients=clients_data)

@app.route('/orders/delete/<int:order_id>')
def delete_order(order_id):
    """Удаление заказа"""
    conn = get_db()
    try:
        conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        conn.commit()
        flash('Заказ успешно удален!', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении заказа: {e}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('orders'))

@app.route('/reports')
def reports():
    """Страница отчетов"""
    conn = get_db()
    
    clients_stats = conn.execute('''
        SELECT 
            COUNT(*) as total_clients,
            COUNT(DISTINCT strftime('%Y-%m', registration_date)) as active_months
        FROM clients
    ''').fetchone()
    
    orders_stats = conn.execute('''
        SELECT status, COUNT(*) as count, SUM(total_amount) as total
        FROM orders 
        GROUP BY status
    ''').fetchall()
    
    conn.close()
    return render_template('reports.html', clients_stats=clients_stats, orders_stats=orders_stats)

@app.route('/test')
def test():
    """Тестовая страница"""
    return '''
    <h1>✅ Тестовая страница работает!</h1>
    <p>Flask работает корректно.</p>
    <ul>
        <li><a href="/">Главная</a></li>
        <li><a href="/clients">Клиенты</a></li>
        <li><a href="/orders">Заказы</a></li>
        <li><a href="/reports">Отчеты</a></li>
    </ul>
    '''

if __name__ == '__main__':
    print("🚀 Запуск системы учета клиентов...")
    init_db()
    print("🌐 Сервер запущен: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)