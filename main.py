from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pytz
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session management

USER_FILE = 'users.txt'
USER_DATA_DIR = 'user_data'  # Directory to store user-specific data

# Function to read user data from file
def read_users():
    users = {}
    try:
        with open(USER_FILE, 'r') as file:
            for line in file:
                username, password = line.strip().split(',')
                users[username] = password
    except FileNotFoundError:
        with open(USER_FILE, 'w') as file:
            pass
    return users

# Function to write user data to file
def write_user(username, password):
    with open(USER_FILE, 'a') as file:
        file.write(f'{username},{password}\n')

    # Create a directory for storing user's personal data
    user_data_dir = os.path.join(USER_DATA_DIR, username)
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to read data from a user's file
def read_user_data(username, filename):
    user_data_dir = os.path.join(USER_DATA_DIR, username)
    file_path = os.path.join(user_data_dir, filename)
    return read_data(file_path)

# Function to write data to a user's file
def write_user_data(username, filename, data):
    user_data_dir = os.path.join(USER_DATA_DIR, username)
    file_path = os.path.join(user_data_dir, filename)
    write_data(file_path, data)

# Function to clear data from a user's file
def clear_user_data(username, filename):
    user_data_dir = os.path.join(USER_DATA_DIR, username)
    file_path = os.path.join(user_data_dir, filename)
    clear_data(file_path)

# Function to read data from a file
def read_data(filename):
    try:
        with open(filename, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        return []

# Function to write data to a file
def write_data(filename, data):
    with open(filename, 'a') as file:
        file.write(data + "\n")

# Function to clear data from a file
def clear_data(filename):
    with open(filename, 'w') as file:
        pass

def get_sg_time():
    sg_timezone = pytz.timezone("Asia/Singapore")
    sg_time = datetime.now(sg_timezone)
    return sg_time.strftime("%Y-%m-%d %H:%M:%S")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = read_users()

        if username in users:
            flash('Username already exists', 'danger')
        else:
            hashed_password = hash_password(password)
            write_user(username, hashed_password)
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template("signup.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = read_users()
        hashed_password = hash_password(password)

        if username in users and users[username] == hashed_password:
            session['logged_in'] = True
            session['username'] = username  # Store the username in session
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template("login.html")

@app.route('/logout', methods=["POST"])
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  # Clear the username from the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=["GET", "POST"])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    username = session['username']
    notes = read_user_data(username, "notes.txt")
    if request.method == "POST":
        note = request.form.get("note")
        if note:
            timestamp = get_sg_time()
            write_user_data(username, "notes.txt", f"{note} (added on {timestamp})")
        return redirect(url_for('index'))
    return render_template("index.html", notes=notes)

@app.route('/clear', methods=["POST"])
def clear_notes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    username = session['username']
    clear_user_data(username, "notes.txt")
    return redirect(url_for('index'))

@app.route('/delete', methods=["POST"])
def delete_note():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    username = session['username']
    notes = read_user_data(username, "notes.txt")
    if notes:
        notes.pop() # Remove the last note
        user_data_dir = os.path.join(USER_DATA_DIR, username)
        file_path = os.path.join(user_data_dir, "notes.txt")
        with open(file_path, "w") as file:
            for note in notes:
                file.write(note)
    return redirect(url_for('index'))

@app.route('/monitor', methods=["GET", "POST"])
def monitor():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    username = session['username']
    advice = ""
    heart_rate = None
    blood_pressure = None
    previous_data = read_user_data(username, "monitor_data.txt")

    if request.method == "POST":
        heart_rate = request.form.get("heart_rate")
        blood_pressure = request.form.get("blood_pressure")

        if heart_rate and blood_pressure:
            heart_rate = int(heart_rate)
            blood_pressure = int(blood_pressure)
            timestamp = get_sg_time()
            data = f"Heart Rate: {heart_rate}, Blood Pressure: {blood_pressure} (added on {timestamp})"
            write_user_data(username, "monitor_data.txt", data)

            if heart_rate < 60 or heart_rate > 100:
                advice += "Your heart rate is abnormal. Please see a doctor. "
            if blood_pressure < 90 or blood_pressure > 140:
                advice += "Your blood pressure is abnormal. Please see a doctor. "
            if not advice:
                advice = "Your vitals are normal."

    return render_template("monitor.html", advice=advice, heart_rate=heart_rate, blood_pressure=blood_pressure, previous_data=previous_data)

@app.route('/bmi', methods=["GET", "POST"])
def bmi():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    username = session['username']
    bmi = None
    advice = ""
    details = ""
    previous_data = read_user_data(username, "bmi_data.txt")

    if request.method == "POST":
        weight = float(request.form.get("weight"))
        height = float(request.form.get("height"))
        bmi = weight / (height ** 2)
        timestamp = get_sg_time()
        data = f"Weight: {weight}, Height: {height}, BMI: {bmi:.2f} (added on {timestamp})"
        write_user_data(username, "bmi_data.txt", data)

        if bmi < 18.5:
            advice = "You are underweight."
            details = """
                <h3>Tips for Gaining Weight:</h3>
                <ul>
                    <li>Gain weight gradually by adding healthy calories – adults could try adding around 300 to 500 extra calories a day.</li>
                    <li>Eat smaller meals more often, adding healthy snacks between meals.</li>
                    <li>Add extra calories to your meals with cheese, nuts, and seeds.</li>
                    <li>Have high-calorie drinks in between meals, such as milkshakes.</li>
                    <li>Have a balanced diet – choose from a variety of food groups, such as fruit and vegetables, starchy carbohydrates and dairy and alternatives.</li>
                    <li>Add protein to your meals with beans, pulses, fish, eggs, and lean meat.</li>
                    <li>Have snacks that are easy to prepare, such as yogurt or rice pudding.</li>
                    <li>Build muscle with strength training or yoga – exercise can also improve your appetite.</li>
                </ul>
            """
        elif 18.5 <= bmi < 24.9:
            advice = "You are within a healthy weight range."
        elif 25 <= bmi < 29.9:
            advice = "You are overweight."
            details = """
                <h3>Exercise Routine:</h>
                <ul>
                    <li>30 minutes of moderate-intensity aerobic activity 5 days a week.</li>
                    <li>Strength training exercises at least 2 days a week.</li>
                    <li>Incorporate flexibility and balance exercises.</li>
                </ul>
            """
        else:
            advice = "You are obese."
            details = """
                <h3>Diet and Exercise Tips:</h>
                <ul>
                    <li>Consult a healthcare provider for a personalized plan.</li>
                    <li>Incorporate more fruits, vegetables, and whole grains into your diet.</li>
                    <li>Aim for 150 to 300 minutes of moderate-intensity activity per week.</li>
                    <li>Consider joining a support group or working with a dietitian.</li>
                </ul>
            """

    return render_template("bmi.html", bmi=bmi, advice=advice, details=details, previous_data=previous_data)

@app.route('/run', methods=["GET", "POST"])
def run():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    username = session['username']
    feedback = ""
    previous_data = read_user_data(username, "run_data.txt")

    if request.method == "POST":
        distance = float(request.form.get("distance"))
        duration = float(request.form.get("duration"))

        if distance and duration:
            speed = distance / duration
            timestamp = get_sg_time()
            data = f"Distance: {distance}km, Duration: {duration}h, Speed: {speed:.2f}km/h (added on {timestamp})"
            write_user_data(username, "run_data.txt", data)

            if speed < 8:
                feedback = "Try to run faster next time!"
            elif speed > 12:
                feedback = "Great job! Keep up the pace!"
            else:
                feedback = "You're doing well. Keep maintaining your speed!"

    return render_template("run.html", feedback=feedback, previous_data=previous_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12345)
