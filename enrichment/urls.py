from django.urls import path

from .views import enrich
from .views import results
from .views import home

urlpatterns = [

    path(
        "",
        home,
        name="home"
    ),

    path(
        "enrich/",
        enrich,
        name="enrich"
    ),

    path(
        "results/",
        results,
        name="results"
    ),
]