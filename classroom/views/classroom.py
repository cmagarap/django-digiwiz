from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views.generic import DetailView
from .raw_sql import get_popular_courses
from ..forms import SearchCourses, UserLoginForm
from ..models import (Course, Lesson, MyFile, Quiz, Subject,
                      Student, TakenQuiz, Teacher, UserLog)


def get_user_type(user):
    if user.is_student:
        return 'student'
    elif user.is_teacher:
        return 'teacher'


class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/course_details.html'

    def get_context_data(self, **kwargs):
        student = None
        teacher = None
        if self.request.user.is_authenticated:
            if self.request.user.is_student:
                # if the logged in user is a student, check if he/she is enrolled in the displayed course
                student = self.request.user.student.taken_courses.values('id', 'status') \
                    .filter(course__id=self.kwargs['pk']).first()

                kwargs['taken_quizzes'] = TakenQuiz.objects\
                    .filter(student=self.request.user.student, course_id=self.kwargs['pk'])

                taken_quiz_count = TakenQuiz.objects.filter(student_id=self.request.user.pk,
                                                            course_id=self.kwargs['pk']) \
                    .values_list('id', flat=True).count()
                quiz_count = Quiz.objects.filter(course_id=self.kwargs['pk']) \
                    .values_list('id', flat=True).count()

                kwargs['progress'] = (taken_quiz_count / quiz_count) * 100 if quiz_count != 0 else 0
                teacher = None

            elif self.request.user.is_teacher:
                # if the logged in user is a teacher, check if he/she owns the displayed course
                teacher = self.request.user.courses.values_list('id', flat=True) \
                    .filter(id=self.kwargs['pk']).first()
                student = None

        kwargs['enrolled'] = student
        kwargs['owns'] = teacher
        kwargs['title'] = self.get_object()
        kwargs['lessons'] = Lesson.objects.select_related('quizzes') \
            .select_related('course') \
            .filter(course__id=self.kwargs['pk']) \
            .order_by('number')
        kwargs['quizzes'] = Quiz.objects.filter(course_id=self.kwargs['pk']) \
            .order_by('title')
        kwargs['files'] = MyFile.objects.filter(course_id=self.kwargs['pk']) \
            .order_by('file')

        return super().get_context_data(**kwargs)


def about(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:course_change_list')
        elif request.user.is_student:
            return redirect('students:mycourses_list')

    context = {
        'title': 'About Us',
        'courses': Course.objects.filter(status__iexact='approved').count(),
        'students': Student.objects.all().count(),
        'teachers': Teacher.objects.all().count(),
        'quizzes': Quiz.objects.all().count()
    }

    return render(request, 'classroom/about.html', context)


def contact_us(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:course_change_list')
        elif request.user.is_student:
            return redirect('students:mycourses_list')
        elif request.user.is_staff:
            return redirect('staff:dashboard')
    return render(request, 'classroom/contact.html', {'title': 'Contact Us'})


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


def browse_courses(request):
    query = None
    subjects = Subject.objects.all()
    courses = Course.objects.filter(status__iexact='approved') \
        .annotate(taken_count=Count('taken_courses',
                                    filter=Q(taken_courses__status__iexact='enrolled'),
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
                                            Q(description__icontains=query)) \
                .filter(status__iexact='approved')

            paginate_result = do_paginate(courses, page_number, 9)
            course_list = paginate_result[0]
            paginator = paginate_result[1]
            base_url = f'/browse-courses/?search={query}&'

            if request.user.is_authenticated:
                UserLog.objects.create(action=f'Searched for "{query}"',
                                       user_type=get_user_type(request.user),
                                       user=request.user)
    else:
        form = SearchCourses()

    context = {
        'title': 'Browse Courses',
        'form': form,
        'courses': course_list,
        'paginator': paginator,
        'search_str': query,
        'subjects': subjects,
        'base_url': base_url
    }
    return render(request, 'classroom/students/courses_list.html', context)


def browse_courses_subject(request, subject_pk):
    courses = Course.objects.filter(status__iexact='approved', subject_id=subject_pk) \
        .annotate(taken_count=Count('taken_courses',
                                    filter=Q(taken_courses__status__iexact='enrolled'),
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
                                            Q(description__icontains=query)) \
                .filter(status__iexact='approved')

            paginate_result = do_paginate(courses, page_number, 9)
            course_list = paginate_result[0]
            paginator = paginate_result[1]
            base_url = f'/browse-courses/{subject_pk}/?search={query}&'

            if request.user.is_authenticated:
                UserLog.objects.create(action=f'Searched for "{query}"',
                                       user_type=get_user_type(request.user),
                                       user=request.user)
    else:
        form = SearchCourses()

    context = {
        'title': 'Browse Courses',
        'form': form,
        'courses': course_list,
        'paginator': paginator,
        'search_str': query,
        'subjects': subjects,
        'base_url': base_url
    }
    return render(request, 'classroom/students/courses_list_subject.html', context)
