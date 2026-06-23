from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from user.serializers import UserRegisterSerializer, UserLoginSerializer
import time
from django.core.files.base import ContentFile
from user.models import Question

User = get_user_model()

class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Пользователь зарегистрирован!"}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            username=serializer.validated_data['email'], 
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response({"error": "Неверный email или пароль"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Успешный вход",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class RegisterPage(View):
    template_name = 'register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        data = {
            "email": request.POST.get("email"), 
            "password": request.POST.get("password")
        }
        
        serializer = UserRegisterSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return redirect(reverse('login_page'))

        return render(request, self.template_name, {"errors": serializer.errors})
    

class LoginPage(View):
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            errors = {"__all__": ["Неверный email или пароль."]}
            return render(request, self.template_name, {"errors": errors})
        

def draw_graph_to_png(function_str):
    plt.clf()
    plt.close('all')
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    func = function_str.replace("y", "").replace("=", "").strip()
    
    x_values = []
    y_values = []
    
    x = -20.0
    while x <= 20.0:
        safe_x = round(x, 2)
        try:
            context = {
                "x": safe_x,
                "sin": np.sin,
                "cos": np.cos,
                "tan": np.tan,
                "sqrt": np.sqrt,
                "pi": np.pi
            }
            
            val = eval(func, {"__builtins__": None}, context)
            
            if abs(val) > 40:
                y_values.append(np.nan)
            else:
                y_values.append(val)
        except ZeroDivisionError:
            y_values.append(np.nan)
        except Exception:
            y_values.append(np.nan)
            
        x_values.append(safe_x)
        x += 0.1

    ax.grid(True, which='both', color='lightgray', linestyle='-', linewidth=0.5)
    
    ax.set_xlim([-20, 20])
    ax.set_ylim([-20, 20])
    
    ax.set_xticks(np.arange(-20, 21, 2))
    ax.set_yticks(np.arange(-20, 21, 2))

    ax.axhline(0, color='black', linewidth=2)
    ax.axvline(0, color='black', linewidth=2)
    
    ax.plot(x_values, y_values, color='red', linewidth=3, zorder=3)
    
    ax.set_title(f"y = {func}", fontsize=14, color='#2c3e50')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    
    return buffer.getvalue()

class HomePage(View):
    def get(self, request):
        if request.user.is_authenticated:
            search_query = request.GET.get("q", "").strip()
            all_questions = request.user.questions.all().order_by('-id')
            
            if search_query:
                history = all_questions.filter(title__icontains=search_query)
            else:
                history = all_questions
            
            latest_graph = all_questions.first()
            
            context = {
                "history": history,
                "search_query": search_query,
                "latest_graph": latest_graph
            }
            return render(request, 'index.html', context)
        else:
            return render(request, 'home.html')

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_page')
            
        function_str = request.POST.get('function_str', '').strip()
        all_questions = request.user.questions.all().order_by('-id')
        
        if not function_str:
            return render(request, 'index.html', {
                'error': 'Поле функции не может быть пустым',
                'history': all_questions,
                'latest_graph': all_questions.first()
            })

        try:
            image_bytes = draw_graph_to_png(function_str)
            new_graph = Question(user=request.user, title=function_str)
            filename = f"graph_{request.user.id}_{int(time.time())}.png"
            new_graph.graph_image.save(filename, ContentFile(image_bytes), save=False)
            new_graph.save()

            return redirect('home_page')
            
        except Exception as e:
            return render(request, 'index.html', {
                'error': f'Ошибка визуализации: {str(e)}',
                'history': all_questions,
                'latest_graph': all_questions.first()
            })

class LogoutPage(View):
    def get(self, request):
        logout(request)
        return redirect('/')