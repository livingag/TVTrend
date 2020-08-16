from tvtrend import db


class Show(db.Model):
    __tablename__ = "shows"
    imdbid = db.Column(db.String(9), primary_key=True)
    name = db.Column(db.String(200))
    votes = db.Column(db.Integer())
    average = db.Column(db.Integer())
    std = db.Column(db.Float())
    episodes = db.relationship('Episode', backref='show', lazy=True)

    def __init__(self, imdbid, name):
        self.imdbid = imdbid
        self.name = name

    def sort_episodes(self):
        self.episodes.sort(key=lambda x: x.name)


class Episode(db.Model):
    __tablename__ = "episodes"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(200))
    season = db.Column(db.Integer())
    number = db.Column(db.Integer())
    rating = db.Column(db.Integer())
    votes = db.Column(db.Integer())
    imdbid = db.Column(db.String(9))
    showid = db.Column(db.String(9), db.ForeignKey('shows.imdbid'))

    def __init__(self, imdbid, showid, name, season, number, rating, votes):
        self.name = name
        self.season = season
        self.number = number
        self.rating = rating
        self.imdbid = imdbid
        self.showid = showid
        self.votes = votes

    def __repr__(self):
        return self.name