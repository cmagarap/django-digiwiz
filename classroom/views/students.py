from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import CreateView, ListView, UpdateView
from ..decorators import student_required
from ..forms import StudentInterestsForm, StudentSignUpForm, TakeQuizForm
from ..models import Course, Quiz, Student, TakenCourse, TakenQuiz, User
from ..tokens import account_activation_token


User = get_user_model()


class BrowseCoursesView(ListView):
    model = Course
    ordering = ('title', )
    context_object_name = 'courses'
    extra_context = {
        'title': 'Browse Courses'
    }
    template_name = 'classroom/students/courses_list.html'

    # Get only the courses that the student is NOT enrolled and Pending
    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_student:
                student = self.request.user.student
                taken_courses = student.courses.values_list('pk', flat=True)
                queryset = Course.objects.exclude(pk__in=taken_courses)
            else:
                queryset = Course.objects.all()
        else:
            queryset = Course.objects.all()
        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class MyCoursesListView(ListView):
    model = TakenCourse
    ordering = ('title', )
    context_object_name = 'taken_courses'
    extra_context = {
        'title': 'My Courses'
    }
    template_name = 'classroom/students/mycourses_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_courses \
            .select_related('course', 'course__subject') \
            .order_by('course__title')\
            .filter(status__in=['Enrolled', 'Pending'])
        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'classroom/students/quiz_list.html'

    def get_queryset(self):
        student = self.request.user.student
        student_interests = student.interests.values_list('pk', flat=True)
        taken_quizzes = student.quizzes.values_list('pk', flat=True)
        queryset = Quiz.objects.filter(subject__in=student_interests) \
            .exclude(pk__in=taken_quizzes) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)
        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class StudentInterestsView(UpdateView):
    model = Student
    form_class = StudentInterestsForm
    template_name = 'classroom/students/interests_form.html'
    success_url = reverse_lazy('students:quiz_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Interests updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'classroom/students/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz', 'quiz__subject') \
            .order_by('quiz__name')
        return queryset


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        # activate user and login:
        user.is_active = True
        user.save()
        login(request, user)
        context = {
            'title': 'Account Activation',
            'result': 'Congratulations!',
            'message': 'Your account has been activated successfully.',
            'alert': 'success'
        }
    else:
        context = {
            'title': 'Account Activation',
            'result': 'We\'re sorry...',
            'message': 'The activation link you provided is invalid. Please try again.',
            'alert': 'danger'
        }
    return render(request, 'authentication/activation.html', context)


@login_required
@student_required
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    student = request.user.student
    take = TakenCourse.objects.create(student=student, course=course)
    take.save()

    messages.info(request, 'You have successfully sent an enrollment request to the teacher in charge.')
    return redirect('course_details', pk)


@login_required
@student_required
def unenroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    student = request.user.student
    TakenCourse.objects.filter(student=student, course=course).delete()

    messages.success(request, 'You have successfully unenrolled from this course.')
    return redirect('course_details', pk)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = StudentSignUpForm(request.POST)
            if form.is_valid():
                user = form.save()
                user.is_active = False
                user.save()

                # Send an email to the user with the token:
                mail_subject = 'DigiWiz: Activate your account.'
                current_site = get_current_site(request)

                message = render_to_string('authentication/email_student_confirm.html', {
                    'user': user,
                    'domain': current_site,
                    # use .decode to convert byte to string (b'NDc' -> NDc)
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })

                to_email = form.cleaned_data.get('email')
                email = EmailMessage(mail_subject, message, to=[to_email])
                # insert try clause:
                email.send()
                context = {
                    'title': 'Account Activation',
                    'result': 'One more step remaining...',
                    'message': 'Please confirm your email address to complete the registration.',
                    'alert': 'info'
                }

                return render(request, 'authentication/activation.html', context)
        else:
            form = StudentSignUpForm()

    context = {
        'form': form,
        'user_type': 'student',
        'title': 'Register as Student'
    }
    return render(request, 'authentication/register_form.html', context)


@login_required
@student_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    student = request.user.student

    if student.quizzes.filter(pk=pk).exists():
        return render(request, 'students/taken_quiz.html')

    total_questions = quiz.questions.count()
    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('students:take_quiz', pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz, answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (quiz.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the quiz %s with success! You scored %s points.' % (quiz.name, score))
                    return redirect('students:quiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'classroom/students/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })
