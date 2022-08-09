import pandas as pd
from models import *
import datetime, gzip
import numpy as np

today = datetime.date.today()
weekday = today.weekday()

def read_tsv(fname, fields=None):
    fh =gzip.GzipFile(filename=fname)
    return pd.read_csv(fh, delimiter='\t', usecols=fields)

db.drop_all()
db.session.commit()
db.create_all()

eps = read_tsv('title.episode.tsv.gz')
ratings = read_tsv('title.ratings.tsv.gz')
ratings = ratings[ratings['numVotes'] > 100]

eps = eps[eps['seasonNumber'] != '\\N']
eps = eps.merge(ratings, how='inner', on='tconst')
del ratings
names = read_tsv('title.basics.tsv.gz', ['tconst', 'primaryTitle'])
names = names.drop_duplicates(subset='tconst')
eps = eps.merge(names, how='left', on='tconst')

for i, ep in enumerate(eps.itertuples()):
    epno = 'S'+str(ep.seasonNumber).zfill(2)+'E'+str(ep.episodeNumber).zfill(2)+' - '
    db.session.add(Episode(ep.tconst, ep.parentTconst, epno+str(ep.primaryTitle), ep.seasonNumber, ep.episodeNumber, int(ep.averageRating*10), int(ep.numVotes)))

db.session.commit()

shows = eps[['parentTconst']].drop_duplicates()
shows = shows.merge(names, left_on='parentTconst', right_on='tconst')

for show in shows.itertuples():
    show = Show(show.parentTconst, show.primaryTitle)
    db.session.add(show)

db.session.commit()

for show in Show.query.all():
    ratings = [e.rating for e in show.episodes]
    show.average = int(np.mean(ratings))
    show.std = np.round(np.std(ratings) / 10, 2)
    show.votes = sum([e.votes for e in show.episodes])

db.session.commit()
