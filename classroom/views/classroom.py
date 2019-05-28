from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.generic import DetailView
from ..forms import UserLoginForm
from ..models import Course


class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    extra_context = {
        'title': 'Course Details'
    }
    template_name = 'classroom/course_details.html'


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
    return render(request, 'authentication/register.html')
