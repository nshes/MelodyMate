from flask import Flask, render_template, request, redirect, url_for, flash, session, get_flashed_messages, jsonify
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os, requests

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SECRET_KEY'] = 'your_very_secret_key_here'
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

class Music(db.Model):
    mid = db.Column(db.Integer, primary_key = True)
    uid = db.Column(db.Integer, nullable = False)
    title = db.Column(db.String, nullable = False)
    artist = db.Column(db.String, nullable = False)
    image_url = db.Column(db.String, nullable = False)

    def __repr__(self):
        return f'{self.artist} {self.title}'

with app.app_context():
    db.create_all()

class User(db.Model):
    uid = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String, unique=True, nullable = False)
    password = db.Column(db.String, nullable = False)

    def __repr__(self):
        return f'{self.uid} {self.email}'
        
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    music_data = []
    try:
        uid_receive = session['uid']
        music_data = Music.query.filter_by(uid=uid_receive)
    except:
        pass

    melon_data = []
    try:
        url = "https://www.melon.com/chart/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        data = requests.get(url, headers=headers)
        soup = BeautifulSoup(data.text, 'html.parser')

        trs = soup.select('table > tbody > tr')
        for tr in trs:
            rank = tr.select_one('.rank').text
            title = tr.select_one('.rank01 > span > a').text
            artist = tr.select_one('.rank02 > a').text
            image = tr.select_one('img')['src']
            melon_data.append({'rank': rank, 'artist': artist, 'title': title, 'image': image})
    except:
        pass

    return render_template('music.html', music_data=music_data, melon_data=melon_data)

@app.route("/register", methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("이미 존재하는 이메일 주소입니다. 다른 이메일을 사용하세요.", "danger")
        return redirect(url_for('home') + '#registrationModal')
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    flash("가입 성공!", "success")
    return redirect(url_for('home'))

@app.route("/login", methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        session['uid'] = user.uid
        flash("로그인에 성공했습니다!", "success")
    else:
        flash("로그인에 실패했습니다. ID와 password를 확인하세요.", "danger")
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.pop('uid', None)
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for('home'))

@app.route("/get_flash_messages", methods=['GET'])
def get_flash_messages():
    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        messages.append({'category': category, 'message': message})
    return jsonify(messages)

@app.route("/like", methods=['POST'])
def like():
    uid_receive = 0
    try:
        uid_receive = session['uid']
    except:
        flash("로그인이 필요합니다.", "danger")
        return redirect(url_for('home'))

    title_receive = request.form["title"]
    artist_receive = request.form["artist"]
    image_receive = request.form["image_url"]

    music = Music.query.filter(Music.uid == uid_receive,
        Music.title == title_receive,
        Music.artist == artist_receive,
        Music.image_url == image_receive).first()
    if music:
        flash("이미 추가된 노래입니다.", "danger")
        return redirect(url_for('home'))
    else:
        music = Music(uid=uid_receive, title=title_receive, artist=artist_receive, image_url=image_receive)
        db.session.add(music)
        db.session.commit()
        flash("좋아요에 추가되었습니다.", "success")
        return redirect(url_for('home'))

@app.route("/unlike", methods=['POST'])
def unlike():
    mid_receive = request.form["mid"]
    uid_receive = session['uid']

    delete_data = Music.query.filter(Music.mid == mid_receive, Music.uid == uid_receive).first()
    db.session.delete(delete_data)
    db.session.commit()
    flash("좋아요에서 제거되었습니다.", "success")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)