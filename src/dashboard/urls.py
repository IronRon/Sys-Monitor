from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),

    path(
        "api/system/",
        views.system_api,
        name="system-api",
    ),
]