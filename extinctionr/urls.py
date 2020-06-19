"""extinctionr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.core import urls as wagtail_urls

# from django.contrib.auth import views
from extinctionr.actions.views import propose_talk


app_name = 'extinctionr'

urlpatterns = [
    path('talk', propose_talk),
    path('', include('django.contrib.auth.urls')),
    path('action/', include('extinctionr.actions.urls', namespace="actions")),
    path('circle/', include('extinctionr.circles.urls', namespace="circles")),
    path('relationships/', include('common.urls', namespace="common")),
    path('relationships/m/', include('marketing.urls', namespace="marketing")),
    path('relationships/accounts/', include('accounts.urls', namespace="accounts")),
    path('relationships/leads/', include('leads.urls', namespace="leads")),
    path('relationships/contacts/', include('contacts.urls', namespace="contacts")),
    path('relationships/opportunities/',
         include('opportunity.urls', namespace="opportunities")),
    path('relationships/cases/', include('cases.urls', namespace="cases")),
    path('relationships/emails/', include('emails.urls', namespace="emails")),
    path('xadmin/', admin.site.urls),
    path('notifications/', include('django_nyt.urls')),
    path('wiki/', include('wiki.urls')),
    path('markdownx/', include('markdownx.urls')),
    path('todo/', include('todo.urls', namespace="todo")),
    path('postorius/', include('postorius.urls')),
    path('mm/', include('django_mailman3.urls')),
    path('accounts/', include('allauth.urls')),
    re_path(r'^admin/', include(wagtailadmin_urls)),
    re_path(r'^documents/', include(wagtaildocs_urls)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    print(settings.MEDIA_ROOT, settings.MEDIA_URL)
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls))
        ] + urlpatterns
    except ImportError:
        pass

urlpatterns += [
    path('', include('extinctionr.info.urls', namespace='extinctionr.info')),
    path('', include(wagtail_urls)),
]
