from django.http import JsonResponse
from django.shortcuts import render

from .services import (
    monitoring_service,
    process_service,
)


def index(request):
    return render(
        request,
        "dashboard/index.html",
    )


def system_api(request):
    data = monitoring_service.get_system_data()

    return JsonResponse(data)


def processes_page(request):
    return render(
        request,
        "dashboard/processes.html",
    )


def processes_api(request):
    data = process_service.get_process_data()

    return JsonResponse(data)