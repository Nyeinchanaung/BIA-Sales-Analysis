# from flask import Flask
# from flask import render_template

# app = Flask(__name__)


# @app.route("/")
# def hello_world():
#     return render_template("index.html")

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from app.helpers import recommender as recommender
import pandas as pd

app = Flask(__name__)
app.secret_key = 'biadashboard'  # Replace with a secure random key in production

# Static credentials
STATIC_USERNAME = 'admin@ait.ac.th'
STATIC_PASSWORD = 'password123'

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password') 

        print(f"Username: {username}, Password: {password}")  # Debugging line
        
        if username == STATIC_USERNAME and password == STATIC_PASSWORD:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            print("Login successful")  # Debugging line
            return redirect(url_for('dashboard'))
        else:
            print("Login Failded")  # Debugging line
            flash('Invalid username or password.', 'danger')
    
    return render_template('index.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # Power BI embed URL (replace with your own)
    powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=2abedde2-07e3-483a-aa60-792f2043f31f&autoAuth=true&ctid=99eeb009-e7a2-47b6-9ded-028cdcc300e6"
    return render_template("dashboard.html", powerbi_url=powerbi_url)

@app.route('/recommender', methods=['GET', 'POST'])
@login_required
def recommendtation():
    recommendations = None
    error = None

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
         # change cusotmer_id into to integer
        try:
            customer_id = int(customer_id)
        except ValueError:
            error = 'Invalid customer ID. Please enter a valid integer.'
            customer_id = None

        if customer_id:
            try:
                # Call the recommender function
                content_based_recommender = recommender.ContentBasedRecommender(top_n=30)
                result = content_based_recommender.recommend(customer_id)
                print(f"Recommendations for customer {customer_id}: {result}")
                
                # Convert result to DataFrame if it's a list
                if isinstance(result, list):
                    recommendations = pd.DataFrame(result, columns=['product_id', 'product_name'])
                elif isinstance(result, pd.DataFrame):
                    recommendations = result
                else:
                    error = 'Unexpected recommendation format.'
                    recommendations = None

                if recommendations is not None and recommendations.empty:
                    error = 'No recommendations available for this customer.'
            except Exception as e:
                error = f'Error generating recommendations: {str(e)}'
        else:
            error = 'Please provide a valid customer ID.'

    return render_template('recommendations.html', recommendations=recommendations, error=error)


@app.route('/segmentation', methods=['GET', 'POST'])
@login_required
def segmentation():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
