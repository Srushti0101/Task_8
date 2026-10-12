# Django Task Manager

## Run
    pip install django
    python manage.py migrate        # REQUIRED the first time (creates tables)
    python manage.py createsuperuser   # optional (admin)
    python manage.py runserver
(On Windows you can also double-click run.bat)
Open http://127.0.0.1:8000/ -> Sign up -> add tasks.

## Where each concept is used (tasks/views.py)
| Requirement | Code |
|---|---|
| User -> Task relationship | `user = ForeignKey(User, related_name='tasks')` in models.py |
| Only logged-in user's tasks | `Task.objects.filter(user=request.user)` + `@login_required` |
| Filter by status/priority | `.filter(status=...)`, `.filter(priority=...)` from `?status=&priority=` |
| exclude() | `.exclude(status='completed')` ("Hide completed" checkbox) |
| get() | `Task.objects.get(pk=pk, user=request.user)` in `_get_own_task` |
| order_by() | `.order_by('due_date')` |

## Practice in the shell (python manage.py shell)
    from django.contrib.auth.models import User
    from tasks.models import Task
    u = User.objects.get(username='alice')          # get()
    u.tasks.all()                                   # reverse relation
    Task.objects.filter(user=u, status='pending')   # filter()
    Task.objects.filter(user=u, priority=3, status='pending')
    Task.objects.filter(user=u).exclude(status='completed')   # exclude()
    Task.objects.filter(user=u).order_by('due_date')          # ascending
    Task.objects.filter(user=u).order_by('-due_date')         # descending
    Task.objects.filter(user=u).order_by('-priority', 'due_date')
    Task.objects.get(pk=1)                          # DoesNotExist if missing
