from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'applicant', 'status', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('job__title', 'applicant__username', 'applicant__email')
