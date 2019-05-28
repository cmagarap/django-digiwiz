from django.urls import include, path

from .views import classroom, students, teachers

urlpatterns = [
    path('', classroom.home, name='home'),

    path('student/', include(([
        path('', students.CourseListView.as_view(), name='mycourses_list'),
        path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
        path('taken/', students.TakenQuizListView.as_view(), name='taken_quiz_list'),
        path('quiz/<int:pk>/', students.take_quiz, name='take_quiz'),
        path('enroll/<int:pk>/', students.enroll, name='enroll')
    ], 'classroom'), namespace='students')),

    path('teacher/', include(([
        path('', teachers.CourseListView.as_view(), name='course_change_list'),
        path('course/add/', teachers.CourseCreateView.as_view(), name='course_add'),
        path('course/<int:pk>/', teachers.CourseUpdateView.as_view(), name='course_change'),
        path('course/<int:pk>/delete/', teachers.CourseDeleteView.as_view(), name='course_delete'),
        path('quiz/<int:pk>/results/', teachers.QuizResultsView.as_view(), name='quiz_results'),
        path('quiz/<int:pk>/question/add/', teachers.question_add, name='question_add'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/', teachers.question_change, name='question_change'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/delete/', teachers.QuestionDeleteView.as_view(), name='question_delete'),
    ], 'classroom'), namespace='teachers')),
]
