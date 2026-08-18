from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),

    path(
        "processes/",
        views.processes_page,
        name="processes",
    ),

    path(
        "api/system/",
        views.system_api,
        name="system-api",
    ),

    path(
        "api/processes/",
        views.processes_api,
        name="processes-api",
    ),

    path(
        "hardware/",
        views.hardware_page,
        name="hardware",
    ),

    path(
        "api/hardware/",
        views.hardware_api,
        name="hardware-api",
    ),
]