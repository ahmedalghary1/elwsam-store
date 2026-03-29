/**
 * Enhanced Validation System for Frontend
 * Provides visual feedback, inline error messages, and comprehensive validation
 */

class ValidationUI {
    constructor() {
        this.errorContainer = null;
        this.init();
    }
    
    init() {
        // Create global error container if it doesn't exist
        if (!document.getElementById('validation-errors')) {
            this.createErrorContainer();
        }
    }
    
    createErrorContainer() {
        const container = document.createElement('div');
        container.id = 'validation-errors';
        container.className = 'validation-errors-container';
        container.setAttribute('role', 'alert');
        container.setAttribute('aria-live', 'polite');
        container.style.display = 'none';
        
        // Insert at top of main content
        const main = document.querySelector('main') || document.body;
        main.insertBefore(container, main.firstChild);
        
        this.errorContainer = container;
    }
    
    /**
     * Show validation errors
     * @param {Object} errors - Object with field names as keys and error messages as values
     * @param {string} generalMessage - General error message
     */
    showErrors(errors, generalMessage = null) {
        if (!this.errorContainer) {
            this.createErrorContainer();
        }
        
        let html = '';
        
        if (generalMessage) {
            html += `<div class="validation-error-general">${generalMessage}</div>`;
        }
        
        if (errors && Object.keys(errors).length > 0) {
            html += '<ul class="validation-error-list">';
            for (const [field, message] of Object.entries(errors)) {
                html += `<li data-field="${field}">${message}</li>`;
                this.highlightField(field);
            }
            html += '</ul>';
        }
        
        this.errorContainer.innerHTML = html;
        this.errorContainer.style.display = 'block';
        this.errorContainer.className = 'validation-errors-container error';
        
        // Auto-hide after 8 seconds
        setTimeout(() => this.hideErrors(), 8000);
        
        // Scroll to errors
        this.errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    /**
     * Show success message
     * @param {string} message - Success message
     */
    showSuccess(message) {
        if (!this.errorContainer) {
            this.createErrorContainer();
        }
        
        this.errorContainer.innerHTML = `<div class="validation-success">${message}</div>`;
        this.errorContainer.style.display = 'block';
        this.errorContainer.className = 'validation-errors-container success';
        
        // Auto-hide after 5 seconds
        setTimeout(() => this.hideErrors(), 5000);
    }
    
    /**
     * Show warning message
     * @param {string} message - Warning message
     */
    showWarning(message) {
        if (!this.errorContainer) {
            this.createErrorContainer();
        }
        
        this.errorContainer.innerHTML = `<div class="validation-warning">${message}</div>`;
        this.errorContainer.style.display = 'block';
        this.errorContainer.className = 'validation-errors-container warning';
        
        // Auto-hide after 6 seconds
        setTimeout(() => this.hideErrors(), 6000);
    }
    
    /**
     * Hide all errors
     */
    hideErrors() {
        if (this.errorContainer) {
            this.errorContainer.style.display = 'none';
            this.errorContainer.innerHTML = '';
        }
        
        // Remove all field highlights
        this.clearAllHighlights();
    }
    
    /**
     * Highlight a specific field with error
     * @param {string} fieldName - Name of the field to highlight
     */
    highlightField(fieldName) {
        // Find field by name, id, or data attribute
        const field = document.querySelector(
            `[name="${fieldName}"], #${fieldName}, [data-field="${fieldName}"]`
        );
        
        if (field) {
            field.classList.add('validation-error-field');
            field.setAttribute('aria-invalid', 'true');
            
            // Add error icon if not exists
            if (!field.parentElement.querySelector('.validation-error-icon')) {
                const icon = document.createElement('span');
                icon.className = 'validation-error-icon';
                icon.innerHTML = '⚠';
                icon.setAttribute('aria-hidden', 'true');
                field.parentElement.style.position = 'relative';
                field.parentElement.appendChild(icon);
            }
        }
    }
    
    /**
     * Clear highlight from a specific field
     * @param {string} fieldName - Name of the field to clear
     */
    clearFieldHighlight(fieldName) {
        const field = document.querySelector(
            `[name="${fieldName}"], #${fieldName}, [data-field="${fieldName}"]`
        );
        
        if (field) {
            field.classList.remove('validation-error-field');
            field.removeAttribute('aria-invalid');
            
            const icon = field.parentElement.querySelector('.validation-error-icon');
            if (icon) {
                icon.remove();
            }
        }
    }
    
    /**
     * Clear all field highlights
     */
    clearAllHighlights() {
        document.querySelectorAll('.validation-error-field').forEach(field => {
            field.classList.remove('validation-error-field');
            field.removeAttribute('aria-invalid');
        });
        
        document.querySelectorAll('.validation-error-icon').forEach(icon => {
            icon.remove();
        });
    }
    
    /**
     * Validate form before submission
     * @param {HTMLFormElement} form - Form to validate
     * @param {Object} customValidators - Custom validation functions
     * @returns {boolean} - True if valid
     */
    validateForm(form, customValidators = {}) {
        const errors = {};
        
        // Check required fields
        form.querySelectorAll('[required]').forEach(field => {
            if (!field.value.trim()) {
                const fieldName = field.name || field.id;
                const label = form.querySelector(`label[for="${field.id}"]`)?.textContent || fieldName;
                errors[fieldName] = `يجب إدخال ${label}`;
            }
        });
        
        // Check email fields
        form.querySelectorAll('[type="email"]').forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                errors[field.name || field.id] = 'البريد الإلكتروني غير صحيح';
            }
        });
        
        // Check password confirmation
        const password = form.querySelector('[name="password"]');
        const passwordConfirm = form.querySelector('[name="password_confirm"]');
        if (password && passwordConfirm && password.value !== passwordConfirm.value) {
            errors['password_confirm'] = 'كلمتا المرور غير متطابقتين';
        }
        
        // Run custom validators
        for (const [fieldName, validator] of Object.entries(customValidators)) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const error = validator(field.value, form);
                if (error) {
                    errors[fieldName] = error;
                }
            }
        }
        
        if (Object.keys(errors).length > 0) {
            this.showErrors(errors, 'يرجى تصحيح الأخطاء التالية:');
            return false;
        }
        
        return true;
    }
    
    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} - True if valid
     */
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    /**
     * Show loading state
     * @param {HTMLElement} button - Button to show loading on
     * @param {string} message - Loading message
     */
    showLoading(button, message = 'جاري التحميل...') {
        if (!button) return;
        
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="spinner"></span> ${message}`;
        button.classList.add('loading');
    }
    
    /**
     * Hide loading state
     * @param {HTMLElement} button - Button to hide loading from
     */
    hideLoading(button) {
        if (!button) return;
        
        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
            delete button.dataset.originalText;
        }
        button.classList.remove('loading');
    }
}

// Create global instance
window.validationUI = new ValidationUI();

// Auto-clear errors when user starts typing
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('input', (e) => {
        if (e.target.matches('input, textarea, select')) {
            const fieldName = e.target.name || e.target.id;
            if (fieldName) {
                window.validationUI.clearFieldHighlight(fieldName);
            }
        }
    });
    
    // Auto-clear errors when user clicks on error field
    document.addEventListener('focus', (e) => {
        if (e.target.matches('.validation-error-field')) {
            const fieldName = e.target.name || e.target.id;
            if (fieldName) {
                window.validationUI.clearFieldHighlight(fieldName);
            }
        }
    }, true);
});


/**
 * Enhanced AJAX Helper with Validation
 */
class AjaxHelper {
    /**
     * Make AJAX request with validation handling
     * @param {string} url - URL to request
     * @param {Object} options - Fetch options
     * @returns {Promise} - Response promise
     */
    static async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    ...options.headers
                },
                ...options
            });
            
            const data = await response.json();
            
            // Handle validation errors
            if (!data.success && data.validation) {
                if (data.validation.errors) {
                    window.validationUI.showErrors(
                        data.validation.errors,
                        data.message || data.validation.message
                    );
                } else {
                    window.validationUI.showWarning(
                        data.message || data.validation.message || 'حدث خطأ'
                    );
                }
                return { success: false, data };
            }
            
            // Handle general errors
            if (!data.success) {
                window.validationUI.showWarning(
                    data.message || data.error || 'حدث خطأ غير متوقع'
                );
                return { success: false, data };
            }
            
            return { success: true, data };
            
        } catch (error) {
            console.error('AJAX Error:', error);
            window.validationUI.showWarning('حدث خطأ في الاتصال بالخادم');
            return { success: false, error };
        }
    }
    
    /**
     * GET request
     */
    static async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl, {
            method: 'GET'
        });
    }
    
    /**
     * POST request
     */
    static async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    /**
     * POST with FormData
     */
    static async postForm(url, formData) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (!data.success && data.validation) {
                window.validationUI.showErrors(
                    data.validation.errors,
                    data.message || data.validation.message
                );
                return { success: false, data };
            }
            
            if (!data.success) {
                window.validationUI.showWarning(
                    data.message || data.error || 'حدث خطأ'
                );
                return { success: false, data };
            }
            
            return { success: true, data };
            
        } catch (error) {
            console.error('AJAX Error:', error);
            window.validationUI.showWarning('حدث خطأ في الاتصال');
            return { success: false, error };
        }
    }
}

window.ajaxHelper = AjaxHelper;


/**
 * Form Validation Helper
 */
class FormValidator {
    /**
     * Attach validation to form
     * @param {string|HTMLFormElement} formSelector - Form selector or element
     * @param {Object} options - Validation options
     */
    static attach(formSelector, options = {}) {
        const form = typeof formSelector === 'string' 
            ? document.querySelector(formSelector)
            : formSelector;
        
        if (!form) return;
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Clear previous errors
            window.validationUI.hideErrors();
            
            // Validate form
            if (!window.validationUI.validateForm(form, options.customValidators)) {
                return;
            }
            
            // Show loading
            const submitBtn = form.querySelector('[type="submit"]');
            window.validationUI.showLoading(submitBtn, options.loadingMessage);
            
            try {
                // Submit form
                const formData = new FormData(form);
                const result = await AjaxHelper.postForm(form.action, formData);
                
                if (result.success) {
                    if (options.onSuccess) {
                        options.onSuccess(result.data, form);
                    } else {
                        window.validationUI.showSuccess(
                            result.data.message || 'تم الحفظ بنجاح'
                        );
                    }
                }
            } finally {
                window.validationUI.hideLoading(submitBtn);
            }
        });
    }
}

window.formValidator = FormValidator;
