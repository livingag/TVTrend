# TVTrend
Plot episode user ratings for TV shows.

Episode rating data is obtained from [IMDb](https://datasets.imdbws.com/).

![Example plot for Lost](static/example.png)

## Config

Config variables are required in a `config.py` file in the root directory, containing:

Variable | Description
--- | ---
`TMDB_API` | TMDB API key
`SECRET_KEY` | flask secret key