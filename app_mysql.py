# ============================================================
#   LeftoverFood Distribution System
#   BCA Final Year Project — by Radha
#   Python Flask + MySQL (XAMPP) + hashlib password hashing
# ============================================================
from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash, jsonify)
import pymysql, hashlib, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'leftoverfood_radha_bca_2024_secret'

# ── MYSQL CONFIG (XAMPP) ──────────────────────────────────────────
DB_HOST     = 'localhost'
DB_USER     = 'root'
DB_PASSWORD = ''           # XAMPP default = no password
DB_NAME     = 'leftoverfood'

# ── EMAIL CONFIG ──────────────────────────────────────────────────
GMAIL_ADDRESS  = 'radharoddappanavar8@gmail.com'
GMAIL_PASSWORD = 'kxrw xlzi bbzt jnws'

def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'LeftoverFood System <{GMAIL_ADDRESS}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f'[EMAIL ERROR] {e}')
        return False

def get_db():
    conn = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(plain, hashed):
    return hash_password(plain) == hashed

def time_ago(dt_val):
    if not dt_val: return ''
    try:
        if isinstance(dt_val, str):
            dt = datetime.strptime(dt_val[:19], '%Y-%m-%d %H:%M:%S')
        else:
            dt = dt_val
        diff = datetime.now() - dt
        s = int(diff.total_seconds())
        if s < 60:      return f'{s} seconds ago'
        elif s < 3600:  return f'{s//60} minutes ago'
        elif s < 86400: return f'{s//3600} hours ago'
        elif s < 604800:return f'{s//86400} days ago'
        else:           return dt.strftime('%d %b %Y')
    except:
        return str(dt_val)[:10]

app.jinja_env.globals['time_ago'] = time_ago

def init_db():
    # First create the database if it doesn't exist
    conn0 = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, charset='utf8mb4')
    with conn0.cursor() as c:
        c.execute(f'CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    conn0.commit(); conn0.close()

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS users(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            role ENUM('admin','donor','collector') NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB''')

        cur.execute('''CREATE TABLE IF NOT EXISTS food(
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            description TEXT,
            quantity VARCHAR(80) NOT NULL,
            food_type VARCHAR(80),
            address VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            phone VARCHAR(20),
            pickup_time DATETIME,
            status ENUM('Available','Collected') DEFAULT 'Available',
            user_id INT NOT NULL,
            collected_by INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(collected_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB''')

        cur.execute('''CREATE TABLE IF NOT EXISTS feedback(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB''')

        cur.execute('''CREATE TABLE IF NOT EXISTS notifications(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            is_read TINYINT(1) DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB''')

        cur.execute('''CREATE TABLE IF NOT EXISTS messages(
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL,
            receiver_id INT NOT NULL,
            message TEXT NOT NULL,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(receiver_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB''')

        cur.execute('SELECT COUNT(*) as cnt FROM users')
        if cur.fetchone()['cnt'] == 0:
            seed = [
                ('Admin User','admin@food.com','admin',hash_password('admin123'),'9000000001','admin'),
                ('Priya Sharma','priya@food.com','donor1',hash_password('donor123'),'9000000002','donor'),
                ('Ravi Kumar','ravi@food.com','donor2',hash_password('donor123'),'9000000003','donor'),
                ('Anita Verma','anita@food.com','collector1',hash_password('collect123'),'9000000004','collector'),
                ('Suresh Nair','suresh@food.com','collector2',hash_password('collect123'),'9000000005','collector'),
            ]
            cur.executemany('INSERT INTO users(name,email,username,password,phone,role) VALUES(%s,%s,%s,%s,%s,%s)', seed)
            sfood = [
                ('Biryani','Freshly cooked','5 kg','Cooked','MG Road, Bangalore','Bangalore','9000000002',None,'Available',2,None),
                ('Idli & Sambar','Morning items','50 pcs','Cooked','Koramangala, Bangalore','Bangalore','9000000002',None,'Available',2,None),
                ('Chapati & Dal','Homemade','30 pcs','Cooked','Indiranagar, Bangalore','Bangalore','9000000003',None,'Collected',3,4),
                ('Rice & Curry','South Indian','3 kg','Cooked','HSR Layout, Bangalore','Bangalore','9000000003',None,'Available',3,None),
            ]
            cur.executemany('INSERT INTO food(title,description,quantity,food_type,address,location,phone,pickup_time,status,user_id,collected_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', sfood)
    conn.commit(); conn.close()

def login_required(f):
    @wraps(f)
    def d(*a,**kw):
        if 'user_id' not in session:
            flash('Please login to access this page.','warning')
            return redirect(url_for('login'))
        return f(*a,**kw)
    return d

def role_required(*roles):
    def dec(f):
        @wraps(f)
        def d(*a,**kw):
            if 'user_id' not in session:
                flash('Please login first.','warning')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied.','danger')
                return redirect(url_for('index'))
            return f(*a,**kw)
        return d
    return dec

def add_notification(user_id, message):
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO notifications(user_id,message) VALUES(%s,%s)',(user_id,message))
    conn.commit(); conn.close()

@app.route('/api/notifications')
@login_required
def get_notifications():
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 20',(session['user_id'],))
        notifs=cur.fetchall()
        cur.execute('SELECT COUNT(*) as cnt FROM notifications WHERE user_id=%s AND is_read=0',(session['user_id'],))
        unread=cur.fetchone()['cnt']
    conn.close()
    for n in notifs:
        if isinstance(n.get('created_at'), datetime):
            n['created_at'] = n['created_at'].strftime('%d %b %Y %H:%M')
    return jsonify({'notifications':notifs,'unread':unread})

@app.route('/api/notifications/mark_read',methods=['POST'])
@login_required
def mark_notifications_read():
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute('UPDATE notifications SET is_read=1 WHERE user_id=%s',(session['user_id'],))
    conn.commit(); conn.close()
    return jsonify({'status':'ok'})

@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM food WHERE status='Available'"); avail=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM food WHERE status='Collected'"); coll=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='donor'"); donors=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='collector'"); collectors=cur.fetchone()['cnt']
        cur.execute("SELECT f.*,u.name AS donor_name FROM food f JOIN users u ON f.user_id=u.id WHERE f.status='Available' ORDER BY f.created_at DESC LIMIT 6")
        recent=cur.fetchall()
    conn.close()
    stats={'available':avail,'collected':coll,'donors':donors,'collectors':collectors}
    return render_template('index.html',stats=stats,recent=recent)

@app.route('/about')
def about(): return render_template('about.html')
@app.route('/contact')
def contact(): return render_template('contact.html')
@app.route('/gallery')
def gallery(): return render_template('gallery.html')
@app.route('/hunger_spots')
def hunger_spots(): return render_template('hunger_spots.html')

@app.route('/collectors_list')
def collectors_list():
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id,name,phone,email FROM users WHERE role='collector'")
        collectors=cur.fetchall()
    conn.close()
    return render_template('collectors_list.html',collectors=collectors)

# ── REGISTER ──────────────────────────────────────────────────────
@app.route('/register',methods=['GET','POST'])
def register():
    if 'user_id' in session: return redirect(url_for('index'))
    error=None
    if request.method=='POST':
        name=request.form.get('name','').strip()
        email=request.form.get('email','').strip().lower()
        username=request.form.get('username','').strip().lower()
        password=request.form.get('password','').strip()
        confirm=request.form.get('confirm_password','').strip()
        phone=request.form.get('phone','').strip()
        role=request.form.get('role','donor')
        if not name or not email or not username or not password:
            error='All fields marked * are required.'
        elif len(username)<4:
            error='Username must be at least 4 characters.'
        elif len(password)<6:
            error='Password must be at least 6 characters.'
        elif password!=confirm:
            error='Passwords do not match.'
        elif role not in ('donor','collector'):
            error='Invalid role selected.'
        else:
            try:
                conn=get_db()
                with conn.cursor() as cur:
                    cur.execute('INSERT INTO users(name,email,username,password,phone,role) VALUES(%s,%s,%s,%s,%s,%s)',
                                (name,email,username,hash_password(password),phone,role))
                conn.commit(); conn.close()
                flash('Registration successful! Please login.','success')
                return redirect(url_for('login'))
            except pymysql.err.IntegrityError as e:
                error='Email already registered.' if 'email' in str(e) else 'Username already taken.'
    return render_template('register.html',error=error)

# ── LOGIN ─────────────────────────────────────────────────────────
@app.route('/login',methods=['GET','POST'])
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    error=None
    if request.method=='POST':
        username=request.form.get('username','').strip()
        password=request.form.get('password','').strip()
        if not username: error='Username is required.'
        elif not password: error='Password is required.'
        else:
            conn=get_db()
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE username=%s OR email=%s',(username,username))
                user=cur.fetchone()
            conn.close()
            if user is None:
                error='No account found with that username/email.'
            elif not check_password(password,user['password']):
                error='Incorrect password. Please try again.'
            else:
                session['user_id']=user['id']; session['username']=user['username']
                session['name']=user['name']; session['role']=user['role']
                flash(f'Welcome back, {user["name"]}!','success')
                if user['role']=='admin': return redirect(url_for('admin_dashboard'))
                elif user['role']=='donor': return redirect(url_for('donor_dashboard'))
                else: return redirect(url_for('collector_dashboard'))
    return render_template('login.html',error=error)

@app.route('/logout')
def logout():
    name=session.get('name','User'); session.clear()
    flash(f'{name} logged out successfully.','info')
    return redirect(url_for('login'))

@app.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    message=None
    DEFAULT_PASSWORD='Food@1234'
    if request.method=='POST':
        email=request.form.get('email','').strip()
        if not email: message=('danger','Please enter your email address.')
        else:
            conn=get_db()
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE email=%s',(email,))
                user=cur.fetchone()
            if user:
                with conn.cursor() as cur:
                    cur.execute('UPDATE users SET password=%s WHERE email=%s',(hash_password(DEFAULT_PASSWORD),email))
                conn.commit(); conn.close()
                html=f'''
                <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:12px;overflow:hidden">
                  <div style="background:#1b5e20;padding:24px;text-align:center"><h2 style="color:#fff;margin:0">🍲 LeftoverFood System</h2></div>
                  <div style="padding:28px">
                    <p>Hello <strong>{user['name']}</strong>,</p>
                    <p>Your password has been reset successfully.</p>
                    <div style="background:#f1fdf4;border:1px solid #a5d6a7;border-radius:8px;padding:16px;text-align:center;margin:20px 0">
                      <p style="margin:0;font-size:13px;color:#555">Your new password is:</p>
                      <p style="font-size:26px;font-weight:bold;color:#1b5e20;margin:8px 0">{DEFAULT_PASSWORD}</p>
                    </div>
                    <p style="color:#e65100;font-size:13px">⚠️ Please login and change your password from Profile.</p>
                    <a href="http://127.0.0.1:5000/login" style="display:inline-block;background:#2e7d32;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold">Login Now</a>
                  </div>
                </div>'''
                sent=send_email(email,'Password Reset - LeftoverFood System',html)
                message=('success',f'Password reset! Email sent to {email}. New password: Food@1234') if sent else ('success','Password reset! New password: Food@1234')
            else:
                conn.close()
                message=('danger','No account found with that email address.')
    return render_template('forgot_password.html',message=message)

# ── ADMIN ─────────────────────────────────────────────────────────
@app.route('/admin_dashboard')
@role_required('admin')
def admin_dashboard():
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE role!='admin' ORDER BY created_at DESC"); users=cur.fetchall()
        cur.execute("SELECT f.*,u.name AS donor_name,u.phone AS donor_phone FROM food f JOIN users u ON f.user_id=u.id ORDER BY f.created_at DESC"); donations=cur.fetchall()
        cur.execute("SELECT f.*,u.name AS donor_name,c.name AS collector_name FROM food f JOIN users u ON f.user_id=u.id JOIN users c ON f.collected_by=c.id WHERE f.status='Collected'"); collections=cur.fetchall()
        cur.execute("SELECT COUNT(*) as cnt FROM users"); tu=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM food"); td=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM food WHERE status='Available'"); av=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM food WHERE status='Collected'"); co=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='donor'"); dn=cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='collector'"); cl=cur.fetchone()['cnt']
    conn.close()
    stats={'total_users':tu,'total_donations':td,'available':av,'collected':co,'donors':dn,'collectors':cl}
    return render_template('admin_dashboard.html',users=users,donations=donations,collections=collections,stats=stats)

@app.route('/delete_user/<int:uid>',methods=['POST'])
@role_required('admin')
def delete_user(uid):
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute('DELETE FROM food WHERE user_id=%s',(uid,))
        cur.execute('DELETE FROM users WHERE id=%s',(uid,))
    conn.commit(); conn.close()
    flash('User deleted.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_status/<int:food_id>',methods=['POST'])
@role_required('admin')
def admin_update_status(food_id):
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute('UPDATE food SET status=%s WHERE id=%s',(request.form.get('status','Available'),food_id))
    conn.commit(); conn.close()
    flash('Status updated.','success'); return redirect(url_for('admin_dashboard'))

# ── DONOR ─────────────────────────────────────────────────────────
@app.route('/donor_dashboard')
@role_required('donor')
def donor_dashboard():
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM food WHERE user_id=%s ORDER BY created_at DESC',(session['user_id'],))
        my_food=cur.fetchall()
    conn.close()
    stats={'total':len(my_food),'available':sum(1 for f in my_food if f['status']=='Available'),'collected':sum(1 for f in my_food if f['status']=='Collected')}
    return render_template('donor_dashboard.html',my_food=my_food,stats=stats)

@app.route('/donate',methods=['GET','POST'])
@role_required('donor')
def donate():
    error=None; conn=get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT address FROM food WHERE user_id=%s AND address!=''",(session['user_id'],))
        prev=cur.fetchall()
    if request.method=='POST':
        title=request.form.get('title','').strip(); quantity=request.form.get('quantity','').strip()
        desc=request.form.get('description','').strip(); food_type=request.form.get('food_type','').strip()
        phone=request.form.get('phone','').strip(); pickup_time=request.form.get('pickup_time','').strip() or None
        gps_lat=request.form.get('gps_lat','').strip(); gps_lng=request.form.get('gps_lng','').strip()
        gps_coords=f"{gps_lat},{gps_lng}" if gps_lat and gps_lng else request.form.get('location','').strip()
        address=request.form.get('selected_address','').strip() or request.form.get('new_address','').strip()
        if not title or not quantity or not address:
            error='Food name, quantity, and address are required.'
        else:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO food(title,description,quantity,food_type,address,location,phone,pickup_time,user_id,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'Available')",
                            (title,desc,quantity,food_type,address,gps_coords,phone,pickup_time,session['user_id']))
                conn.commit()
                cur.execute("SELECT * FROM users WHERE role='collector'")
                collectors=cur.fetchall()
            for c in collectors:
                add_notification(c['id'],f"🍲 New food available: {title} ({quantity}) at {address}")
                html=f'''<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:12px;overflow:hidden">
                  <div style="background:#1b5e20;padding:24px;text-align:center"><h2 style="color:#fff;margin:0">🍲 New Food Available!</h2></div>
                  <div style="padding:28px">
                    <p>Hello <strong>{c['name']}</strong>,</p>
                    <div style="background:#f1fdf4;border:1px solid #a5d6a7;border-radius:8px;padding:16px;margin:16px 0">
                      <p><strong>🍛 Food:</strong> {title}</p><p><strong>📦 Qty:</strong> {quantity}</p>
                      <p><strong>📍 Address:</strong> {address}</p><p><strong>👤 Donor:</strong> {session['name']}</p>
                    </div>
                    <a href="http://127.0.0.1:5000/collector_dashboard" style="display:inline-block;background:#2e7d32;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold">View & Claim</a>
                  </div></div>'''
                send_email(c['email'],f'New Food Available: {title} — LeftoverFood',html)
            conn.close(); flash('Donation added! Thank you.','success'); return redirect(url_for('donor_dashboard'))
    conn.close(); return render_template('donate.html',error=error,prev_addresses=prev)

@app.route('/delete_donation/<int:fid>',methods=['POST'])
@role_required('donor','admin')
def delete_donation(fid):
    conn=get_db()
    with conn.cursor() as cur:
        if session['role']=='admin': cur.execute('DELETE FROM food WHERE id=%s',(fid,))
        else: cur.execute('DELETE FROM food WHERE id=%s AND user_id=%s',(fid,session['user_id']))
    conn.commit(); conn.close(); flash('Donation removed.','info')
    return redirect(url_for('donor_dashboard') if session['role']=='donor' else url_for('admin_dashboard'))

# ── COLLECTOR ─────────────────────────────────────────────────────
@app.route('/collector_dashboard')
@role_required('collector')
def collector_dashboard():
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT f.*,u.name AS donor_name,u.phone AS donor_phone FROM food f JOIN users u ON f.user_id=u.id ORDER BY f.created_at DESC")
        food_items=cur.fetchall()
        cur.execute("SELECT f.*,u.name AS donor_name FROM food f JOIN users u ON f.user_id=u.id WHERE f.collected_by=%s ORDER BY f.created_at DESC",(session['user_id'],))
        my_collections=cur.fetchall()
    conn.close()
    return render_template('collector_dashboard.html',food_items=food_items,my_collections=my_collections)

@app.route('/mark_collected/<int:fid>',methods=['POST'])
@role_required('collector')
def mark_collected(fid):
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM food WHERE id=%s AND status='Available'",(fid,)); food=cur.fetchone()
    if food:
        with conn.cursor() as cur:
            cur.execute("UPDATE food SET status='Collected',collected_by=%s WHERE id=%s",(session['user_id'],fid))
        conn.commit()
        add_notification(food['user_id'],f"✅ Your donation '{food['title']}' has been collected by {session['name']}!")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE id=%s',(food['user_id'],)); donor=cur.fetchone()
        if donor:
            html=f'''<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:12px;overflow:hidden">
              <div style="background:#1b5e20;padding:24px;text-align:center"><h2 style="color:#fff;margin:0">✅ Food Collected!</h2></div>
              <div style="padding:28px">
                <p>Hello <strong>{donor['name']}</strong>,</p>
                <div style="background:#f1fdf4;border:1px solid #a5d6a7;border-radius:8px;padding:16px;margin:16px 0">
                  <p><strong>🍛 Food:</strong> {food['title']}</p><p><strong>📦 Qty:</strong> {food['quantity']}</p>
                  <p><strong>🙏 Collected by:</strong> {session['name']}</p>
                </div>
                <p style="color:#2e7d32;font-weight:bold">Thank you for your generous donation! 💚</p>
                <a href="http://127.0.0.1:5000/donor_dashboard" style="display:inline-block;background:#2e7d32;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold">View Dashboard</a>
              </div></div>'''
            send_email(donor['email'],f"Your donation '{food['title']}' has been collected!",html)
        flash('Food marked as collected!','success')
    else: flash('No longer available.','warning')
    conn.close(); return redirect(url_for('collector_dashboard'))

# ── PROFILE ───────────────────────────────────────────────────────
@app.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    conn=get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM users WHERE id=%s',(session['user_id'],)); user=cur.fetchone()
    error=None
    if request.method=='POST':
        action=request.form.get('action')
        if action=='update_profile':
            name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); phone=request.form.get('phone','').strip()
            if not name or not email: error='Name and email required.'
            else:
                try:
                    with conn.cursor() as cur:
                        cur.execute('UPDATE users SET name=%s,email=%s,phone=%s WHERE id=%s',(name,email,phone,session['user_id']))
                    conn.commit(); session['name']=name; flash('Profile updated!','success'); conn.close(); return redirect(url_for('profile'))
                except pymysql.err.IntegrityError: error='Email already used by another account.'
        elif action=='change_password':
            cur_pw=request.form.get('current_password','').strip(); new=request.form.get('new_password','').strip(); con=request.form.get('confirm_password','').strip()
            if not cur_pw or not new or not con: error='All password fields required.'
            elif not check_password(cur_pw,user['password']): error='Current password incorrect.'
            elif len(new)<6: error='New password must be at least 6 characters.'
            elif new!=con: error='New passwords do not match.'
            else:
                with conn.cursor() as cur2:
                    cur2.execute('UPDATE users SET password=%s WHERE id=%s',(hash_password(new),session['user_id']))
                conn.commit(); flash('Password changed!','success'); conn.close(); return redirect(url_for('profile'))
    conn.close(); return render_template('profile.html',user=user,error=error)

# ── SEARCH ────────────────────────────────────────────────────────
@app.route('/search',methods=['GET','POST'])
@login_required
def search_donations():
    results=[]; keyword=''
    if request.method=='POST':
        keyword=request.form.get('keyword','').strip()
        if keyword:
            like=f'%{keyword}%'; conn=get_db()
            with conn.cursor() as cur:
                cur.execute("SELECT f.*,u.name AS donor_name,u.phone AS donor_phone FROM food f JOIN users u ON f.user_id=u.id WHERE f.title LIKE %s OR f.description LIKE %s OR f.address LIKE %s ORDER BY f.created_at DESC",(like,like,like))
                results=cur.fetchall()
            conn.close()
    return render_template('search.html',results=results,keyword=keyword)

# ── MESSAGES ──────────────────────────────────────────────────────
@app.route('/messages/<int:other_id>')
@login_required
def view_messages(other_id):
    my_id=session['user_id']; conn=get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT m.*,u1.name AS sender_name,u2.name AS receiver_name FROM messages m JOIN users u1 ON m.sender_id=u1.id JOIN users u2 ON m.receiver_id=u2.id WHERE (m.sender_id=%s AND m.receiver_id=%s) OR (m.sender_id=%s AND m.receiver_id=%s) ORDER BY m.sent_at ASC",(my_id,other_id,other_id,my_id))
        chat=cur.fetchall()
        cur.execute('SELECT * FROM users WHERE id=%s',(other_id,)); other_user=cur.fetchone()
    conn.close()
    return render_template('messages.html',chat=chat,other_user=other_user,other_id=other_id)

@app.route('/send_message/<int:receiver_id>',methods=['POST'])
@login_required
def send_message(receiver_id):
    msg=request.form.get('message','').strip()
    if msg:
        conn=get_db()
        with conn.cursor() as cur:
            cur.execute('INSERT INTO messages(sender_id,receiver_id,message) VALUES(%s,%s,%s)',(session['user_id'],receiver_id,msg))
        conn.commit(); conn.close()
    return redirect(url_for('view_messages',other_id=receiver_id))

# ── FEEDBACK ──────────────────────────────────────────────────────
@app.route('/feedback',methods=['GET','POST'])
def feedback():
    conn=get_db(); error=None
    if request.method=='POST':
        name=request.form.get('name','').strip(); message=request.form.get('message','').strip()
        if not name or not message: error='Both fields required.'
        else:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO feedback(name,message) VALUES(%s,%s)',(name,message))
            conn.commit(); conn.close(); return render_template('thank_you.html')
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM feedback ORDER BY created_at DESC'); feedbacks=cur.fetchall()
    conn.close()
    return render_template('feedback.html',feedbacks=feedbacks,error=error)

if __name__=='__main__':
    init_db()
    print("\n"+"="*55)
    print("  LeftoverFood Distribution System — MySQL VERSION")
    print("="*55)
    print("  URL       : http://127.0.0.1:5000")
    print("  Admin     : admin / admin123")
    print("  Donor     : donor1 / donor123")
    print("  Collector : collector1 / collect123")
    print("  Database  : MySQL → leftoverfood (XAMPP)")
    print("="*55+"\n")
    app.run(debug=True)
