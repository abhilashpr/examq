from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ExamQuestionPDFs
from django.contrib import messages

from django import forms
import os
from PyPDF2 import PdfReader
from .models import QuestionList
from django.contrib.auth import get_user_model
from .models import UserAnswer

class PDFUploadForm(forms.ModelForm):
    class Meta:
        model = ExamQuestionPDFs
        fields = ['title', 'pdf']

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Invalid credentials')
            except User.DoesNotExist:
                messages.error(request, 'User does not exist')
    else:
        form = LoginForm()
    return render(request, 'dashboard/login.html', {'form': form})

def user_exam_login(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('user_dashboard')
                else:
                    messages.error(request, 'Invalid credentials')
            except User.DoesNotExist:
                messages.error(request, 'User does not exist')
    else:
        form = UserLoginForm()
    return render(request, 'dashboard/user_login.html', {'form': form})

def admin_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_superuser)(view_func)
    return decorated_view_func

@admin_required
def dashboard(request):
    pdfs = ExamQuestionPDFs.objects.filter(uploaded_by=request.user)
    return render(request, 'dashboard/dashboard.html', {'pdfs': pdfs})

@login_required
def user_dashboard(request):
    # Get total questions count
    total_questions = QuestionList.objects.count()
    
    # Get user's answer statistics
    user_answers = UserAnswer.objects.filter(user=request.user)
    user_attempted = user_answers.count()
    user_correct = user_answers.filter(is_correct=True).count()
    user_wrong = user_answers.filter(is_correct=False).count()
    
    return render(request, 'dashboard/user_dashboard.html', {
        'total_questions': total_questions,
        'user_attempted': user_attempted,
        'user_correct': user_correct,
        'user_wrong': user_wrong
    })

@admin_required
def upload_pdf(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_obj = form.save(commit=False)
            pdf_obj.uploaded_by = request.user
            pdf_obj.save()
            messages.success(request, 'PDF uploaded successfully!')
            return redirect('dashboard')
    else:
        form = PDFUploadForm()
    return render(request, 'dashboard/upload_pdf.html', {'form': form})

@admin_required
def extract_questions(request, pdf_id):
    pdf_obj = ExamQuestionPDFs.objects.get(id=pdf_id, uploaded_by=request.user)
    if pdf_obj.questions.exists():
        messages.info(request, 'Questions already extracted for this PDF.')
        return redirect('dashboard')
    pdf_path = pdf_obj.pdf.path
    questions = parse_pdf_questions(pdf_path)
    for q in questions:
        QuestionList.objects.create(
            exam_pdf=pdf_obj,
            question_text=q['question'],
            option_a=q['a'],
            option_b=q['b'],
            option_c=q['c'],
            option_d=q['d'],
            answer=q['answer']
        )
    messages.success(request, 'Questions extracted and saved!')
    return redirect('dashboard')

def parse_pdf_questions(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    # Simple parser: expects format like:
    # 1. What is ...?\na) ...\nb) ...\nc) ...\nd) ...\nAnswer: a\n
    import re
    pattern = re.compile(r"\d+\.\s*(.*?)\n\s*a\)\s*(.*?)\n\s*b\)\s*(.*?)\n\s*c\)\s*(.*?)\n\s*d\)\s*(.*?)\n\s*Answer:\s*([abcd])", re.DOTALL|re.IGNORECASE)
    matches = pattern.findall(text)
    questions = []
    for match in matches:
        questions.append({
            'question': match[0].strip(),
            'a': match[1].strip(),
            'b': match[2].strip(),
            'c': match[3].strip(),
            'd': match[4].strip(),
            'answer': match[5].lower()
        })
    return questions

@admin_required
def question_list(request):
    questions = QuestionList.objects.select_related('exam_pdf').all().order_by('-id')
    return render(request, 'dashboard/question_list.html', {'questions': questions})

@admin_required
def edit_question(request, question_id):
    question = QuestionList.objects.get(id=question_id)
    if request.method == 'POST':
        question.question_text = request.POST.get('question_text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.answer = request.POST.get('answer')
        question.save()
        messages.success(request, 'Question updated successfully!')
        return redirect('question_list')
    return render(request, 'dashboard/edit_question.html', {'question': question})

@admin_required
def user_list(request):
    User = get_user_model()
    users = User.objects.all().order_by('-id')
    return render(request, 'dashboard/user_list.html', {'users': users})

@admin_required
def add_user(request):
    User = get_user_model()
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        is_staff = bool(request.POST.get('is_staff'))
        is_superuser = bool(request.POST.get('is_superuser'))
        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            messages.success(request, 'User added successfully!')
            return redirect('user_list')
    return render(request, 'dashboard/add_user.html')

@login_required
def take_exam(request):
    if request.method == 'POST':
        # Handle answer submission
        question_id = request.POST.get('question_id')
        user_answer = request.POST.get('answer')
        
        try:
            question = QuestionList.objects.get(id=question_id)
            is_correct = user_answer.lower() == question.answer.lower()
            
            # Save or update user answer
            user_answer_obj, created = UserAnswer.objects.get_or_create(
                user=request.user,
                question=question,
                defaults={
                    'user_answer': user_answer.lower(),
                    'is_correct': is_correct
                }
            )
            
            if not created:
                # Update existing answer
                user_answer_obj.user_answer = user_answer.lower()
                user_answer_obj.is_correct = is_correct
                user_answer_obj.save()
            
            # Show feedback
            if is_correct:
                messages.success(request, 'Correct! Well done!')
            else:
                messages.error(request, f'Wrong! The correct answer is {question.answer.upper()}. Try again!')
            
            return redirect('take_exam')
            
        except QuestionList.DoesNotExist:
            messages.error(request, 'Question not found.')
            return redirect('take_exam')
    
    # Get questions that user hasn't answered correctly yet
    answered_correctly = UserAnswer.objects.filter(user=request.user, is_correct=True).values_list('question_id', flat=True)
    available_questions = QuestionList.objects.exclude(id__in=answered_correctly)
    
    if available_questions.exists():
        import random
        question = random.choice(available_questions)
        return render(request, 'dashboard/take_exam.html', {'question': question})
    else:
        messages.success(request, 'Congratulations! You have answered all questions correctly!')
        return redirect('user_dashboard')

@login_required
def exam_history(request):
    # Get user's exam history
    exam_history = UserAnswer.objects.filter(user=request.user).select_related('question').order_by('-attempted_at')
    
    return render(request, 'dashboard/exam_history.html', {
        'exam_history': exam_history
    })

def user_logout(request):
    logout(request)
    return redirect('login')
