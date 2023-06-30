import random
import requests
import time
import logging

from Config.ConfigManager import ConfigManager

logging.basicConfig(filename='time_analysis.log', level=logging.INFO)


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

# Movie page
for i in range(500):
    page = random.randint(1, 100)
    movie_page = f'http://{host}:{port}/page/{page}'

    try:
        start_time = time.perf_counter()

        response = requests.get(movie_page)

        end_time = time.perf_counter()

        movie_page_arr.append(end_time - start_time)

        logging.info(f"Time taken to load page {page}: {end_time - start_time} seconds")

        with open('movie_page.csv', 'a') as f:
            f.write(f"{page},{end_time - start_time}\n")

        time.sleep(random.uniform(0.5, 1.5))

    except Exception as e:
        logging.error(f"Error occurred while loading page {page}: {str(e)}")

# Movie details page
for movie in movies:
    movie_details = f'http://{host}:{port}/movie/{movie}'

    try:
        start_time = time.perf_counter()

        response = requests.get(movie_details)

        end_time = time.perf_counter()

        movie_details_arr.append(end_time - start_time)

        logging.info(f"Time taken to load movie {movie}: {end_time - start_time} seconds")

    except Exception as e:
        logging.error(f"Error occurred while loading movie {movie}: {str(e)}")

average_page_load_time = sum(movie_page_arr) / len(movie_page_arr)
average_details_load_time = sum(movie_details_arr) / len(movie_details_arr)

logging.info(f"Average time taken to load movie page: {average_page_load_time} seconds")
