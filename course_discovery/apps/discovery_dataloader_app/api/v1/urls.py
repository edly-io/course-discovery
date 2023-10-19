from discovery_dataloader_app.api.v1.views import dataloader_api
from django.urls import path
from rest_framework import routers

app_name = 'v1'

urlpatterns = [
    path('dataloader/', dataloader_api.DiscoveryDataLoaderView.as_view(), name='discovery_dataloader'),
]

router = routers.SimpleRouter()
router.register(r'search/course_runs', dataloader_api.DataLoaderCourseRunSearchViewSet, basename='search-course_runs')

urlpatterns += router.urls
