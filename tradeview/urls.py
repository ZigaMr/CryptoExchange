from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(r'refresh_orderbook/', views.refresh_orderbook, name='refresh_orderbook'),
    path(r'signup/', views.signup, name='signup'),
    path(r'trade_page/', views.trade_page, name='trade_page'),
    path(r'refresh_table/', views.refresh_table, name='refresh_table'),
    path(r'trade_page/update_session/', views.update_session, name='update_session'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)