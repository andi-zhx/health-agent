"""
医疗客户与健康档案管理系统 - 单机版
仅需 Python：运行后浏览器访问 http://localhost:5000
数据存于 medical_system.db，无 Node/npm 依赖
"""

from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import pandas as pd
from datetime import datetime

# 项目根目录（app.py 所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'))

DB_PATH = os.path.join(BASE_DIR, 'medical_system.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'exports')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_list(rows):
    return [dict(r) for r in rows]


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            id_card TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            gender TEXT,
            birth_date TEXT,
            medical_history TEXT,
            allergies TEXT,
            diet_habits TEXT,
            chronic_diseases TEXT,
            health_status TEXT,
            therapy_contraindications TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 历史数据库兼容：缺失字段时自动补齐
    c.execute('PRAGMA table_info(customers)')
    customer_columns = {row[1] for row in c.fetchall()}
    extra_customer_columns = {
        'diet_habits': 'TEXT',
        'chronic_diseases': 'TEXT',
        'health_status': 'TEXT',
        'therapy_contraindications': 'TEXT',
    }
    for col, col_type in extra_customer_columns.items():
        if col not in customer_columns:
            c.execute(f'ALTER TABLE customers ADD COLUMN {col} {col_type}')

    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            model TEXT,
            location TEXT,
            status TEXT DEFAULT 'available',
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            appointment_id INTEGER,
            usage_date TEXT NOT NULL,
            duration_minutes INTEGER,
            parameters TEXT,
            notes TEXT,
            operator TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS satisfaction_surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            appointment_id INTEGER,
            service_rating INTEGER,
            equipment_rating INTEGER,
            environment_rating INTEGER,
            staff_rating INTEGER,
            overall_rating INTEGER,
            feedback TEXT,
            suggestions TEXT,
            survey_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            height_cm REAL,
            weight_kg REAL,
            blood_pressure TEXT,
            symptoms TEXT,
            diagnosis TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS visit_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            checkin_time TEXT NOT NULL,
            purpose TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    c.execute("SELECT COUNT(*) FROM equipment")
    if c.fetchone()[0] == 0:
        for row in [
            ('红外理疗仪', '理疗设备', 'IR-2024-A', 'A区101室', 'available', '用于肌肉放松'),
            ('超声波治疗仪', '理疗设备', 'US-2024-B', 'A区102室', 'available', '深层组织治疗'),
            ('电刺激治疗仪', '康复设备', 'ES-2024-C', 'B区201室', 'available', '神经肌肉电刺激'),
            ('磁疗仪', '理疗设备', 'MT-2024-D', 'B区202室', 'available', '磁场疗法'),
            ('牵引床', '康复设备', 'TB-2024-E', 'C区301室', 'available', '颈椎腰椎牵引'),
            ('中药熏蒸舱', '中医设备', 'HC-2024-F', 'C区302室', 'available', '中药熏蒸'),
        ]:
            c.execute(
                'INSERT INTO equipment (name, type, model, location, status, description) VALUES (?,?,?,?,?,?)',
                row
            )

    conn.commit()
    conn.close()
    print('数据库初始化完成，数据文件: %s' % DB_PATH)


# ========== 静态页面 ==========
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_file(path):
    return send_from_directory(app.static_folder, path)


# ========== 客户 ==========
@app.route('/api/customers', methods=['GET'])
def api_customers_list():
    q = request.args.get('search', '')
    conn = get_db()
    c = conn.cursor()
    if q:
        c.execute(
            'SELECT * FROM customers WHERE name LIKE ? OR id_card LIKE ? OR phone LIKE ? ORDER BY created_at DESC',
            (f'%{q}%', f'%{q}%', f'%{q}%')
        )
    else:
        c.execute('SELECT * FROM customers ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/customers/<int:cid>', methods=['GET'])
def api_customer_get(cid):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM customers WHERE id = ?', (cid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': '客户不存在'}), 404
    cust = dict(row)
    c.execute(
        'SELECT a.*, e.name as equipment_name FROM appointments a JOIN equipment e ON a.equipment_id=e.id WHERE a.customer_id=? ORDER BY a.appointment_date DESC, a.start_time DESC',
        (cid,)
    )
    cust['appointments'] = row_list(c.fetchall())
    c.execute(
        'SELECT eu.*, e.name as equipment_name FROM equipment_usage eu JOIN equipment e ON eu.equipment_id=e.id WHERE eu.customer_id=? ORDER BY eu.usage_date DESC',
        (cid,)
    )
    cust['usage_records'] = row_list(c.fetchall())
    c.execute('SELECT * FROM health_records WHERE customer_id=? ORDER BY record_date DESC', (cid,))
    cust['health_records'] = row_list(c.fetchall())
    c.execute('SELECT * FROM visit_checkins WHERE customer_id=? ORDER BY checkin_time DESC', (cid,))
    cust['visit_checkins'] = row_list(c.fetchall())
    conn.close()
    return jsonify(cust)


@app.route('/api/customers', methods=['POST'])
def api_customer_create():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO customers (name, id_card, phone, email, address, gender, birth_date, medical_history, allergies, diet_habits, chronic_diseases, health_status, therapy_contraindications)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            d.get('name'), d.get('id_card'), d.get('phone'), d.get('email'), d.get('address'),
            d.get('gender'), d.get('birth_date'), d.get('medical_history'), d.get('allergies'),
            d.get('diet_habits'), d.get('chronic_diseases'), d.get('health_status'), d.get('therapy_contraindications')
        ))
        conn.commit()
        id = c.lastrowid
        conn.close()
        return jsonify({'id': id, 'message': '客户创建成功'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': '身份证号已存在'}), 400


@app.route('/api/customers/<int:cid>', methods=['PUT'])
def api_customer_update(cid):
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM customers WHERE id=?', (cid,))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': '客户不存在'}), 404
    c.execute('''
        UPDATE customers SET name=?, id_card=?, phone=?, email=?, address=?, gender=?, birth_date=?, medical_history=?, allergies=?, diet_habits=?, chronic_diseases=?, health_status=?, therapy_contraindications=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
    ''', (
        d.get('name'), d.get('id_card'), d.get('phone'), d.get('email'), d.get('address'),
        d.get('gender'), d.get('birth_date'), d.get('medical_history'), d.get('allergies'),
        d.get('diet_habits'), d.get('chronic_diseases'), d.get('health_status'), d.get('therapy_contraindications'), cid
    ))
    conn.commit()
    conn.close()
    return jsonify({'message': '更新成功'})


@app.route('/api/customers/<int:cid>', methods=['DELETE'])
def api_customer_delete(cid):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM customers WHERE id=?', (cid,))
    conn.commit()
    conn.close()
    return jsonify({'message': '已删除'})


# ========== 健康档案 ==========
@app.route('/api/health-records', methods=['GET'])
def api_health_records_list():
    customer_id = request.args.get('customer_id', type=int)
    conn = get_db()
    c = conn.cursor()
    if customer_id:
        c.execute('SELECT h.*, c.name as customer_name FROM health_records h JOIN customers c ON h.customer_id=c.id WHERE h.customer_id=? ORDER BY h.record_date DESC', (customer_id,))
    else:
        c.execute('SELECT h.*, c.name as customer_name FROM health_records h JOIN customers c ON h.customer_id=c.id ORDER BY h.record_date DESC')
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/health-records', methods=['POST'])
def api_health_record_create():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO health_records (customer_id, record_date, height_cm, weight_kg, blood_pressure, symptoms, diagnosis, notes)
        VALUES (?,?,?,?,?,?,?,?)
    ''', (
        d.get('customer_id'), d.get('record_date'), d.get('height_cm'), d.get('weight_kg'),
        d.get('blood_pressure'), d.get('symptoms'), d.get('diagnosis'), d.get('notes')
    ))
    conn.commit()
    id = c.lastrowid
    conn.close()
    return jsonify({'id': id, 'message': '健康档案已添加'}), 201


# ========== 来访签到 ==========
@app.route('/api/visit-checkins', methods=['GET'])
def api_visit_checkins_list():
    customer_id = request.args.get('customer_id', type=int)
    conn = get_db()
    c = conn.cursor()
    if customer_id:
        c.execute('SELECT v.*, c.name as customer_name FROM visit_checkins v JOIN customers c ON v.customer_id=c.id WHERE v.customer_id=? ORDER BY v.checkin_time DESC', (customer_id,))
    else:
        c.execute('SELECT v.*, c.name as customer_name FROM visit_checkins v JOIN customers c ON v.customer_id=c.id ORDER BY v.checkin_time DESC')
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/visit-checkins', methods=['POST'])
def api_visit_checkin_create():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO visit_checkins (customer_id, checkin_time, purpose, notes)
        VALUES (?,?,?,?)
    ''', (d.get('customer_id'), d.get('checkin_time') or datetime.now().strftime('%Y-%m-%d %H:%M'), d.get('purpose'), d.get('notes')))
    conn.commit()
    id = c.lastrowid
    conn.close()
    return jsonify({'id': id, 'message': '签到成功'}), 201


# ========== 设备 ==========
@app.route('/api/equipment', methods=['GET'])
def api_equipment_list():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM equipment ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/equipment/available', methods=['GET'])
def api_equipment_available():
    date = request.args.get('date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    if not all([date, start_time, end_time]):
        return jsonify({'error': '缺少 date, start_time, end_time'}), 400
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT equipment_id FROM appointments
        WHERE appointment_date=? AND status='scheduled'
        AND ((start_time<=? AND end_time>?) OR (start_time<? AND end_time>=?) OR (start_time>=? AND end_time<=?))
    ''', (date, start_time, start_time, end_time, end_time, start_time, end_time))
    booked = [r['equipment_id'] for r in c.fetchall()]
    if booked:
        ph = ','.join('?' * len(booked))
        c.execute(f"SELECT * FROM equipment WHERE status='available' AND id NOT IN ({ph}) ORDER BY name", booked)
    else:
        c.execute("SELECT * FROM equipment WHERE status='available' ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/equipment/availability-summary', methods=['GET'])
def api_equipment_availability_summary():
    date = request.args.get('date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    if not all([date, start_time, end_time]):
        return jsonify({'error': '缺少 date, start_time, end_time'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM equipment WHERE status='available' ORDER BY name")
    all_equipment = row_list(c.fetchall())
    c.execute('''
        SELECT DISTINCT equipment_id FROM appointments
        WHERE appointment_date=? AND status='scheduled'
        AND ((start_time<=? AND end_time>?) OR (start_time<? AND end_time>=?) OR (start_time>=? AND end_time<=?))
    ''', (date, start_time, start_time, end_time, end_time, start_time, end_time))
    booked_ids = {r['equipment_id'] for r in c.fetchall()}
    conn.close()

    available_equipment = [e for e in all_equipment if e['id'] not in booked_ids]
    return jsonify({
        'date': date,
        'start_time': start_time,
        'end_time': end_time,
        'total_equipment': len(all_equipment),
        'available_count': len(available_equipment),
        'booked_count': len(booked_ids),
        'available_equipment': available_equipment,
    })


# ========== 预约 ==========
@app.route('/api/appointments', methods=['GET'])
def api_appointments_list():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    conn = get_db()
    c = conn.cursor()
    sql = 'SELECT a.*, c.name as customer_name, c.phone as customer_phone, e.name as equipment_name FROM appointments a JOIN customers c ON a.customer_id=c.id JOIN equipment e ON a.equipment_id=e.id WHERE 1=1'
    params = []
    if date_from:
        sql += ' AND a.appointment_date>=?'
        params.append(date_from)
    if date_to:
        sql += ' AND a.appointment_date<=?'
        params.append(date_to)
    if status:
        sql += ' AND a.status=?'
        params.append(status)
    sql += ' ORDER BY a.appointment_date DESC, a.start_time DESC'
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/appointments', methods=['POST'])
def api_appointment_create():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM appointments WHERE equipment_id=? AND appointment_date=? AND status='scheduled'
        AND ((start_time<=? AND end_time>?) OR (start_time<? AND end_time>=?) OR (start_time>=? AND end_time<=?))
    ''', (
        d.get('equipment_id'), d.get('appointment_date'),
        d.get('start_time'), d.get('start_time'), d.get('end_time'), d.get('end_time'),
        d.get('start_time'), d.get('end_time')
    ))
    if c.fetchone()[0] > 0:
        conn.close()
        return jsonify({'error': '该时段设备已被预约'}), 400
    c.execute('''
        INSERT INTO appointments (customer_id, equipment_id, appointment_date, start_time, end_time, notes)
        VALUES (?,?,?,?,?,?)
    ''', (d.get('customer_id'), d.get('equipment_id'), d.get('appointment_date'), d.get('start_time'), d.get('end_time'), d.get('notes')))
    conn.commit()
    id = c.lastrowid
    conn.close()
    return jsonify({'id': id, 'message': '预约成功'}), 201


@app.route('/api/appointments/<int:aid>', methods=['PUT'])
def api_appointment_update(aid):
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE appointments SET customer_id=?, equipment_id=?, appointment_date=?, start_time=?, end_time=?, status=?, notes=? WHERE id=?',
              (d.get('customer_id'), d.get('equipment_id'), d.get('appointment_date'), d.get('start_time'), d.get('end_time'), d.get('status'), d.get('notes'), aid))
    conn.commit()
    conn.close()
    return jsonify({'message': '更新成功'})


@app.route('/api/appointments/<int:aid>/cancel', methods=['POST'])
def api_appointment_cancel(aid):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return jsonify({'message': '已取消'})


# ========== 设备使用 ==========
@app.route('/api/equipment-usage', methods=['GET'])
def api_equipment_usage_list():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT eu.*, c.name as customer_name, e.name as equipment_name FROM equipment_usage eu JOIN customers c ON eu.customer_id=c.id JOIN equipment e ON eu.equipment_id=e.id ORDER BY eu.usage_date DESC')
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/equipment-usage', methods=['POST'])
def api_equipment_usage_create():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO equipment_usage (customer_id, equipment_id, appointment_id, usage_date, duration_minutes, parameters, notes, operator)
        VALUES (?,?,?,?,?,?,?,?)
    ''', (d.get('customer_id'), d.get('equipment_id'), d.get('appointment_id'), d.get('usage_date'), d.get('duration_minutes'), d.get('parameters'), d.get('notes'), d.get('operator')))
    conn.commit()
    id = c.lastrowid
    conn.close()
    return jsonify({'id': id, 'message': '记录已添加'}), 201


# ========== 满意度 ==========
@app.route('/api/satisfaction-surveys', methods=['GET'])
def api_surveys_list():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT s.*, c.name as customer_name FROM satisfaction_surveys s JOIN customers c ON s.customer_id=c.id ORDER BY s.survey_date DESC')
    rows = c.fetchall()
    conn.close()
    return jsonify(row_list(rows))


@app.route('/api/satisfaction-surveys', methods=['POST'])
def api_survey_create():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO satisfaction_surveys (customer_id, appointment_id, service_rating, equipment_rating, environment_rating, staff_rating, overall_rating, feedback, suggestions)
        VALUES (?,?,?,?,?,?,?,?,?)
    ''', (d.get('customer_id'), d.get('appointment_id'), d.get('service_rating'), d.get('equipment_rating'), d.get('environment_rating'), d.get('staff_rating'), d.get('overall_rating'), d.get('feedback'), d.get('suggestions')))
    conn.commit()
    id = c.lastrowid
    conn.close()
    return jsonify({'id': id, 'message': '提交成功'}), 201


# ========== 综合查询 ==========
@app.route('/api/search', methods=['GET'])
def api_search():
    q = (request.args.get('q') or '').strip()
    kind = request.args.get('type', 'all')
    if not q and kind == 'all':
        return jsonify({'customers': [], 'health_records': [], 'appointments': [], 'visit_checkins': [], 'equipment_usage': [], 'surveys': []})

    conn = get_db()
    c = conn.cursor()
    like = f'%{q}%'
    result = {}

    if kind in ('all', 'customers'):
        c.execute('SELECT * FROM customers WHERE name LIKE ? OR id_card LIKE ? OR phone LIKE ? OR email LIKE ? OR address LIKE ? ORDER BY created_at DESC LIMIT 100',
                  (like, like, like, like, like))
        result['customers'] = row_list(c.fetchall())

    if kind in ('all', 'health'):
        c.execute('SELECT h.*, c.name as customer_name FROM health_records h JOIN customers c ON h.customer_id=c.id WHERE c.name LIKE ? OR c.id_card LIKE ? OR c.phone LIKE ? OR h.symptoms LIKE ? OR h.diagnosis LIKE ? OR h.notes LIKE ? ORDER BY h.record_date DESC LIMIT 100',
                  (like, like, like, like, like, like))
        result['health_records'] = row_list(c.fetchall())

    if kind in ('all', 'appointments'):
        c.execute('''SELECT a.*, c.name as customer_name, c.phone as customer_phone, e.name as equipment_name
            FROM appointments a JOIN customers c ON a.customer_id=c.id JOIN equipment e ON a.equipment_id=e.id
            WHERE c.name LIKE ? OR c.id_card LIKE ? OR c.phone LIKE ? OR a.notes LIKE ?
            ORDER BY a.appointment_date DESC, a.start_time DESC LIMIT 100''', (like, like, like, like))
        result['appointments'] = row_list(c.fetchall())

    if kind in ('all', 'checkins'):
        c.execute('SELECT v.*, c.name as customer_name FROM visit_checkins v JOIN customers c ON v.customer_id=c.id WHERE c.name LIKE ? OR c.id_card LIKE ? OR c.phone LIKE ? OR v.purpose LIKE ? OR v.notes LIKE ? ORDER BY v.checkin_time DESC LIMIT 100',
                  (like, like, like, like, like))
        result['visit_checkins'] = row_list(c.fetchall())

    if kind in ('all', 'usage'):
        c.execute('''SELECT eu.*, c.name as customer_name, e.name as equipment_name
            FROM equipment_usage eu JOIN customers c ON eu.customer_id=c.id JOIN equipment e ON eu.equipment_id=e.id
            WHERE c.name LIKE ? OR c.id_card LIKE ? OR c.phone LIKE ? OR eu.notes LIKE ? OR eu.operator LIKE ?
            ORDER BY eu.usage_date DESC LIMIT 100''', (like, like, like, like, like))
        result['equipment_usage'] = row_list(c.fetchall())

    if kind in ('all', 'surveys'):
        c.execute('SELECT s.*, c.name as customer_name FROM satisfaction_surveys s JOIN customers c ON s.customer_id=c.id WHERE c.name LIKE ? OR c.id_card LIKE ? OR c.phone LIKE ? OR s.feedback LIKE ? OR s.suggestions LIKE ? ORDER BY s.survey_date DESC LIMIT 100',
                  (like, like, like, like, like))
        result['surveys'] = row_list(c.fetchall())

    for key in ('customers', 'health_records', 'appointments', 'visit_checkins', 'equipment_usage', 'surveys'):
        if key not in result:
            result[key] = []

    conn.close()
    return jsonify(result)


# ========== 仪表盘 ==========
@app.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) as n FROM customers')
    total_customers = c.fetchone()['n']
    c.execute("SELECT COUNT(*) as n FROM appointments WHERE appointment_date=? AND status='scheduled'", (today,))
    today_appointments = c.fetchone()['n']
    c.execute("SELECT COUNT(*) as n FROM appointments WHERE appointment_date>=? AND status='scheduled'", (today,))
    pending = c.fetchone()['n']
    c.execute('SELECT COUNT(*) as n FROM equipment')
    total_equipment = c.fetchone()['n']
    c.execute("SELECT COUNT(*) as n FROM equipment WHERE status='available'")
    available = c.fetchone()['n']
    conn.close()
    return jsonify({
        'total_customers': total_customers,
        'today_appointments': today_appointments,
        'pending_appointments': pending,
        'total_equipment': total_equipment,
        'available_equipment': available,
    })


# ========== 导出与下载 ==========
@app.route('/api/export/customers', methods=['GET'])
def api_export_customers():
    conn = get_db()
    df = pd.read_sql_query('SELECT * FROM customers ORDER BY created_at DESC', conn)
    conn.close()
    fn = 'customers_%s.xlsx' % datetime.now().strftime('%Y%m%d_%H%M%S')
    fp = os.path.join(UPLOAD_FOLDER, fn)
    df.to_excel(fp, index=False, engine='openpyxl')
    return jsonify({'filename': fn, 'download_url': '/api/download/' + fn})


@app.route('/api/export/appointments', methods=['GET'])
def api_export_appointments():
    conn = get_db()
    df = pd.read_sql_query('''SELECT a.id, c.name as customer_name, c.phone, e.name as equipment_name, a.appointment_date, a.start_time, a.end_time, a.status, a.notes
        FROM appointments a JOIN customers c ON a.customer_id=c.id JOIN equipment e ON a.equipment_id=e.id ORDER BY a.appointment_date DESC''', conn)
    conn.close()
    fn = 'appointments_%s.xlsx' % datetime.now().strftime('%Y%m%d_%H%M%S')
    fp = os.path.join(UPLOAD_FOLDER, fn)
    df.to_excel(fp, index=False, engine='openpyxl')
    return jsonify({'filename': fn, 'download_url': '/api/download/' + fn})


@app.route('/api/export/equipment-usage', methods=['GET'])
def api_export_usage():
    conn = get_db()
    df = pd.read_sql_query('''SELECT eu.id, c.name as customer_name, e.name as equipment_name, eu.usage_date, eu.duration_minutes, eu.parameters, eu.notes, eu.operator
        FROM equipment_usage eu JOIN customers c ON eu.customer_id=c.id JOIN equipment e ON eu.equipment_id=e.id ORDER BY eu.usage_date DESC''', conn)
    conn.close()
    fn = 'equipment_usage_%s.xlsx' % datetime.now().strftime('%Y%m%d_%H%M%S')
    fp = os.path.join(UPLOAD_FOLDER, fn)
    df.to_excel(fp, index=False, engine='openpyxl')
    return jsonify({'filename': fn, 'download_url': '/api/download/' + fn})


@app.route('/api/download/<filename>', methods=['GET'])
def api_download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    init_db()
    print('请在浏览器打开: http://localhost:5000')
    app.run(host='127.0.0.1', port=5000, debug=True)
