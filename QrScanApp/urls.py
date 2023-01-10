from django.urls import path
from . import views
urlpatterns = [
       path('inv',views.InvPdf, name='inv'),
       path('ewaybill',views.EwayBillPdf, name='ewaybill')
]