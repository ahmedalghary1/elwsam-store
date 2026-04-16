"""
Product Variant Validation Utilities
Comprehensive validation for product variants, cart operations, and user selections.
"""

from django.core.exceptions import ValidationError
from .models import Product, Pattern, PatternSize, ProductVariant, ProductColor, ProductSize, ProductType, ProductTypeColor, PatternColor


class VariantValidator:
    """
    Validates product variant selections and enforces business rules.
    """
    
    @staticmethod
    def validate_variant_selection(product, pattern_id=None, color_id=None, size_id=None, type_id=None):
        """
        Comprehensive validation of variant selection.
        
        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'field': str or None,
                'errors': dict
            }
        """
        errors = {}
        has_type_colors = False

        if type_id:
            product_type_exists = ProductType.objects.filter(
                product=product,
                type_id=type_id
            ).exists()
            if not product_type_exists:
                errors['type'] = 'النوع المحدد غير متوفر لهذا المنتج'
            else:
                type_colors = ProductTypeColor.objects.filter(
                    product_type__product=product,
                    product_type__type_id=type_id
                )
                has_type_colors = type_colors.exists()
                if has_type_colors and not color_id:
                    errors['color'] = 'يجب اختيار اللون'
                elif color_id and not type_colors.filter(color_id=color_id).exists():
                    errors['color'] = 'اللون المحدد غير متوفر لهذا النوع'
        
        # Check if product has patterns and pattern is required
        has_patterns = product.check_if_has_patterns()
        if has_patterns and not pattern_id:
            errors['pattern'] = 'يجب اختيار النمط أولاً'
        
        # Validate pattern if provided
        if pattern_id:
            try:
                pattern = Pattern.objects.get(id=pattern_id, product=product)
                
                # Check if pattern requires size
                if pattern.has_sizes and not size_id:
                    errors['size'] = 'يجب اختيار المقاس لهذا النمط'
                
                # Validate size belongs to pattern if provided
                if size_id and pattern.has_sizes:
                    pattern_size_exists = PatternSize.objects.filter(
                        pattern=pattern,
                        size_id=size_id
                    ).exists()
                    
                    if not pattern_size_exists:
                        errors['size'] = 'المقاس المحدد غير متوفر لهذا النمط'
                
            except Pattern.DoesNotExist:
                errors['pattern'] = 'النمط المحدد غير موجود'
        
        # Check if color is required
        # Priority: PatternColor (if pattern selected) → ProductColor
        if pattern_id:
            try:
                pattern_obj = Pattern.objects.get(id=pattern_id, product=product)
                has_pattern_colors = PatternColor.objects.filter(pattern=pattern_obj).exists()
                if has_pattern_colors and not color_id:
                    errors['color'] = 'يجب اختيار اللون'
                if color_id and has_pattern_colors:
                    if not PatternColor.objects.filter(
                        pattern=pattern_obj, color_id=color_id
                    ).exists():
                        errors['color'] = 'اللون المحدد غير متوفر لهذا النمط'
            except Pattern.DoesNotExist:
                pass
        else:
            has_colors = ProductColor.objects.filter(product=product).exists()
            if has_colors and not color_id and not has_type_colors:
                errors['color'] = 'يجب اختيار اللون'
            if color_id and not pattern_id and not has_type_colors:
                if not ProductColor.objects.filter(product=product, color_id=color_id).exists():
                    errors['color'] = 'اللون المحدد غير متوفر لهذا المنتج'

        # Check if product has product-level sizes (not pattern-based)
        has_colors = ProductColor.objects.filter(product=product).exists()
        if not product.check_if_has_patterns() and not has_colors:
            has_product_sizes = ProductSize.objects.filter(product=product).exists()
            if has_product_sizes and not size_id:
                errors['size'] = 'يجب اختيار المقاس'
        
        # Validate size belongs to product if provided (for product-level sizes)
        if size_id and not pattern_id:
            size_exists = ProductSize.objects.filter(
                product=product,
                size_id=size_id
            ).exists()
            
            if not size_exists:
                errors['size'] = 'المقاس المحدد غير متوفر لهذا المنتج'
        
        # Build response
        if errors:
            # Determine primary field and message
            field_priority = ['pattern', 'color', 'size', 'type']
            primary_field = next((f for f in field_priority if f in errors), None)
            primary_message = errors.get(primary_field, 'يجب إكمال جميع الخيارات المطلوبة')
            
            return {
                'valid': False,
                'message': primary_message,
                'field': primary_field,
                'errors': errors
            }
        
        return {
            'valid': True,
            'message': '',
            'field': None,
            'errors': {}
        }
    
    @staticmethod
    def validate_stock_availability(variant_id, quantity=1):
        """
        Validate stock availability for a variant.
        
        Returns:
            dict: {
                'available': bool,
                'message': str,
                'stock': int
            }
        """
        try:
            variant = ProductVariant.objects.get(id=variant_id)
            
            if variant.stock <= 0:
                return {
                    'available': False,
                    'message': 'المنتج غير متوفر حالياً',
                    'stock': 0
                }
            
            if variant.stock < quantity:
                return {
                    'available': False,
                    'message': f'الكمية المتوفرة فقط {variant.stock} قطعة',
                    'stock': variant.stock
                }
            
            return {
                'available': True,
                'message': 'متوفر',
                'stock': variant.stock
            }
            
        except ProductVariant.DoesNotExist:
            return {
                'available': False,
                'message': 'المتغير المحدد غير موجود',
                'stock': 0
            }
    
    @staticmethod
    def get_variant_or_validate(product_id, pattern_id=None, color_id=None, size_id=None, type_id=None):
        """
        Get variant if valid, or return validation errors.
        
        Returns:
            tuple: (variant or None, validation_result dict)
        """
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return None, {
                'valid': False,
                'message': 'المنتج غير موجود',
                'field': None,
                'errors': {'product': 'المنتج غير موجود'}
            }
        
        # Validate selection
        validation = VariantValidator.validate_variant_selection(
            product, pattern_id, color_id, size_id, type_id
        )
        
        if not validation['valid']:
            return None, validation
        
        # Try to find matching variant
        try:
            variant = ProductVariant.objects.get(
                product=product,
                pattern_id=pattern_id,
                color_id=color_id,
                size_id=size_id
            )
            
            # Check stock
            if variant.stock <= 0:
                return None, {
                    'valid': False,
                    'message': 'هذا التركيب غير متوفر حالياً',
                    'field': None,
                    'errors': {'stock': 'غير متوفر'}
                }
            
            return variant, {'valid': True, 'message': '', 'field': None, 'errors': {}}
            
        except ProductVariant.DoesNotExist:
            if not pattern_id and not size_id:
                return None, {'valid': True, 'message': '', 'field': None, 'errors': {}}

            return None, {
                'valid': False,
                'message': 'هذا التركيب غير متوفر',
                'field': None,
                'errors': {'variant': 'التركيب غير موجود'}
            }


class CartValidator:
    """
    Validates cart operations.
    """
    
    @staticmethod
    def validate_add_to_cart(product_id, variant_id=None, quantity=1):
        """
        Validate adding item to cart.
        
        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'errors': dict
            }
        """
        errors = {}
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1:
            errors['quantity'] = 'الكمية يجب أن تكون رقم صحيح أكبر من صفر'
        
        if quantity > 100:
            errors['quantity'] = 'الكمية القصوى المسموح بها 100 قطعة'
        
        # Validate product exists
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            errors['product'] = 'المنتج غير موجود أو غير متاح'
            return {
                'valid': False,
                'message': 'المنتج غير موجود أو غير متاح',
                'errors': errors
            }
        
        # Check if product requires variant
        has_variants = ProductVariant.objects.filter(product=product).exists()
        
        if has_variants and not variant_id:
            errors['variant'] = 'يجب اختيار خيارات المنتج أولاً'
            return {
                'valid': False,
                'message': 'يجب اختيار خيارات المنتج أولاً',
                'errors': errors
            }
        
        # Validate variant if provided
        if variant_id:
            stock_check = VariantValidator.validate_stock_availability(variant_id, quantity)
            
            if not stock_check['available']:
                errors['stock'] = stock_check['message']
                return {
                    'valid': False,
                    'message': stock_check['message'],
                    'errors': errors
                }
        
        if errors:
            return {
                'valid': False,
                'message': 'حدث خطأ في التحقق من البيانات',
                'errors': errors
            }
        
        return {
            'valid': True,
            'message': 'تم التحقق بنجاح',
            'errors': {}
        }
    
    @staticmethod
    def validate_update_quantity(cart_item, new_quantity):
        """
        Validate updating cart item quantity.
        
        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'max_quantity': int
            }
        """
        if not isinstance(new_quantity, int) or new_quantity < 0:
            return {
                'valid': False,
                'message': 'الكمية يجب أن تكون رقم صحيح',
                'max_quantity': 0
            }
        
        if new_quantity == 0:
            return {
                'valid': True,
                'message': 'سيتم حذف المنتج من السلة',
                'max_quantity': 0
            }
        
        # Check stock if variant exists
        if hasattr(cart_item, 'variant') and cart_item.variant:
            stock_check = VariantValidator.validate_stock_availability(
                cart_item.variant.id, 
                new_quantity
            )
            
            if not stock_check['available']:
                return {
                    'valid': False,
                    'message': stock_check['message'],
                    'max_quantity': stock_check['stock']
                }
        
        return {
            'valid': True,
            'message': 'تم التحديث بنجاح',
            'max_quantity': new_quantity
        }


class AuthValidator:
    """
    Validates authentication operations.
    """
    
    @staticmethod
    def validate_login_credentials(username, password):
        """
        Validate login credentials format.
        
        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'errors': dict
            }
        """
        errors = {}
        
        if not username or not username.strip():
            errors['username'] = 'يجب إدخال اسم المستخدم'
        
        if not password or not password.strip():
            errors['password'] = 'يجب إدخال كلمة المرور'
        
        if len(username) > 150:
            errors['username'] = 'اسم المستخدم طويل جداً'
        
        if errors:
            return {
                'valid': False,
                'message': 'يرجى إكمال جميع الحقول المطلوبة',
                'errors': errors
            }
        
        return {
            'valid': True,
            'message': '',
            'errors': {}
        }
    
    @staticmethod
    def validate_registration(username, email, password, password_confirm):
        """
        Validate registration data.
        
        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'errors': dict
            }
        """
        errors = {}
        
        # Username validation
        if not username or not username.strip():
            errors['username'] = 'يجب إدخال اسم المستخدم'
        elif len(username) < 3:
            errors['username'] = 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل'
        elif len(username) > 150:
            errors['username'] = 'اسم المستخدم طويل جداً'
        
        # Email validation
        if not email or not email.strip():
            errors['email'] = 'يجب إدخال البريد الإلكتروني'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'البريد الإلكتروني غير صحيح'
        
        # Password validation
        if not password:
            errors['password'] = 'يجب إدخال كلمة المرور'
        elif len(password) < 8:
            errors['password'] = 'كلمة المرور يجب أن تكون 8 أحرف على الأقل'
        
        # Password confirmation
        if password != password_confirm:
            errors['password_confirm'] = 'كلمتا المرور غير متطابقتين'
        
        if errors:
            return {
                'valid': False,
                'message': 'يرجى تصحيح الأخطاء في النموذج',
                'errors': errors
            }
        
        return {
            'valid': True,
            'message': '',
            'errors': {}
        }
