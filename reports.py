import csv
import datetime
import json
import os
import re
import sqlite3
import xlrd
import pandas as pd
from collections import OrderedDict

from src.ProgressBar import ProgressBar
from src.utils import getColumnsFromExcelFile, normalize_isbn, sortUnique

dir = os.path.dirname(__file__)
reports_dir = dir + '\\Reports'

# Make and Reset database
conn = sqlite3.connect(dir + "\\tmp\\sample_db.sqlite")
cursor = conn.cursor()

#Fetch category Ids
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Bookstore List",))
BOOKSTORE_CAT = cursor.fetchone()[0]
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Catalog List",))
CATALOG_CAT = cursor.fetchone()[0]
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Publisher List",))
PUBLISHER_CAT = cursor.fetchone()[0]
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Class List",))
CLASS_CAT = cursor.fetchone()[0]
    
def booksInBookstoreListAlsoInCatalog(file):
	cursor.execute("select * from books where isbn in " + 
					"(select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)" + 
					" intersect " + 
					"select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1))", 
                    (BOOKSTORE_CAT, CATALOG_CAT,))
	q1 = cursor.fetchall()
	
	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q1, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')


def booksInBookstoreListNotInCatalog(file):
	cursor.execute("select * from books where isbn in " + 
					"(select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)" + 
					" except " + 
					"select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1))", 
                    (BOOKSTORE_CAT, CATALOG_CAT,))
	q2 = cursor.fetchall()

	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q2, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')
	
def booksInBothCatalogAndIn_UsePublisher(file):
	cursor.execute("select * from books where isbn in " + 
					"(select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)" + 
					" intersect " + 
					"select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1))", 
                    (CATALOG_CAT, PUBLISHER_CAT,))
	q3 = cursor.fetchall()

	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q3, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')
	
def booksInBookstoreListAlsoIn_UsePublisher(file):
	cursor.execute("select * from books where isbn in " + 
					"(select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)" + 
					" intersect " + 
					"select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1))", 
                    (BOOKSTORE_CAT, PUBLISHER_CAT,))
	q4 = cursor.fetchall()

	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q4, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')
    
def booksInBookstoreListNotInCatalogAndInPublisherList(file):
	cursor.execute("select * from books where isbn in " + 
					"(select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)" + 
					" except " + 
					"select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1))" + 
                    " intersect " + 
                    "select * from books where isbn in " + 
                    "(select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1))", 
                    (BOOKSTORE_CAT, CATALOG_CAT, PUBLISHER_CAT,))
	q2 = cursor.fetchall()

	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q2, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')

booksInBookstoreListAlsoInCatalog('r1_books_in_BookstoreList_Also_in_Catalog.csv')
booksInBookstoreListNotInCatalog('r2_books_in_BookstoreList_Not_in_Catalog.csv')
booksInBothCatalogAndIn_UsePublisher('r3_books_in_Catalog_And_In_Use_Publisher.csv')
booksInBookstoreListAlsoIn_UsePublisher('r4_books_in_BookstoreList_Also_In_Use_Publisher.csv')
booksInBookstoreListNotInCatalogAndInPublisherList('r5_books_in_BookstoreList_Not_in_Catalog_And_In_Publisher.csv')