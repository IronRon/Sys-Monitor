from django.http import JsonResponse
from django.shortcuts import render

from .services import (
    monitoring_service,
    hardware_service,
)


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

def hardware_page(request):

    return render(
        request,
        "dashboard/hardware.html",
    )


def hardware_api(request):

    data = hardware_service.get_hardware_data()


    return JsonResponse(
        data
    )