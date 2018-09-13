-- CLEAR
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS lists;
DROP TABLE IF EXISTS expanded_isbns;
DROP TABLE IF EXISTS lists_books;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS courses_books;

-- STATIC
CREATE TABLE books
(
    isbn       VARCHAR(13) PRIMARY KEY,
    title      VARCHAR,
    author     VARCHAR,
    year       DATE,
    electronic BIT,
    callnumber VARCHAR
);

CREATE TABLE categories
(
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR
);

CREATE TABLE lists
(
    list_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name    VARCHAR,
    updated DATE,
    in_use  BIT,
    -- CONNECTIONS
    category_id INTEGER,

    FOREIGN KEY(category_id) REFERENCES categories(category_id)
);

-- PAIRS
CREATE TABLE lists_books
(
    -- CONNECTIONS
    isbn    VARCHAR(13),
    list_id INTEGER,

    PRIMARY KEY(isbn, list_id),

    FOREIGN KEY(isbn) REFERENCES books(isbn),
    FOREIGN KEY(list_id) REFERENCES lists(list_id)
);

-- CREATE TABLE expanded_isbns
-- (
--     isbn_src      VARCHAR(13),
--     isbn_expanded VARCHAR(13),
--
--     PRIMARY KEY(isbn_src, isbn_expanded),
--
--     FOREIGN KEY(isbn_src) REFERENCES books(isbn_src),
--     FOREIGN KEY(isbn_expanded) REFERENCES books(isbn_expanded)
-- );

CREATE TABLE `courses` (
	`course_code`	TEXT,
	`professor_name`	TEXT,
	`professor_email`	TEXT,
	`num_students`	INTEGER,

	PRIMARY KEY(`course_code`)
);

CREATE TABLE `courses_books` (
	`isbn`	VARCHAR(13),
	`course_code`	TEXT,
	`type`	TEXT,
	`price`	REAL,

	PRIMARY KEY(`isbn`,`course_code`)

    FOREIGN KEY(course_code) REFERENCES courses(course_code)
);