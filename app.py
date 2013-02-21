
from flask import Flask, render_template
import os, sys, time, random, json

app = Flask(__name__)
app.secret_key = "change_me"

@app.route('/')
def routeRoot():
    return render_template('base.html')

@app.route('/api/get_num_users')
def routeGetNumUsers():
    return random.randint(200, 300)

if __name__ == '__main__':
    app.run(debug=True)
