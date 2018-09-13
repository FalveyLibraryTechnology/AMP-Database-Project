DROP TABLE IF EXISTS tmp_bookstore;
DROP TABLE IF EXISTS tmp_catalog;

CREATE TEMPORARY TABLE tmp_bookstore AS 
	SELECT isbn FROM lists_books WHERE list_id IN (SELECT list_id FROM lists WHERE category_id = 1 AND in_use = 1);
		
CREATE TEMPORARY TABLE tmp_catalog AS
	SELECT isbn FROM lists_books WHERE list_id IN (SELECT list_id FROM lists WHERE category_id = 2 AND in_use = 1);

SELECT isbn, callnumber, title, year, 1 as electronic FROM books
	WHERE (isbn IN (SELECT * FROM tmp_bookstore INTERSECT SELECT * FROM tmp_catalog) AND electronic = 1)
		OR isbn IN (SELECT isbn_src FROM expanded_isbns)
	GROUP BY isbn;