from django.http import JsonResponse
from django.shortcuts import render

from .services import monitoring_service


def index(request):
    return render(
        request,
        "dashboard/index.html",
    )


def system_api(request):
    data = monitoring_service.get_system_data()

    return JsonResponse(data)