from django.urls import path
from . import views

app_name = 'circles'

job_view = views.JobView.as_view()
person_view = views.PersonView.as_view()

urlpatterns = [
    path('person/<int:contact_id>/', person_view, name='person'),
    path('person/me/', person_view, name='person-me'),
    path('person/import/', views.csv_import, name='person-import'),
    path('person/export/', views.csv_export, name='person-export'),
    path('person/autocomplete/', views.ContactAutocomplete.as_view(), name='person-autocomplete'),
    path('person/find/', views.FindFormView.as_view(), name='find-person'),
]
