from django.urls import path
from . import views

urlpatterns = [
    path('calculator/', views.tax_calculator, name='tax_calculator'),
    path('api/calculate/', views.calculate_tax_contribution, name='calculate_tax_contribution'),
    path('api/grant-share/<int:grant_id>/', views.grant_share_calculator, name='grant_share_calculator'),
]