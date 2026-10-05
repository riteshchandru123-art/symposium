from django.urls import path
from . import views

urlpatterns = [
    path("api/reindex", views.api_reindex, name="api_reindex"),
]
