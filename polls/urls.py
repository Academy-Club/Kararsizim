from django.urls import path

from . import views

app_name = "polls"

urlpatterns = [
    path("", views.index, name="index"),
    path("anket/olustur/", views.create, name="create"),
    path("anket/<str:public_id>/", views.detail, name="detail"),
    path("kullanici/<str:username>/", views.profile, name="profile"),
]
