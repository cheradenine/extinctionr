from django.urls import include, path

from . import views

app_name = 'extinctionr.info'

urlpatterns = [
    path('pr/', views.PRListView.as_view(), name='pr-list'),
    path('pr/<str:slug>', views.PRDetailView.as_view(), name='pr-detail'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('contact', views.ContactView.as_view(), name="contact"),
    path('groups/', views.list_chapters, name='groups'),
    path('join/', views.SignupFormView.as_view(), name='join'),
    path('welcome/thankyou', views.serve_thankyou, name='thankyou'),
    path('', views.InfoView.as_view(), kwargs={'page': 'home'}, name='index'),
    views.wrap_info_path(path('<path:page>', views.InfoView.as_view(), name='page')),
]
