# from flask import Flask
# from flask import render_template

# app = Flask(__name__)


# @app.route("/")
# def hello_world():
#     return render_template("index.html")

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
# for digital ocean 
# from app.helpers import recommender as recommender

# for local  
from helpers import recommender as recommender
import pandas as pd
import os
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'biadashboard'  # Replace with a secure random key in production

# Static credentials
STATIC_USERNAME = 'admin@ait.ac.th'
STATIC_PASSWORD = 'password123'

# Load KMeans model and scaler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/ directory
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'kmeans_with_scaler.pkl')

try:
    saved_objects = joblib.load(MODEL_PATH)
    kmeans = saved_objects['model']
    scaler = saved_objects['scaler']
    logger.info(f"Successfully loaded model from {MODEL_PATH}")
except FileNotFoundError as e:
    logger.error(f"Failed to load model: {e}")
    raise

cluster_definition = {0: 'Regular', 1: 'Inactive', 2: 'Premium', 3: 'New'}

def predict_cluster(recency_days, frequency, monetary):
    new_data = [[recency_days, frequency, monetary]]
    scaled_data = scaler.transform(new_data)
    predicted_cluster = kmeans.predict(scaled_data)
    cluster_center = kmeans.cluster_centers_[predicted_cluster]
    importance = scaled_data[0] - cluster_center
    return cluster_definition[predicted_cluster[0]], importance[0]

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
            session['user_id'] = 1
            session['name'] = "Admin John Doe"
            session['email'] = "admin@ait.ac.th"
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
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # Power BI embed URL (replace with your own)
    #powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=2abedde2-07e3-483a-aa60-792f2043f31f&autoAuth=true&ctid=99eeb009-e7a2-47b6-9ded-028cdcc300e6"
    # powerbi_url = "https://app.powerbi.com/view?r=eyJrIjoiZWUyOWRiMTMtNzFhOS00NWY1LTgyNzUtNWRiNzg3YTUzYjIxIiwidCI6Ijk5ZWViMDA5LWU3YTItNDdiNi05ZGVkLTAyOGNkY2MzMDBlNiIsImMiOjEwfQ%3D%3D&pageName=894da8eb5dacfce1aaf4"
    powerbi_url = "https://app.powerbi.com/view?r=eyJrIjoiZWUyOWRiMTMtNzFhOS00NWY1LTgyNzUtNWRiNzg3YTUzYjIxIiwidCI6Ijk5ZWViMDA5LWU3YTItNDdiNi05ZGVkLTAyOGNkY2MzMDBlNiIsImMiOjEwfQ%3D%3D"
    return render_template("dashboard.html", powerbi_url=powerbi_url)

@app.route('/recommender', methods=['GET', 'POST'])
@login_required
def recommendtation():
    recommendations = None
    customer_profile = None
    error = None
    customer_id = None

    # get the customer list for the dropdown
    Customer = recommender.GetCustomer()
    customer_list = Customer.customer_list()
    
    if customer_list is not None:
        customer_list = customer_list.to_dict(orient='records')
        print(f"Customer list: {customer_list}")
    else:
        error = 'Error loading customer list.'
        customer_list = []
    if request.method == 'GET':
        customer_id = 97475543
         # change cusotmer_id into to integer

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
         # change cusotmer_id into to integer
    try:
        customer_id = int(customer_id)
    except ValueError:
        error = 'Invalid customer ID. Please enter a valid integer.'
        customer_id = None

    if customer_id:
        #Get customer profile
        customer_profile = Customer.customer_profile(customer_id)
        if customer_profile is not None:
            customer_profile = customer_profile.to_dict(orient='records')[0]
            print(f"Customer profile: {customer_profile}")
        else:
            error = 'Customer profile not found.'
            customer_profile = None
        try:
            # Call the recommender function
            content_based_recommender = recommender.ContentBasedRecommender(top_n=30)
            result = content_based_recommender.recommend(customer_id)
            # print(f"Recommendations for customer {customer_id}: {result}")
                
            # Convert result to DataFrame if it's a list
            if isinstance(result, list):
                recommendations = pd.DataFrame(result, columns=['product_id', 'product_name','category','brand','price','mrp','margin_percentage'])
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

    return render_template('recommendations.html', 
                           recommendations=recommendations, 
                           customer_list=customer_list,
                           customer_profile=customer_profile,
                           customer_id=customer_id,
                           error=error)


# Classification route (protected)
@app.route('/classification', methods=['GET', 'POST'])
@login_required
def classification():
    cluster = None
    importance = None
    error = None
    
    # Default values for recency_days, frequency, and monetary
    if request.method == 'GET':
        
        recency_days = 20
        frequency = 5
        monetary = 100

    # Check if the form is submitted
    if request.method == 'POST':
        recency_days = float(request.form.get('recency_days'))
        frequency = float(request.form.get('frequency'))
        monetary = float(request.form.get('monetary'))

    try:
        cluster, importance = predict_cluster(recency_days, frequency, monetary)
        importance = importance.tolist()  # Convert numpy array to list for template
    except (ValueError, TypeError) as e:
        error = f"Invalid input: {str(e)}"
    return render_template('classification.html', 
                           cluster=cluster, 
                           importance=importance, 
                           recency_days=recency_days if 'recency_days' in locals() else 20,
                           frequency=frequency if 'frequency' in locals() else 5,
                           monetary=monetary if 'monetary' in locals() else 100,
                           error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
