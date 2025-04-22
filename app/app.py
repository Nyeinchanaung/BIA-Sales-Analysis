# from flask import Flask
# from flask import render_template

# app = Flask(__name__)


# @app.route("/")
# def hello_world():
#     return render_template("index.html")

from flask import Flask, render_template
from flask import Flask, render_template, redirect, url_for, request
import helpers.recommender as recommender

app = Flask(__name__)

@app.route("/")
def index():
    # Power BI embed URL (replace with your own)
    powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=2abedde2-07e3-483a-aa60-792f2043f31f&autoAuth=true&ctid=99eeb009-e7a2-47b6-9ded-028cdcc300e6"
    return render_template("index.html", powerbi_url=powerbi_url)

@app.route("/dashboard")
def dashboard():
    # Power BI embed URL (replace with your own)
    powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=2abedde2-07e3-483a-aa60-792f2043f31f&autoAuth=true&ctid=99eeb009-e7a2-47b6-9ded-028cdcc300e6"
    return render_template("dashboard.html", powerbi_url=powerbi_url)

@app.route("/recommender", methods=["GET", "POST"])
def recommendations():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        if customer_id:
            # Call the recommender functions here
            content_based_recommender = recommender.ContentBasedRecommender()
            recommendations = content_based_recommender.recommend(customer_id)
            print(f"Recommendations for customer {customer_id}: {recommendations}")
            return render_template("recommendations.html", recommendations=recommendations)
    return render_template("recommendations.html")

if __name__ == "__main__":
    app.run(debug=True)
