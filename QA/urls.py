from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_page, name="upload"),
    path("analyze/", views.analyze, name="analyze"),
    path("history/", views.history, name="history"),
]
