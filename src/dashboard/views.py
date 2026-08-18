from django.http import JsonResponse
from django.shortcuts import render

from .services import monitoring_service


def index(request):

    monitoring_service.start()

    return render(
        request,
        "dashboard/index.html",
    )


def processes_page(request):

    monitoring_service.start()

    return render(
        request,
        "dashboard/processes.html",
    )


def system_api(request):

    data = (
        monitoring_service
        .get_system_data()
    )

    return JsonResponse(data)


def processes_api(request):

    data = (
        monitoring_service
        .get_process_data()
    )

    return JsonResponse(data)