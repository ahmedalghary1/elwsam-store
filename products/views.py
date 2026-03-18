from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from .models import Product, Category, ProductVariant, ProductImage, ProductColor, ProductSize, Pattern, ProductSpecification


# =========================
# List of Categories
# =========================
class CategoryListView(ListView):
    model = Category
    template_name = "products/category_list.html"
    context_object_name = "categories"
    ordering = ['order']


# =========================
#  List of Products in a Category
# =========================
class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        queryset = Product.objects.filter(category_id=category_id).order_by('order')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category, id=self.kwargs.get('category_id'))
        return context


# =========================
# Product Detail View
# =========================
class ProductDetailView(View):
    template_name = "products/product_detail.html"

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        # كل الصور الخاصة بالمنتج
        images = ProductImage.objects.filter(product=product).order_by('order')

        # كل الألوان المتاحة للمنتج
        product_colors = ProductColor.objects.filter(product=product).order_by('order')
        # كل المقاسات المتاحة للمنتج
        product_sizes = ProductSize.objects.filter(product=product).order_by('order')
        # كل الأنماط (Patterns)
        patterns = Pattern.objects.filter(product=product).order_by('order')
        # Variants
        variants = ProductVariant.objects.filter(product=product).select_related('color', 'size', 'pattern').order_by('order')
        # مواصفات المنتج
        specs = product.specs.all().order_by('order')

        context = {
            'product': product,
            'images': images,
            'colors': product_colors,
            'sizes': product_sizes,
            'patterns': patterns,
            'variants': variants,
            'specs': specs
        }

        return render(request, self.template_name, context)


# =========================
#  AJAX: تغيير الصور حسب اللون 
# =========================
from django.http import JsonResponse

def product_images_by_color(request, product_id, color_id):
    """
    إرجاع قائمة الصور حسب اللون باستخدام AJAX
    """
    images = ProductImage.objects.filter(product_id=product_id, color_id=color_id).order_by('order')
    image_urls = [img.image.url for img in images]
    return JsonResponse({'images': image_urls})


# =========================
#  Search / Filter Products
# =========================
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query).order_by('order')
    context = {
        'products': products,
        'query': query
    }
    return render(request, "products/product_search.html", context)