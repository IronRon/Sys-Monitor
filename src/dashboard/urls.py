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

    path(
        "memory/",
        views.memory_page,
        name="memory",
    ),

    path(
        "api/memory/",
        views.memory_api,
        name="memory-api",
    ),

    path(
        "disk/",
        views.disk_page,
        name="disk",
    ),

    path(
        "api/disk/",
        views.disk_api,
        name="disk-api",
    ),

    path(
        "network/",
        views.network_page,
        name="network",
    ),

    path(
        "api/network/",
        views.network_api,
        name="network-api",
    ),

    path(
        "api/self/",
        views.self_monitor_api,
        name="self-monitor-api",
    ),
]