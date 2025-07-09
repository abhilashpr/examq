from django.contrib import admin
from .models import ExamQuestionPDFs, QuestionList, UserAnswer

admin.site.register(ExamQuestionPDFs)
admin.site.register(QuestionList)
admin.site.register(UserAnswer)

# Register your models here.
