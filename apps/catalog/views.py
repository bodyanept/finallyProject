from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from .models import Product, Category
from .serializers import ProductSerializer


class DefaultPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = Product.objects.select_related("category").all().order_by("name")
        params = self.request.query_params

        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(sku__icontains=search)
                | Q(manufacturer__icontains=search)
            )

        category = params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        price_min = params.get("price_min")
        if price_min:
            qs = qs.filter(price__gte=price_min)

        price_max = params.get("price_max")
        if price_max:
            qs = qs.filter(price__lte=price_max)

        in_stock = params.get("in_stock")
        if in_stock in {"1", "true", "True"}:
            qs = qs.filter(in_stock__gt=0)

        sort = params.get("sort")
        if sort == "price":
            qs = qs.order_by("price")
        elif sort == "-price":
            qs = qs.order_by("-price")
        elif sort == "new":
            qs = qs.order_by("-created_at")
        elif sort == "-new":
            qs = qs.order_by("created_at")

        return qs


class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = "slug"
    queryset = Product.objects.select_related("category").all()


# ---------------------- Site (HTML) views ----------------------
def site_catalog(request):
    params = request.GET
    qs = Product.objects.select_related("category").all().order_by("name")

    search = params.get("search")
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(sku__icontains=search)
            | Q(manufacturer__icontains=search)
        )

    category = params.get("category")
    if category:
        qs = qs.filter(category__slug=category)

    price_min = params.get("price_min")
    if price_min:
        qs = qs.filter(price__gte=price_min)

    price_max = params.get("price_max")
    if price_max:
        qs = qs.filter(price__lte=price_max)

    in_stock = params.get("in_stock")
    if in_stock in {"1", "true", "True"}:
        qs = qs.filter(in_stock__gt=0)

    sort = params.get("sort")
    if sort == "price":
        qs = qs.order_by("price")
    elif sort == "-price":
        qs = qs.order_by("-price")
    elif sort == "new":
        qs = qs.order_by("-created_at")
    elif sort == "-new":
        qs = qs.order_by("created_at")

    categories = Category.objects.all()
    context = {
        "products": qs[:60],  # simple limit for now
        "categories": categories,
    }
    return render(request, "catalog/list.html", context)


def site_product_detail(request, slug: str):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug)
    context = {
        "product": product,
    }
    return render(request, "catalog/detail.html", context)
