create table if not exists Actor
(
    actor_id   int auto_increment
        primary key,
    actor_name varchar(255) not null,
    tmdb_id    varchar(255) not null
);

create table if not exists Director
(
    director_id   int auto_increment
        primary key,
    director_name varchar(255) not null,
    tmdb_id       varchar(255) not null
);

create table if not exists Genre
(
    genre_id int auto_increment
        primary key,
    name     varchar(255) not null,
    constraint name
        unique (name)
);

create table if not exists Movie
(
    movie_id     int auto_increment
        primary key,
    title        varchar(255) not null,
    release_date date         not null,
    synopsis     text         not null
);

create table if not exists Movie_Actor
(
    movie_id        int  not null,
    actor_id        int  not null,
    movie_character text not null,
    constraint Movie_Actor_ibfk_1
        foreign key (movie_id) references Movie (movie_id),
    constraint Movie_Actor_ibfk_2
        foreign key (actor_id) references Actor (actor_id)
);

create index if not exists actor_id
    on Movie_Actor (actor_id);

create index if not exists movie_id
    on Movie_Actor (movie_id);

create table if not exists Movie_Director
(
    movie_id    int not null,
    director_id int not null,
    primary key (movie_id, director_id),
    constraint Movie_Director_ibfk_1
        foreign key (movie_id) references Movie (movie_id),
    constraint Movie_Director_ibfk_2
        foreign key (director_id) references Director (director_id)
);

create index if not exists director_id
    on Movie_Director (director_id);

create table if not exists Movie_Genre
(
    movie_id int not null,
    genre_id int not null,
    primary key (movie_id, genre_id),
    constraint Movie_Genre_ibfk_1
        foreign key (movie_id) references Movie (movie_id),
    constraint Movie_Genre_ibfk_2
        foreign key (genre_id) references Genre (genre_id)
);

create index if not exists genre_id
    on Movie_Genre (genre_id);

