from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category, ProductVariant, ProductImage, ProductColor, ProductSize, Pattern, ProductSpecification


# =========================
# List of Categories
# =========================
class CategoryListView(ListView):
    model = Category
    template_name = "categories.html"
    context_object_name = "categories"
    ordering = ['order']
    
    def get_queryset(self):
        return Category.objects.all().order_by('order').prefetch_related('product_set')


def category_products(request, slug):
    """
    عرض جميع المنتجات الخاصة بقسم معين (حسب slug)
    مع إمكانية الفرز والتصفية
    """
    category = get_object_or_404(Category, slug=slug)
    
    # الحصول على جميع المنتجات النشطة للقسم
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).order_by('order').prefetch_related('images', 'variants', 'specs')
    
    # التصفية حسب المعاملات (Query Parameters)
    sort_by = request.GET.get('sort', 'order')
    if sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    
    # البحث عن منتج محدد
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    context = {
        'category': category,
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
        'products_count': products.count(),
    }
    return render(request, 'category-products.html', context)


# =========================
#  List of All Products
# =========================
class ProductListView(ListView):
    model = Product
    template_name = "products.html"
    context_object_name = "products"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).order_by('order')
        queryset = queryset.prefetch_related('images', 'variants', 'specs')
        
        # التصفية حسب الفئة إن وجدت
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        return queryset


# =========================
# Product Detail View
# =========================
class ProductDetailView(View):
    template_name = "product.html"

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        
        # كل الصور الخاصة بالمنتج (مرتبة حسب الرتبة)
        images = ProductImage.objects.filter(product=product).order_by('order')
        
        # كل الألوان المتاحة للمنتج
        product_colors = ProductColor.objects.filter(product=product).order_by('order')
        
        # كل المقاسات المتاحة للمنتج
        product_sizes = ProductSize.objects.filter(product=product).order_by('order')
        
        # كل الأنماط (Patterns)
        patterns = Pattern.objects.filter(product=product).order_by('order')
        
        # Variants مع البيانات المرتبطة
        variants = ProductVariant.objects.filter(product=product).select_related(
            'color', 'size', 'pattern'
        ).order_by('order')
        
        # مواصفات المنتج
        specs = product.specs.all().order_by('order')
        
        # المنتجات المشابهة (من نفس الفئة)
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id).order_by('order')[:6]

        context = {
            'product': product,
            'images': images,
            'colors': product_colors,
            'sizes': product_sizes,
            'patterns': patterns,
            'variants': variants,
            'specs': specs,
            'related_products': related_products,
        }

        return render(request, self.template_name, context)


# =========================
#  AJAX: تغيير الصور حسب اللون 
# =========================
def product_images_by_color(request, product_id, color_id):
    """
    إرجاع قائمة الصور حسب اللون باستخدام AJAX
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        images = ProductImage.objects.filter(
            product=product,
            color_id=color_id
        ).order_by('order')
        
        image_urls = [img.image.url for img in images]
        
        return JsonResponse({
            'success': True,
            'images': image_urls
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =========================
#  Search / Filter Products
# =========================
def search_products(request):
    """
    بحث شامل عن المنتجات
    """
    query = request.GET.get('q', '').strip()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).order_by('-created_at').prefetch_related('images', 'variants', 'specs')
    else:
        products = Product.objects.none()
    
    context = {
        'products': products,
        'query': query,
        'results_count': products.count(),
    }
    return render(request, "search_results.html", context)
# =========================
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query).order_by('order')
    context = {
        'products': products,
        'query': query
    }
    return render(request, "products/product_search.html", context)