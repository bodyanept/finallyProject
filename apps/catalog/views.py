from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import render, get_object_or_404
from django.db import connection

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
            tokens = [t.strip().casefold() for t in search.split() if t.strip()]
            if tokens:
                if connection.vendor == 'sqlite':
                    # SQLite LOWER/LIKE are ASCII-only; do Python-level casefold matching
                    ids = []
                    for p in qs:
                        text = " ".join([
                            (p.name or ""),
                            (p.description or ""),
                            (p.sku or ""),
                            (p.manufacturer or ""),
                        ]).casefold()
                        if any(t in text for t in tokens):
                            ids.append(p.id)
                    qs = qs.filter(id__in=ids)
                else:
                    qs = qs.annotate(
                        name_l=Lower("name"),
                        desc_l=Lower("description"),
                        sku_l=Lower("sku"),
                        manufacturer_l=Lower("manufacturer"),
                    )
                    q = Q()
                    for t in tokens:
                        q |= (
                            Q(name_l__contains=t)
                            | Q(desc_l__contains=t)
                            | Q(sku_l__contains=t)
                            | Q(manufacturer_l__contains=t)
                        )
                    qs = qs.filter(q)

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
        tokens = [t.strip().casefold() for t in search.split() if t.strip()]
        if tokens:
            if connection.vendor == 'sqlite':
                ids = []
                for p in qs:
                    text = " ".join([
                        (p.name or ""),
                        (p.description or ""),
                        (p.sku or ""),
                        (p.manufacturer or ""),
                        (getattr(p.category, 'name', '') or ""),
                    ]).casefold()
                    if any(t in text for t in tokens):
                        ids.append(p.id)
                qs = qs.filter(id__in=ids)
            else:
                qs = qs.annotate(
                    name_l=Lower("name"),
                    desc_l=Lower("description"),
                    sku_l=Lower("sku"),
                    manufacturer_l=Lower("manufacturer"),
                    category_l=Lower("category__name"),
                )
                q = Q()
                for t in tokens:
                    q |= (
                        Q(name_l__contains=t)
                        | Q(desc_l__contains=t)
                        | Q(sku_l__contains=t)
                        | Q(manufacturer_l__contains=t)
                        | Q(category_l__contains=t)
                    )
                qs = qs.filter(q)

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

    # If exactly one product matched and user requested goto, redirect to its detail
    if request.GET.get('goto') == '1':
        try:
            count = qs.count()
            if count == 1:
                only = qs.first()
                return redirect(f"/parts/{only.slug}/")
        except Exception:
            pass

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
