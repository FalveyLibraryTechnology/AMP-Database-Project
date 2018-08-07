import argparse
import json
import os
import progressbar
import requests
import sqlite3
import time
from lxml import html

# Time to crawl
polite_delay = 3


def getHTML(url):
    # print (url)
    response = requests.get(url.replace("&amp;", "&"))
    return html.fromstring(response.content)


parser = argparse.ArgumentParser()
parser.add_argument("-db", "--databasename", required=True, help="Database name")
parser.add_argument("-in", "--inputjson", required=True, help="Input json file (2018_1_fall)")
args = parser.parse_args()

dir = os.path.dirname(__file__)
if not dir:
    dir = "."

if not os.path.exists("%s\\%s" % (dir, args.inputjson)):
    print("Couldn't open input json file: %s\\%s" % (dir, args.inputjson))
    exit(1)
classes = json.load(open("%s\\%s" % (dir, args.inputjson), "r"))

db_path = dir + "\\..\\tmp\\" + args.databasename + ".sqlite"

# Make and Reset database
if not os.path.exists(db_path):
    print("Unable to open database: %s" % db_path)
    exit(1)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("DELETE FROM courses_books")

bar = progressbar.ProgressBar(max_value=len(classes))
for index in range(0, len(classes)):
    tree = getHTML(classes[index]["booklist"])
    isbns = [x.text_content()[6:] for x in
             tree.xpath("//span[contains(@id,'materialISBN')]")]  # document.querySelectorAll("#materialISBN")
    prices = [x.text for x in tree.xpath(
        "//div[@class='material-group-table']//tr[2]/td[8]")]  # .print_background:nth-child(2) td.right_border
    types = [x.text.strip() for x in tree.xpath(
        "//div[@class='material-group-table']//tr[2]/td[2]")]  # .print_background:nth-child(2) td.right_border

    for i in range(len(isbns)):
        price = float(prices[i][1:])
        cursor.execute(
            "INSERT INTO courses_books (course_code, isbn, price, type) VALUES (?,?,?,?)",
            (classes[index]["code"], isbns[i], price, types[i])
        )
    time.sleep(polite_delay)
    bar.update(index)
bar.finish()

conn.commit()
conn.close()
