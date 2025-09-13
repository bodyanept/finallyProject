from django.shortcuts import render
from apps.catalog.models import Product


def home(request):
    featured = Product.objects.order_by('-created_at')[:8]
    context = {
        "title": "ZapChasti — учебный проект",
        "featured": featured,
    }
    return render(request, "home.html", context)
