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
from django.views.generic import ListView, DetailView, UpdateView
from .raw_sql import get_taken_quiz
from ..decorators import student_required
from ..forms import (StudentInterestsForm, StudentProfileForm,
                     StudentSignUpForm, TakeQuizForm, UserUpdateForm)
from ..models import (Course, Lesson, Quiz, Student, StudentAnswer,
                      TakenCourse, TakenQuiz, User)
from ..tokens import account_activation_token


User = get_user_model()


@method_decorator([login_required, student_required], name='dispatch')
class LessonListView(ListView):
    model = Lesson
    context_object_name = 'lessons'
    extra_context = {
        'title': 'Lessons',
    }
    template_name = 'classroom/students/lessons.html'
    paginate_by = 1

    def get_queryset(self, **kwargs):
        return Lesson.objects.select_related('quizzes') \
            .select_related('course') \
            .filter(course__id=self.kwargs['pk']) \
            .order_by('number')


@method_decorator([login_required, student_required], name='dispatch')
class MyCoursesListView(ListView):
    model = TakenCourse
    ordering = ('title', )
    context_object_name = 'taken_courses'
    extra_context = {
        'title': 'My Courses',
    }
    template_name = 'classroom/students/mycourses_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_courses \
            .select_related('course', 'course__subject') \
            .filter(status__in=['enrolled', 'pending']) \
            .order_by('course__title')

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
    success_url = reverse_lazy('students:mycourses_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Your interests are successfully updated!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizDetailView(DetailView):
    model = TakenQuiz
    context_object_name = 'taken_quiz'
    template_name = 'classroom/students/taken_quiz_result.html'

    def get_context_data(self, **kwargs):
        kwargs['student_answer'] = StudentAnswer.objects.raw(
            get_taken_quiz(self.request.user.pk, self.kwargs['pk']))
        kwargs['taken_quiz'] = TakenQuiz.objects \
            .select_related('quiz') \
            .get(id=self.kwargs['pk'])
        return super().get_context_data(**kwargs)


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    extra_context = {
        'title': 'My Taken Quizzes'
    }
    template_name = 'classroom/students/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz') \
            .order_by('quiz__title')
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


@login_required
@student_required
def profile(request):
    if request.method == 'POST':
        user_update_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = StudentProfileForm(request.POST, request.FILES, instance=request.user.student)

        if user_update_form.is_valid() and profile_form.is_valid():
            user_update_form.save()
            profile_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('students:profile')

    else:
        user_update_form = UserUpdateForm(instance=request.user)
        profile_form = StudentProfileForm(instance=request.user.student)

    context = {
        'u_form': user_update_form,
        'p_form': profile_form,
        'title': 'My Profile'
    }

    return render(request, 'classroom/students/student_profile.html', context)


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
def take_quiz(request, course_pk, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    student = request.user.student

    if student.quizzes.filter(pk=quiz_pk).exists():
        messages.error(request, 'You already took that quiz!')
        return redirect('course_details', course_pk)

    total_questions = quiz.questions.count()
    if total_questions == 0:
        messages.error(request, 'We\'re sorry, there are currently no questions available for that quiz.')
        return redirect('course_details', course_pk)

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
                    return redirect('students:take_quiz', course_pk, quiz_pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz,
                                                                  answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz,
                                             score=score, status='Finished')
                    if score < 50.0:
                        messages.warning(request, f'Better luck next time! Your score for the '
                                                  f'quiz { quiz.title } was { score }.')
                    else:
                        messages.success(request, f'Congratulations! You completed the '
                                                  f'quiz { quiz.title } with success! You scored { score } points.')
                    return redirect('course_details', course_pk)
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'classroom/students/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })
