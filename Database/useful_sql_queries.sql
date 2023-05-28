# Check for duplicates in Actor table where actor_name is duplicated
SELECT actor_name, COUNT(actor_name) AS count
FROM Actor
GROUP BY actor_name
HAVING count > 1;

# Select Movie and director name where movie_director.movie_id = movie.movie_id and
# movie_director.director_id = director.director_id
# To check if there are any duplicates in the movie_director table
SELECT Movie.movie_id, title, director_name, Movie.release_date
FROM Movie
INNER JOIN Movie_Director ON Movie.movie_id = Movie_Director.movie_id
INNER JOIN Director ON Movie_Director.director_id = Director.director_id
GROUP BY release_date DESC;

select count(*) from Movie_Director;
select count(*) from Movie;

# Use OFFSET to get the last 30 movies
# Useful for "pages" function
SELECT * from Movie
WHERE release_date < CURRENT_DATE()
ORDER BY release_date DESC
Limit 30
OFFSET 30; # TO get the next 30 movies after the first 30