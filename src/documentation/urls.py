from django.urls import path

from . import views


app_name = "documentation"


urlpatterns = [
    path(
        "",
        views.docs_index,
        name="index",
    ),

    path(
        "<slug:slug>/",
        views.docs_page,
        name="page",
    ),
]