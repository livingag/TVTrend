from flask import render_template, request, redirect, url_for, jsonify, flash
from tvtrend import app
import json, requests, hmac, hashlib
import numpy as np
from datetime import datetime
from models import Show


@app.route("/")
def home():
    shownames = [{"title": x.name, "id": x.imdbid} for x in Show.query.all()]
    return render_template("home.html", shownames=shownames)


@app.route("/popular")
def popular():
    return render_template(
        "popular.html", shows=Show.query.order_by(Show.votes.desc()).all()[:250]
    )


@app.route("/<string:imdbId>")
def plot_show(imdbId):
    """Plot trend of episode ratings for a given tv show IMDb ID.

    Takes IMDb ID and returns response template with trend data plotted.

    Args:
        imdbID: IMDb ID of TV show to be plotted.

    Returns:
        Plotting page response.
    """

    r = requests.get(
        "https://api.themoviedb.org/3/find/{}?api_key={}&external_source=imdb_id".format(
            imdbId, app.config["TMDB_API"]
        )
    )

    ratings = {}
    epInfo = {"names": []}
    shInfo = {}

    try:
        shInfo["poster"] = (
            "https://image.tmdb.org/t/p/w500"
            + json.loads(r.content)["tv_results"][0]["poster_path"]
        )
    except:
        pass

    show = Show.query.filter_by(imdbid=imdbId).first()
    show.sort_episodes()
    seasons = set([e.season for e in show.episodes])
    for sea in seasons:
        ratings[sea] = [x.rating / 10 for x in show.episodes if x.season == sea]
    epInfo["names"] = [e.name for e in show.episodes]
    epInfo["dates"] = [e.votes for e in show.episodes]
    shInfo["name"] = show.name
    shInfo["average"] = show.average / 10
    shInfo["std"] = show.std
    shInfo["votes"] = show.votes

    data = []
    fits = {"season": [], "series": []}
    x = 0
    for _, r in ratings.items():
        xx = list(range(x + 1, len(r) + x + 1))
        data.append(r)
        bestfit = list(np.poly1d(np.polyfit(xx, r, 1))(np.unique(xx)))
        fits["season"].append(bestfit)
        x += len(r)

    seriesdata = [b for a in data for b in a]
    xx = list(np.arange(1, len(seriesdata) + 1))
    seriesfit = list(np.poly1d(np.polyfit(xx, seriesdata, 1))(np.unique(xx)))
    fits["series"] = [xx, seriesfit]

    return render_template(
        "plot.html", show=shInfo, ratings=data, epInfo=epInfo, fits=fits
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    import git
    from pathlib import Path

    if request.method == "POST":
        signature = request.headers.get("X-Hub-Signature")
        if not signature or not signature.startswith("sha1="):
            return "", 400

        digest = hmac.new(
            app.config["GITHUB_SECRET"].encode(), request.data, hashlib.sha1
        ).hexdigest()

        if hmac.compare_digest(signature, "sha1=" + digest):
            repo = git.Repo(".")
            origin = repo.remotes.origin
            repo.create_head("master", origin.refs.master).set_tracking_branch(
                origin.refs.master
            ).checkout()
            origin.pull()
            Path("/var/www/tvtrend_livingag_com_wsgi.py").touch()
            return "", 200
        else:
            return "", 400
    else:
        return "", 400
