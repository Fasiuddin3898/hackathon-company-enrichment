from django.db import models

class Company(models.Model):

    url = models.URLField()

    website_name = models.CharField(max_length=255)

    company_name = models.CharField(max_length=255)

    address = models.TextField(blank=True)

    mobile_number = models.CharField(
        max_length=100,
        blank=True
    )

    mail = models.JSONField(default=list)

    core_service = models.TextField(blank=True)

    target_customer = models.TextField(blank=True)

    probable_pain_point = models.TextField(blank=True)

    outreach_opener = models.TextField(blank=True)