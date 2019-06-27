from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views.generic import DetailView
from ..forms import SearchCourses, UserLoginForm
from ..models import (Course, Lesson, MyFile, Quiz, Student,
                      TakenQuiz, Teacher, UserLog)


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
        kwargs['title'] = Course.objects.get(id=self.kwargs['pk'])
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
    return render(request, 'classroom/home.html')


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


def browse_courses(request):
    query = None
    courses = Course.objects.filter(status__iexact='approved') \
        .annotate(taken_count=Count('taken_courses',
                                    filter=Q(taken_courses__status__iexact='enrolled'),
                                    distinct=True)) \
        .order_by('title')

    if request.user.is_authenticated:
        if request.user.is_student:
            courses = Course.objects.filter(status__iexact='approved') \
                .annotate(taken_count=Count('taken_courses',
                                            filter=Q(taken_courses__status__iexact='enrolled'),
                                            distinct=True)) \
                .order_by('title')

    if 'search' in request.GET:
        form = SearchCourses(request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('search')
            courses = Course.objects.filter(Q(title__icontains=query) |
                                            Q(description__icontains=query)) \
                .filter(status__iexact='approved')

            if request.user.is_authenticated:
                UserLog.objects.create(action=f'Searched for "{query}"',
                                       user_type=get_user_type(request.user),
                                       user=request.user)
    else:
        form = SearchCourses()

    context = {
        'title': 'Browse Courses',
        'form': form,
        'courses': courses,
        'search_str': query
    }
    return render(request, 'classroom/students/courses_list.html', context)
