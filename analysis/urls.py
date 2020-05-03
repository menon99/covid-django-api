from django.urls import path
from .views import *


urlpatterns = [
    path('hello/', hello),
    path('rnaught/<str:state>/', getR0),
    path('growth/india', getGrowthIndia),
    path('growth/<str:state>', getGrowth),
    path('arima/india', indiaArima),
    path('arima/<str:state>', stateArima),
    path('update/rnaught/1', updateR01),
    path('update/rnaught/2', updateR02),
    path('update/growth', updateGrowth),
]
