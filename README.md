# AMP-Database-Project
### Overview
To allow for more flexibility in reporting, the AMP python code is getting re-written to leverage a relational database. SQLite is used as database.

The database will contain information on the three sources of information needed to generate the reports: 

 1. Bookstore Lists– All the books required for classes in the upcoming semester. Sourced from an Excel sheet sent to us 3 weeks before the semester starts. 

 2. Catalog Lists– All the books available in the Falvey catalog. Sourced from Access. 

 3. Publisher Lists – Multiple lists of DRM-free ebooks available for purchase. This should include ebooks that we currently own and ebooks we don’t own. These lists are then compared by ISBN numbers to create the final reports. 

normalize_solr.py script converts the isbns to ISBN-13 format and saves them along with book title, publihed year to a csv file.

### Setup Database
To initially setup the database, make the constant NUKE true in the script and run it.

setup_db.py loads the Bookstore Lists, Catalog Lists, Publisher Lists into database. It also creates a 'configuration.csv' file with a list of names of all the bookstore, catalog and publisher lists along with an in_use field. Format of configuration.csv is:

| in_use | category_id | category | list_id | list_name
| --- | --- | --- | --- | --- |
 No | 2 | CATALOG_LISTS | 25 | catalog_l1.csv

User can configure which lists to use for reports by setting 'in_use' flag to Yes in configuration.csv and run update_db.py script.

To run setup_db.py provide database name as a command line argument.
eg: python.exe 'path of setup_db.py' -db database name

### Update Database
update_db.py reads configuration.csv file and for those lists with in_use field as 'yes', sets the corresponding in_use field of the list in lists table to 1. When reports are generated only those lists with in_use field set will be considered.

To run update_db.py provide database name as a command line argument.
eg: python.exe 'path of update_db.py' -db database name

### Generate Reports
reports.py will generate following reports in csv format and will be stored in Reports folder.

 1. A list of books in the latest Bookstore List that are also in the Catalog.
 2. A list of books in the latest Bookstore List that are not in the Catalog. 
 3. A list of books in both the Catalog and in_use Publisher lists. 
 4. A list of books in the latest Bookstore List that is also on an in_use Publisher list. 
 5. Items from the second list that are also on an in_use Publisher List 

### To Do
Class enrollment information i.e., course, Professor, class strength, books used etc. should be stored in database. Following reports relating to class information should be designed:

 1. Matching the books from the existing reports with the class and teacher they'll be affecting.
 2. List if books not in catalog that can be purchased from a publisher
