from flask import Flask, json, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from flask_mysqldb import MySQL
import MySQLdb.cursors
import pandas as pd
import os
from model import recommend
from flask_login import login_required
from flask_login import UserMixin
from flask_login import LoginManager
from flask_login import login_user






app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'mindcareai223'

mysql = MySQL(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

# User loader function
@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user)  
    return None



class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.name = user_data['name']
        self.email = user_data['email']

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False


# Routes
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        country = data.get('country')

        # Validate input
        if not all([name, email, password, country]):
            return jsonify({'error': 'Please fill all fields.'}), 400

        # Insert into the database
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'INSERT INTO user (name, email, password, country) VALUES (%s, %s, %s, %s)',
                (name, email, password, country)
            )
            mysql.connection.commit()
            cursor.close()

            # Simulate user login by loading user details
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
            user = cursor.fetchone()
            cursor.close()

            if user:
                user_obj = User(user)
                login_user(user_obj)  # Log the user in

            # Respond with a success message and redirect URL
            return jsonify({'success': 'Signup successful!', 'redirect': url_for('profile')}), 200

        except MySQLdb.IntegrityError:
            return jsonify({'error': 'Email already exists.'}), 400
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': 'An error occurred while processing your request.'}), 500
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Validate input
        if not all([email, password]):
            return jsonify({'error': 'Please fill all fields.'}), 400

        # Verify user credentials
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
            user = cursor.fetchone()
            cursor.close()

            if user and user['email'] == email and user['password'] == password:  # Use password hashing
                user_obj = User(user)
                login_user(user_obj)  # Log the user in
                return jsonify({'success': 'Login successful!'}), 200
            else:
                return jsonify({'error': 'Invalid email or password.'}), 401
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': 'An error occurred while processing your request.'}), 500
    return render_template('login.html')


from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from flask import session

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            data = request.get_json()
            experience = data.get('experience')
            weight = float(data.get('weight'))
            height = float(data.get('height')) / 100  # Convert cm to meters
            age = int(data.get('age'))
            gender = data.get('gender')
            injury = data.get('injury')
            medication = data.get('medication')

            if age < 11:
                return jsonify({'error': 'Under age 10 cannot continue'}), 400

            if height <= 0 or weight <= 0:
                return jsonify({'error': 'Invalid input values. Please provide realistic values.'}), 400

            bmi = round(weight / (height ** 2), 2)

            


            # Determine BMI category
            if 18.5 <= bmi <= 24.9:
                bmi_category = "Equal"
            elif bmi < 18.5:
                bmi_category = "Lesser than average"
            else:
                bmi_category = "Greater than average"

            
            if (bmi_category == "Equal"):
                bmi_status = "Normal"
            elif (bmi_category == "Lesser than average"):
                bmi_status = "UnderWeight"
            else:
                bmi_status = "OverWeight"

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            query = ('INSERT INTO profile (user_id, experience, weight, height, age, gender, injury, medication, bmi,bmi_category) '
                     'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)')
            values = (current_user.id, experience, weight, height, age, gender, injury, medication, bmi,bmi_status)
            cursor.execute(query, values)
            mysql.connection.commit()
            cursor.close()

            # Get recommendation data
            result = recommend((bmi_category, experience, injury, medication))

            if not result:
                return jsonify({'error': 'Recommendation data not found'}), 400

        # Save the result in the session
            session['result'] = result
            return jsonify({
                'redirect': url_for('exercise')
            })
        
        except Exception as e:
            print(f"Error processing profile: {e}")
            return jsonify({'error': 'An error occurred while processing the profile.'}), 500
    
    return render_template('profile.html')




@app.route('/profile/exercise', methods=['GET'])
@login_required
def exercise():
    result = session.get('result')
    if not result:
        return jsonify({'error': 'No exercise data available. Please update your profile.'}), 404
    return render_template('exercise.html', result=result)





@app.route('/profile/exercise/diet_plan', methods=['GET'])
@login_required
def diet_plan():
    
    return render_template('diet.html')




@app.route('/profile_details', methods=['GET'])
@login_required
def profile_details():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM profile WHERE user_id = %s ORDER BY profile_id DESC LIMIT 1', (current_user.id,))
    profile = cursor.fetchone()
    cursor.close()

    if profile:
        # Pass profile data and recommendation to the template
        recommendation = request.args.get('recommendation', default="", type=str)
        return render_template("profile_details.html", recommendation=recommendation, **profile)
    return jsonify({'error': 'No profile data found.'}), 404





@app.route('/performance', methods=['GET'])
@login_required
def performance():
    # Retrieve profile details from session
    bmi = session.get('bmi')
    experience = session.get('experience')
    age = session.get('age')
    weight = session.get('weight')
    height = session.get('height')


    return render_template("analysis.html")



if __name__ == '__main__':
    app.run(debug=True)
