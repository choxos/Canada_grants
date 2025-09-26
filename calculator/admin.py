from django.contrib import admin
from .models import TaxCalculation

@admin.register(TaxCalculation)
class TaxCalculationAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'annual_income', 'total_tax_contribution', 
                   'revenue_share_percentage', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation through admin