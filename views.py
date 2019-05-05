from flask import render_template, request, redirect, url_for, jsonify
from tvtrend import app
import requests, json
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime

headers = {
    'Content-Type': 'application/json',
    'trakt-api-version': '2',
    'trakt-api-key': app.config['TRAKT_API']
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        showname = request.form['showname'].replace(' ','%20')

        r = requests.get('https://api.trakt.tv/search/show?query={}'.format(showname),headers=headers)
        imdbId = json.loads(r.content)[0]['show']['ids']['imdb']

        return redirect(url_for('plot_show',imdbId=imdbId)+'?source={}'.format(request.form['source']))
    else:
        return redirect(url_for('home'))

@app.route('/<string:imdbId>')
def plot_show(imdbId):
    if 'source' in request.args.keys():
        source = request.args['source']
    else:
        source = 'imdb'

    r = requests.get('https://api.trakt.tv/shows/{}/seasons'.format(imdbId),headers=headers)

    ratings = {}
    epInfo = {'names': [], 'dates': []}

    for season in [a['number'] for a in json.loads(r.content)]:
        if season > 0:
            seasonratings = []
            if source =='imdb':
                r = requests.get('https://www.imdb.com/title/{}/episodes?season={}'.format(imdbId,season))
                soup = BeautifulSoup(r.content)
                for div in soup.find_all("div","ipl-rating-star small"):
                    span = div.find_all("span","ipl-rating-star__rating")[0]
                    seasonratings.append(float(span.text))
                eplist = soup.find_all("div","list detail eplist")[0]
                if len(seasonratings) > 0:
                    epInfo['names'].extend(['S{}E{} - '.format(season,ep+1)+a.text for ep, a in enumerate(eplist.find_all("strong"))])
                    epInfo['dates'].extend([a.text.strip() for a in eplist.find_all("div","airdate")])
                    ratings[season] = seasonratings
            elif source == 'trakt':
                r = requests.get('https://trakt.tv/shows/{}/seasons/{}'.format(imdbId,season))
                soup = BeautifulSoup(r.content)
                rates = [int(a.text[:-1])/10 for a in soup.find_all("div", "percentage")]
                names = [a.text for a in soup.find_all("span","main-title")[::2]]
                li = soup.find("div",{"id": "seasons-episodes-sortable"})
                dates = [a['data-date'][:10] for a in li.findChildren("span","convert-date")][::2]
                for i, d in enumerate(dates):
                    if datetime.strptime(d,'%Y-%m-%d') <= datetime.now():
                        seasonratings.append(rates[i])
                        epInfo['names'].append('S{}E{} - '.format(season,i+1)+names[i])
                        epInfo['dates'].append(d)
                ratings[season] = seasonratings
            else:
                return redirect(url_for('home'))

    data = []
    fits = {'season': [], 'series': []}
    x = 0
    for _, r in ratings.items():
        xx = list(range(x+1,len(r)+x+1))
        data.append(r)
        fits['season'].append(list(np.poly1d(np.polyfit(xx, r, 1))(np.unique(xx))))
        x += len(r)

    seriesdata = [b for a in data for b in a]
    xx = list(np.arange(1,len(seriesdata)+1))
    fits['series'] = [xx,list(np.poly1d(np.polyfit(xx, seriesdata, 1))(np.unique(xx)))]

    r = requests.get('https://api.trakt.tv/shows/{}'.format(imdbId),headers=headers)
    showname = json.loads(r.content)['title']

    return render_template('plot.html',showname=showname,ratings=data,epInfo=epInfo,fits=fits)

@app.route('/webhook', methods=['POST'])
def webhook():
    import git
    from pathlib import Path
    if request.method == 'POST':
        repo = git.Repo('.')
        origin = repo.remotes.origin
        repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
        origin.pull()
        Path('/var/www/tvtrend_livingag_com_wsgi.py').touch()
        return '', 200
    else:
        return '', 400