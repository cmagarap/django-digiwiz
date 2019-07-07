from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView
from random import sample
from .raw_sql import get_popular_courses
from .teachers import get_enrollment_requests_count
from ..forms import ContactUsForm, SearchCourses, UserLoginForm
from ..models import (Course, Lesson, MyFile, Quiz, Student,
                      Subject, TakenQuiz, User, UserLog)


def do_paginate(data_list, page_number, results_per_page):
    ret_data_list = data_list
    # build the paginator object.
    paginator = Paginator(data_list, results_per_page)
    try:
        # get data list for the specified page_number.
        ret_data_list = paginator.page(page_number)
    except EmptyPage:
        # get the lat page data if the page_number is bigger than last page number.
        ret_data_list = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        # if the page_number is not an integer then return the first page data.
        ret_data_list = paginator.page(1)
    return [ret_data_list, paginator]


def get_suggested_courses(page_course_id, current_subject_id=None, subject_interests=None):
    """Gets the suggested courses.
    If a student is logged in, suggestions are based on his/her interests.
    Else, suggestions are based on subject."""
    course_ids = None
    if current_subject_id is not None:
        course_ids = tuple(Course.objects.values_list('id', flat=True)
                           .filter(subject_id=current_subject_id, status='approved')
                           .exclude(id=page_course_id))[:3]

    if subject_interests is not None:
        course_ids = tuple(Course.objects.values_list('id', flat=True)
                           .filter(subject__in=subject_interests, status='approved')
                           .exclude(id=page_course_id))[:3]

    return Course.objects.filter(id__in=sample(course_ids, len(course_ids)))


def get_user_type(user):
    if user.is_student:
        return 'student'
    elif user.is_teacher:
        return 'teacher'
    elif user.is_staff:
        return 'admin'


class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/course_details.html'

    def get_context_data(self, **kwargs):
        student = None
        teacher = None
        kwargs['title'] = self.get_object()
        kwargs['lessons'] = Lesson.objects.select_related('quizzes') \
            .select_related('course') \
            .filter(course__id=self.kwargs['pk']) \
            .order_by('number')
        kwargs['quizzes'] = Quiz.objects.filter(course_id=self.kwargs['pk']) \
            .order_by('lesson__number')
        kwargs['files'] = MyFile.objects.filter(course_id=self.kwargs['pk']) \
            .order_by('file')

        if self.request.user.is_authenticated:
            if self.request.user.is_student:
                teacher = None
                # if the logged in user is a student, check if he/she is enrolled in the displayed course
                student = self.request.user.student.taken_courses.values('id', 'status') \
                    .filter(course__id=self.kwargs['pk']).first()

                kwargs['taken_quizzes'] = TakenQuiz.objects \
                    .filter(student=self.request.user.student, course_id=self.kwargs['pk'])

                taken_quiz_count = TakenQuiz.objects.filter(student_id=self.request.user.pk,
                                                            course_id=self.kwargs['pk']) \
                    .values_list('id', flat=True).count()
                quiz_count = Quiz.objects.filter(course_id=self.kwargs['pk']) \
                    .values_list('id', flat=True).count()

                kwargs['progress'] = (taken_quiz_count / quiz_count) * 100 if quiz_count != 0 else 0

                subject_interests = Student.objects.values_list('interests').filter(pk=self.request.user)
                kwargs['related_courses'] = get_suggested_courses(self.kwargs['pk'],
                                                                  subject_interests=subject_interests)

                kwargs['course'] = get_object_or_404(Course.objects.filter(status='approved'),
                                                     pk=self.kwargs['pk'])

            elif self.request.user.is_teacher:
                student = None
                # if the logged in user is a teacher, check if he/she owns the displayed course
                teacher = self.request.user.courses.values_list('id', flat=True) \
                    .filter(id=self.kwargs['pk']).first()

                kwargs['enrollment_request_count'] = get_enrollment_requests_count(self.request.user)
                kwargs['course'] = get_object_or_404(Course.objects.exclude(status='deleted'),
                                                     pk=self.kwargs['pk'])

                current_subject = kwargs['course'].subject_id
                kwargs['related_courses'] = get_suggested_courses(self.kwargs['pk'],
                                                                  current_subject_id=current_subject)

        else:
            kwargs['course'] = get_object_or_404(Course.objects.filter(status='approved'),
                                                 pk=self.kwargs['pk'])

            current_subject = kwargs['course'].subject_id
            kwargs['related_courses'] = get_suggested_courses(self.kwargs['pk'],
                                                              current_subject_id=current_subject)

        kwargs['enrolled'] = student
        kwargs['owns'] = True if teacher else None

        return super().get_context_data(**kwargs)


def about(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:course_change_list')
        elif request.user.is_student:
            return redirect('students:mycourses_list')

    context = {
        'title': 'About Us',
        'courses': Course.objects.values_list('id', flat=True)
                                 .filter(status__iexact='approved').count(),
        'students': User.objects.values_list('id', flat=True)
                                .filter(is_student=True, is_active=True).count(),
        'teachers': User.objects.values_list('id', flat=True)
                                .filter(is_teacher=True, is_active=True).count(),
        'quizzes': Quiz.objects.values_list('id', flat=True)
                               .all().count()
    }

    return render(request, 'classroom/about.html', context)


def browse_courses(request):
    if request.user.is_authenticated and request.user.is_teacher:
        enrollment_requests_count = get_enrollment_requests_count(request.user)
    else:
        enrollment_requests_count = None

    query = None
    subjects = Subject.objects.all()
    courses = Course.objects.filter(status__iexact='approved') \
        .annotate(taken_count=Count('taken_courses',
                                    filter=Q(taken_courses__status='enrolled'),
                                    distinct=True)) \
        .order_by('title')

    page_number = request.GET.get('page', 1)
    paginate_result = do_paginate(courses, page_number, 9)
    course_list = paginate_result[0]
    paginator = paginate_result[1]
    base_url = '/browse-courses/?'

    if 'search' in request.GET:
        form = SearchCourses(request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('search')
            courses = Course.objects.filter(Q(title__icontains=query) |
                                            Q(code__icontains=query) |
                                            Q(description__icontains=query)) \
                .filter(status__iexact='approved') \
                .annotate(taken_count=Count('taken_courses',
                                            filter=Q(taken_courses__status='enrolled'),
                                            distinct=True))

            paginate_result = do_paginate(courses, page_number, 9)
            course_list = paginate_result[0]
            paginator = paginate_result[1]
            base_url = f'/browse-courses/?search={query}&'

            if request.user.is_authenticated:
                UserLog.objects.create(action=f'Searched for "{query}"',
                                       user_type=get_user_type(request.user),
                                       user=request.user)
                enrollment_requests_count = get_enrollment_requests_count(request.user)
    else:
        form = SearchCourses()

    context = {
        'title': 'Browse Courses',
        'form': form,
        'courses': course_list,
        'paginator': paginator,
        'search_str': query,
        'subjects': subjects,
        'base_url': base_url,
        'enrollment_request_count': enrollment_requests_count
    }
    return render(request, 'classroom/students/courses_list.html', context)


def browse_courses_subject(request, subject_pk):
    if request.user.is_authenticated and request.user.is_teacher:
        enrollment_requests_count = get_enrollment_requests_count(request.user)
    else:
        enrollment_requests_count = None

    courses = Course.objects.filter(status__iexact='approved', subject_id=subject_pk) \
        .annotate(taken_count=Count('taken_courses',
                                    filter=Q(taken_courses__status='enrolled'),
                                    distinct=True)) \
        .order_by('title')

    page_number = request.GET.get('page', 1)
    paginate_result = do_paginate(courses, page_number, 9)
    course_list = paginate_result[0]
    paginator = paginate_result[1]
    base_url = f'/browse-courses/{subject_pk}/?'

    query = None
    subjects = Subject.objects.all()

    if 'search' in request.GET:
        form = SearchCourses(request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('search')
            courses = Course.objects.filter(Q(title__icontains=query) |
                                            Q(code__icontains=query) |
                                            Q(description__icontains=query)) \
                .filter(status__iexact='approved') \
                .annotate(taken_count=Count('taken_courses',
                                            filter=Q(taken_courses__status='enrolled'),
                                            distinct=True))

            paginate_result = do_paginate(courses, page_number, 9)
            course_list = paginate_result[0]
            paginator = paginate_result[1]
            base_url = f'/browse-courses/{subject_pk}/?search={query}&'

            if request.user.is_authenticated:
                UserLog.objects.create(action=f'Searched for "{query}"',
                                       user_type=get_user_type(request.user),
                                       user=request.user)
                enrollment_requests_count = get_enrollment_requests_count(request.user)
    else:
        form = SearchCourses()

    context = {
        'title': 'Browse Courses',
        'form': form,
        'courses': course_list,
        'paginator': paginator,
        'search_str': query,
        'subjects': subjects,
        'base_url': base_url,
        'enrollment_request_count': enrollment_requests_count
    }
    return render(request, 'classroom/students/courses_list_subject.html', context)


def contact_us(request):
    form = None
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:course_change_list')
        elif request.user.is_student:
            return redirect('students:mycourses_list')
        elif request.user.is_staff:
            return redirect('staff:dashboard')
    else:
        if request.method == 'POST':
            form = ContactUsForm(request.POST)
            if form.is_valid():
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']
                sender = form.cleaned_data['email']
                cc_myself = form.cleaned_data['cc_myself']

                recipients = ['digiwiz.sq@gmail.com']
                if cc_myself:
                    recipients.append(sender)

                try:
                    send_mail(subject, message, sender, recipients)

                    messages.success(request, 'You successfully sent an email to us. '
                                              'Please wait for a response in your email, thank you.')

                    return redirect('contact_us')
                except Exception:
                    messages.error(request, 'An unexpected error has occurred. Please try again.')

                    return redirect('contact_us')
        else:
            form = ContactUsForm()

    return render(request, 'classroom/contact.html', {'title': 'Contact Us', 'form': form})


def home(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:course_change_list')
        elif request.user.is_student:
            return redirect('students:mycourses_list')
        elif request.user.is_staff:
            return redirect('staff:dashboard')
    else:
        context = {
            'popular_courses': Course.objects.raw(get_popular_courses()),
            'subjects': Subject.objects.all().order_by('name')
        }

        return render(request, 'classroom/home.html', context)


def login_view(request):
    next_link = request.GET.get('next')
    form = UserLoginForm(request.POST or None)

    if request.user.is_authenticated:
        return redirect('home')
    else:
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            login(request, user)

            if next_link:
                return redirect(next_link)
            else:
                return redirect('/')

    return render(request, 'authentication/login.html', {'form': form, 'title': 'Login'})


def logout_view(request):
    logout(request)
    return redirect('/')


def register_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'authentication/register.html', {'title': 'Register'})
