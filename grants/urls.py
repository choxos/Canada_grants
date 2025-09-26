from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Domestic Grants
    path('grants/', views.grant_list, name='grant_list'),
    path('grants/<int:pk>/', views.grant_detail, name='grant_detail'),
    path('major-funding/', views.major_funding, name='major_funding'),
    path('notable/', views.notable_grants, name='notable_grants'),
    path('statistics/', views.statistics_page, name='statistics'),
    
    # Global Affairs Canada (GAC) Grants
    path('global-affairs/', views.gac_grant_list, name='gac_grant_list'),
    path('global-affairs/<int:pk>/', views.gac_grant_detail, name='gac_grant_detail'),
    path('global-affairs/statistics/', views.gac_statistics, name='gac_statistics'),
    
    # API Documentation
    path('api/', views.api_documentation, name='api_documentation'),
    
    # Domestic Grants API Endpoints
    path('api/stats/', views.grant_stats_api, name='grant_stats_api'),
    path('api/search/', views.grants_search_api, name='grants_search_api'),
    path('api/recipients/', views.recipients_api, name='recipients_api'),
    path('api/comprehensive-stats/', views.comprehensive_stats_api, name='comprehensive_stats_api'),
    
    # GAC Grants API Endpoints
    path('api/gac/stats/', views.gac_stats_api, name='gac_stats_api'),
    path('api/gac/search/', views.gac_search_api, name='gac_search_api'),
]