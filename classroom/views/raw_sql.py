def get_taken_quiz(student_id, taken_quiz_id):
    sql = (f'SELECT * FROM classroom_takenquiz tq '
           f'JOIN classroom_quiz q ON tq.quiz_id = q.id '
           f'JOIN classroom_question cq ON q.id = cq.quiz_id '
           f'JOIN classroom_answer ca on cq.id = ca.question_id '
           f'JOIN classroom_studentanswer cs on ca.id = cs.answer_id '
           f'WHERE tq.id = {taken_quiz_id} AND cs.student_id = {student_id} ')

    return sql


def get_popular_courses():
    sql = ('SELECT * FROM star_ratings_rating sr '
           'JOIN classroom_course c ON sr.object_id = c.id '
           'WHERE c.status = \'approved\' '
           'ORDER BY average DESC LIMIT 6')

    return sql