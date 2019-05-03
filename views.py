from flask import render_template, request, redirect, url_for, jsonify
from tvtrend import app
import tvdb_api, requests
from bs4 import BeautifulSoup
import numpy as np

t = tvdb_api.Tvdb()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        showname = request.form['showname']

        show = t[showname]

        return redirect(url_for('plot_show',tvdbId=show.data['id']))
    else:
        return redirect(url_for('home'))

@app.route('/<string:tvdbId>')
def plot_show(tvdbId):
    show = t[int(tvdbId)]

    ratings = {}
    epNames = []

    for season in show.keys():
        if season > 0:
            seasonratings = []
            r = requests.get('https://www.imdb.com/title/{}/episodes?season={}'.format(show.data['imdbId'],season))
            soup = BeautifulSoup(r.content)
            for div in soup.find_all("div","ipl-rating-star small"):
                span = div.find_all("span","ipl-rating-star__rating")[0]
                seasonratings.append(float(span.text))
            eplist = soup.find_all("div","list detail eplist")[0]
            epNames.extend(['S{}E{} - '.format(season,ep+1)+a.text for ep, a in enumerate(eplist.find_all("strong"))])
            ratings[season] = seasonratings

    data = []
    fits = []
    x = 0
    for _, r in ratings.items():
        xx = list(range(x+1,len(r)+x+1))
        data.append(r)
        fits.append(list(np.poly1d(np.polyfit(xx, r, 1))(np.unique(xx))))
        x += len(r)

    return render_template('plot.html',show=show,ratings=data,epNames=epNames,fits=fits)