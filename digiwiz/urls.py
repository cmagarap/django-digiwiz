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
from ckeditor_uploader import views as uploader_views
from classroom.views import classroom, students, teachers
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import static, staticfiles_urlpatterns
from django.urls import include, path
from django.views.decorators.cache import never_cache
from . import settings


urlpatterns = [
    path('', include('classroom.urls')),
    path('about-us/', classroom.about, name='about_us'),
    path('activate-student/<str:uidb64>/<str:token>', students.activate, name='activate_student'),
    path('activate-teacher/<str:uidb64>/<str:token>', teachers.activate, name='activate_teacher'),
    path('browse-courses/', classroom.browse_courses, name='browse_courses'),
    path('browse-courses/<int:subject_pk>/', classroom.browse_courses_subject, name='browse_courses_subject'),
    path('ckeditor/upload/', uploader_views.upload, name='ckeditor_upload'),
    path('ckeditor/browse/', never_cache(uploader_views.browse), name='ckeditor_browse'),
    path('contact-us/', classroom.contact_us, name='contact_us'),
    path('course/details/<int:pk>/', classroom.CourseDetailView.as_view(), name='course_details'),
    path('course/details/<int:pk>/lesson', students.LessonListView.as_view(), name='lesson_list'),
    path('django-admin/', admin.site.urls),
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
    path('password-reset-confirm/<str:uidb64>/<str:token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('ratings/', include('star_ratings.urls', namespace='ratings')),
    path('register/', classroom.register_page, name='register'),
    path('register/student/', students.register, name='student_register'),
    path('register/teacher/', teachers.register, name='teacher_register')
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
