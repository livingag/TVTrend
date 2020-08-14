import requests, gzip, io, os
import pandas as pd
from models import *
import datetime

today = datetime.date.today()
weekday = today.weekday()

def read_tsv(url, fields=None):
    r = requests.get(url, timeout=30, stream=True)
    gz = r.content
    f = io.BytesIO(gz)
    fh =gzip.GzipFile(fileobj=f)
    r.close()
    return pd.read_csv(fh, delimiter='\t', usecols=fields)

if (weekday == 0):
    db.drop_all()
    db.session.commit()
    db.create_all()

    eps = read_tsv('https://datasets.imdbws.com/title.episode.tsv.gz')
    ratings = read_tsv('https://datasets.imdbws.com/title.ratings.tsv.gz')

    eps = eps.set_index('tconst').join(ratings.set_index('tconst')).fillna(0)
    del ratings
    names = read_tsv('https://datasets.imdbws.com/title.basics.tsv.gz', ['tconst', 'primaryTitle'])
    eps = eps.merge(names, how='left', on='tconst')
    eps = eps.merge(names, how='left', left_on='parentTconst', right_on='tconst')
    del names
    eps = eps.rename(columns= {'primaryTitle_x': 'epTitle', 'primaryTitle_y': 'showTitle', 'tconst_x': 'tconst'})
    eps = eps[(eps['numVotes'] > 100) & (eps['seasonNumber'] != '\\N')]

    for i, ep in enumerate(eps.itertuples()):
        epno = 'S'+str(ep.seasonNumber).zfill(2)+'E'+str(ep.episodeNumber).zfill(2)+' - '
        db.session.add(Episode(ep.tconst, ep.parentTconst, epno+ep.epTitle, ep.seasonNumber, ep.episodeNumber, int(ep.averageRating*10), ep.numVotes))

    db.session.commit()

    shows = eps.drop_duplicates(subset=['parentTconst'])

    for show in shows.itertuples():
        show = Show(show.parentTconst, show.showTitle)
        db.session.add(show)

    db.session.commit()
