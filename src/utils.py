import io
import json
import os
import re
import sys
import string
import requests
from checksumdir import dirhash # folder md5
from xlrd import open_workbook  # Excel files

from .ProgressBar import ProgressBar


def comma(num):
    return '{:,}'.format(num)


def sortUnique(arr):
    return sorted(list(set(filter(None, arr))))


def isbn_checksum(op):
    digits = [int(c) for c in op]
    sum = 0
    for i in range(0, len(digits)):
        if i % 2 == 0:
            sum += digits[i]
        else:
            sum += 3 * digits[i]
    #temp = str(10 - (sum % 10)) if ((10 - (sum % 10)) < 10) else '0'
    mod = sum % 10
    return str(10 - mod) if mod > 0 else '0'


def normalize_isbn(op):
    round = str(op).split(".")[0]
    trimmed = re.sub(r"[^0-9X]", "", round)
    if len(trimmed) == 10:
        trimmed = "978" + trimmed
    elif len(trimmed) != 13:
        raise ValueError("Invalid ISBN: %s" % op)
    minus_cs = trimmed[0:12]
    return minus_cs + isbn_checksum(minus_cs)


def getColumnsFromExcelFile(column_names, filepath):
    rows = []
    with open_workbook(filepath) as book:
        row_count = 0
        for s in range(book.nsheets):
            sheet = book.sheet_by_index(s)
            row_count += sheet.nrows
        bar = ProgressBar(row_count, label="  getting columns ")
        for s in range(book.nsheets):
            sheet = book.sheet_by_index(s)
            books_columns = {}
            body = False
            for row in range(0, sheet.nrows):
                rvalues = sheet.row_values(row)
                if not body:
                    for col in column_names:
                        if col in rvalues:
                            books_columns[col] = rvalues.index(col)
                            body = True
                else:
                    row = {}
                    for col in books_columns:
                        row[col] = rvalues[books_columns[col]]
                    rows.append(row)
                bar.progress()
        bar.finish()
    return rows