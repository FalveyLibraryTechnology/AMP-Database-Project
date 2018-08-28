import csv
import datetime
import json
import os
import sys
import re
import sqlite3
import xlrd
import pandas as pd
import argparse
from collections import OrderedDict

from src.ProgressBar import ProgressBar
from src.utils import getColumnsFromExcelFile, normalize_isbn, sortUnique

NUKE = True
dir = os.path.dirname(__file__)
if not dir:
    dir = "."

parser = argparse.ArgumentParser()
parser.add_argument("-db", "--databasename", required=True, help="Database name")
args = parser.parse_args()

db_path = dir + "\\tmp\\" + args.databasename + ".sqlite"

# Check if exists
if NUKE and os.path.exists(db_path):
    print("Erasing all content in %s" % args.databasename)
    os.remove(db_path)

# Make and Reset database
try:
    conn = sqlite3.connect(db_path)
except sqlite3.OperationalError:
    print("Unable to open database: %s" % db_path)
    exit(1)
cursor = conn.cursor()
if NUKE:
    init_sql = open(dir + "\\db_tables.sql", "r").read()
    cursor.executescript(init_sql)
    cursor.execute("INSERT INTO categories(name) VALUES (?)", ("Bookstore List",))
    BOOKSTORE_CAT = cursor.lastrowid
    cursor.execute("INSERT INTO categories(name) VALUES (?)", ("Catalog List",))
    CATALOG_CAT = cursor.lastrowid
    cursor.execute("INSERT INTO categories(name) VALUES (?)", ("Publisher List",))
    PUBLISHER_CAT = cursor.lastrowid
    cursor.execute("INSERT INTO categories(name) VALUES (?)", ("Class List",))
    CLASS_CAT = cursor.lastrowid
    conn.commit()
else:
    cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Bookstore List",))
    BOOKSTORE_CAT = cursor.fetchone()[0]
    cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Catalog List",))
    CATALOG_CAT = cursor.fetchone()[0]
    cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Publisher List",))
    PUBLISHER_CAT = cursor.fetchone()[0]
    cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Class List",))
    CLASS_CAT = cursor.fetchone()[0]


def normalize_course_code(code):
    return code.replace(" - ", " ").strip()


def parsePublisherCSV(filepath):
    pass


def parsePublisherExcel(filepath):
    books = []
    print(filepath)
    rows = getColumnsFromExcelFile(
        ["Title", "Electronic ISBN", "Print ISBN", "Pub Year"],
        filepath
    )
    bar = ProgressBar(len(rows), label="  parsing ")
    for row in rows:
        title = None
        if "Title" in row and row["Title"]:
            title = row["Title"]
        pub_year = None
        if "Pub Year" in row and row["Pub Year"]:
            try:
                pub_year = int(row["Pub Year"])
            except ValueError:
                pass
        if "Electronic ISBN" in row and row["Electronic ISBN"]:
            books.append({
                "title": title,
                "pub_year": pub_year,
                "isbn": normalize_isbn(row["Electronic ISBN"]),
                "electronic": True
            })
        if "Print ISBN" in row and row["Print ISBN"]:
            books.append({
                "title": title,
                "pub_year": pub_year,
                "isbn": normalize_isbn(row["Print ISBN"]),
                "electronic": False
            })
        bar.update()
    bar.finish()
    return books


def addPublisherFiles():
    publisher_dir = dir + '\\Publishers Adjusted'
    publisher_files = [file.name for file in os.scandir(publisher_dir) if file.is_file()]
    for file in publisher_files:
        # Save file as list
        cursor.execute("SELECT 1 FROM lists WHERE name=?", (file,))
        if cursor.fetchone():
            continue
        cursor.execute(
            "INSERT INTO lists(name, updated, in_use, category_id) VALUES (?,?,?,?)",
            (file, datetime.datetime.now(), True, PUBLISHER_CAT)
        )
        FILE_ID = cursor.lastrowid

        books = []
        filepath = os.path.join(publisher_dir, file)
        if file[-3:] == "csv":
            print("TODO txt processing")
        elif file[-4:] == "json":
            books = json.load(filepath)
        else:  # Excel
            books = parsePublisherExcel(filepath)
        bar = ProgressBar(len(books), label="  saving (%d) " % len(books))
        for book in books:
            cursor.execute("SELECT isbn FROM books WHERE isbn=?", (book["isbn"],))
            ISBN = cursor.fetchone()
            if ISBN:
                cursor.execute("SELECT 1 FROM lists_books WHERE isbn=? AND list_id=?", (book["isbn"], FILE_ID))
                if cursor.fetchone():
                    continue
                ISBN = ISBN[0]
            else:
                cursor.execute(
                    "INSERT INTO books(isbn, title, year, electronic) VALUES (?,?,?,?)",
                    (book["isbn"], book["title"], book["pub_year"], book["electronic"])
                )
                ISBN = book["isbn"]
            cursor.execute(
                "INSERT INTO lists_books(isbn, list_id) VALUES (?,?)",
                (ISBN, FILE_ID)
            )
            bar.update()
        bar.finish()
        conn.commit()


def parseBookstoreList(filepath):
    print(filepath)

    wb = xlrd.open_workbook(filepath)
    sheet = wb.sheet_by_index(0)

    # Get the column header row
    for rowidx in range(0, 20):
        row = sheet.row(rowidx)
        find = False
        for colidx, cell in enumerate(row):
            if cell.value == "AUTHOR":
                startRow = rowidx
                dataStartRow = startRow + 3
                authorIdx = colidx
                find = True
                break
        if find:
            break

    # Get the column indexes
    for rowidx in range(startRow, startRow + 3):
        row = sheet.row(rowidx)
        for colidx, cell in enumerate(row):
            if type(cell.value) == str:
                if cell.value == "TITLE":
                    titleIdx = colidx
                elif cell.value == "EDITION":
                    editionIdx = colidx
                elif cell.value == "ED":
                    edIdx = colidx
                elif cell.value == "CY":
                    cyIdx = colidx
                elif cell.value == "ISBN":
                    isbnIdx = colidx
                elif cell.value == "PUB":
                    pubIdx = colidx
                elif cell.value == "NOTE":
                    noteIdx = colidx
                elif cell.value == "NEW":
                    if "RETAIL" in sheet.cell(rowidx - 1, colidx).value:
                        retailNewIdx = colidx
                    else:
                        rentalNewIdx = colidx
                elif cell.value == "USED":
                    if "RETAIL" in sheet.cell(rowidx - 1, colidx).value or "RETAIL" in sheet.cell(rowidx - 1,
                                                                                                  colidx - 1).value:
                        retailUsedIdx = colidx
                    else:
                        rentalUsedIdx = colidx
                elif cell.value == "COURSE":
                    courseIdx = colidx
                elif cell.value == "INSTRUCTOR":
                    instructorIdx = colidx
                elif "CLASS START" in cell.value:
                    clsStartIdx = colidx
                elif cell.value == "USE":
                    useIdx = colidx

    books = []
    bar = ProgressBar(sheet.nrows - startRow, label="  parsing ")

    books_list = []
    book = OrderedDict()
    names = ['course', 'instructor', 'note', 'class start date', 'use']
    prev_isbn = sheet.cell_value(dataStartRow, isbnIdx)
    for r in range(dataStartRow, sheet.nrows + 1):
        if r == sheet.nrows:
            ordered_dictionary = [OrderedDict(zip(names, subl)) for subl in list_of_lists]
            book['courses_ins'] = ordered_dictionary
            books_list.append(book)
            break
        new_isbn = sheet.cell_value(r, isbnIdx)
        row_values = sheet.row_values(r)
        if new_isbn != "":
            if new_isbn != prev_isbn:
                ordered_dictionary = [OrderedDict(zip(names, subl)) for subl in list_of_lists]
                book['courses_ins'] = ordered_dictionary
                books_list.append(book)
                book = OrderedDict()
                prev_isbn = new_isbn
            list_of_lists = []
            book['author'] = row_values[authorIdx]
            book['title'] = row_values[titleIdx]
            book['ed'] = row_values[edIdx]
            book['cy'] = row_values[cyIdx]
            book['isbn'] = row_values[isbnIdx]
            book['pub'] = row_values[pubIdx]
            book['retail new price'] = row_values[retailNewIdx]
            book['retail used price'] = row_values[retailUsedIdx]
            book['rental new price'] = row_values[rentalNewIdx]
            book['rental used price'] = row_values[rentalUsedIdx]
        else:
            ls = [row_values[courseIdx], row_values[instructorIdx], row_values[noteIdx], row_values[clsStartIdx],
                  row_values[useIdx]]
            list_of_lists.append(ls)
        bar.update()
    bar.finish()
    return books_list


def addBookstoreList():
    bookstore_dir = dir + '\\BookList Files'
    bookstore_files = [file.name for file in os.scandir(bookstore_dir) if file.is_file()]
    for file in bookstore_files:
        # Save file as list
        cursor.execute("SELECT 1 FROM lists WHERE name=?", (file,))
        if cursor.fetchone():
            continue
        cursor.execute(
            "INSERT INTO lists(name, updated, in_use, category_id) VALUES (?,?,?,?)",
            (file, datetime.datetime.now(), True, BOOKSTORE_CAT)
        )
        FILE_ID = cursor.lastrowid

        books = []
        print(file)
        filepath = os.path.join(bookstore_dir, file)
        if file[-3:] == "csv":
            print("TODO txt processing")
        elif file[-4:] == "json":
            books = json.load(filepath)
        else:  # Excel
            books = parseBookstoreList(filepath)

        bar = ProgressBar(len(books), label="  saving (%d) " % len(books))
        for book in books:
            cursor.execute("SELECT isbn FROM books WHERE isbn=?", (book["isbn"],))
            if cursor.fetchone():
                cursor.execute("SELECT 1 FROM lists_books WHERE isbn=? AND list_id=?", (book["isbn"], FILE_ID))
                if cursor.fetchone():
                    continue
            else:
                cursor.execute(
                    "INSERT INTO books(isbn, title, year) VALUES (?,?,?)",
                    (book["isbn"], book["title"], book["cy"])
                )
            cursor.execute(
                "INSERT INTO lists_books(isbn, list_id) VALUES (?,?)",
                (book["isbn"], FILE_ID)
            )
            if (len(book["courses_ins"]) > 0):
                for course in book["courses_ins"]:
                    # Courses
                    code = normalize_course_code(course["course"])
                    cursor.execute("SELECT 1 FROM courses WHERE course_code=?",
                                   (code,))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO courses(course_code, professor_name) VALUES (?,?)",
                                       (code, course["instructor"]))
                    # Course books
                    cursor.execute("SELECT 1 FROM courses_books WHERE isbn=? and course_code=?",
                                   (book["isbn"], code,))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO courses_books(isbn, course_code) VALUES (?,?)",
                                       (book["isbn"], code))
            bar.update()
        bar.finish()
        conn.commit()


def parseCatalogCSVList(filepath):
    print(filepath)
    books_list = []
    with open(filepath, 'r', encoding="utf-8") as f:
        reader = csv.reader(f)
        your_list = list(reader)
    bar = ProgressBar(len(your_list), label="  parsing ")
    for ls in your_list:
        book = OrderedDict()
        book["isbn"] = normalize_isbn(ls[0])
        book["title"] = ls[1][:-2]
        book["pub_yr"] = ls[2]
        book["electronic"] = "Online" in ls[3] if len(ls) > 3 else None
        book["callnumber"] = ls[4] if len(ls) > 4 else None
        books_list.append(book)
        bar.update()
    bar.finish()
    return books_list


# Specialized for JSTOR
def addCatalogJSTORExcel(filepath):
    books = []
    print(filepath)
    rows = getColumnsFromExcelFile(
        ["Book title", "eISBN", "ISBN", "Copyright year"],
        filepath
    )
    bar = ProgressBar(len(rows), label="  parsing ")
    for row in rows:
        title = None
        if "Book title" in row and row["Book title"]:
            title = row["Book title"]
        pub_year = None
        if "Copyright year" in row and row["Copyright year"]:
            try:
                pub_year = int(row["Copyright year"])
            except ValueError:
                pass
        if "eISBN" in row and row["eISBN"]:
            books.append({
                "title": title,
                "pub_yr": pub_year,
                "isbn": normalize_isbn(row["eISBN"]),
                "electronic": True,
                "callnumber": None
            })
        if "ISBN" in row and row["ISBN"]:
            books.append({
                "title": title,
                "pub_yr": pub_year,
                "isbn": normalize_isbn(row["ISBN"]),
                "electronic": True, # All JSTOR are electronic
                "callnumber": None
            })
        bar.update()
    bar.finish()
    return books


def addCatalogList():
    catalog_dir = dir + '\\CatalogFiles'
    bookstore_files = [file.name for file in os.scandir(catalog_dir) if file.is_file()]
    print(bookstore_files)
    for file in bookstore_files:
        # Save file as list
        cursor.execute("SELECT 1 FROM lists WHERE name=?", (file,))
        if cursor.fetchone():
            continue
        cursor.execute(
            "INSERT INTO lists(name, updated, in_use, category_id) VALUES (?,?,?,?)",
            (file, datetime.datetime.now(), True, CATALOG_CAT)
        )
        FILE_ID = cursor.lastrowid

        books = []
        filepath = os.path.join(catalog_dir, file)
        if file[-3:] == "csv":
            books = parseCatalogCSVList(filepath)
        elif file[-4:] == "json":
            books = json.load(filepath)
        else:  # Excel
            books = addCatalogJSTORExcel(filepath)
        bar = ProgressBar(len(books), label="  saving (%d) " % len(books))
        for book in books:
            cursor.execute("SELECT isbn FROM books WHERE isbn=?", (book["isbn"],))
            ISBN = cursor.fetchone()
            if ISBN:
                cursor.execute("SELECT 1 FROM lists_books WHERE isbn=? AND list_id=?", (book["isbn"], FILE_ID))
                if cursor.fetchone():
                    continue
                ISBN = ISBN[0]
            else:
                cursor.execute(
                    "INSERT INTO books(isbn, title, year, electronic, callnumber) VALUES (?,?,?,?,?)",
                    (book["isbn"], book["title"], book["pub_yr"], book["electronic"], book["callnumber"])
                )
                ISBN = book["isbn"]
            cursor.execute(
                "INSERT INTO lists_books(isbn, list_id) VALUES (?,?)",
                (ISBN, FILE_ID)
            )
            bar.update()
        bar.finish()
        conn.commit()


def parseClassJsonList(filepath):
    with open(filepath, 'r') as f:
        cls_json = json.load(f)
    f.close()

    cls_list = []
    print(filepath)
    bar = ProgressBar(len(cls_json), label="  parsing ")
    for row in cls_json:
        cls = OrderedDict()
        cls['code'] = row['code']
        cls['prof_name'] = row['prof_name']
        cls['prof_email'] = row['prof_email']
        cls['num_stu'] = row['students']
        cls['books'] = []
        '''
        if (len(row['books']) > 0):
            ordered_dictionary = [r for r in row['books']]
            cls['books'] = ordered_dictionary
        '''
        cls_list.append(cls)
        bar.update()
    bar.finish()
    return cls_list


def addClassList():
    class_dir = dir + '\\ClassList'
    classlist_files = [file.name for file in os.scandir(class_dir) if file.is_file()]
    for file in classlist_files:
        if re.match('^\d+.*.json$', file):
            print(file)
            # Save file as list
            cursor.execute("SELECT 1 FROM lists WHERE name=?", (file,))
            if cursor.fetchone():
                continue
            cursor.execute(  # insert into lists
                "INSERT INTO lists(name, updated, category_id) VALUES (?,?,?)",
                (file, datetime.datetime.now(), CLASS_CAT)
            )
            FILE_ID = cursor.lastrowid
            classes = []
            filepath = os.path.join(class_dir, file)
            if file[-3:] == "csv":
                print("TODO txt processing")
            elif file[-4:] == "json":
                classes = parseClassJsonList(filepath)
            else:  # Excel
                print("TODO excel processing")
            bar = ProgressBar(len(classes), label="  saving (%d) " % len(classes))
            for cls in classes:
                code = normalize_course_code(cls["code"])
                cursor.execute("SELECT course_code FROM courses WHERE course_code=?",
                               (code,))  # chk if course_code is in courses
                if cursor.fetchone():  # course_code = ...
                    cursor.execute(
                        "UPDATE courses SET num_students=?, professor_name=?, professor_email=? WHERE course_code=?",
                        (cls["num_stu"], cls["prof_name"], cls["prof_email"], code))
                else:
                    # insert into courses
                    cursor.execute(
                        "INSERT INTO courses(num_students, professor_name, professor_email, course_code) VALUES (?,?,?,?)",
                        (cls["num_stu"], cls["prof_name"], cls["prof_email"], code))

                bar.update()
            bar.finish()
            conn.commit()


def getCategoryLists(CAT_ID, CAT_NAME):
    # Get category files
    cursor.execute("select category_id,list_id,name from lists where category_id=?", (CAT_ID,))
    category_list = cursor.fetchall()

    category_df = pd.DataFrame(([cat[0], cat[1], cat[2]] for cat in category_list),
                               columns=['category_id', 'list_id', 'list_name'])
    category_df[['in_use', 'category']] = pd.DataFrame([['No', CAT_NAME]], index=category_df.index)
    category_df = category_df[['in_use', 'category_id', 'category', 'list_id', 'list_name']]

    conn.commit()
    return category_df


def createConfigFile():
    catalog_df = getCategoryLists(CATALOG_CAT, 'CATALOG_LISTS')
    bookstore_df = getCategoryLists(BOOKSTORE_CAT, 'BOOKSTORE_LISTS')
    classlist_df = getCategoryLists(CLASS_CAT, 'CLASS_LISTS')
    publisher_df = getCategoryLists(PUBLISHER_CAT, 'PUBLISHER_LISTS')

    frames = [catalog_df, bookstore_df, classlist_df, publisher_df]
    category_df = pd.concat(frames)

    category_df.to_csv(dir + "\\configuration.csv", index=False, encoding='utf-8')


addCatalogList()
addBookstoreList()
addClassList()
# addPublisherFiles()
createConfigFile()
