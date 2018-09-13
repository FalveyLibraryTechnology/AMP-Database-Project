import argparse
import csv
import datetime
from math import floor
import progressbar
import re
import sqlite3
from string import ascii_uppercase
import xlwings as xw

parser = argparse.ArgumentParser()
parser.add_argument("-db", "--databasename", required=True, help="Database name")
args = parser.parse_args()

conn = sqlite3.connect("tmp/%s.sqlite" % args.databasename)

def get_book_rows():
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS tmp_bookstore;")
    cursor.execute("DROP TABLE IF EXISTS tmp_catalog;")
    cursor.execute("CREATE TEMPORARY TABLE tmp_bookstore AS SELECT isbn FROM lists_books WHERE list_id IN (SELECT list_id FROM lists WHERE category_id = 1 AND in_use = 1);")
    cursor.execute("CREATE TEMPORARY TABLE tmp_catalog AS SELECT isbn FROM lists_books WHERE list_id IN (SELECT list_id FROM lists WHERE category_id = 2 AND in_use = 1);")
    cursor.execute("""SELECT isbn, callnumber, title, author, year, electronic FROM books
            WHERE isbn IN (SELECT * FROM tmp_bookstore INTERSECT SELECT * FROM tmp_catalog)
            GROUP BY isbn;""")
    return cursor.fetchall()

def get_lists_books():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT courses_books.isbn, courses.num_students, courses.course_code, courses.professor_email
            FROM courses
            INNER JOIN courses_books ON courses_books.course_code = courses.course_code
            INNER JOIN lists_books ON lists_books.isbn = courses_books.isbn
            INNER JOIN lists ON lists.list_id = lists_books.list_id
            WHERE lists.in_use = 1""")
    isbn_map = {}
    ISBN = 0
    NUM = 1
    CODE = 2
    EMAIL = 3
    for line in cursor.fetchall():
        if not line[NUM]:
            continue
        if line[ISBN] in isbn_map:
            isbn_map[line[ISBN]].append("%s (%d)" % (line[CODE], line[NUM]))
            isbn_map[line[ISBN]].append(line[EMAIL])
            isbn_map[line[ISBN]][ISBN] += line[NUM]
        else:
            isbn_map[line[ISBN]] = [
                line[NUM],
                "%s (%d)" % (line[CODE], line[NUM]),
                line[EMAIL]
            ]
    return isbn_map


def make_row(row, courses):
    isbn, callnumber, title, author, year, electronic = row
    arr = [
        isbn,   # ISBN
        title,  # Title
        author, # Author
        year,  # Pub Year
        "Yes" if electronic == 1 else "No", # Electronic Catalog Match (Y/N)
        "Yes" if electronic == 0 else "No", # Print Catalog Match (Y/N)
        "",                                 # Print Match Pulled for Course Reserves (date)
        callnumber, # Call Number
        "",         # GOBI Ebook ISBN
        "",         # Platform
        "",         # GOBI Lowest Purchase Price
        "",         # Alternate Edition Notes (ebook may be 1, 3, or unlimited seat)
        "",         # Blackboard Link Name
        "",         # Ebook URL
        "",         # Purchase Platform
        "",         # Purchase Price
        "",         # Purchase Fund
        "",         # Confirmed Purchase Price
        "",         # Purchase Date
        ""          # Notes
    ]
    return (arr + courses)

rows = get_book_rows()
isbn_map = get_lists_books()
date_str = datetime.datetime.now().strftime("%Y-%m-%d")
outfile = open("Reports/AMP Report.%s.csv" % date_str, "w", newline='', encoding="utf-8");
writer = csv.writer(outfile)
writer.writerow(["ISBN", "Title", "Author", "Pub Year", "Electronic Catalog Match (Y/N)", "Print Catalog Match (Y/N)", "Print Match Pulled for Course Reserves (date)", "Call Number", "GOBI Ebook ISBN", "Platform", "GOBI Lowest Purchase Price", "Alternate Edition Notes (ebook may be 1, 3,  or unlimited seat)", "Blackboard Link Name", "Ebook URL", "Purchase Platform", "Purchase Price", "Purchase Fund", "Confirmed Purchase Price", "Purchase Date", "Notes", "Total Enrollment", "Course 1", "Instructor 1"])
for row in rows:
    writer.writerow(make_row(row, isbn_map[row[0]] if row[0] in isbn_map else []))
conn.close()
