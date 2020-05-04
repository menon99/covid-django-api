from django.urls import path
from .views import *


urlpatterns = [
    path('hello/', hello),
    path('rnaught/<str:state>/', getR0),
    path('growth/india', getGrowthIndia),
    path('growth/<str:state>', getGrowth),
    path('arima/india', indiaArima),
    path('arima/<str:state>', stateArima),
    path('update/rnaught/<int:num>', updateR0),
    path('update/growth', updateGrowth),
]
