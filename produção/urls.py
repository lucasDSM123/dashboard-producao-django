"""
URL configuration for produção project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from cadastro import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('buscar-obra/', views.index, name='index'),
    path('materiais-cadastrados/', views.materiais_cadastrados, name='materiais cadastrados'),
    path('excluir-material/<int:material_id>/', views.excluir_material, name='excluir_material'), # Nova rota
    path('exportar-excel/<str:numero_obra>/', views.exportar_excel, name='exportar_excel'),
    path('todas-as-obras/', views.lista_obras, name='lista_obras'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('editar/<int:pk>/', views.editar_material, name='editar_material'),
    path('excluir/<int:pk>/', views.excluir_material, name='excluir_material'),
]