"""blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
# from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path("", views.view_index),
    path("page/<int:page_num>", views.view_index),
    path("blog/<str:post_name>", views.view_post),
    path("blog/<str:post_name>/<str:attach_name>", views.view_attach),
    path("tags/<str:tag_name>", views.view_tags),
    path("tag:<str:tag_name>", views.view_tags_redirect),
]
