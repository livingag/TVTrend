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

episodes = [Episode(*ep.values) for _, ep in eps.iterrows()]

db.session.bulk_save_objects(episodes)
db.session.flush()

shows = eps[['parentTconst']].drop_duplicates()
shows = shows.merge(names, left_on='parentTconst', right_on='tconst')
shows = shows.drop('tconst', axis=1)

shows = [Show(*show.values) for _, show in shows.iterrows()]
db.session.bulk_save_objects(shows)

db.session.flush()

for show in Show.query.all():
    show.update_stats()

db.session.commit()
