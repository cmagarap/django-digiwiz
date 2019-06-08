from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from ..decorators import staff_required
from ..models import Course


class CourseRequestsView(ListView):
    model = Course
    context_object_name = 'courses'
    extra_context = {
        'title': 'Course Requests',
        'sidebar': 'course_requests'
    }
    template_name = 'classroom/staff/course_requests_list.html'

    def get_context_data(self, **kwargs):
        kwargs['courses'] = Course.objects \
            .filter(status__iexact='pending') \
            .order_by('-updated_at')

        return super().get_context_data(**kwargs)


@login_required
@staff_required
def accept_course(request, course_pk):
    Course.objects.filter(id=course_pk).update(status='Approved')

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
@staff_required
def reject_course(request, course_pk):
    Course.objects.filter(id=course_pk).update(status='Rejected')

    messages.success(request, 'The course has been successfully rejected.')
    return redirect('staff:course_requests')
