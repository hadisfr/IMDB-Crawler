from sys import stderr
from math import log10

import requests
from bs4 import BeautifulSoup

from actors_graph import ActorsGraph
from movie import Movie

DEFAULT_MAX_MOVIE_COUNT = 100
DEFAULT_MAX_UNAVAILABLE_COUNT = 20


class Crawler(object):
    main_url = 'https://www.imdb.com/title/'

    def __init__(self, movies_list_path,
                 max_movie_count=DEFAULT_MAX_MOVIE_COUNT,
                 max_unavailable_count=DEFAULT_MAX_UNAVAILABLE_COUNT):
        self.movies_list_path = movies_list_path
        self.max_movie_count = max_movie_count
        self.max_unavailable_count = max_unavailable_count

    def get_page_content(self, url):
        r = requests.get(url)
        if not r.status_code == 200:
            raise RuntimeError('Problem accessing page data.')
        return r.text

    def get_movie_name(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        all_h1 = soup.find_all('h1')
        title = [x for x in all_h1 if 'itemprop="name"' in str(x)]
        title = str(title[0]).split('>')[1].split('<')[0]
        return title

    def get_director_name(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        all_spans = soup.find_all('span')
        director = [x for x in all_spans if 'itemprop="director"' in str(x)]
        if len(director) == 0:
            return ''
        director = str(director[0]).split('>')[-4].split('<')[0]
        return director

    def change_movie_url(self, number, prefix):
        return prefix + max([6 - int(log10(number)), 0]) * '0' + str(number)

    def write_results_to_file(self, item):
        with open(self.movies_list_path, 'a') as f:
            f.write(str(item))

    def get_movie_actors(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        all_tds = soup.find_all('td')
        cast_tds = [x for x in all_tds if 'itemprop="actor"' in str(x)]
        cast_span = [x.find_all('span') for x in cast_tds]
        cast_names = []
        for item in cast_span:
            for nestedItem in item:
                cast_names.append(nestedItem.text)
        return cast_names

    def crawl_the_website(self):
        movies = []
        count = 0
        actors_graph = ActorsGraph()
        count_not_found = 0
        while count < self.max_movie_count and count_not_found < self.max_unavailable_count:
            count += 1
            print('Crawling... ' + str(count), file=stderr)
            this_movie_url = self.change_movie_url(count, 'tt')
            try:
                content = self.get_page_content(self.main_url + this_movie_url + '/')
                count_not_found = 0
                title = self.get_movie_name(content)
                director = self.get_director_name(content)
                actors = self.get_movie_actors(content)
                actors_graph.add_edges(actors)
                movies.append(Movie(title, director, actors))
                self.write_results_to_file(movies[-1])
            except RuntimeError as e:
                print(e, file=stderr)
                count_not_found += 1
        return movies, actors_graph
