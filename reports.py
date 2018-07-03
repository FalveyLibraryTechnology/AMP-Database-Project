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

dir = os.path.dirname(__file__)
reports_dir = dir + '\\Reports'

parser = argparse.ArgumentParser()
parser.add_argument("-db", "--databasename", required=True, help="Database name")
args = parser.parse_args()

db_path = dir + "\\tmp\\" + args.databasename + ".sqlite"
config_path = dir + "\\configuration.csv"

# Check if db file exists
if os.path.exists(db_path):
	# Make and Reset database
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
else:
	print("No such database file exists. Please run setup_db.py to create database \'%s\' first" % (args.databasename))

# Make and Reset database
#conn = sqlite3.connect(dir + "\\tmp\\sample_db.sqlite")
#cursor = conn.cursor()

#Fetch category Ids
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Bookstore List",))
BOOKSTORE_CAT = cursor.fetchone()[0]
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Catalog List",))
CATALOG_CAT = cursor.fetchone()[0]
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Publisher List",))
PUBLISHER_CAT = cursor.fetchone()[0]
cursor.execute("SELECT category_id FROM categories WHERE name=?", ("Class List",))
CLASS_CAT = cursor.fetchone()[0]

#create temp tables to fetch isbns of in use lists
cursor.execute("CREATE TEMPORARY TABLE tmp_bookstore AS " + 
               "Select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)", (BOOKSTORE_CAT,))
               
cursor.execute("CREATE TEMPORARY TABLE tmp_catalog AS " + 
               "Select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)", (CATALOG_CAT,))

cursor.execute("CREATE TEMPORARY TABLE tmp_publisher AS " + 
               "Select isbn from lists_books where list_id in (select list_id from lists where category_id = ? and in_use = 1)", (PUBLISHER_CAT,))

def booksInBookstoreListAlsoInCatalog(file):
	cursor.execute("select * from books where isbn in " + 
					"(select * from tmp_bookstore" + 
					" intersect " + 
					"select * from tmp_catalog)")
	q1 = cursor.fetchall()
	
	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q1, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')


def booksInBookstoreListNotInCatalog(file):
	cursor.execute("select * from books where isbn in " + 
					"(select * from tmp_bookstore" + 
					" except " + 
					"select * from tmp_catalog)")
	q2 = cursor.fetchall()

	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q2, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')
	
def booksInBothCatalogAndIn_UsePublisher(file):
	cursor.execute("select * from books where isbn in " + 
					"(select * from tmp_catalog" + 
					" intersect " + 
					"select * from tmp_publisher)")
	q3 = cursor.fetchall()

	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q3, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')
	
def booksInBookstoreListAlsoIn_UsePublisher(file):
	cursor.execute("select * from books where isbn in " + 
					"(select * from tmp_bookstore" + 
					" intersect " + 
					"select * from tmp_publisher)")
	q4 = cursor.fetchall()

	if not os.path.exists(reports_dir):
			os.makedirs(reports_dir)

	df = pd.DataFrame(q4, columns=['isbn', 'title', 'year', 'electronic'])

	df.to_csv(reports_dir + "\\" + file, index=False, encoding='utf-8')
    
def booksInBookstoreListNotInCatalogAndInPublisherList(file):
	cursor.execute("select * from books where isbn in " + 
					"(select * from tmp_bookstore" + 
					" except " + 
					"select * from tmp_catalog)" + 
                    " intersect " + 
                    "select * from books where isbn in " + 
                    "(select * from tmp_publisher)")
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

cursor.execute("drop table tmp_bookstore")
cursor.execute("drop table tmp_catalog")
cursor.execute("drop table tmp_publisher")
conn.close()