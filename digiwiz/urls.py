"""digiwiz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from classroom.views import classroom, students, teachers
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from . import settings
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', include('classroom.urls')),
    path('about-us/', classroom.about, name='about_us'),
    path('activate-student/<uidb64>/<token>', students.activate, name='activate_student'),
    path('activate-teacher/<uidb64>/<token>', teachers.activate, name='activate_teacher'),
    path('admin/', admin.site.urls),
    path('browse-courses/', students.BrowseCourseView.as_view(), name='browse_courses'),
    path('course/details/<int:pk>/', classroom.CourseDetailView.as_view(), name='course_details'),
    path('login/', classroom.login_view, name='login'),
    path('logout/', classroom.logout_view, name='logout'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='authentication/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'),
         name='password_reset_complete'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('register/', classroom.register_page, name='register'),
    path('register/student/', students.register, name='student_register'),
    path('register/teacher/', teachers.register, name='teacher_register'),

]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
