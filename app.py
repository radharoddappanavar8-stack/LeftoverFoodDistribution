# ============================================================
#   LeftoverFood Distribution System
#   BCA Final Year Project — by Radha
#   Python Flask + SQLite + hashlib password hashing
# ============================================================
from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash)
import sqlite3, hashlib, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'leftoverfood_radha_bca_2024_secret'
DATABASE = 'leftoverfood.db'

# ── EMAIL CONFIG ─────────────────────────────────────────────────
GMAIL_ADDRESS  = 'radharoddappanavar8@gmail.com'
GMAIL_PASSWORD = 'kxrw xlzi bbzt jnws'

def send_email(to_email, subject, html_body):
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'LeftoverFood System <{GMAIL_ADDRESS}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))
        import smtplib
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f'[EMAIL ERROR] {e}')
        return False

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(plain, hashed):
    return hash_password(plain) == hashed

def time_ago(dt_str):
    if not dt_str: return ''
    try:
        from datetime import datetime
        dt = datetime.strptime(str(dt_str)[:19], '%Y-%m-%d %H:%M:%S')
        diff = datetime.now() - dt
        s = int(diff.total_seconds())
        if s < 60: return f'{s} seconds ago'
        elif s < 3600: return f'{s//60} minutes ago'
        elif s < 86400: return f'{s//3600} hours ago'
        elif s < 604800: return f'{s//86400} days ago'
        else: return dt.strftime('%d %b %Y')
    except: return str(dt_str)[:10]

app.jinja_env.globals['time_ago'] = time_ago

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,phone TEXT,
        role TEXT NOT NULL CHECK(role IN('admin','donor','collector')),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS food(
        id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,
        description TEXT,quantity TEXT NOT NULL,food_type TEXT,
        address TEXT NOT NULL,location TEXT,phone TEXT,pickup_time TEXT,
        status TEXT DEFAULT 'Available',user_id INTEGER NOT NULL,
        collected_by INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(collected_by) REFERENCES users(id))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,
        message TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,
        message TEXT NOT NULL,is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,message TEXT NOT NULL,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(receiver_id) REFERENCES users(id))''')
    if cur.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        seed = [
            ('Admin User','admin@food.com','admin',hash_password('admin123'),'9000000001','admin'),
            ('Priya Sharma','priya@food.com','donor1',hash_password('donor123'),'9000000002','donor'),
            ('Ravi Kumar','ravi@food.com','donor2',hash_password('donor123'),'9000000003','donor'),
            ('Anita Verma','anita@food.com','collector1',hash_password('collect123'),'9000000004','collector'),
            ('Suresh Nair','suresh@food.com','collector2',hash_password('collect123'),'9000000005','collector'),
        ]
        cur.executemany('INSERT INTO users(name,email,username,password,phone,role) VALUES(?,?,?,?,?,?)',seed)
        sfood = [
            ('Biryani','Freshly cooked','5 kg','Cooked','MG Road, Bangalore','Bangalore','9000000002','2025-12-31 20:00','Available',2,None),
            ('Idli & Sambar','Morning items','50 pcs','Cooked','Koramangala, Bangalore','Bangalore','9000000002','2025-12-31 12:00','Available',2,None),
            ('Chapati & Dal','Homemade','30 pcs','Cooked','Indiranagar, Bangalore','Bangalore','9000000003','2025-12-31 15:00','Collected',3,4),
            ('Rice & Curry','South Indian','3 kg','Cooked','HSR Layout, Bangalore','Bangalore','9000000003','2025-12-31 18:00','Available',3,None),
        ]
        cur.executemany('INSERT INTO food(title,description,quantity,food_type,address,location,phone,pickup_time,status,user_id,collected_by) VALUES(?,?,?,?,?,?,?,?,?,?,?)',sfood)
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
                flash('Access denied. Insufficient permissions.','danger')
                return redirect(url_for('index'))
            return f(*a,**kw)
        return d
    return dec

def add_notification(user_id, message):
    conn=get_db()
    conn.execute('INSERT INTO notifications(user_id,message) VALUES(?,?)',(user_id,message))
    conn.commit(); conn.close()

@app.route('/api/notifications')
@login_required
def get_notifications():
    from flask import jsonify
    conn=get_db()
    notifs=conn.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 20',(session['user_id'],)).fetchall()
    unread=conn.execute('SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0',(session['user_id'],)).fetchone()[0]
    conn.close()
    return jsonify({'notifications':[dict(n) for n in notifs],'unread':unread})

@app.route('/api/notifications/mark_read',methods=['POST'])
@login_required
def mark_notifications_read():
    from flask import jsonify
    conn=get_db()
    conn.execute('UPDATE notifications SET is_read=1 WHERE user_id=?',(session['user_id'],))
    conn.commit(); conn.close()
    return jsonify({'status':'ok'})


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn=get_db()
    stats={'available':conn.execute("SELECT COUNT(*) FROM food WHERE status='Available'").fetchone()[0],
           'collected':conn.execute("SELECT COUNT(*) FROM food WHERE status='Collected'").fetchone()[0],
           'donors':conn.execute("SELECT COUNT(*) FROM users WHERE role='donor'").fetchone()[0],
           'collectors':conn.execute("SELECT COUNT(*) FROM users WHERE role='collector'").fetchone()[0]}
    recent=conn.execute("SELECT f.*,u.name AS donor_name FROM food f JOIN users u ON f.user_id=u.id WHERE f.status='Available' ORDER BY f.created_at DESC LIMIT 6").fetchall()
    conn.close()
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
    collectors=conn.execute("SELECT id,name,phone,email FROM users WHERE role='collector'").fetchall()
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
                conn.execute('INSERT INTO users(name,email,username,password,phone,role) VALUES(?,?,?,?,?,?)',
                             (name,email,username,hash_password(password),phone,role))
                conn.commit(); conn.close()
                flash('Registration successful! Please login.','success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError as e:
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
        if not username:
            error='Username is required.'
        elif not password:
            error='Password is required.'
        else:
            conn=get_db()
            user=conn.execute('SELECT * FROM users WHERE username=? OR email=?',(username,username)).fetchone()
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
            conn=get_db(); user=conn.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            if user:
                conn.execute('UPDATE users SET password=? WHERE email=?',(hash_password(DEFAULT_PASSWORD),email))
                conn.commit()
                # Send real email
                html = f'''
                <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:12px;overflow:hidden">
                  <div style="background:#1b5e20;padding:24px;text-align:center">
                    <h2 style="color:#fff;margin:0">🍲 LeftoverFood System</h2>
                  </div>
                  <div style="padding:28px">
                    <p style="font-size:16px">Hello <strong>{user['name']}</strong>,</p>
                    <p>Your password has been reset successfully.</p>
                    <div style="background:#f1fdf4;border:1px solid #a5d6a7;border-radius:8px;padding:16px;text-align:center;margin:20px 0">
                      <p style="margin:0;font-size:13px;color:#555">Your new password is:</p>
                      <p style="font-size:26px;font-weight:bold;color:#1b5e20;margin:8px 0">{DEFAULT_PASSWORD}</p>
                    </div>
                    <p style="color:#e65100;font-size:13px">⚠️ Please login and change your password immediately from your Profile page.</p>
                    <a href="http://127.0.0.1:5000/login" style="display:inline-block;background:#2e7d32;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:10px">Login Now</a>
                  </div>
                  <div style="background:#f9f9f9;padding:14px;text-align:center;font-size:12px;color:#999">LeftoverFood Distribution System — BCA Final Year Project</div>
                </div>'''
                sent = send_email(email, 'Password Reset - LeftoverFood System', html)
                conn.close()
                if sent:
                    message=('success',f'Password reset! A confirmation email has been sent to {email} with your new password: Food@1234')
                else:
                    message=('success',f'Password reset! Your new password is: Food@1234 — (Email could not be sent, note it down)')
            else:
                conn.close()
                message=('danger','No account found with that email address.')
    return render_template('forgot_password.html',message=message)

# ── ADMIN ─────────────────────────────────────────────────────────
@app.route('/admin_dashboard')
@role_required('admin')
def admin_dashboard():
    conn=get_db()
    users=conn.execute("SELECT * FROM users WHERE role!='admin' ORDER BY created_at DESC").fetchall()
    donations=conn.execute("SELECT f.*,u.name AS donor_name,u.phone AS donor_phone FROM food f JOIN users u ON f.user_id=u.id ORDER BY f.created_at DESC").fetchall()
    collections=conn.execute("SELECT f.*,u.name AS donor_name,c.name AS collector_name,c.phone AS collector_phone FROM food f JOIN users u ON f.user_id=u.id JOIN users c ON f.collected_by=c.id WHERE f.status='Collected'").fetchall()
    stats={'total_users':conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
           'total_donations':conn.execute("SELECT COUNT(*) FROM food").fetchone()[0],
           'available':conn.execute("SELECT COUNT(*) FROM food WHERE status='Available'").fetchone()[0],
           'collected':conn.execute("SELECT COUNT(*) FROM food WHERE status='Collected'").fetchone()[0],
           'donors':conn.execute("SELECT COUNT(*) FROM users WHERE role='donor'").fetchone()[0],
           'collectors':conn.execute("SELECT COUNT(*) FROM users WHERE role='collector'").fetchone()[0]}
    conn.close()
    return render_template('admin_dashboard.html',users=users,donations=donations,collections=collections,stats=stats)

@app.route('/delete_user/<int:uid>',methods=['POST'])
@role_required('admin')
def delete_user(uid):
    conn=get_db(); conn.execute('DELETE FROM food WHERE user_id=?',(uid,)); conn.execute('DELETE FROM users WHERE id=?',(uid,)); conn.commit(); conn.close()
    flash('User deleted successfully.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_status/<int:food_id>',methods=['POST'])
@role_required('admin')
def admin_update_status(food_id):
    conn=get_db(); conn.execute('UPDATE food SET status=? WHERE id=?',(request.form.get('status','Available'),food_id)); conn.commit(); conn.close()
    flash('Donation status updated.','success'); return redirect(url_for('admin_dashboard'))

# ── DONOR ─────────────────────────────────────────────────────────
@app.route('/donor_dashboard')
@role_required('donor')
def donor_dashboard():
    conn=get_db()
    my_food=conn.execute('SELECT * FROM food WHERE user_id=? ORDER BY created_at DESC',(session['user_id'],)).fetchall()
    stats={'total':len(my_food),'available':sum(1 for f in my_food if f['status']=='Available'),'collected':sum(1 for f in my_food if f['status']=='Collected')}
    conn.close(); return render_template('donor_dashboard.html',my_food=my_food,stats=stats)

@app.route('/donate',methods=['GET','POST'])
@role_required('donor')
def donate():
    error=None; conn=get_db()
    prev=conn.execute("SELECT DISTINCT address FROM food WHERE user_id=? AND address!=''",(session['user_id'],)).fetchall()
    if request.method=='POST':
        title=request.form.get('title','').strip(); quantity=request.form.get('quantity','').strip()
        desc=request.form.get('description','').strip(); food_type=request.form.get('food_type','').strip()
        phone=request.form.get('phone','').strip(); pickup_time=request.form.get('pickup_time','').strip()
        location=request.form.get('location_display','').strip() or request.form.get('location','').strip()
        gps_lat=request.form.get('gps_lat','').strip()
        gps_lng=request.form.get('gps_lng','').strip()
        gps_coords=f"{gps_lat},{gps_lng}" if gps_lat and gps_lng else location
        address=request.form.get('selected_address','').strip() or request.form.get('new_address','').strip()
        if not title or not quantity or not address:
            error='Food name, quantity, and address are required.'
        else:
            conn.execute("INSERT INTO food(title,description,quantity,food_type,address,location,phone,pickup_time,user_id,status) VALUES(?,?,?,?,?,?,?,?,?,'Available')",
                         (title,desc,quantity,food_type,address,gps_coords,phone,pickup_time,session['user_id']))
            conn.commit()
            # Notify all collectors about new donation
            collectors=conn.execute("SELECT * FROM users WHERE role='collector'").fetchall()
            for c in collectors:
                add_notification(c['id'],f"🍲 New food available: {title} ({quantity}) at {address}")
                # Send email to each collector
                html = f'''
                <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:12px;overflow:hidden">
                  <div style="background:#1b5e20;padding:24px;text-align:center">
                    <h2 style="color:#fff;margin:0">🍲 New Food Available!</h2>
                  </div>
                  <div style="padding:28px">
                    <p>Hello <strong>{c['name']}</strong>,</p>
                    <p>A new food donation is available for pickup:</p>
                    <div style="background:#f1fdf4;border:1px solid #a5d6a7;border-radius:8px;padding:16px;margin:16px 0">
                      <p><strong>🍛 Food:</strong> {title}</p>
                      <p><strong>📦 Quantity:</strong> {quantity}</p>
                      <p><strong>📍 Address:</strong> {address}</p>
                      <p><strong>👤 Donor:</strong> {session['name']}</p>
                    </div>
                    <a href="http://127.0.0.1:5000/collector_dashboard" style="display:inline-block;background:#2e7d32;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold">View & Claim</a>
                  </div>
                  <div style="background:#f9f9f9;padding:14px;text-align:center;font-size:12px;color:#999">LeftoverFood Distribution System</div>
                </div>'''
                send_email(c['email'], f'New Food Available: {title} — LeftoverFood', html)
            conn.close(); flash('Donation added successfully! Thank you.','success'); return redirect(url_for('donor_dashboard'))
    conn.close(); return render_template('donate.html',error=error,prev_addresses=prev)

@app.route('/delete_donation/<int:fid>',methods=['POST'])
@role_required('donor','admin')
def delete_donation(fid):
    conn=get_db()
    if session['role']=='admin': conn.execute('DELETE FROM food WHERE id=?',(fid,))
    else: conn.execute('DELETE FROM food WHERE id=? AND user_id=?',(fid,session['user_id']))
    conn.commit(); conn.close(); flash('Donation removed.','info')
    return redirect(url_for('donor_dashboard') if session['role']=='donor' else url_for('admin_dashboard'))

# ── COLLECTOR ─────────────────────────────────────────────────────
@app.route('/collector_dashboard')
@role_required('collector')
def collector_dashboard():
    conn=get_db()
    food_items=conn.execute("SELECT f.*,u.name AS donor_name,u.phone AS donor_phone FROM food f JOIN users u ON f.user_id=u.id ORDER BY f.created_at DESC").fetchall()
    my_collections=conn.execute("SELECT f.*,u.name AS donor_name FROM food f JOIN users u ON f.user_id=u.id WHERE f.collected_by=? ORDER BY f.created_at DESC",(session['user_id'],)).fetchall()
    conn.close(); return render_template('collector_dashboard.html',food_items=food_items,my_collections=my_collections)

@app.route('/mark_collected/<int:fid>',methods=['POST'])
@role_required('collector')
def mark_collected(fid):
    conn=get_db(); food=conn.execute("SELECT * FROM food WHERE id=? AND status='Available'",(fid,)).fetchone()
    if food:
        conn.execute("UPDATE food SET status='Collected',collected_by=? WHERE id=?",(session['user_id'],fid)); conn.commit()
        # Notify the donor
        add_notification(food['user_id'],f"✅ Your donation '{food['title']}' has been collected by {session['name']}!")
        # Send email to donor
        donor=conn.execute('SELECT * FROM users WHERE id=?',(food['user_id'],)).fetchone()
        if donor:
            html = f'''
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:12px;overflow:hidden">
              <div style="background:#1b5e20;padding:24px;text-align:center">
                <h2 style="color:#fff;margin:0">✅ Food Collected!</h2>
              </div>
              <div style="padding:28px">
                <p>Hello <strong>{donor['name']}</strong>,</p>
                <p>Great news! Your food donation has been successfully collected.</p>
                <div style="background:#f1fdf4;border:1px solid #a5d6a7;border-radius:8px;padding:16px;margin:16px 0">
                  <p><strong>🍛 Food:</strong> {food['title']}</p>
                  <p><strong>📦 Quantity:</strong> {food['quantity']}</p>
                  <p><strong>🙏 Collected by:</strong> {session['name']}</p>
                </div>
                <p style="color:#2e7d32;font-weight:bold">Thank you for your generous donation! 💚</p>
                <a href="http://127.0.0.1:5000/donor_dashboard" style="display:inline-block;background:#2e7d32;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold">View Dashboard</a>
              </div>
              <div style="background:#f9f9f9;padding:14px;text-align:center;font-size:12px;color:#999">LeftoverFood Distribution System</div>
            </div>'''
            send_email(donor['email'], f"Your donation '{food['title']}' has been collected!", html)
        flash('Food marked as collected! Great work.','success')
    else: flash('This donation is no longer available.','warning')
    conn.close(); return redirect(url_for('collector_dashboard'))

# ── PROFILE ───────────────────────────────────────────────────────
@app.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    conn=get_db(); user=conn.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone(); error=None
    if request.method=='POST':
        action=request.form.get('action')
        if action=='update_profile':
            name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); phone=request.form.get('phone','').strip()
            if not name or not email: error='Name and email are required.'
            else:
                try:
                    conn.execute('UPDATE users SET name=?,email=?,phone=? WHERE id=?',(name,email,phone,session['user_id'])); conn.commit(); session['name']=name
                    flash('Profile updated successfully!','success'); conn.close(); return redirect(url_for('profile'))
                except sqlite3.IntegrityError: error='Email already used by another account.'
        elif action=='change_password':
            cur=request.form.get('current_password','').strip(); new=request.form.get('new_password','').strip(); con=request.form.get('confirm_password','').strip()
            if not cur or not new or not con: error='All password fields are required.'
            elif not check_password(cur,user['password']): error='Current password is incorrect.'
            elif len(new)<6: error='New password must be at least 6 characters.'
            elif new!=con: error='New passwords do not match.'
            else:
                conn.execute('UPDATE users SET password=? WHERE id=?',(hash_password(new),session['user_id'])); conn.commit()
                flash('Password changed successfully!','success'); conn.close(); return redirect(url_for('profile'))
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
            results=conn.execute("SELECT f.*,u.name AS donor_name,u.phone AS donor_phone FROM food f JOIN users u ON f.user_id=u.id WHERE f.title LIKE ? OR f.description LIKE ? OR f.address LIKE ? ORDER BY f.created_at DESC",(like,like,like)).fetchall()
            conn.close()
    return render_template('search.html',results=results,keyword=keyword)

# ── MESSAGES ──────────────────────────────────────────────────────
@app.route('/messages/<int:other_id>')
@login_required
def view_messages(other_id):
    my_id=session['user_id']; conn=get_db()
    chat=conn.execute("SELECT m.*,u1.name AS sender_name,u2.name AS receiver_name FROM messages m JOIN users u1 ON m.sender_id=u1.id JOIN users u2 ON m.receiver_id=u2.id WHERE (m.sender_id=? AND m.receiver_id=?) OR (m.sender_id=? AND m.receiver_id=?) ORDER BY m.sent_at ASC",(my_id,other_id,other_id,my_id)).fetchall()
    other_user=conn.execute('SELECT * FROM users WHERE id=?',(other_id,)).fetchone(); conn.close()
    return render_template('messages.html',chat=chat,other_user=other_user,other_id=other_id)

@app.route('/send_message/<int:receiver_id>',methods=['POST'])
@login_required
def send_message(receiver_id):
    msg=request.form.get('message','').strip()
    if msg:
        conn=get_db(); conn.execute('INSERT INTO messages(sender_id,receiver_id,message) VALUES(?,?,?)',(session['user_id'],receiver_id,msg)); conn.commit(); conn.close()
    return redirect(url_for('view_messages',other_id=receiver_id))

# ── FEEDBACK ──────────────────────────────────────────────────────
@app.route('/feedback',methods=['GET','POST'])
def feedback():
    conn=get_db(); error=None
    if request.method=='POST':
        name=request.form.get('name','').strip(); message=request.form.get('message','').strip()
        if not name or not message: error='Both name and feedback message are required.'
        else:
            conn.execute('INSERT INTO feedback(name,message) VALUES(?,?)',(name,message)); conn.commit(); conn.close()
            return render_template('thank_you.html')
    feedbacks=conn.execute('SELECT * FROM feedback ORDER BY created_at DESC').fetchall(); conn.close()
    return render_template('feedback.html',feedbacks=feedbacks,error=error)

if __name__=='__main__':
    init_db()
    print("\n"+"="*55)
    print("  LeftoverFood Distribution System — RUNNING")
    print("="*55)
    print("  URL       : http://127.0.0.1:5000")
    print("  Admin     : admin / admin123")
    print("  Donor     : donor1 / donor123")
    print("  Collector : collector1 / collect123")
    print("="*55+"\n")
    app.run(debug=True)
