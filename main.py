from flask import Flask, send_file, render_template, redirect
import yt_dlp as youtube_dl

import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column
import shutil
import threading
from dotenv import load_dotenv
load_dotenv()
import os
from proxy import get_proxy


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
# db.init_app(app)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    yt_id = db.Column(db.String(255), nullable=False)


with app.app_context():
    db.create_all()
scheduler = BackgroundScheduler()
scheduler.start()



def sync_db():
    with app.app_context():
        res = db.session.execute(text("SELECT * FROM song"))
        for file in os.listdir("static/downloaded"):
            info = file.split("@")
            if file.endswith(".mp3") and file.replace(".mp3", ".webm") not in os.listdir("static/downloaded"):
                if file not in os.listdir("static/indb"):
                    song = Song(title=info[2], artist=info[1], yt_id=info[0])
                    db.session.add(song)
                    shutil.move(f"static/downloaded/{file}", f"static/indb")
                else:
                    os.remove(f"static/downloaded/{file}")
        db.session.commit()

scheduler.add_job(sync_db, 'interval', seconds=5)

    

def downloadsong(url: str):
    proxy = get_proxy()
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'verbose': True,
        'outtmpl': 'static/downloaded/%(id)s@%(artist)s@%(title)s.%(ext)s',
        'ignoreerrors': True,
        'proxy': proxy
    }
    try:
        
        with app.app_context():
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                yt_id = info_dict.get('id')
                res = db.session.execute(text("SELECT * FROM song WHERE yt_id = :yt_id"), {"yt_id": yt_id}).fetchone()
                print(res)
                if res is None:
                    print("not found")
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        ydl.download(url)
                        
                else:
                    print("downloaded already")
                
    except Exception as e:
        print(e)

# downloadsong("https://music.youtube.com/playlist?list=PLiEWsl0vGZ6DUba7stAZlQt2pU5EZUXQl&si=n15MurPxImfz-ejL")


@app.route("/download", methods=["POST"])
def index():
    url = request.headers.get("url")
    threading.Thread(target=downloadsong, args=(url,)).start()
    return "Hello, World!"


@app.route("/list_songs")
def list_songs():
    returned = []
    res = db.session.execute(text("SELECT * FROM song")).fetchall()
    for re in res:
        returned.append({"id": re[0], "title": re[1], "artist": re[2], "yt_id": re[3]})
        
    return returned


@app.route("/song/<int:id>")
def song(id: int):
    res = db.session.execute(text("SELECT * FROM song WHERE id = :id"), {"id": id}).fetchone()

    return send_file(f'static/indb/{res[3]}@{res[2]}@{res[1]}', mimetype='audio/mpeg')

@app.route("/song_from_yt/<yt_id>")
def song_from_yt(yt_id: str):
    res = db.session.execute(text("SELECT * FROM song WHERE yt_id = :yt_id"), {"id": yt_id}).fetchone()

    return send_file(f'static/indb/{res[3]}@{res[2]}@{res[1]}', mimetype='audio/mpeg')

@app.route("/delete/<int:id>/<key>", methods=['POST'])
def delete(id: int, key: str):
    real_key = os.getenv("key")
    if key != real_key:
        return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley")
    res = db.session.execute(text("SELECT * FROM song WHERE id = :id"), {"id": id}).fetchone()
    if res is not None:
        db.session.execute(text("DELETE FROM song WHERE id = :id"), {"id": id})
        db.session.commit()
        os.remove(f"static/indb/{res[3]}@{res[2]}@{res[1]}")
        return {"message": "deleted"}
    else:
        return {"error": "Song with that id doesnt exist"}

@app.route("/admin/<key>", methods=['GET'])
def admin(key: str):
    real_key = os.getenv("key")
    if key != real_key:
        return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley")
    returned = []
    with app.app_context():
        res = db.session.execute(text("SELECT * FROM song")).fetchall()
        for re in res:
            returned.append({"id": re[0], "title": re[1], "artist": re[2], "yt_id": re[3]})
    
    return render_template("admin.html", songs=returned, key=key)
            
@app.route("/fix/<key>")
def fix(key: str):
    with app.app_context():
        real_key = os.getenv("key")
        if key != real_key:
            return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley")
        for file in os.listdir("static/indb"):
            if file.split("@")[1] == "NA":
                if " - " in file.split("@")[2]:
                    artist = file.split("@")[2].split(" - ")[0]
                
                    yt_id = file.split('@')[0]
                    new_title = file.replace("NA", artist).replace(f"{artist} - ", "")
                    query = text("UPDATE song SET artist = :artist, title = :new_title WHERE yt_id = :yt_id")
                    db.session.execute(query, {"artist":artist, "new_title": new_title, "yt_id": yt_id})

                    os.rename(f"static/indb/{file}", f"static/indb/{new_title}")
        db.session.commit()
    
    return "done"
if __name__ == "__main__":
    app.run(debug=False, port=27237, host="0.0.0.0")
