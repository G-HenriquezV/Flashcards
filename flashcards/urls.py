from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name="home.html"), name='home'),
    path('account/', include('flashcards.users.urls', namespace='users')),
    path('flashcards/', include('flashcards.flashes.urls', namespace='flashes'))
]
