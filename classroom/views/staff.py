from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from .raw_sql import get_popular_courses
from ..decorators import staff_required, superuser_required
from ..forms import AdminAddForm, SubjectUpdateForm, UserUpdateForm
from ..models import Course, Quiz, Subject, User, UserLog


@method_decorator([login_required, superuser_required], name='dispatch')
class AdminCreateView(CreateView):
    model = User
    form_class = AdminAddForm
    template_name = 'classroom/staff/admin_add_form.html'
    extra_context = {
        'title': 'New Admin',
        'sidebar': 'admin_list'
    }

    def form_valid(self, form):
        user = form.save(commit=False)
        user.save()
        messages.success(self.request, 'The admin account has been successfully created!')
        return redirect('staff:admin_list')

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)


@method_decorator([login_required, superuser_required], name='dispatch')
class AdminListView(ListView):
    model = User
    context_object_name = 'admins'
    extra_context = {
        'title': 'Admin Accounts',
        'sidebar': 'admin_list'
    }
    template_name = 'classroom/staff/admin_list.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets all the admin/staff accounts but not the superuser."""
        return User.objects.filter(is_staff=True, is_active=True) \
            .exclude(is_superuser=True) \
            .order_by('username')


@method_decorator([login_required, staff_required], name='dispatch')
class ChangePassword(PasswordChangeView):
    success_url = reverse_lazy('staff:account')
    template_name = 'classroom/staff/change_password.html'

    def form_valid(self, form):
        messages.success(self.request, 'Your successfully changed your password!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)


@method_decorator([login_required, staff_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    extra_context = {
        'title': 'Courses',
        'sidebar': 'course_list'
    }
    template_name = 'classroom/staff/course_list.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets all the approved courses."""
        return Course.objects.filter(status__iexact='approved') \
            .order_by('title')


@method_decorator([login_required, staff_required], name='dispatch')
class CourseRequestsView(ListView):
    model = Course
    context_object_name = 'courses'
    extra_context = {
        'title': 'Course Requests',
        'sidebar': 'course_requests'
    }
    template_name = 'classroom/staff/course_requests_list.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets all the courses that have pending as their status."""
        return Course.objects.filter(status__iexact='pending') \
            .order_by('-updated_at')


@method_decorator([login_required, staff_required], name='dispatch')
class SubjectCreateView(CreateView):
    model = Subject
    form_class = SubjectUpdateForm
    template_name = 'classroom/staff/subject_add_form.html'
    extra_context = {
        'title': 'New Subject',
        'sidebar': 'subject_list'
    }

    def form_valid(self, form):
        subject = form.save(commit=False)
        subject.save()
        messages.success(self.request, 'The subject has been successfully created!')
        return redirect('staff:subject_list')

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)


@method_decorator([login_required, staff_required], name='dispatch')
class SubjectListView(ListView):
    model = Subject
    context_object_name = 'subjects'
    extra_context = {
        'title': 'Subjects',
        'sidebar': 'subject_list'
    }
    template_name = 'classroom/staff/subject_list.html'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets all the approved courses."""
        return Subject.objects.all().order_by('name')


@method_decorator([login_required, staff_required], name='dispatch')
class StudentListView(ListView):
    model = User
    context_object_name = 'students'
    extra_context = {
        'title': 'Students',
        'sidebar': 'student_list'
    }
    template_name = 'classroom/staff/students_list.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets all the student accounts."""
        return User.objects.filter(is_student=True, is_active=True) \
            .order_by('username')


@method_decorator([login_required, staff_required], name='dispatch')
class SubjectUpdateView(UpdateView):
    model = Subject
    form_class = SubjectUpdateForm
    context_object_name = 'subjects'
    template_name = 'classroom/staff/subject_change_form.html'
    extra_context = {
        'title': 'Edit Subject',
        'sidebar': 'subject_list'
    }

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return Subject.objects.all()

    def get_success_url(self):
        title = self.get_object()
        messages.success(self.request, f'{title} has been successfully updated.')
        return reverse('staff:subject_list')


@method_decorator([login_required, staff_required], name='dispatch')
class TeacherListView(ListView):
    model = User
    context_object_name = 'teachers'
    extra_context = {
        'title': 'Teachers',
        'sidebar': 'teacher_list'
    }
    template_name = 'classroom/staff/teacher_list.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """Gets all the teacher accounts."""
        return User.objects.filter(is_teacher=True, is_active=True) \
            .order_by('username')


@method_decorator([login_required, staff_required], name='dispatch')
class UserLogListView(ListView):
    model = UserLog
    context_object_name = 'logs'
    extra_context = {
        'title': 'User Log',
        'sidebar': 'user_log'
    }
    template_name = 'classroom/staff/user_log_list.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        kwargs['course_request_count'] = Course.objects.values_list('id', flat=True).filter(status='pending').count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return UserLog.objects.filter(is_active=True).order_by('-id')


@login_required
@staff_required
def accept_course(request, course_pk):
    """Sets the status of the course to Approved given the course id."""
    Course.objects.filter(id=course_pk).update(status='approved')

    messages.success(request, 'The course has been successfully approved.')
    return redirect('staff:course_requests')


@login_required
@staff_required
def account(request):
    if request.method == 'POST':
        user_update_form = UserUpdateForm(request.POST, instance=request.user)

        if user_update_form.is_valid():
            user_update_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('staff:account')

    else:
        user_update_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': user_update_form,
        'title': 'My Profile',
        'course_request_count': Course.objects.values_list('id', flat=True).filter(status='pending').count()
    }

    return render(request, 'classroom/staff/account.html', context)


@login_required
@staff_required
def dashboard(request):
    context = {
        'title': 'Admin',
        'sidebar': 'dashboard',
        'course_request_count': Course.objects.values_list('id', flat=True).filter(status='pending').count(),
        'courses_count': Course.objects.values_list('id', flat=True)
                                       .filter(status__iexact='approved').count(),
        'students_count': User.objects.values_list('id', flat=True)
                                      .filter(is_student=True, is_active=True).count(),
        'teachers_count': User.objects.values_list('id', flat=True)
                                      .filter(is_teacher=True, is_active=True).count(),
        'quizzes_count': Quiz.objects.values_list('id', flat=True)
                                     .exclude(course__status='deleted').count(),
        'latest_user_log': UserLog.objects.all().order_by('-id')[:6],
        'popular_courses': Course.objects.raw(get_popular_courses()),
    }
    return render(request, 'classroom/staff/dashboard.html', context)


@login_required
@superuser_required
def deactivate_admin(request, pk):
    User.objects.filter(id=pk).update(is_active=False)

    messages.success(request, 'The admin account has been successfully deleted.')
    return redirect('staff:admin_list')


@login_required
@staff_required
def deactivate_student(request, pk):
    User.objects.filter(id=pk).update(is_active=False)

    messages.success(request, 'The student account has been successfully deleted.')
    return redirect('staff:student_list')


@login_required
@staff_required
def deactivate_teacher(request, pk):
    User.objects.filter(id=pk).update(is_active=False)

    messages.success(request, 'The teacher account has been successfully deleted.')
    return redirect('staff:teacher_list')


@login_required
@staff_required
def delete_course(request, course_pk):
    """Sets the status of the course to Deleted given the course id."""
    Course.objects.filter(id=course_pk).update(status='deleted')

    messages.success(request, 'The course has been successfully deleted.')
    return redirect('staff:course_list')


@login_required
@staff_required
def delete_log(request, pk):
    """Permanently deletes the log from the table"""
    UserLog.objects.filter(id=pk).delete()

    messages.success(request, 'The log has been successfully deleted.')
    return redirect('staff:user_log_list')


@login_required
@staff_required
def delete_subject(request, pk):
    Subject.objects.filter(id=pk).delete()

    messages.success(request, 'The subject has been successfully deleted.')
    return redirect('staff:subject_list')


@login_required
@staff_required
def get_course_status(request):
    status_grp_by = tuple(Course.objects.values_list('status')
                          .annotate(status_count=Count('status'))
                          .order_by('status'))

    status_list = []
    status_count_list = []

    for i in status_grp_by:
        status_list.append(i[0])
        status_count_list.append(i[1])

    data = {
        'status_label': status_list,
        'status_count': status_count_list
    }

    return JsonResponse(data)


@login_required
@staff_required
def get_user_activities(request):
    select_data = {"action_date": "strftime('%%m-%%d-%%Y', datetime(created_at, 'localtime'))"}
    action_dates = list(reversed(UserLog.objects.extra(select=select_data)
                                 .values_list('action_date')
                                 .distinct()
                                 .order_by('-action_date')[:7]))
    student = list(reversed(UserLog.objects.extra(select=select_data)
                            .values_list('action_date')
                            .filter(user_type='student')
                            .exclude(user_type='admin')
                            .annotate(action_count=Count('id'))
                            .order_by('-action_date')[:7]))
    teacher = list(reversed(UserLog.objects.extra(select=select_data)
                            .values_list('action_date')
                            .filter(user_type='teacher')
                            .exclude(user_type='admin')
                            .annotate(action_count=Count('id'))
                            .order_by('-action_date')[:7]))

    student_list = []
    teacher_list = []
    date_list = []

    for tuple_l in student:
        student_list.append(tuple_l[1])

    for tuple_l in teacher:
        teacher_list.append(tuple_l[1])

    for tuple_l in action_dates:
        date_list.append(tuple_l[0])

    data = {
        'student': student_list,
        'teacher': teacher_list,
        'date_label': date_list
    }

    return JsonResponse(data)


@login_required
@staff_required
def reject_course(request, course_pk):
    """Sets the status of the course to Rejected given the course id."""
    Course.objects.filter(id=course_pk).update(status='rejected')

    messages.success(request, 'The course has been successfully rejected.')
    return redirect('staff:course_requests')
