import logging
import random
import time

import requests

from Config.ConfigManager import ConfigManager

logging.basicConfig(filename='time_analysis.log', level=logging.INFO)

config_manager = ConfigManager()
config = config_manager.get_config()
port = config.get('FLASK', 'PORT')
host = config.get('FLASK', 'HOST') or '127.0.0.1'
no_of_trials = 10


def cal_average_time_for_page_load():
    movie_page_arr = []

    # Movie page
    for i in range(no_of_trials):
        page = random.randint(1, 100)
        movie_page = f'http://{host}:{port}/page/{page}'

        try:
            start_time = time.perf_counter()

            response = requests.get(movie_page)

            end_time = time.perf_counter()

            movie_page_arr.append(end_time - start_time)

            logging.info(f"Time taken to load page {page}: {end_time - start_time} seconds")

            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logging.error(f"Error occurred while loading page {page}: {str(e)}")

    average_page_load_time = sum(movie_page_arr) / len(movie_page_arr)
    logging.info(f"Average time taken to load movie page: {average_page_load_time} seconds")


def cal_average_time_for_details_load():
    movie_details_arr = []
    movies = [
        "Live Free or Die Hard",
        "Cold Blood",
        "Underwater",
        "The Platform",
        "Jumanji: The Next Level",
        "The Twilight Saga: Eclipse",
        "Sonic the Hedgehog",
        "Star Wars: The Rise of Skywalker",
        "Onward",
        "Emma.",
        "Pocahontas II: Journey to a New World",
        "Lara Croft: Tomb Raider - The Cradle of Life",
    ]

    # Movie details page
    for movie in movies:
        movie_details = f'http://{host}:{port}/movie/{movie}'

        try:
            start_time = time.perf_counter()

            response = requests.get(movie_details)

            end_time = time.perf_counter()

            movie_details_arr.append(end_time - start_time)

            logging.info(f"Time taken to load movie {movie}: {end_time - start_time} seconds")

            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logging.error(f"Error occurred while loading movie {movie}: {str(e)}")

    average_details_load_time = sum(movie_details_arr) / len(movie_details_arr)
    logging.info(f"Average time taken to load movie page: {average_details_load_time} seconds")


if __name__ == '__main__':
    logging.info("Starting time analysis...")
    cal_average_time_for_page_load()
    cal_average_time_for_details_load()
    logging.info("Time analysis completed.")
