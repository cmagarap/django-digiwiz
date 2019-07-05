from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.html import escape, mark_safe
from sorl.thumbnail import ImageField
from star_ratings.models import Rating


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        for field_name in ['first_name', 'last_name']:
            val = getattr(self, field_name, False)
            if val:
                setattr(self, field_name, val.title())

        super(User, self).save(*args, **kwargs)


class UserLog(models.Model):
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    user_type = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_logs')

    def __str__(self):
        return f'{self.user.username}: {self.action}'


class Subject(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=9, default='#007bff')

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = f'<span class="badge badge-primary" style="background-color: {color}">{name}</span>'
        return mark_safe(html)


class Course(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='courses',
                              help_text='Recommended image resolution: 740px x 480px')
    status = models.CharField(max_length=10, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    ratings = GenericRelation(Rating, related_query_name='courses')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Set every first letter to capital:
        setattr(self, 'title', getattr(self, 'title', False).title())
        # Set the course code to ALL CAPS
        setattr(self, 'code', getattr(self, 'code', False).upper())
        super(Course, self).save(*args, **kwargs)


class Lesson(models.Model):
    title = models.CharField(max_length=100)
    number = models.IntegerField()
    description = models.TextField(max_length=1000)
    content = RichTextUploadingField(external_plugin_resources=[(
        'youtube',
        '/static/classroom/vendor/ckeditor_plugins/youtube/youtube/',
        'plugin.js',
    )])
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        setattr(self, 'title', getattr(self, 'title', False).title())
        super(Lesson, self).save(*args, **kwargs)


class Quiz(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quizzes')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        setattr(self, 'title', getattr(self, 'title', False).title())
        super(Quiz, self).save(*args, **kwargs)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Question', max_length=500)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('', max_length=500)
    is_correct = models.BooleanField('Correct answer', default=False)

    def __str__(self):
        return self.text


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    image = ImageField(default='profile_pics/default-user.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} - teacher'


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    image = ImageField(default='profile_pics/default-user.jpg', upload_to='profile_pics')
    courses = models.ManyToManyField(Course, through='TakenCourse')
    quizzes = models.ManyToManyField(Quiz, through='TakenQuiz')
    interests = models.ManyToManyField(Subject, related_name='interested_students')

    def get_unanswered_questions(self, quiz):
        answered_questions = self.quiz_answers \
            .filter(answer__question__quiz=quiz) \
            .values_list('answer__question__pk', flat=True)
        questions = quiz.questions.exclude(pk__in=answered_questions).order_by('id')
        return questions

    def __str__(self):
        return f'{self.user.username} - student'


class TakenCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='taken_courses')
    status = models.CharField(max_length=12, default='pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.user.username}: {self.course.title}'


class TakenQuiz(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.user.username}: {self.quiz.title}'


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+')


class MyFile(models.Model):
    file = models.FileField(upload_to='class_resources/')
    created_at = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='my_files')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_files')

    def __str__(self):
        return f'{self.file}'
