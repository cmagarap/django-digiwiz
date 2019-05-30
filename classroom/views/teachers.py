from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from ..decorators import teacher_required
from ..forms import BaseAnswerInlineFormSet, LessonForm, QuestionForm, TeacherSignUpForm
from ..models import Answer, Course, Lesson, Question, Quiz, User
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
class CourseDeleteView(DeleteView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_delete_confirm.html'
    success_url = reverse_lazy('teachers:course_change_list')

    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, f'The course {course.title} was deleted with success!')
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        """This method is an implicit object-level permission management.
        This view will only match the ids of existing courses that belongs
        to the logged in user."""
        return self.request.user.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    ordering = ('title', )
    context_object_name = 'courses'
    extra_context = {
        'title': 'My Courses'
    }
    template_name = 'classroom/teachers/course_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.courses \
            .select_related('subject')
        return queryset


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseUpdateView(UpdateView):
    model = Course
    fields = ('title', 'code', 'subject', 'description', 'image')
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_change_form.html'
    extra_context = {
        'title': 'Edit Course'
    }

    # def get_context_data(self, **kwargs):
    #     kwargs['questions'] = self.get_object().questions.annotate(answers_count=Count('answers'))
    #     return super().get_context_data(**kwargs)
    #
    def get_queryset(self):
        return self.request.user.courses.all()

    def get_success_url(self):
        title = self.get_object()
        messages.success(self.request, f'{title} has been successfully updated.')
        return reverse('teachers:course_change_list')


@method_decorator([login_required, teacher_required], name='dispatch')
class LessonDeleteView(DeleteView):
    model = Lesson
    context_object_name = 'lesson'
    template_name = 'classroom/teachers/lesson_delete_confirm.html'
    pk_url_kwarg = 'lesson_pk'

    def get_context_data(self, **kwargs):
        lesson = self.get_object()
        kwargs['course'] = lesson.course
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        lesson = self.get_object()
        messages.success(request, f'The lesson {lesson.title} was deleted with success!')
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Lesson.objects.filter(course__owner=self.request.user)

    def get_success_url(self):
        lesson = self.get_object()
        return reverse('teachers:course_change_list')


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


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'classroom/teachers/quiz_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.quizzes \
            .select_related('subject') \
            .annotate(questions_count=Count('questions', distinct=True)) \
            .annotate(taken_count=Count('taken_quizzes', distinct=True))
        return queryset


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizCreateView(CreateView):
    model = Quiz
    fields = ('name', 'subject', )
    template_name = 'classroom/teachers/quiz_add_form.html'

    def form_valid(self, form):
        quiz = form.save(commit=False)
        quiz.owner = self.request.user
        quiz.save()
        messages.success(self.request, 'The quiz was created with success! Go ahead and add some questions now.')
        return redirect('teachers:quiz_change', quiz.pk)


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizUpdateView(UpdateView):
    model = Quiz
    fields = ('name', 'subject', )
    context_object_name = 'quiz'
    template_name = 'classroom/teachers/quiz_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['questions'] = self.get_object().questions.annotate(answers_count=Count('answers'))
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """This method is an implicit object-level permission management
        This view will only match the ids of existing quizzes that belongs
        to the logged in user."""
        return self.request.user.quizzes.all()

    def get_success_url(self):
        return reverse('teachers:quiz_change', kwargs={'pk': self.object.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizDeleteView(DeleteView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'classroom/teachers/quiz_delete_confirm.html'
    success_url = reverse_lazy('teachers:quiz_change_list')

    def delete(self, request, *args, **kwargs):
        quiz = self.get_object()
        messages.success(request, 'The quiz %s was deleted with success!' % quiz.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()


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
        form = LessonForm(request.user, data=request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            # lesson.course = course
            lesson.save()
            messages.success(request, 'The lesson was successfully created.')
            return redirect('teachers:course_change_list')
    else:
        form = LessonForm(current_user=request.user)

    context = {
        'form': form,
        'title': 'Add a Lesson'
    }
    return render(request, 'classroom/teachers/lesson_add_form.html', context)


@login_required
@teacher_required
def edit_lesson(request, course_pk, lesson_pk):
    course = get_object_or_404(Course, pk=course_pk, owner=request.user)
    lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)

    if request.method == 'POST':
        form = LessonForm(request.user, data=request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()
            messages.success(request, 'The lesson was successfully changed.')
            return redirect('teachers:course_change_list')
    else:
        form = LessonForm(current_user=request.user, instance=lesson)

    context = {
        'course': course,
        'lesson': lesson,
        'form': form,
        'title': 'Edit Lesson'
    }
    return render(request, 'classroom/teachers/lesson_change_form.html', context)


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
                    # use .decode to convert byte to string (b'NDc' -> NDc)
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode('utf-8'),
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
def question_add(request, pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'You may now add answers/options to the question.')
            return redirect('teachers:question_change', quiz.pk, question.pk)
    else:
        form = QuestionForm()

    return render(request, 'classroom/teachers/question_add_form.html', {'quiz': quiz, 'form': form})


@login_required
@teacher_required
def question_change(request, quiz_pk, question_pk):
    # Similar to the `question_add` view, this view is also managing
    # the permissions at object-level. By querying both `quiz` and
    # `question` we are making sure only the owner of the quiz can
    # change its details and also only questions that belongs to this
    # specific quiz can be changed via this url (in cases where the
    # user might have forged/player with the url params.
    quiz = get_object_or_404(Quiz, pk=quiz_pk, owner=request.user)
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
            return redirect('teachers:quiz_change', quiz.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormSet(instance=question)

    return render(request, 'classroom/teachers/question_change_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'formset': formset
    })


@method_decorator([login_required, teacher_required], name='dispatch')
class QuestionDeleteView(DeleteView):
    model = Question
    context_object_name = 'question'
    template_name = 'classroom/teachers/question_delete_confirm.html'
    pk_url_kwarg = 'question_pk'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        kwargs['quiz'] = question.quiz
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        messages.success(request, 'The question %s was deleted with success!' % question.text)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Question.objects.filter(quiz__owner=self.request.user)

    def get_success_url(self):
        question = self.get_object()
        return reverse('teachers:quiz_change', kwargs={'pk': question.quiz_id})
