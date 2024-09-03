from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.shortcuts import redirect
from django.shortcuts import render

from .forms import LoginForm
from .forms import SignUpForm


def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":
        # with connection.cursor() as cursor:
        #     # 删除已有的用户记录（如果存在）
        #     cursor.execute("DELETE FROM home_customuser WHERE username IN ('1', '2')")
        #     cursor.execute("DELETE FROM home_customuser WHERE username BETWEEN '3' AND '9'")
        #
        #     # 插入1个管理员
        #     cursor.execute("""
        #         INSERT INTO home_customuser (username, password, role, is_superuser, is_staff, is_active, first_name, last_name, email, date_joined)
        #         VALUES ('1', %s, 'admin', 0, 1, 1, "", "", "", datetime('now'))
        #     """, [make_password('Longtai@8888')])
        #
        #     # 插入1个质检员
        #     cursor.execute("""
        #         INSERT INTO home_customuser (username, password, role, is_superuser, is_staff, is_active, first_name, last_name, email, date_joined)
        #         VALUES ('2', %s, 'inspector', 0, 1, 1, "", "", "", datetime('now'))
        #     """, [make_password('Longtai@8888')])
        #
        #     # 插入7个操作员
        #     for i in range(3, 10):
        #         cursor.execute("""
        #             INSERT INTO home_customuser (username, password, role, is_superuser, is_staff, is_active, first_name, last_name, email, date_joined)
        #             VALUES (%s, %s, 'operator', 0, 1, 1, "", "", "", datetime('now'))
        #         """, [str(i), make_password('Longtai@8888')])

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True

            # return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})
