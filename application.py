import os
import sqlalchemy
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime, timedelta, date
from flask_sqlalchemy import SQLAlchemy
import shortuuid

app = Flask(__name__)
app.secret_key = 'woo'

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


### Local database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/indecisive'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class polldb(db.Model):
    poll_id = db.Column('poll_id', db.String(), primary_key=True)
    question = db.Column(db.String())
    answer1 = db.Column(db.String())
    answer2 = db.Column(db.String())
    answer3 = db.Column(db.String())
    answer4 = db.Column(db.String())
    result1 = db.Column(db.Integer)
    result2 = db.Column(db.Integer)
    result3 = db.Column(db.Integer)
    result4 = db.Column(db.Integer)
    time = db.Column(db.Time)
    name = db.Column(db.String())
    date = db.Column(db.Date)
    datetime = db.Column()

    def __init__(self, poll_id, question, answer1, answer2, answer3, answer4, \
    result1, result2, result3, result4, time, name, date, datetime):
        self.poll_id = poll_id
        self.question = question
        self.answer1 = answer1
        self.answer2 = answer2
        self.answer3 = answer3
        self.answer4 = answer4
        self.result1 = result1
        self.result2 = result2
        self.result3 = result3
        self.result4 = result4
        self.time = time
        self.name = name
        self.date = date
        self.datetime = datetime

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    if request.method =="POST":
        if request.form['submit'] == 'NEW':
            return redirect(url_for("new"))
        else:
            return redirect(url_for("browse"))


@app.route('/new', methods=["GET", "POST"])
def new():
    if request.method == "GET":
        time = datetime.now() + timedelta(hours=2)
        time = time.strftime("%H:%M")
        return render_template("new.html", time=time)

    if request.method =="POST":

        url = shortuuid.uuid()
        check = polldb.query.filter_by(poll_id = url)
        print(check)

        if url in check:
            return redirect(url_for("new"))

        poll_id = url
        name = request.form.get("name")
        question = request.form.get("question")
        answer1 = request.form.get("answer1")
        answer2 = request.form.get("answer2")
        answer3 = request.form.get("answer3")
        answer4 = request.form.get("answer4")
        # time = request.form.get("time")
        time = datetime.now() + timedelta(hours=2)
        poll_datetime = datetime.now() + timedelta(hours=2)

        if not answer1:
            flash("Please fill in all fields")
            return redirect(url_for("new"))

        if not answer2:
            flash("Please fill in all fields")
            return redirect(url_for("new"))

        newPoll = polldb(poll_id=poll_id, question=question, answer1=answer1, answer2=answer2, answer3=answer3, answer4=answer4,\
        result1=0,result2=0,result3=0,result4=0,time=time, name=name, date=date.today(), datetime=poll_datetime)
        db.session.add(newPoll)
        db.session.commit()

        flash("Click the share button below to share this poll with friends and family so they can vote")
        session["name"] = name
        session["question"] = question
        session["answer1"] = answer1
        session["answer2"] = answer2
        session["answer3"] = answer3
        session["answer4"] = answer4
        return redirect(url_for("poll", poll_id=poll_id))

@app.route("/poll/<poll_id>", methods=["GET", "POST"])
def poll(poll_id):

    # If there is still time to complete the poll
    if request.method == "GET":

        details = polldb.query.filter_by(poll_id=poll_id).first()

        if details.datetime >= datetime.now():
            return render_template("pollTemplate.html", details=details)
        #
        flash("This poll has now finished. Here are the results")
        return redirect(url_for("results", poll_id=poll_id))

    if request.method =="POST":

        details = polldb.query.filter_by(poll_id=poll_id).first()
        result = request.form['toggle']
        if result == "result1":
            details.result1 = details.result1 + 1
            db.session.commit()
        elif result == "result2":
            details.result2 = details.result2 + 1
            db.session.commit()
        elif result == "result3":
            details.result3 = details.result3 + 1
            db.session.commit()
        elif result == "result4":
            details.result4 = details.result4 + 1
            db.session.commit()

        return redirect(url_for("results", poll_id=poll_id))

    # If there is NO time left to complete the poll
    # redirect to results

@app.route("/poll/<poll_id>/results")
def results(poll_id):

        details = polldb.query.filter_by(poll_id=poll_id).first()

        return render_template("results.html",\
        # question=question, answer1=answer1, answer2=answer2, answer3=answer3, answer4=answer4, \
        details=details)

@app.route("/browse")
def browse():
    if request.method == "GET":

        details = polldb.query.all()

        endingsoon = datetime.now() + timedelta(hours=1)
        # time = time.strftime("%H:%M")
        endinglater = datetime.now() + timedelta(hours=3)
        ending = polldb.query.filter(polldb.datetime > datetime.now(), polldb.datetime < endingsoon).all()
        responses = polldb.query.filter(polldb.datetime > datetime.now()).all()

        return render_template("browse.html", ending=ending, responses=responses)

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
