from flask import Flask, render_template, request
import os
import sqlite3
import requests

app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/bkel2mail'
path = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=["POST"])
def submit():
    email = request.form.get("email")
    token = request.form.get("token")
    userid = None
    noti = None
    sentID = ''
    conn = sqlite3.connect(path + '/database.db')
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")

    if len(token) != 32:
        return render_template('submit.html', status="Vui lòng xem lại token.")
    
    exist = conn.execute("select id from users where email = ? or token = ?", (email,token)).fetchone()
    if exist is not None:
        return render_template('submit.html', status="Email/Token đã được sử dụng")
        
    query = {'wstoken':token, 'wsfunction':'core_webservice_get_site_info'}
    response = requests.get('http://e-learning.hcmut.edu.vn/webservice/rest/server.php?moodlewsrestformat=json', params=query)
    try:
        userid = response.json()['userid']
    except:
        return render_template('submit.html', status="Đã xảy ra lỗi")
        
    query = {'wstoken':token, 'useridto':userid, 'limitnum':50, 'read':0, 'wsfunction':'core_message_get_messages', 'type':'both'}
    response = requests.get('http://e-learning.hcmut.edu.vn/webservice/rest/server.php?moodlewsrestformat=json', params=query)
    
    try:
        noti = response.json()['messages']
    except:
        return render_template('submit.html', status="Đã xảy ra lỗi")
        
    for messages in noti:
        sentID += str(messages['id']) + ','
                    
    script = "INSERT INTO users (email, token, sentID) VALUES ('" + email + "', '" + token + "', '" + sentID + "')"
    conn.execute(script)
    conn.commit()
    conn.close()
    return render_template('submit.html', status="Đăng kí thành công!")
    
@app.route('/howto')
def howto():
    return render_template('howto.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
