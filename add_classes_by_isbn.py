import argparse
from math import floor
import progressbar
import re
import sqlite3
from string import ascii_uppercase
import xlwings as xw

parser = argparse.ArgumentParser()
parser.add_argument("-db", "--databasename", required=True, help="Database name")
parser.add_argument("-in", "--excelfile", required=True, help="Excel file name")
parser.add_argument("-o", "--outfile", help="Output file name")
args = parser.parse_args()


def get_column_letter(number):
    letter = ascii_uppercase[number % 26]
    if number >= 26:
        letter = get_column_letter(floor(number / 26) - 1) + letter
    return letter


def excel_match_data_map(filepath, output, column_re, data):
    wb = xw.Book(filepath)
    wb.app.visible = False
    sheet = wb.sheets[0]
    body = False
    columns = []
    last_cell = sheet.range('A1').current_region.last_cell
    rownum = last_cell.row
    rowend = last_cell.column
    bar = progressbar.ProgressBar(max_value=rownum)
    for row in range(1, rownum + 1):
        rvalues = sheet.range("%d:%d" % (row, row)).value
        if not body:
            if row > 10:
                raise ValueError("no header found in %s" % filepath)
            col_index = 0
            for col in rvalues:
                if col is None:
                    continue
                if column_re.search(col):
                    columns.append(col_index)
                    body = True
                col_index += 1
        else:
            for col in columns:
                norm_col_value = str(rvalues[col]).split(".")[0] # Number issues in Excel
                if norm_col_value in data:
                    row_addition = data[norm_col_value]
                    if hasattr(row_addition, "__iter__"):
                        index = 0
                        for cell in row_addition:
                            sheet.range("%s%d" % (get_column_letter(rowend + index), row)).value = cell
                            index += 1
                    else:
                        sheet.range("%s%d" % (get_column_letter(rowend), row)).value = row_addition
        bar.update(row)
    bar.finish()
    wb.save(output)
    print("\tsaved to %s..." % output)
    wb.app.kill()


conn = sqlite3.connect("tmp/%s.sqlite" % args.databasename)
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

outfile = args.outfile if args.outfile is not None else re.sub(r"\.([^\.]+?)$", ".with-classes.\g<1>", args.excelfile)
excel_match_data_map(args.excelfile, outfile, re.compile("isbn", flags=re.I), isbn_map)
