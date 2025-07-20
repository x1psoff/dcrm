from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Record

def home(request):
    records = Record.objects.all()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        #подлиность(айтификация
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Вход в сс')
            return redirect('home')
        else:
            messages.success(request,'Ошибка входа')
            return redirect('home')
    else:
        return render(request, 'home.html',{'records': records})


def custom_record(request,pk):
    if request.user.is_authenticated:
        customer_record=Record.objects.get(id=pk)
        return render(request, 'home.html', {'records': records})




def logout_user(request):
    logout(request)
    messages.success(request,'Выход')
    return redirect('home')


