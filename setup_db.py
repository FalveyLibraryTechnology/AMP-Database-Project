import csv
import datetime
import json
import os
import re
import sqlite3
import xlrd
import pandas as pd
import argparse
from collections import OrderedDict

from src.ProgressBar import ProgressBar
from src.utils import getColumnsFromExcelFile, normalize_isbn, sortUnique

NUKE = False
dir = os.path.dirname(__file__)

parser = argparse.ArgumentParser()
parser.add_argument("-db", "--databasename", required=True, help="Database name")
args = parser.parse_args()

db_path = dir + "\\tmp\\" + args.databasename + ".sqlite"

# Check if exists
if NUKE and os.path.exists(db_path):
    os.remove(db_path)

# Make and Reset database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
if NUKE:
    init_sql = open(dir + "\\db_tables.sql", "r").read()
    cursor.executescript(init_sql)
    cursor.execute("INSERT INTO categories(name) VALUES (?);", ("Bookstore List",))
    BOOKSTORE_CAT = cursor.lastrowid
    cursor.execute("INSERT INTO categories(name) VALUES (?);", ("Catalog List",))
    CATALOG_CAT = cursor.lastrowid
    cursor.execute("INSERT INTO categories(name) VALUES (?);", ("Publisher List",))
    PUBLISHER_CAT = cursor.lastrowid
    conn.commit()
else:
    cursor.execute("SELECT category_id FROM categories WHERE name=?;", ("Bookstore List",))
    BOOKSTORE_CAT = cursor.fetchone()[0]
    cursor.execute("SELECT category_id FROM categories WHERE name=?;", ("Catalog List",))
    CATALOG_CAT = cursor.fetchone()[0]
    cursor.execute("SELECT category_id FROM categories WHERE name=?;", ("Publisher List",))
    PUBLISHER_CAT = cursor.fetchone()[0]


def parsePublisherCSV(filepath):
    pass


def parsePublisherExcel(filepath):
    books = []
    print (filepath)
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
            "INSERT INTO lists(name, updated, in_use, category_id) VALUES (?,?,?,?);",
            (file, datetime.datetime.now(), True, PUBLISHER_CAT)
        )
        FILE_ID = cursor.lastrowid

        books = []
        filepath = os.path.join(publisher_dir, file)
        if file[-3:] == "csv":
            print ("TODO txt processing")
        elif file[-4:] == "json":
            books = json.load(filepath)
        else: # Excel
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
                    "INSERT INTO books(isbn, title, year, electronic) VALUES (?,?,?,?);",
                    (book["isbn"], book["title"], book["pub_year"], book["electronic"])
                )
                ISBN = book["isbn"]
            cursor.execute(
                "INSERT INTO lists_books(isbn, list_id) VALUES (?,?);",
                (ISBN, FILE_ID)
            )
            bar.update()
        bar.finish()
        conn.commit()


		
def parseBookstoreList(filepath):
	books = []
	print(filepath)
	
	wb = xlrd.open_workbook(filepath)  
	sheet = wb.sheet_by_index(0)
	bar = ProgressBar(sheet.nrows-7, label="  parsing ")

	books_list = []
	book = OrderedDict()
	names = ['course', 'instructor', 'note', 'class start date', 'use']
	prev_isbn = sheet.cell_value(8, 6)
	for r in range(8, sheet.nrows + 1):
		if r == sheet.nrows:
			ordered_dictionary = [OrderedDict(zip(names, subl)) for subl in list_of_lists]
			book['courses_ins'] = ordered_dictionary
			books_list.append(book)
			break
		new_isbn = sheet.cell_value(r, 6)
		row_values = sheet.row_values(r)
		if new_isbn != "":
			if new_isbn != prev_isbn:
				ordered_dictionary = [OrderedDict(zip(names, subl)) for subl in list_of_lists]
				book['courses_ins'] = ordered_dictionary
				books_list.append(book)
				book = OrderedDict()
				prev_isbn = new_isbn
			list_of_lists = []
			book['author'] = row_values[0]
			book['title'] = row_values[1]
			book['ed'] = row_values[4]
			book['cy'] = row_values[5]
			book['isbn'] = row_values[6]
			book['pub'] = row_values[9]
			book['retail new price'] = row_values[10]
			book['retail used price'] = row_values[11]
			book['rental new price'] = row_values[12]
			book['rental used price'] = row_values[13]
		else:
			ls = [row_values[0],row_values[2],row_values[3],row_values[7],row_values[8]]
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
            "INSERT INTO lists(name, updated, in_use, category_id) VALUES (?,?,?,?);",
            (file, datetime.datetime.now(), True, BOOKSTORE_CAT)
        )
        FILE_ID = cursor.lastrowid

        books = []
        print(file)
        filepath = os.path.join(bookstore_dir, file)
        if file[-3:] == "csv":
            print ("TODO txt processing")
        elif file[-4:] == "json":
            books = json.load(filepath)
        else: # Excel
            books = parseBookstoreList(filepath)
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
                    "INSERT INTO books(isbn, title, year) VALUES (?,?,?);",
                    (book["isbn"], book["title"], book["cy"])
                )
                ISBN = book["isbn"]
            cursor.execute(
                "INSERT INTO lists_books(isbn, list_id) VALUES (?,?);",
                (ISBN, FILE_ID)
            )
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
        book['isbn'] = normalize_isbn(ls[0])
        book['title'] = ls[1][:-2]
        book['pub_yr'] = ls[2]
        books_list.append(book)
        bar.update()
    bar.finish()
    return books_list


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
            "INSERT INTO lists(name, updated, in_use, category_id) VALUES (?,?,?,?);",
            (file, datetime.datetime.now(), True, CATALOG_CAT)
        )
        FILE_ID = cursor.lastrowid

        books = []
        print(file)
        filepath = os.path.join(catalog_dir, file)
        if file[-3:] == "csv":
            books = parseCatalogCSVList(filepath)      
        elif file[-4:] == "json":
            books = json.load(filepath)
        else: # Excel
            print ("TODO excel processing")
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
                    "INSERT INTO books(isbn, title, year) VALUES (?,?,?);",
                    (book["isbn"], book["title"], book["pub_yr"])
                )
                ISBN = book["isbn"]
            cursor.execute(
                "INSERT INTO lists_books(isbn, list_id) VALUES (?,?);",
                (ISBN, FILE_ID)
            )
            bar.update()
        bar.finish()
        conn.commit()

		
def getCategoryLists(CAT_ID, CAT_NAME):
	#Get category files
	cursor.execute("select category_id,list_id,name from lists where category_id=?;", (CAT_ID,))
	category_list = cursor.fetchall()
	
	category_df = pd.DataFrame(([cat[0],cat[1],cat[2]] for cat in category_list), columns=['category_id', 'list_id', 'list_name'])
	category_df[['in_use','category']] = pd.DataFrame([['No',CAT_NAME]], index=category_df.index)
	category_df = category_df[['in_use', 'category_id', 'category', 'list_id', 'list_name']]

	conn.commit()
	return category_df


def createConfigFile():
	catalog_df = getCategoryLists(CATALOG_CAT, 'CATALOG_LISTS')
	bookstore_df = getCategoryLists(BOOKSTORE_CAT, 'BOOKSTORE_LISTS')
	publisher_df = getCategoryLists(PUBLISHER_CAT, 'PUBLISHER_LISTS')
	
	frames = [catalog_df, bookstore_df, publisher_df]
	category_df = pd.concat(frames)
	
	category_df.to_csv(dir + "\\configuration.csv", index=False, encoding='utf-8')


createConfigFile()	
addPublisherFiles()
addBookstoreList()
addCatalogList()

