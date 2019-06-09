from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from ..decorators import staff_required, superuser_required
from ..forms import AdminAddForm, SubjectUpdateForm
from ..models import Course, Subject, User


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


@method_decorator([login_required, superuser_required], name='dispatch')
class AdminListView(ListView):
    model = User
    context_object_name = 'admins'
    extra_context = {
        'title': 'Admin Accounts',
        'sidebar': 'admin_list'
    }
    template_name = 'classroom/staff/admin_list.html'

    def get_queryset(self):
        """Gets all the admin/staff accounts but not the superuser."""
        return User.objects.filter(is_staff=True, is_active=True) \
            .exclude(is_superuser=True) \
            .order_by('username')


@method_decorator([login_required, staff_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    context_object_name = 'courses'
    extra_context = {
        'title': 'Courses',
        'sidebar': 'course_list'
    }
    template_name = 'classroom/staff/course_list.html'

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


@method_decorator([login_required, staff_required], name='dispatch')
class SubjectListView(ListView):
    model = Subject
    context_object_name = 'subjects'
    extra_context = {
        'title': 'Subjects',
        'sidebar': 'subject_list'
    }
    template_name = 'classroom/staff/subject_list.html'

    def get_queryset(self):
        """Gets all the approved courses."""
        return Subject.objects.all().order_by('name')


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

    def get_queryset(self):
        """Gets all the teacher accounts."""
        return User.objects.filter(is_teacher=True, is_active=True) \
            .order_by('username')


@login_required
@staff_required
def accept_course(request, course_pk):
    """Sets the status of the course to Approved given the course id."""
    Course.objects.filter(id=course_pk).update(status='approved')

    messages.success(request, 'The course has been successfully approved.')
    return redirect('staff:course_requests')


@login_required
@staff_required
def dashboard(request):
    context = {
        'title': 'Admin',
        'sidebar': 'dashboard'
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
def delete_subject(request, pk):
    Subject.objects.filter(id=pk).delete()

    messages.success(request, 'The subject has been successfully deleted.')
    return redirect('staff:subject_list')


@login_required
@staff_required
def reject_course(request, course_pk):
    """Sets the status of the course to Rejected given the course id."""
    Course.objects.filter(id=course_pk).update(status='rejected')

    messages.success(request, 'The course has been successfully rejected.')
    return redirect('staff:course_requests')
