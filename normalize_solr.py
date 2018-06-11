# SOLR SOURCE: http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=isbn,title,publishDate&indent=on&q=isbn:*&wt=csv&rows=99999

import csv
import os
import sys
from src.utils import normalize_isbn

items = []

dir = os.path.dirname(__file__)

with open(dir + "\\isbns-solr-may-2018.csv", "r", encoding="utf-8") as csvfile:
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
with open(catalog_dir + "\\normalized-from-solr-may-2018.csv", "w", newline='', encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerows(items)
