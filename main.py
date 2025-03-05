from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


class Base(DeclarativeBase):
    pass


# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class UpdateForm(FlaskForm):
    rating = StringField('Your rating out of 10', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Update')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    add = SubmitField('Add Movie')


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(500), nullable=True)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)

tmdb_url = "https://api.themoviedb.org/3/"
image_url = "https://image.tmdb.org/t/p/w500"
access_token = os.getenv('ACCESS_TOKEN')
headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.ranking.asc()))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    movie_id = request.args.get('id')
    update_form = UpdateForm()
    movie = db.get_or_404(Movie, movie_id)
    if update_form.validate_on_submit():
        movie.rating = float(update_form.rating.data)
        movie.review = update_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template('edit.html', form=update_form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    movie_form = AddForm()

    if movie_form.validate_on_submit():
        title = movie_form.title.data
        url = f"{tmdb_url}search/movie"
        response = requests.get(url, headers=headers, params={'query': title})
        all_movies = response.json()['results']
        return render_template('select.html', movies=all_movies)
    else:
        return render_template('add.html', form=movie_form)

@app.route("/find_movie")
def find_movie():
    movie_id = request.args.get('id')
    if movie_id:
        url = f"{tmdb_url}movie/{movie_id}"

        response = requests.get(url, headers=headers)
        movie_data = response.json()

        movie_title = movie_data['title']
        movie_poster = f"{image_url}{movie_data['poster_path']}"
        movie_year = movie_data['release_date'][:4]
        movie_description = movie_data['overview']

        movie_to_add = Movie(id=movie_id, title=movie_title, img_url=movie_poster, year=movie_year, description=movie_description, rating=0.0, review='', ranking=0)
        db.session.add(movie_to_add)
        db.session.commit()

        return redirect(url_for('edit', id=movie_id))

if __name__ == '__main__':
    app.run(debug=True)
