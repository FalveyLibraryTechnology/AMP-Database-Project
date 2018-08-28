SELECT isbn || ": { isbn: " || isbn || ", "
	|| 
	, GROUP_CONCAT(course_code) as classes 
	FROM courses_books 
	INNER JOIN 
	GROUP BY isbn