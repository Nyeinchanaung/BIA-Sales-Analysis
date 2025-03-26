# from flask import Flask
# from flask import render_template

# app = Flask(__name__)


# @app.route("/")
# def hello_world():
#     return render_template("index.html")

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    # Power BI embed URL (replace with your own)
    powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=2abedde2-07e3-483a-aa60-792f2043f31f&autoAuth=true&ctid=99eeb009-e7a2-47b6-9ded-028cdcc300e6"
    return render_template("index.html", powerbi_url=powerbi_url)

if __name__ == "__main__":
    app.run(debug=True)
