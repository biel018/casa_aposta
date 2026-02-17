from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('wallet/', include('wallet.urls')),
    path('betting/', include('betting.urls')),
    path('api/', include('betting.api_urls')),
    path('predictions/', include('predictions.urls')),
    path('api/predictions/', include('predictions.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customização do Admin
admin.site.site_header = 'Casa de Apostas - Admin'
admin.site.site_title = 'Casa de Apostas'
admin.site.index_title = 'Painel Administrativo'
