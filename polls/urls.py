from django.urls import path

from . import views

app_name = "polls"

urlpatterns = [
    path("", views.index, name="index"),
    path("anket/olustur/", views.create, name="create"),
    path("anket/<str:public_id>/", views.detail, name="detail"),
    path("anket/<str:public_id>/oy/", views.vote, name="vote"),
    path("anket/<str:public_id>/sonuc/", views.results, name="results"),
    path("anket/<str:public_id>/kapat/", views.close, name="close"),
    path("anket/<str:public_id>/sil/", views.delete, name="delete"),
    path("kullanici/<str:username>/", views.profile, name="profile"),
]
