"""
Seeds a handful of demo employees with known RFID tags so the RFID
sensor simulator (sensor_simulators/) has real tags to "scan" and the
scanner.html frontend page has someone to check in/out.

Also creates a demo Django User (username: admin / password: admin123)
so the frontend login page (total_frontend/frontend/index.html) has
something to authenticate against. This is intentionally separate from
Employee -- the frontend's JWT login is a Django auth User (a "who can
use this dashboard" account), not an Employee (a "who gets tracked by
sensors" record). Nothing else in the codebase links the two.

Usage:
    python manage.py seed_demo
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from employees.models import Employee

DEMO_EMPLOYEES = [
    dict(employee_id="EMP001", first_name="Aoife", last_name="Byrne",
         email="aoife.byrne@example.com", department="IT", rfid_tag="RFID-A1001"),
    dict(employee_id="EMP002", first_name="Sean", last_name="Murphy",
         email="sean.murphy@example.com", department="Finance", rfid_tag="RFID-A1002"),
    dict(employee_id="EMP003", first_name="Niamh", last_name="Kelly",
         email="niamh.kelly@example.com", department="HR", rfid_tag="RFID-A1003"),
    dict(employee_id="EMP004", first_name="Cian", last_name="Doyle",
         email="cian.doyle@example.com", department="Security", rfid_tag="RFID-A1004"),
    dict(employee_id="EMP005", first_name="Grace", last_name="Walsh",
         email="grace.walsh@example.com", department="Admin", rfid_tag="RFID-A1005"),
]

DEMO_ADMIN_USERNAME = "admin"
DEMO_ADMIN_PASSWORD = "admin123"


class Command(BaseCommand):
    help = "Seed demo employees + a demo admin login for the frontend/scanner demo."

    def handle(self, *args, **options):
        created_count = 0
        for data in DEMO_EMPLOYEES:
            obj, created = Employee.objects.get_or_create(
                employee_id=data["employee_id"],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created {obj}"))
            else:
                self.stdout.write(f"Already exists: {obj}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created_count} new employee(s) created, {len(DEMO_EMPLOYEES) - created_count} already existed."
        ))

        if not User.objects.filter(username=DEMO_ADMIN_USERNAME).exists():
            User.objects.create_superuser(
                username=DEMO_ADMIN_USERNAME,
                email="admin@example.com",
                password=DEMO_ADMIN_PASSWORD,
            )
            self.stdout.write(self.style.SUCCESS(
                f"Created demo login -> username: {DEMO_ADMIN_USERNAME}  password: {DEMO_ADMIN_PASSWORD}"
            ))
        else:
            self.stdout.write(
                f"Demo login already exists -> username: {DEMO_ADMIN_USERNAME}  password: {DEMO_ADMIN_PASSWORD}"
            )
        self.stdout.write(self.style.WARNING(
            "This is a demo-only account with a hardcoded password -- fine for local/coursework "
            "use, do not seed it in anything resembling a production or publicly reachable deployment."
        ))
