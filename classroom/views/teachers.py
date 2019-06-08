from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import (CreateView, DetailView, ListView,
                                  UpdateView)
from ..decorators import teacher_required
from ..forms import (BaseAnswerInlineFormSet, LessonAddForm, LessonEditForm,
                     QuizAddForm, QuizEditForm, QuestionForm, TeacherProfileForm,
                     TeacherSignUpForm, UserUpdateForm)
from ..models import Answer, Course, Lesson, Question, Quiz, TakenCourse, User
from ..tokens import account_activation_token


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseCreateView(CreateView):
    model = Course
    fields = ('title', 'code', 'subject', 'description', 'image')
    template_name = 'classroom/teachers/course_add_form.html'
    extra_context = {
        'title': 'New Course'
    }

    def form_valid(self, form):
        course = form.save(commit=False)
        course.owner = self.request.user
        course.save()
        messages.success(self.request, 'The course was created with success!')
        return redirect('teachers:course_change_list')


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    extra_context = {
        'title': 'My Courses'
    }
    template_name = 'classroom/teachers/course_list.html'

    def get_context_data(self, **kwargs):
        # Get only the courses that the logged in teacher owns
        # and count the enrolled students
        kwargs['courses'] = self.request.user.courses \
            .annotate(taken_count=Count('taken_courses',
                                        filter=Q(taken_courses__status__iexact='enrolled'),
                                        istinct=True))

        return super().get_context_data(**kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class LessonListView(ListView):
    model = Lesson
    context_object_name = 'lessons'
    extra_context = {
        'title': 'My Lessons'
    }
    template_name = 'classroom/teachers/lesson_list.html'

    def get_queryset(self):
        """Gets the lesson that the user owns through course FK."""
        return Lesson.objects.filter(course__in=self.request.user.courses.all()).order_by('title')


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseUpdateView(UpdateView):
    model = Course
    fields = ('title', 'code', 'subject', 'description', 'image')
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_change_form.html'
    extra_context = {
        'title': 'Edit Course'
    }

    def get_queryset(self):
        """This method is an implicit object-level permission management.
        This view will only match the ids of existing courses that belongs
        to the logged in user."""
        return self.request.user.courses.all()

    def get_success_url(self):
        title = self.get_object()
        messages.success(self.request, f'{title} has been successfully updated.')
        return reverse('teachers:course_change_list')


class EnrollmentRequestsListView(ListView):
    model = Course
    context_object_name = 'taken_courses'
    extra_context = {
        'title': 'Enrollment Requests'
    }
    template_name = 'classroom/teachers/enrollment_requests_list.html'

    def get_queryset(self):
        """This method gets the enrollment requests of students."""
        return TakenCourse.objects.filter(course__in=self.request.user.courses.all(),
                                          status__iexact='pending')


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    context_object_name = 'quizzes'
    template_name = 'classroom/teachers/quiz_list.html'

    def get_queryset(self):
        # queryset = self.request.user.quizzes \
        #     .select_related('subject') \
        #     .annotate(questions_count=Count('questions', distinct=True)) \
        #     .annotate(taken_count=Count('taken_quizzes', distinct=True))

        queryset = Quiz.objects.filter(course__owner=self.request.user) \
            .annotate(questions_count=Count('questions', distinct=True))
        return queryset


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizResultsView(DetailView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'classroom/teachers/quiz_results.html'

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        taken_quizzes = quiz.taken_quizzes.select_related('student__user').order_by('-date')
        total_taken_quizzes = taken_quizzes.count()
        quiz_score = quiz.taken_quizzes.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_quizzes': taken_quizzes,
            'total_taken_quizzes': total_taken_quizzes,
            'quiz_score': quiz_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()


class TeacherSignUpView(CreateView):
    model = User
    form_class = TeacherSignUpForm
    template_name = 'authentication/register_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('teachers:quiz_change_list')


@login_required
@teacher_required
def accept_enrollment(request, taken_course_pk):
    TakenCourse.objects.filter(id=taken_course_pk).update(status='Enrolled')

    messages.success(request, 'The student has been successfully enrolled.')
    return redirect('teachers:enrollment_requests_list')


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
@teacher_required
def add_lesson(request):
    if request.method == 'POST':
        form = LessonAddForm(request.user, data=request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()
            messages.success(request, 'The lesson was successfully created.')
            return redirect('teachers:lesson_list')
    else:
        form = LessonAddForm(current_user=request.user)

    context = {
        'form': form,
        'title': 'Add a Lesson'
    }
    return render(request, 'classroom/teachers/lesson_add_form.html', context)


@login_required
@teacher_required
def add_question(request, course_pk, quiz_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course=course)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'You may now add answers/options to the question.')
            return redirect('teachers:question_change', quiz.course.pk, quiz.pk, question.pk)
    else:
        form = QuestionForm()

    return render(request, 'classroom/teachers/question_add_form.html', {'quiz': quiz, 'form': form})


@login_required
@teacher_required
def add_quiz(request):
    if request.method == 'POST':
        form = QuizAddForm(request.user, data=request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.save()
            messages.success(request, 'The quiz was successfully created. You may now add some questions.')
            return redirect('teachers:quiz_edit', quiz.course.pk, quiz.pk)
    else:
        form = QuizAddForm(current_user=request.user)

    context = {
        'form': form,
        'title': 'Add a Quiz'
    }
    return render(request, 'classroom/teachers/quiz_add_form.html', context)


@login_required
@teacher_required
def delete_course(request, pk):
    request.user.courses.filter(id=pk).update(status='Deleted')
    messages.success(request, 'The course has been successfully deleted.')
    return redirect('teachers:course_change_list')


@login_required
@teacher_required
def delete_lesson(request, course_pk, lesson_pk):
    teacher = request.user
    Lesson.objects.filter(id=lesson_pk, course__owner=teacher).delete()
    messages.success(request, 'The lesson has been successfully deleted.')

    return redirect('course_details', course_pk)


@login_required
@teacher_required
def delete_lesson_from_list(request, lesson_pk):
    Lesson.objects.filter(id=lesson_pk, course__owner=request.user).delete()
    messages.success(request, 'The lesson has been successfully deleted.')

    return redirect('teachers:lesson_list')


@login_required
@teacher_required
def delete_question(request, course_pk, quiz_pk, question_pk):
    teacher = request.user
    quiz = Quiz.objects.get(id=quiz_pk, course__owner=teacher)
    Question.objects.get(id=question_pk, quiz=quiz).delete()
    messages.success(request, 'The question has been successfully deleted.')

    return redirect('teachers:quiz_edit', course_pk, quiz_pk)


@login_required
@teacher_required
def delete_quiz(request, quiz_pk):
    teacher = request.user
    Quiz.objects.filter(id=quiz_pk, course__owner=teacher).delete()
    messages.success(request, 'The quiz has been successfully deleted.')

    return redirect('teachers:course_change_list')


@login_required
@teacher_required
def delete_quiz_from_list(request, quiz_pk):
    Quiz.objects.filter(id=quiz_pk, course__owner=request.user).delete()
    messages.success(request, 'The quiz has been successfully deleted.')

    return redirect('teachers:quiz_list')


@login_required
@teacher_required
def edit_lesson(request, course_pk, lesson_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)

    if request.method == 'POST':
        form = LessonEditForm(data=request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()
            messages.success(request, 'The lesson was successfully changed.')
            return redirect('teachers:lesson_list')
    else:
        form = LessonEditForm(instance=lesson)

    context = {
        'course': course,
        'lesson': lesson,
        'form': form,
        'title': 'Edit Lesson'
    }
    return render(request, 'classroom/teachers/lesson_change_form.html', context)


@login_required
@teacher_required
def edit_question(request, course_pk, quiz_pk, question_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course=course)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)

    AnswerFormSet = inlineformset_factory(
        Question,  # parent model
        Answer,  # base model
        formset=BaseAnswerInlineFormSet,
        fields=('text', 'is_correct'),
        min_num=2,
        validate_min=True,
        max_num=10,
        validate_max=True
    )

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Question and answers saved with success!')
            return redirect('teachers:quiz_edit', course.pk, quiz.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormSet(instance=question)

    return render(request, 'classroom/teachers/question_change_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'formset': formset
    })


@login_required
@teacher_required
def edit_quiz(request, course_pk, quiz_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course=course)
    question = Question.objects.filter(quiz=quiz).annotate(answers_count=Count('answers'))

    if request.method == 'POST':
        form = QuizEditForm(data=request.POST, instance=quiz)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.save()
            messages.success(request, 'The quiz was successfully changed.')
            return redirect('teachers:quiz_edit', quiz.course.pk, quiz.pk)
    else:
        form = QuizEditForm(instance=quiz)

    context = {
        'course': course,
        'quiz': quiz,
        'questions': question,
        'form': form,
        'title': 'Edit Quiz'
    }
    return render(request, 'classroom/teachers/quiz_change_form.html', context)


@login_required
@teacher_required
def load_lessons(request):
    course_id = request.GET.get('course')
    lessons = Lesson.objects.filter(course_id=course_id).order_by('title')
    return render(request, 'classroom/teachers/lesson_dropdown_list_options.html', {'lessons': lessons})


@login_required
@teacher_required
def profile(request):
    if request.method == 'POST':
        user_update_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = TeacherProfileForm(request.POST, request.FILES, instance=request.user.teacher)

        if user_update_form.is_valid() and profile_form.is_valid():
            user_update_form.save()
            profile_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('teachers:profile')

    else:
        user_update_form = UserUpdateForm(instance=request.user)
        profile_form = TeacherProfileForm(instance=request.user.teacher)

    context = {
        'u_form': user_update_form,
        'p_form': profile_form,
        'title': 'My Profile'
    }

    return render(request, 'classroom/teachers/teacher_profile.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = TeacherSignUpForm(request.POST)
            if form.is_valid():
                user = form.save()
                user.is_active = False
                user.save()

                # Send an email to the user with the token:
                mail_subject = 'DigiWiz: Activate your account.'
                current_site = get_current_site(request)

                message = render_to_string('authentication/email_teacher_confirm.html', {
                    'user': user,
                    'domain': current_site,
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
            form = TeacherSignUpForm()

    context = {
        'form': form,
        'user_type': 'teacher',
        'title': 'Register as Teacher'
    }
    return render(request, 'authentication/register_form.html', context)


@login_required
@teacher_required
def reject_enrollment(request, taken_course_pk):
    TakenCourse.objects.filter(id=taken_course_pk).delete()

    messages.success(request, 'The student\'s request has been successfully rejected.')
    return redirect('teachers:enrollment_requests_list')
