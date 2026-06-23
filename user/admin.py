from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Question

admin.site.register(User, UserAdmin)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('title', 'user__email')