from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)


class Subject(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#007bff')

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = f'<span class="badge badge-primary" style="background-color: {color}">{name}</span>'
        return mark_safe(html)


class Course(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    description = models.TextField()
    image = models.ImageField(upload_to='courses')
    status = models.CharField(max_length=10, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        for field_name in ['title', 'description']:
            val = getattr(self, field_name, False)
            if val:
                # Set the first letter of the strings to Capital letter
                setattr(self, field_name, val.title())
        # Set the course code to ALL CAPS
        setattr(self, 'code', getattr(self, 'code', False).upper())
        super(Course, self).save(*args, **kwargs)


class Lesson(models.Model):
    title = models.CharField(max_length=50)
    number = models.IntegerField()
    description = models.TextField()
    content = models.TextField(default='')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        for field_name in ['title', 'description', 'content']:
            val = getattr(self, field_name, False)
            if val:
                # Set the first letter of the string to Capital letter
                setattr(self, field_name, val.title())
        super(Lesson, self).save(*args, **kwargs)


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        for field_name in ['title']:
            val = getattr(self, field_name, False)
            if val:
                # Set the first letter of the string to Capital letter
                setattr(self, field_name, val.title())
        super(Quiz, self).save(*args, **kwargs)



class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Question', max_length=255)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('Answer', max_length=255)
    is_correct = models.BooleanField('Correct answer', default=False)

    def __str__(self):
        return self.text


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    image = models.ImageField(default='profile_pics/default-user.png', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} - teacher'


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    image = models.ImageField(default='profile_pics/default-user.png', upload_to='profile_pics')
    courses = models.ManyToManyField(Course, through='TakenCourse')
    interests = models.ManyToManyField(Subject, related_name='interested_students')

    def get_unanswered_questions(self, quiz):
        answered_questions = self.quiz_answers \
            .filter(answer__question__quiz=quiz) \
            .values_list('answer__question__pk', flat=True)
        questions = quiz.questions.exclude(pk__in=answered_questions).order_by('text')
        return questions

    def __str__(self):
        return f'{self.user.username} - student'


class TakenCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='taken_courses')
    status = models.CharField(max_length=12, default='Pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.user.username}: {self.course.title}'


class TakenQuiz(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+')
