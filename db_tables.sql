-- CLEAR
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS lists;
DROP TABLE IF EXISTS expanded_isbns;
DROP TABLE IF EXISTS lists_books;

-- STATIC
CREATE TABLE books
(
    isbn       VARCHAR(13) PRIMARY KEY,
    title      VARCHAR,
    year       DATE,
    electronic BIT
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
    isbn    INTEGER,
    list_id INTEGER,

    PRIMARY KEY(isbn, list_id),

    FOREIGN KEY(isbn) REFERENCES books(isbn),
    FOREIGN KEY(list_id) REFERENCES lists(list_id)
);

CREATE TABLE expanded_isbns
(
    isbn_src      INTEGER,
    isbn_expanded INTEGER,

    PRIMARY KEY(isbn_src, isbn_expanded),

    FOREIGN KEY(isbn_src) REFERENCES books(isbn_src),
    FOREIGN KEY(isbn_expanded) REFERENCES books(isbn_expanded)
);
