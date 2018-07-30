# SOLR SOURCE: http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=isbn,title,publishDate&indent=on&q=isbn:*&wt=csv&rows=999999

import urllib.request
import csv
import os
import sys
from src.utils import normalize_isbn

items = []

dir = os.path.dirname(__file__)

url = 'http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=isbn,title,publishDate&indent=on&q=isbn:*&wt=csv&rows=999999'
request = urllib.request.Request(url)
response = urllib.request.urlopen(request)
html = response.read()

isbnsFile = 'isbns-solr-june-2018.csv'
normalizedISBNSFile = 'normalized-from-solr-june-2018.csv'

with open(dir + '\\' + isbnsFile, 'wb') as f:
    f.write(html)

with open(dir + "\\" + isbnsFile, "r", encoding="utf-8") as csvfile:
    records = csv.reader(csvfile)
    for line in records:
        isbns = line[0].strip().split(",")
        for isbn in isbns:
            try:
                norm_isbn = normalize_isbn(isbn)
                items.append((norm_isbn, line[1], line[2]))
            except:
                pass

catalog_dir = dir + '\\CatalogFiles'
with open(catalog_dir + "\\" + normalizedISBNSFile, "w", newline='', encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerows(items)
