from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm, TaskForm
from .models import Task


def register(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome, {user.username}! Your account has been created.')
        return redirect('task_list')
    return render(request, 'registration/register.html', {'form': form})


def _get_own_task(request, pk):
    """get(): fetch exactly one task, but only if it belongs to the logged-in user."""
    try:
        return Task.objects.get(pk=pk, user=request.user)
    except Task.DoesNotExist:
        raise Http404('Task not found')


@login_required
def task_list(request):
    today = timezone.localdate()

    # filter(): ONLY the logged-in user's tasks
    my_tasks = Task.objects.filter(user=request.user)

    # Dashboard counters
    stats = {
        'total': my_tasks.count(),
        'pending': my_tasks.filter(status='pending').count(),
        'in_progress': my_tasks.filter(status='in_progress').count(),
        'completed': my_tasks.filter(status='completed').count(),
        # filter() + exclude(): past due and not completed
        'overdue': my_tasks.filter(due_date__lt=today).exclude(status='completed').count(),
    }

    tasks = my_tasks

    # filter(): status / priority from the query string
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)

    # exclude(): hide completed tasks
    hide_completed = request.GET.get('hide_completed') == 'on'
    if hide_completed:
        tasks = tasks.exclude(status='completed')

    # order_by(): soonest due date first
    tasks = tasks.order_by('due_date')

    context = {
        'tasks': tasks,
        'stats': stats,
        'today': today,
        'status': status,
        'priority': priority,
        'hide_completed': hide_completed,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'filters_active': bool(status or priority or hide_completed),
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, pk):
    task = _get_own_task(request, pk)
    return render(request, 'tasks/task_detail.html', {'task': task, 'today': timezone.localdate()})


@login_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        messages.success(request, 'Task created.')
        return redirect('task_list')
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'New task'})


@login_required
def task_update(request, pk):
    task = _get_own_task(request, pk)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Task updated.')
        return redirect('task_list')
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Edit task'})


@login_required
@require_POST
def task_complete(request, pk):
    task = _get_own_task(request, pk)
    task.status = 'completed'
    task.save(update_fields=['status'])
    messages.success(request, f'"{task.title}" marked as completed.')
    return redirect(request.POST.get('next') or 'task_list')


@login_required
def task_delete(request, pk):
    task = _get_own_task(request, pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})
