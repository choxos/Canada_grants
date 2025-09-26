from django.contrib import admin
from .models import Grant, GlobalAffairsGrant, TaxBracket, CanadianTaxData

@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ['agreement_title_en', 'recipient_legal_name', 'agreement_value', 
                   'recipient_province', 'fiscal_year', 'is_major_funding', 'is_notable']
    list_filter = ['recipient_province', 'fiscal_year', 'is_major_funding', 'is_notable', 'recipient_type']
    search_fields = ['agreement_title_en', 'recipient_legal_name', 'description_en', 'program_name_en']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('reference_number', 'recipient_province', 'recipient_city_en', 
                      'recipient_legal_name', 'recipient_operating_name', 'recipient_type', 
                      'recipient_postal_code')
        }),
        ('Agreement Details', {
            'fields': ('agreement_title_en', 'agreement_number', 'agreement_value', 
                      'description_en', 'expected_results_en')
        }),
        ('Dates', {
            'fields': ('agreement_start_date', 'agreement_end_date')
        }),
        ('Program Information', {
            'fields': ('program_name_en', 'program_purpose_en', 'naics_identifier', 'naics_sector_en')
        }),
        ('Classification', {
            'fields': ('is_notable', 'is_major_funding', 'notable_reason', 'fiscal_year')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_notable', 'mark_as_major_funding', 'unmark_notable']
    
    def mark_as_notable(self, request, queryset):
        queryset.update(is_notable=True)
        self.message_user(request, f"{queryset.count()} grants marked as notable.")
    mark_as_notable.short_description = "Mark selected grants as notable"
    
    def mark_as_major_funding(self, request, queryset):
        queryset.update(is_major_funding=True)
        self.message_user(request, f"{queryset.count()} grants marked as major funding.")
    mark_as_major_funding.short_description = "Mark selected grants as major funding"
    
    def unmark_notable(self, request, queryset):
        queryset.update(is_notable=False, notable_reason='')
        self.message_user(request, f"{queryset.count()} grants unmarked as notable.")
    unmark_notable.short_description = "Unmark selected grants as notable"

@admin.register(TaxBracket)
class TaxBracketAdmin(admin.ModelAdmin):
    list_display = ['year', 'min_income', 'max_income', 'tax_rate']
    list_filter = ['year']
    ordering = ['year', 'min_income']

@admin.register(CanadianTaxData)
class CanadianTaxDataAdmin(admin.ModelAdmin):
    list_display = ['year', 'total_federal_revenue', 'gst_hst_revenue', 'income_tax_revenue']
    ordering = ['-year']

@admin.register(GlobalAffairsGrant)
class GlobalAffairsGrantAdmin(admin.ModelAdmin):
    list_display = ['title', 'project_number', 'primary_country', 'maximum_contribution', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['title', 'project_number', 'description', 'country']
    ordering = ['-maximum_contribution']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_number', 'title', 'description', 'status')
        }),
        ('Geographic & Partners', {
            'fields': ('country', 'region', 'executing_agency_partner', 'contributing_organization')
        }),
        ('Financial', {
            'fields': ('maximum_contribution', 'budget')
        }),
        ('Dates', {
            'fields': ('date_modified', 'start_date', 'end_date')
        }),
        ('Development Classification', {
            'fields': ('dac_sector', 'aid_type', 'collaboration_type', 'finance_type', 'selection_mechanism'),
            'classes': ('collapse',)
        }),
        ('Program & Policy', {
            'fields': ('program_name', 'policy_markers', 'expected_results', 'progress_and_results_achieved'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('locations', 'alternate_im_position', 'other_identifier'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('date_modified',)
    
    def get_queryset(self, request):
        """Optimize queries for admin interface"""
        return super().get_queryset(request).select_related().prefetch_related()