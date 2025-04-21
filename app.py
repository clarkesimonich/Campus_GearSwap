# app.py
import sqlite3
from flask import Flask, render_template, redirect, url_for, request, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session and flash messages

DATABASE = 'campus_gearswap.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # so you can use column names
    return conn

# Homepage route
@app.route("/")
def home():
    return render_template("index.html", title="Campus GearSwap", message="Find or Share Gear Easily!")

# Gear listing page
# Gear listing page
@app.route("/gear", methods=["GET", "POST"])
def gear():
    conn = get_db_connection()
    cursor = conn.cursor()

    search_term = request.args.get('search')

    if search_term:
        cursor.execute("SELECT * FROM gear WHERE title LIKE ?", ('%' + search_term + '%',))
    else:
        cursor.execute("SELECT * FROM gear")

    all_gear = cursor.fetchall()
    conn.close()

    return render_template("gear.html", title="Gear Listings", gear=all_gear)

@app.route("/gear/add", methods=["GET", "POST"])
def add_gear():
    if 'user_id' not in session:
        flash('You must be logged in to add new gear.', 'error')
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        condition = request.form["condition"]
        availability = request.form["availability"]

        if not title or not description or not category or not condition or not availability:
            flash('Please complete all fields to post your gear.', 'error')
            return redirect(url_for('add_gear'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gear (user_id, title, description, category, condition, availability, date_posted)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (session['user_id'], title, description, category, condition, availability))
        conn.commit()
        conn.close()

        flash('Your gear listing has been posted successfully!', 'success')
        return redirect(url_for('gear'))

    return render_template("add_gear.html", title="Add Gear")

@app.route("/gear/edit/<int:gear_id>", methods=["GET", "POST"])
def edit_gear(gear_id):
    if 'user_id' not in session:
        flash('You must be logged in to edit your gear.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gear WHERE gear_id = ?', (gear_id,))
    gear = cursor.fetchone()

    if not gear:
        conn.close()
        flash('Gear not found.', 'error')
        return redirect(url_for('gear'))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        condition = request.form["condition"]
        availability = request.form["availability"]

        if not title or not description or not category or not condition or not availability:
            flash('Please complete all fields to update your gear.', 'error')
            return redirect(url_for('edit_gear', gear_id=gear_id))

        cursor.execute('''
            UPDATE gear
            SET title = ?, description = ?, category = ?, condition = ?, availability = ?
            WHERE gear_id = ?
        ''', (title, description, category, condition, availability, gear_id))
        conn.commit()
        conn.close()

        flash('Your gear listing has been updated successfully!', 'success')
        return redirect(url_for('gear'))

    conn.close()
    return render_template("edit_gear.html", title="Edit Gear", gear=gear)

@app.route("/gear/delete/<int:gear_id>", methods=["POST"])
def delete_gear(gear_id):
    if 'user_id' not in session:
        flash('You must be logged in to delete gear.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gear WHERE gear_id = ?', (gear_id,))
    gear = cursor.fetchone()

    if not gear:
        conn.close()
        flash('Gear not found.', 'error')
        return redirect(url_for('gear'))

    cursor.execute('DELETE FROM gear WHERE gear_id = ?', (gear_id,))
    conn.commit()
    conn.close()

    flash('Your gear listing has been deleted successfully.', 'success')
    return redirect(url_for('gear'))

@app.route("/gear/reserve/<int:gear_id>", methods=["GET", "POST"])
def reserve_gear(gear_id):
    if 'user_id' not in session:
        flash('You must be logged in to reserve gear.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gear WHERE gear_id = ?', (gear_id,))
    gear = cursor.fetchone()

    if not gear:
        conn.close()
        flash('Gear not found.', 'error')
        return redirect(url_for('gear'))

    if request.method == "POST":
        reservation_date = request.form["reservation_date"]
        return_due_date = request.form["return_due_date"]

        if not reservation_date or not return_due_date:
            flash('Please select both reservation and return dates.', 'error')
            return redirect(url_for('reserve_gear', gear_id=gear_id))

        if return_due_date < reservation_date:
            flash('Return date cannot be before the reservation date. Please select valid dates.', 'error')
            return redirect(url_for('reserve_gear', gear_id=gear_id))

        cursor.execute('''
            INSERT INTO reservations (user_id, gear_id, reservation_date, return_due_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], gear_id, reservation_date, return_due_date, 'Reserved'))
        conn.commit()
        conn.close()

        flash('Gear reserved successfully! Please pick up and return on time.', 'success')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template("reserve_gear.html", title="Reserve Gear", gear=gear)


# User dashboard after login
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access your dashboard.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT gear.title, reservations.reservation_date, reservations.return_due_date, reservations.status
        FROM reservations
        JOIN gear ON reservations.gear_id = gear.gear_id
        WHERE reservations.user_id = ?
    ''', (session['user_id'],))
    reservations = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", title="Dashboard", user_name=session.get('user_name'), reservations=reservations)


# Login page (GET and POST)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and user["password"] == password:
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template("login.html", title="Login")

# Register page (GET and POST)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Check for missing fields
        if not name or not email or not password:
            flash('Please complete all required fields.', 'error')
            return redirect(url_for('register'))

        # Check for IU email domain
        if not email.endswith("@iu.edu"):
            flash('Please use a valid @iu.edu email address to register.', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('register'))
        finally:
            conn.close()

    return render_template("register.html", title="Register")


# Logout route
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

# Profile page
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = session['user_id']
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    # ✅ New: Pull the user's average rating
    cursor.execute('SELECT AVG(score) as avg_rating FROM ratings WHERE reviewed_id = ?', (user_id,))
    avg_rating_row = cursor.fetchone()
    avg_rating = avg_rating_row['avg_rating'] if avg_rating_row else None

    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        if not name:
            flash('Name cannot be empty.', 'error')
            return redirect(url_for('profile'))

        if password:  # Only update password if a new one is provided
            cursor.execute('''
                UPDATE users
                SET name = ?, password = ?
                WHERE user_id = ?
            ''', (name, password, user_id))
        else:
            cursor.execute('''
                UPDATE users
                SET name = ?
                WHERE user_id = ?
            ''', (name, user_id))

        conn.commit()
        conn.close()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    conn.close()
    return render_template("profile.html", title="Profile", user=user, avg_rating=avg_rating)





# Messages page
@app.route("/messages")
def messages():
    if 'user_id' not in session:
        flash('Please log in to view your messages.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Updated to also SELECT the response
    cursor.execute('''
        SELECT messages.message_id, messages.content, messages.timestamp, messages.response, users.name AS sender_name
        FROM messages
        JOIN users ON messages.sender_id = users.user_id
        WHERE messages.receiver_id = ?
        ORDER BY messages.timestamp DESC
    ''', (session['user_id'],))
    all_messages = cursor.fetchall()

    conn.close()

    return render_template("messages.html", title="Messages", messages=all_messages)


# Send Messages
@app.route("/messages/send/<int:receiver_id>", methods=["GET", "POST"])
def send_message(receiver_id):
    if 'user_id' not in session:
        flash('Please log in to send messages.', 'error')
        return redirect(url_for('login'))

    if request.method == "POST":
        content = request.form["content"]

        if not content:
            flash('Message cannot be empty.', 'error')
            return redirect(url_for('send_message', receiver_id=receiver_id))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        ''', (session['user_id'], receiver_id, content))
        conn.commit()
        conn.close()

        flash('Message sent successfully!', 'success')
        return redirect(url_for('messages'))

    return render_template("send_message.html", title="Send Message", receiver_id=receiver_id)

#Reply messages
@app.route("/messages/reply/<int:message_id>", methods=["GET", "POST"])
def reply_message(message_id):
    if 'user_id' not in session:
        flash('Please log in to reply to messages.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch original message
    cursor.execute('SELECT * FROM messages WHERE message_id = ?', (message_id,))
    original_message = cursor.fetchone()

    if not original_message:
        conn.close()
        flash('Original message not found.', 'error')
        return redirect(url_for('messages'))

    if request.method == "POST":
        reply_content = request.form["response"]

        if not reply_content:
            flash('Reply cannot be empty.', 'error')
            return redirect(url_for('reply_message', message_id=message_id))

        # Create a new message: sender = me, receiver = original sender
        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        ''', (session['user_id'], original_message['sender_id'], reply_content))

        conn.commit()
        conn.close()

        flash('Reply sent successfully!', 'success')
        return redirect(url_for('messages'))

    conn.close()
    return render_template("reply_message.html", title="Reply to Message", message=original_message)

@app.route("/rate/<int:reviewed_id>", methods=["GET", "POST"])
def rate_user(reviewed_id):
    if 'user_id' not in session:
        flash('Please log in to leave a review.', 'error')
        return redirect(url_for('login'))

    if request.method == "POST":
        score = int(request.form["score"])
        comment = request.form["comment"]

        if score < 1 or score > 5:
            flash('Rating must be between 1 and 5.', 'error')
            return redirect(url_for('rate_user', reviewed_id=reviewed_id))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ratings (reviewer_id, reviewed_id, score, comment)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], reviewed_id, score, comment))
        conn.commit()
        conn.close()

        flash('Review submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template("rate_user.html", title="Leave a Review")


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
