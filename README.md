# 🍲 LeftoverFood Distribution System
## BCA Final Year Project — by Radha

---

## 📌 Project Overview
A Python Flask web application that connects **Food Donors**, **Collectors/Volunteers**, and **Admins**
to reduce food waste and fight hunger.

---

## ✅ Features Implemented

| Feature | Status |
|---|---|
| Login Authentication (Username + Password) | ✅ Done |
| Password Hashing using **hashlib SHA-256** | ✅ Done |
| User Roles: Admin / Donor / Collector | ✅ Done |
| Role-based Page Access | ✅ Done |
| Input Validation (empty fields, wrong login) | ✅ Done |
| Session Management + Logout | ✅ Done |
| SQLite Database (no MySQL needed) | ✅ Done |
| Admin Dashboard – manage users & donations | ✅ Done |
| Donor Dashboard – add/view donations | ✅ Done |
| Collector Dashboard – claim pickups | ✅ Done |
| Search Food Donations | ✅ Done |
| Profile Update + Password Change | ✅ Done |
| Feedback System | ✅ Done |
| Messaging between users | ✅ Done |
| Hunger Spots info page | ✅ Done |
| Gallery, About, Contact pages | ✅ Done |

---

## 🔐 Security Features

### 1. Password Hashing (hashlib)
```python
import hashlib
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
```
- Password entered → SHA-256 hash → stored in database
- On login: hash the entered password → compare with stored hash
- Plain text password is NEVER stored

### 2. User Roles
| Role | Permissions |
|---|---|
| **Admin** | View all users, delete users, update donation status, see all data |
| **Donor** | Add food donations, view own donations, delete own donations |
| **Collector** | View available food, claim pickups, see collection history |

### 3. Input Validation
- Empty username/password → error shown
- Wrong credentials → "Invalid username or password"
- Username too short → error
- Password < 6 chars → error
- Passwords don't match → error
- Duplicate username/email → error

### 4. Session Control
- After login: session stores user_id, username, name, role
- All protected routes check `session['user_id']`
- Logout clears entire session → `session.clear()`
- Role mismatch → redirected with "Access denied" message

---

## 🗄️ Database: SQLite (leftoverfood.db)
No MySQL installation needed! SQLite file is created automatically.

### Tables:
- **users** — id, name, email, username, password(hashed), phone, role
- **food** — id, title, description, quantity, food_type, address, location, phone, pickup_time, status, user_id, collected_by
- **feedback** — id, name, message, created_at
- **messages** — id, sender_id, receiver_id, message, sent_at

---

## 🚀 How to Run

### Step 1 — Install Python (3.9+)
Download from https://python.org

### Step 2 — Install Flask
```bash
pip install Flask
```

### Step 3 — Run the app
```bash
python app.py
```

### Step 4 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🔑 Default Login Credentials

| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Donor | donor1 | donor123 |
| Donor | donor2 | donor123 |
| Collector | collector1 | collect123 |
| Collector | collector2 | collect123 |

---

## 📁 Project Structure
```
FoodShare_Complete/
├── app.py                  ← Main Flask application
├── requirements.txt        ← Dependencies
├── leftoverfood.db         ← SQLite database (auto-created)
├── static/
│   └── images/             ← Gallery images
└── templates/
    ├── base.html           ← Base layout with sidebar
    ├── login.html          ← Login page
    ├── register.html       ← Registration page
    ├── forgot_password.html
    ├── index.html          ← Home page
    ├── admin_dashboard.html
    ├── donor_dashboard.html
    ├── collector_dashboard.html
    ├── donate.html         ← Add donation form
    ├── profile.html        ← Profile & password change
    ├── search.html         ← Search donations
    ├── messages.html       ← User messaging
    ├── feedback.html       ← Feedback form
    ├── about.html
    ├── contact.html
    ├── gallery.html
    ├── hunger_spots.html
    ├── collectors_list.html
    └── thank_you.html
```

---

## 🧑‍💻 Technologies Used
- **Python 3** — Programming language
- **Flask** — Web framework
- **SQLite** — Database
- **hashlib** — Password hashing (SHA-256)
- **Jinja2** — HTML templating
- **HTML5 + CSS3** — Frontend
- **Font Awesome** — Icons
- **Google Fonts** — Typography

---

*Project by Radha — BCA Final Year, 2024*
