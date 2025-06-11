from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = '../songs'  # <--- Using your existing songs/ folder
db = SQLAlchemy(app)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

ADMIN_USERNAME = 'amisha'
ADMIN_PASSWORD = 'amisha123##'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Credentials")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    songs = Song.query.all()
    return render_template('dashboard.html', songs=songs)

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        file = request.files['file']
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        new_song = Song(name=name, filename=filename)
        db.session.add(new_song)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_song.html')

@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    song = Song.query.get_or_404(song_id)
    if request.method == 'POST':
        song.name = request.form['name']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_song.html', song=song)

@app.route('/delete/<int:song_id>')
def delete_song(song_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    song = Song.query.get_or_404(song_id)
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], song.filename))
    except:
        pass
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
