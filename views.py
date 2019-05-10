from flask import render_template, request, redirect, url_for, jsonify, flash
from tvtrend import app
import json
import requests
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
    """Queries the trakt.tv API for the specified show name.

    Args:
        showname: Show name to query (from form input).

    Returns:
        Redirect to plot_show with the corresponding IMDb ID, or back to
        home if show cannot be found.
    """
    if request.method == 'POST':
        showname = request.form['showname'].replace(' ', '%20')

        r = requests.get(
            'https://api.trakt.tv/search/show?query={}'.format(showname),
            headers=headers
        )

        if len(json.loads(r.content)) > 0:
            imdbId = json.loads(r.content)[0]['show']['ids']['imdb']

            return redirect(
                url_for('plot_show', imdbId=imdbId) +
                '?source={}'.format(request.form['source'])
            )

        else:
            flash('Show could not be found!')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/<string:imdbId>')
def plot_show(imdbId):
    """Plot trend of episode ratings for a given tv show IMDb ID.

    Scrapes the specified source (IMDb or trakt.tv) for episode ratings
    and returns response template with trend data plotted. Source is
    specified through query string.

    Args:
        imdbID: IMDb ID of TV show to be plotted.
        source (optional): source for episode ratings. Defaults to 'imdb'.

    Returns:
        Plotting page response.
    """
    if 'source' in request.args.keys():
        source = request.args['source']
    else:
        source = 'imdb'

    r = requests.get(
        'https://api.trakt.tv/shows/{}/seasons'.format(imdbId),
        headers=headers
    )

    if r.status_code != 200:
        flash('Invalid IMDb ID!')
        return redirect(url_for('home'))

    ratings = {}
    epInfo = {'names': [], 'dates': []}

    for season in [a['number'] for a in json.loads(r.content)]:
        if season > 0:
            seasonratings = []
            if source == 'imdb':
                r = requests.get(
                    'https://www.imdb.com/title/{}/episodes?season={}'.format(
                        imdbId, season
                    )
                )
                soup = BeautifulSoup(r.content)
                for div in soup.find_all("div", "ipl-rating-star small"):
                    span = div.find_all("span", "ipl-rating-star__rating")[0]
                    seasonratings.append(float(span.text))
                eplist = soup.find_all("div", "list detail eplist")[0]
                if len(seasonratings) > 0:
                    names = [
                        'S{}E{} - '.format(season, ep+1) +
                        a.text for ep, a in enumerate(
                            eplist.find_all("strong")
                        )
                    ]
                    dates = [
                        a.text.strip() for a in eplist.find_all(
                            "div", "airdate"
                        )
                    ]
                    epInfo['names'].extend(names)
                    epInfo['dates'].extend(dates)
                    ratings[season] = seasonratings
            elif source == 'trakt':
                r = requests.get(
                    'https://trakt.tv/shows/{}/seasons/{}'.format(
                        imdbId, season
                    )
                )
                soup = BeautifulSoup(r.content)
                rates = [
                    int(a.text[:-1])/10 for a
                    in soup.find_all("div", "percentage")
                ]
                names = [
                    a.text for a
                    in soup.find_all("span", "main-title")[::2]
                ]
                li = soup.find("div", {"id": "seasons-episodes-sortable"})
                dates = [
                    a['data-date'][:10] for a
                    in li.findChildren("span", "convert-date")
                ][::2]
                for i, d in enumerate(dates):
                    if datetime.strptime(d, '%Y-%m-%d') <= datetime.now():
                        seasonratings.append(rates[i])
                        epInfo['names'].append(
                            'S{}E{} - '.format(season, i+1) +
                            names[i]
                        )
                        epInfo['dates'].append(d)
                ratings[season] = seasonratings
            else:
                flash('Invalid ratings source - must be imdb or trakt')
                return redirect(url_for('home'))

    data = []
    fits = {'season': [], 'series': []}
    x = 0
    for _, r in ratings.items():
        xx = list(range(x+1, len(r)+x+1))
        data.append(r)
        bestfit = list(np.poly1d(np.polyfit(xx, r, 1))(np.unique(xx)))
        fits['season'].append(bestfit)
        x += len(r)

    seriesdata = [b for a in data for b in a]
    xx = list(np.arange(1, len(seriesdata)+1))
    seriesfit = list(np.poly1d(np.polyfit(xx, seriesdata, 1))(np.unique(xx)))
    fits['series'] = [xx, seriesfit]

    r = requests.get(
        'https://api.trakt.tv/shows/{}'.format(imdbId),
        headers=headers
    )
    showname = json.loads(r.content)['title']

    return render_template('plot.html',
                           showname=showname,
                           ratings=data,
                           epInfo=epInfo,
                           fits=fits)


@app.route('/webhook', methods=['POST'])
def webhook():
    import git
    from pathlib import Path
    if request.method == 'POST':
        repo = git.Repo('.')
        origin = repo.remotes.origin
        repo.create_head(
            'master',
            origin.refs.master
        ).set_tracking_branch(origin.refs.master).checkout()
        origin.pull()
        Path('/var/www/tvtrend_livingag_com_wsgi.py').touch()
        return '', 200
    else:
        return '', 400
