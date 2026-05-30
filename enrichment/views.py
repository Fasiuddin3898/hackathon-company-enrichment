from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render

from .models import Company
from .serializers import CompanySerializer
from .scraper import enrich_company

@api_view(["POST"])
def enrich(request):

    urls = request.data.get("urls")

    if not urls:
        return Response(
            {"error": "urls required"},
            status=400
        )

    results = []

    for url in urls:

        try:

            data = enrich_company(url)

            company = Company.objects.create(
                url=url,
                website_name=data.get("website_name", ""),
                company_name=data.get("company_name", ""),
                address=data.get("address", ""),
                mobile_number=data.get("mobile_number", ""),
                mail=data.get("mail", []),
                core_service=data.get("core_service", ""),
                target_customer=data.get("target_customer", ""),
                probable_pain_point=data.get(
                    "probable_pain_point", ""
                ),
                outreach_opener=data.get(
                    "outreach_opener", ""
                )
            )

            results.append(
                CompanySerializer(company).data
            )

        except Exception as e:

            results.append({
                "url": url,
                "error": str(e)
            })

    return Response(results)
    
@api_view(["GET"])
def results(request):

    companies = Company.objects.all()

    serializer = CompanySerializer(
        companies,
        many=True
    )

    return Response(serializer.data)

def home(request):
    return render(
        request,
        "index.html"
    )