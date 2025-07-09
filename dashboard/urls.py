from django.urls import path
from . import views

urlpatterns = [
    # Admin routes (original functionality)
    path('', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('logout/', views.user_logout, name='logout'),
    path('extract_questions/<int:pdf_id>/', views.extract_questions, name='extract_questions'),
    path('questions/', views.question_list, name='question_list'),
    path('questions/edit/<int:question_id>/', views.edit_question, name='edit_question'),
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.add_user, name='add_user'),
    
    # User exam routes
    path('exam/', views.user_exam_login, name='exam_home'),
    path('exam/login/', views.user_exam_login, name='user_exam_login'),
    path('exam/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('exam/take/', views.take_exam, name='take_exam'),
    path('exam/history/', views.exam_history, name='exam_history'),
] 