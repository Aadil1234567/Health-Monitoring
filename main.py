from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pytz
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session management

USER_FILE = 'users.txt'

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

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template("login.html")

@app.route('/logout', methods=["POST"])
def logout():
    session.pop('logged_in', None)  # Remove the 'logged_in' key from the session
    flash('You have been logged out.', 'info')  # Optionally, flash a message to inform the user
    return redirect(url_for('login'))  # Redirect to the login page


@app.route('/', methods=["GET", "POST"])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    notes = read_data("notes.txt")
    if request.method == "POST":
        note = request.form.get("note")
        if note:
            timestamp = get_sg_time()
            write_data("notes.txt", f"{note} (added on {timestamp})")
        return redirect(url_for('index'))
    return render_template("index.html", notes=notes)

@app.route('/clear', methods=["POST"])
def clear_notes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    clear_data("notes.txt")
    return redirect(url_for('index'))

@app.route('/delete', methods=["POST"])
def delete_note():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    notes = read_data("notes.txt")
    if notes:
        notes.pop() # Remove the last note
        with open("notes.txt", "w") as file:
            for note in notes:
                file.write(note + "\n")
    return redirect(url_for('index'))

@app.route('/monitor', methods=["GET", "POST"])
def monitor():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    advice = ""
    heart_rate = None
    blood_pressure = None
    previous_data = read_data("monitor_data.txt")

    if request.method == "POST":
        heart_rate = request.form.get("heart_rate")
        blood_pressure = request.form.get("blood_pressure")

        if heart_rate and blood_pressure:
            heart_rate = int(heart_rate)
            blood_pressure = int(blood_pressure)
            timestamp = get_sg_time()
            data = f"Heart Rate: {heart_rate}, Blood Pressure: {blood_pressure} (added on {timestamp})"
            write_data("monitor_data.txt", data)

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

    bmi = None
    advice = ""
    details = ""
    previous_data = read_data("bmi_data.txt")

    if request.method == "POST":
        weight = float(request.form.get("weight"))
        height = float(request.form.get("height"))
        bmi = weight / (height ** 2)
        timestamp = get_sg_time()
        data = f"Weight: {weight}, Height: {height}, BMI: {bmi:.2f} (added on {timestamp})"
        write_data("bmi_data.txt", data)

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
                <h3>Exercise Routine:</h3>
                <ul>
                    <li>30 minutes of moderate-intensity aerobic activity 5 days a week.</li>
                    <li>Strength training exercises at least 2 days a week.</li>
                    <li>Incorporate flexibility and balance exercises.</li>
                </ul>
            """
        else:
            advice = "You are obese. Please see a doctor."
            details = """
                <h3>Exercise and Diet Tips for Weight Loss:</h3>
                <ul>
                    <li>Eat a moderate amount, stop when you feel full and avoid snacking so that you do not consume excess calories per day. Avoid crash diets or fad diets as they are dangerous to your health and unsustainable in the long run.</li>
                    <li>Diets that boast to be low-fat or low-carb may reduce weight, but their long-term effects are not known. A qualified dietician can help you plan a balanced diet with fewer calories to achieve weight loss and maintenance.</li>
                    <li>Add more physical activity into your daily routine, such as climbing the stairs instead of taking the lift. Do moderate-intensity exercise five times a week, up to a maximum of 30 minutes each session. This can include brisk walking, light cycling or sports such as badminton. As your fitness levels improve, gradually incorporate more intense workouts like jogging or swimming. By this point, you can cut back on duration and frequency as these activities require more of you. Try exercising for at least 20 minutes three days a week.</li>
                    <li>Some individuals may need extra help from medications to control weight. These medications may be used for a short period (six to 12 months) or in the long term (up to three years) in combination with diet modification and exercise.</li>
                    <li>Set realistic goals, for example, target a loss of 1kg a week.</li>
                    <li>Reward yourself when you reach a weight goal with activities like an outing or a good meal (remember, moderation is key).</li>
                    <li>Make healthy eating and exercise part of your lifestyle, and involve your family or friends to increase accountability.</li>
                    <li>Visualise a slimmer and healthier you, and tell yourself you can do it.</li>
                    <li>Even if you miss exercise sessions or cannot keep to your diet for some time, it is important to think positively and resume your plans as soon as you can!</li>
                </ul>
            """
    return render_template("bmi.html", bmi=bmi, advice=advice, details=details, previous_data=previous_data)

@app.route('/run', methods=["GET", "POST"])
def run():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    previous_data = read_data("run_data.txt")
    if request.method == "POST":
        distance = request.form.get("distance")
        duration = request.form.get("duration")
        if distance and duration:
            timestamp = get_sg_time()
            data = f"Distance: {distance} km, Duration: {duration} minutes (added on {timestamp})"
            write_data("run_data.txt", data)
        return redirect(url_for('run'))
    return render_template("run.html", previous_data=previous_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12345)
