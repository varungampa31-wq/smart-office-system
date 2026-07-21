from django.db import models


class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ("IT", "Information Technology"),
        ("HR", "Human Resources"),
        ("Finance", "Finance"),
        ("Admin", "Administration"),
        ("Security", "Security"),
    ]

    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
    )

    rfid_tag = models.CharField(
        max_length=50,
        unique=True,
    )

    fingerprint_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    face_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["employee_id"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"