# -*- coding: utf-8 -*-
"""
Provides a basic api for looking up media information using any installed and
configured services.
"""
from __future__ import unicode_literals
try:
    import configparser  # py3
except ImportError:
    import ConfigParser as configparser
from tranny import app

# Config section names
_tmdb_section = "themoviedb"
_imdb_section = "imdb"

_imdb_cache = {}

# Try and load imdb
try:
    import imdb

    _imdb_enabled = True
except (ImportError, configparser.Error):
    imdb, _imdb_enabled = False, False

# Try and load themoviedb
try:
    from ..service import tmdb

    _tmdb_enabled = True
except (ImportError, configparser.Error):
    tmdb, _tmdb_enabled = False, False


def score(title, min_votes=0, precision=1):
    """ Fetch a average score based on the enabled and installed movie/tv info
    database modules.

    :param title: Media title to lookup
    :type title: unicode
    :param min_votes: Minimum number of votes required to allow the score to be used
    :type min_votes: int
    :param precision: set the score precision returned
    :type precision: int
    :return: Average score across all enabled backend services
    :rtype: float
    """
    scores = []
    if imdb and _imdb_enabled and app.config.getboolean("imdb", "enabled"):
        scores.append(_imdb_score(title, min_votes=min_votes))
    if tmdb and _tmdb_enabled and app.config.getboolean("themoviedb", "enabled"):
        scores.append(_tmdb_score(title, min_votes=min_votes))
    if not scores:
        return 0
    return round(sum(scores) / float(len(scores)), precision)


def imdb_info(title):
    """ Search IMDB for the title provided. Return the 1st match returned making
    the assumption its accurate

    :param title: Name of the show/movie to lookup
    :type title: unicode
    :return: Info about the title
    :rtype: dict
    """
    try:
        if title in _imdb_cache:
            return _imdb_cache[title]
    except KeyError:
        pass
    i = imdb.IMDb()
    search_result = i.search_movie(title, results=1)
    if not search_result:
        return None
    result = search_result[0]
    i.update(result)
    _imdb_cache[title] = result
    return result


def _imdb_score(title, min_votes=0):
    """ Get the IMDB score for the title provided. If the minimum number of votes
    is greater than 0 and the vote count is less than that number, 0 will be returned

    :param title: Name of the show/movie to lookup
    :type title: unicode
    :param min_votes: Minimum required votes to allow the score to be used
    :type min_votes: int
    :return: IMDB score
    :rtype: float
    """
    info = imdb_info(title)
    if info:
        if min_votes and info['votes'] < min_votes:
            return 0
        return info['rating']
    return 0


def tmdb_info(title):
    """ Search themoviedb for the title provided. Return the 1st match returned making
    the assumption its accurate

    :param title: Media name to lookup
    :type title: unicode
    :return: Info about the title
    :rtype: dict
    """
    result = False
    search_result = tmdb.Movies(title, limit=True)
    for movie in search_result.iter_results():
        result = movie
        break
    return result


def _tmdb_score(title, min_votes=0):
    """ Get themoviedb score for the title provided. If the minimum number of votes
    is greater than 0 and the vote count is less than that number, 0 will be returned

    :param title: Name of the show/movie to lookup
    :type title: unicode
    :param min_votes: Minimum required votes to allow the score to be used
    :type min_votes: int
    :return: themoviedb score
    :rtype: float
    """
    info = tmdb_info(title)
    if info:
        if min_votes and info['votes'] < min_votes:
            return 0
        return info['vote_average']
    return 0
