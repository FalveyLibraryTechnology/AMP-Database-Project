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

dir = os.path.dirname(__file__)

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

	
def updateListInUse(LIST_ID, CATEGORY_ID, in_use):
    in_use = 1 if(in_use.lower() == "yes") else 0
    bar = ProgressBar(1, label="  updating ")
    cursor.execute("UPDATE lists SET in_use = ? WHERE list_id=? and category_id=?;", (in_use,LIST_ID,CATEGORY_ID))
    bar.update()
    bar.finish()
    conn.commit()


def parseConfigurationFile():	
	# Loading csv
	with open(config_path, 'r', encoding="utf-8") as csv_file:
		header_line = next(csv_file)
		reader = csv.reader(csv_file)
		for r in reader:
			in_use = r[0]
			category_id = r[1]
			list_id = r[3]
			#if(in_use.lower() == "yes"):
			updateListInUse(list_id, category_id, in_use)
		

# Check if configuration file exists and get row count
if os.path.exists(config_path):
	row_count = sum(1 for row in open(config_path))
	print("row_count is %d" %(row_count))
	parseConfigurationFile()
else:
	print("No configuration file exists. Please run setup_db.py to create configuration.csv")


