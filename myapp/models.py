from django.db import models
from django.utils import timezone



# =====================================================
# Custom User Model 
# =====================================================
class CustomerUser(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('banned', 'Banned'),
    )

    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        blank=True,
        null=True
    )
    dob = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username



from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class HealthRecord(models.Model):

    user = models.ForeignKey("CustomerUser", on_delete=models.CASCADE)

    date = models.DateField(default=timezone.now)

    weight = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(300)]
    )

    systolic_bp = models.IntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(250)]
    )

    diastolic_bp = models.IntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(150)]
    )

    sugar_level = models.FloatField(
        validators=[MinValueValidator(50), MaxValueValidator(500)]
    )

    sleep_hours = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(24)]
    )

    exercise_minutes = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(600)]
    )

    stress_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"