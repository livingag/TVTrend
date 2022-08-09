from tvtrend import db
import numpy as np


class Show(db.Model):
    __tablename__ = "shows"
    imdbid = db.Column(db.String(9), primary_key=True)
    name = db.Column(db.String(200))
    votes = db.Column(db.Integer())
    average = db.Column(db.Integer())
    std = db.Column(db.Float())
    episodes = db.relationship("Episode", backref="show", lazy=False)

    def __init__(self, imdbid, name):
        self.imdbid = imdbid
        self.name = name

    def sort_episodes(self):
        self.episodes.sort(key=lambda x: x.name)

    def update_stats(self):
        ratings = np.array([e.rating for e in self.episodes])
        self.average = int(ratings.mean())
        self.std = np.round(ratings.std() / 10, 2)
        self.votes = sum([e.votes for e in self.episodes])


class Episode(db.Model):
    __tablename__ = "episodes"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(200))
    season = db.Column(db.Integer())
    number = db.Column(db.Integer())
    rating = db.Column(db.Integer())
    votes = db.Column(db.Integer())
    imdbid = db.Column(db.String(9))
    showid = db.Column(db.String(9), db.ForeignKey("shows.imdbid"))

    def __init__(self, imdbid, showid, season, number, rating, votes, name):
        self.season = season
        self.number = number
        self.rating = int(rating*10)
        self.imdbid = imdbid
        self.showid = showid
        self.votes = int(votes)
        self.name = (
            "S" + str(season).zfill(2) + "E" + str(number).zfill(2) + " - " + name
        )

    def __repr__(self):
        return self.name
