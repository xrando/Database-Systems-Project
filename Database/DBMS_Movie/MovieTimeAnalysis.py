import time
import requests
import random
from Config.ConfigManager import ConfigManager
from pprint import pprint

config_manager = ConfigManager()
config = config_manager.get_config()
port = config.get('FLASK', 'PORT')
host = config.get('FLASK', 'HOST') or '127.0.0.1'
movies = [
    'The%20Little%20Mermaid%20(2023)',
    'The%20Flash%20(2023)',
    'The%20Machine%20(2023)'
]

movie_page_arr = []
movie_details_arr = []

for i in range(500):
    # random int between 1 and 100
    page = random.randint(1, 100)
    movie_page = f'http://{host}:{port}/page/{page}'
    # Create a GET request to the movie page, and time it
    start_time = time.time()
    response = requests.get(movie_page)
    end_time = time.time()
    movie_page_arr.append(end_time - start_time)
    print(f"Time taken to load page {page}: {end_time - start_time} seconds")
    # write to csv where first column is page number, second column is time taken to load page
    with open('movie_page.csv', 'a') as f:
        f.write(f"{page},{end_time - start_time}\n")

for movie in movies:
    movie_details = f'http://{host}:{port}/movie/{movie}'
    start_time = time.time()
    # Create a GET request to the movie details page, and time it
    response = requests.get(movie_details)
    end_time = time.time()
    movie_details_arr.append(end_time - start_time)
    print(f"Time taken to load movie {movie}: {end_time - start_time} seconds")

print(f"Average time taken to load movie page: {sum(movie_page_arr) / len(movie_page_arr)} seconds")
print(f"Average time taken to load movie details page: {sum(movie_details_arr) / len(movie_details_arr)} seconds")
