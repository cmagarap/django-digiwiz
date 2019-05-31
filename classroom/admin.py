from django.contrib import admin
from .models import *

admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(User)
admin.site.register(Subject)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Student)
admin.site.register(TakenQuiz)
admin.site.register(TakenCourse)
admin.site.register(StudentAnswer)
