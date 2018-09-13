SELECT books.isbn, books.title, books.year, books.electronic, 
	SUM(courses.num_students) as enrollment, GROUP_CONCAT(courses.course_code) FROM books
	INNER JOIN courses_books ON courses_books.isbn = books.isbn
	INNER JOIN courses ON courses.course_code = courses_books.course_code
	WHERE books.isbn IN (
		SELECT lists_books.isbn FROM lists_books 
			INNER JOIN lists ON lists.list_id = lists_books.list_id
			WHERE lists.category_id = 1 AND lists.in_use = 1
	)
	GROUP BY books.isbn
	ORDER BY enrollment DESC