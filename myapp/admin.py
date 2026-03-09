from django.contrib import admin
from .models import CustomerUser, HealthRecord

# =========================
# CustomerUser Admin
# =========================
@admin.register(CustomerUser)
class CustomerUserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'full_name', 'email', 'gender', 'status', 'last_login', 'created_at'
    )
    list_filter = ('status', 'gender', 'country')
    search_fields = ('username', 'full_name', 'email', 'phone')
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    ordering = ('username',)
    fieldsets = (
        ('Account Info', {
            'fields': ('username', 'email', 'password', 'status')
        }),
        ('Personal Info', {
            'fields': ('full_name', 'profile_image', 'bio', 'phone', 'gender', 'dob', 'country')
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )


# =========================
# HealthRecord Admin
# =========================
@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date', 'weight', 'systolic_bp', 'diastolic_bp', 
        'sugar_level', 'sleep_hours', 'exercise_minutes', 'stress_level', 'created_at'
    )
    list_filter = ('date', 'user')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    ordering = ('-date',)
    date_hierarchy = 'date'