#!/usr/bin/env python3

from sys import stderr

import requests
from bs4 import BeautifulSoup

from actors_graph import ActorsGraph
from movie import Movie


MAIN_URL = 'https://www.imdb.com/title/'
MOVIES_LIST_PATH = 'movies.txt'

MAX_MOVIE_COUNT = 100
MAX_UNAVAILABLE_COUNT = 20


def get_page_content(url):
    r = requests.get(url)
    if not r.status_code == 200:
        raise RuntimeError('Problem accessing page data.')
    return r.text


def get_movie_name(content):
    soup = BeautifulSoup(content, 'html.parser')
    all_h1 = soup.find_all('h1')
    title = [x for x in all_h1 if 'itemprop="name"' in str(x)]
    title = str(title[0])
    title = title.split('>')
    title = title[1].split('<')[0]
    return title


def get_director_name(content):
    soup = BeautifulSoup(content, 'html.parser')
    all_spans = soup.find_all('span')
    director = [x for x in all_spans if 'itemprop="director"' in str(x)]
    if len(director) == 0:
        return ''
    director = str(director[0]).split('>')[-4]
    director = director.split('<')[0]
    return director


def change_movie_url(count, prefix):
    if count < 10:
        return prefix + '000000' + str(count)
    if count >= 10 and count < 100:
        return prefix + '00000' + str(count)
    if count >= 100 and count < 1000:
        return prefix + '0000' + str(count)
    if count >= 1000 and count < 10000:
        return prefix + '000' + str(count)
    if count >= 10000 and count < 100000:
        return prefix + '00' + str(count)
    if count >= 100000 and count < 1000000:
        return prefix + '0' + str(count)
    if count >= 1000000 and count < 10000000:
        return prefix + str(count)


def write_results_to_file(item):
    thefile = open(MOVIES_LIST_PATH, 'a')
    thefile.write(item)
    thefile.close()


def get_movie_actors(content):
    soup = BeautifulSoup(content, 'html.parser')
    all_tds = soup.find_all('td')
    cast_tds = [x for x in all_tds if 'itemprop="actor"' in str(x)]
    cast_span = [x.find_all('span') for x in cast_tds]
    cast_names = []
    for item in cast_span:
        for nestedItem in item:
            cast_names.append(nestedItem.text)
    return cast_names


def crawl_the_website():
    movies = []
    count = 0
    actors_graph = ActorsGraph()
    count_not_found = 0
    while count < MAX_MOVIE_COUNT and count_not_found < MAX_UNAVAILABLE_COUNT:
        count += 1
        print('Crawling...' + str(count), file=stderr)
        this_movie_url = change_movie_url(count, 'tt')
        try:
            content = get_page_content(MAIN_URL + this_movie_url + '/')
            count_not_found = 0
            title = get_movie_name(content)
            director = get_director_name(content)
            actors = get_movie_actors(content)
            actors_graph.add_edges(actors)
            this_movie = Movie()
            this_movie.set_all(title, director)
            this_movie.set_actors(actors)
            movies.append(this_movie)
            write_results_to_file(movies[-1].get_all_info())
        except RuntimeError:
            print('Movie not found.', file=stderr)
            count_not_found += 1
    return movies, actors_graph
