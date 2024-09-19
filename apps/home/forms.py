# myapp/forms.py

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Process
from .models import Task


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "用户名",
                "class": "form-control"
            }
        )
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "手机号",
                "class": "form-control"
            }
        )
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,  # 确保引用模型中的 ROLE_CHOICES
        widget=forms.Select(
            attrs={
                "class": "form-control"
            }
        )
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "密码",
                "class": "form-control"
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "确认密码",
                "class": "form-control"
            }
        )
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'role', 'password1', 'password2')

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        if commit:
            user.email = 'default@example.com'  # 设置默认邮箱
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'role', 'is_active', 'is_staff', 'is_superuser')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'role')


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'task_start_time',
            'task_end_time',
            'order_code',
            'product_code',
            'process_i',
            'process_name',
            'device_name'
        ]
        widgets = {
            'task_start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'task_end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['task_start_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['task_end_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['order_code'].widget.attrs.update({'class': 'form-control'})
        self.fields['product_code'].widget.attrs.update({'class': 'form-control'})
        self.fields['process_i'].widget.attrs.update({'class': 'form-control'})
        self.fields['process_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['device_name'].widget.attrs.update({'class': 'form-control'})

class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ['process_i','process_name', 'process_capacity', 'process_duration', 'product_code', 'device_name', 'is_outside', 'is_last_process']
        widgets = {
            'is_outside': forms.RadioSelect(),
            'is_last_process': forms.RadioSelect(),
        }