from django.urls import include, path

app_name = 'discovery_dataloader_app'

urlpatterns = [
    path('v1/dataloader_app/', include('course_discovery.apps.discovery_dataloader_app.api.v1.urls')),
]
