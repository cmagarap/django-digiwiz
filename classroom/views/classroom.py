from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.generic import DetailView
from ..forms import UserLoginForm
from ..models import Course, Lesson


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
                student = self.request.user.student.taken_courses.filter(course__id=self.kwargs['pk']).first()
                teacher = None
            elif self.request.user.is_teacher:
                # if the logged in user is a teacher, check if he/she owns the displayed course
                teacher = self.request.user.courses.get(id=self.kwargs['pk'])
                student = None

        kwargs['enrolled'] = student
        kwargs['owns'] = teacher
        kwargs['title'] = Course.objects.get(id=self.kwargs['pk'])
        kwargs['lessons'] = Lesson.objects.get(course__id=self.kwargs['pk'])

        return super().get_context_data(**kwargs)


def about(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:quiz_change_list')
        elif request.user.is_student:
            return redirect('students:quiz_list')

    return render(request, 'classroom/about.html')


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
    next = request.GET.get('next')
    form = UserLoginForm(request.POST or None)

    if request.user.is_authenticated:
        return redirect('home')
    else:
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            login(request, user)

            if next:
                return redirect(next)
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
