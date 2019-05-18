from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from ..forms import UserLoginForm


def home(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:quiz_change_list')
        else:
            return redirect('students:quiz_list')
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

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/')


def signup_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'registration/signup.html')
