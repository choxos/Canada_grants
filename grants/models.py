from django.db import models
from django.urls import reverse
import re

class Grant(models.Model):
    # Basic Information
    reference_number = models.CharField(max_length=100, unique=True)
    recipient_province = models.CharField(max_length=50)
    recipient_city_en = models.CharField(max_length=100)
    recipient_legal_name = models.TextField()
    recipient_operating_name = models.TextField(blank=True)
    recipient_type = models.CharField(max_length=10)
    recipient_postal_code = models.CharField(max_length=10)
    
    # Agreement Details
    agreement_title_en = models.TextField()
    agreement_number = models.CharField(max_length=100)
    agreement_value = models.DecimalField(max_digits=15, decimal_places=2)
    description_en = models.TextField()
    expected_results_en = models.TextField(blank=True)
    
    # Dates
    agreement_start_date = models.DateField(null=True, blank=True)
    agreement_end_date = models.DateField(null=True, blank=True)
    
    # Program Information
    program_name_en = models.TextField()
    program_purpose_en = models.TextField(blank=True)
    
    # Classification
    naics_identifier = models.CharField(max_length=20, blank=True)
    naics_sector_en = models.CharField(max_length=200, blank=True)
    
    # Flags for special categories
    is_notable = models.BooleanField(default=False)
    is_major_funding = models.BooleanField(default=False)
    notable_reason = models.TextField(blank=True)
    
    # Metadata
    fiscal_year = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-agreement_value', '-agreement_start_date']
        indexes = [
            models.Index(fields=['agreement_value']),
            models.Index(fields=['recipient_province']),
            models.Index(fields=['fiscal_year']),
            models.Index(fields=['is_notable']),
            models.Index(fields=['is_major_funding']),
        ]
    
    def __str__(self):
        return f"{self.agreement_title_en[:50]}... - ${self.agreement_value:,.2f}"
    
    def get_absolute_url(self):
        return reverse('grant_detail', kwargs={'pk': self.pk})
    
    @property
    def is_controversial(self):
        """Check if grant might be controversial based on keywords"""
        controversial_keywords = [
            'gender', 'diversity', 'equity', 'inclusion', 'climate', 'carbon',
            'indigenous', 'reconciliation', 'arts', 'culture', 'international'
        ]
        text_to_check = f"{self.agreement_title_en} {self.description_en}".lower()
        return any(keyword in text_to_check for keyword in controversial_keywords)
    
    @property
    def formatted_value(self):
        return f"${self.agreement_value:,.2f}"
    
    def save(self, *args, **kwargs):
        # Auto-flag major funding (over $1M)
        if self.agreement_value >= 1000000:
            self.is_major_funding = True
        super().save(*args, **kwargs)


class GlobalAffairsGrant(models.Model):
    """Model for Global Affairs Canada international development grants"""
    
    # Status choices based on the data
    STATUS_CHOICES = [
        ('operational', 'Operational'),
        ('closed', 'Closed'),
        ('terminating', 'Terminating'),
    ]
    
    # Basic Information
    project_number = models.CharField(max_length=100, unique=True)  # Increased from 50
    date_modified = models.DateField()
    title = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Geographic Information
    country = models.TextField()  # Can include multiple countries with percentages
    region = models.CharField(max_length=500, blank=True)  # Increased from 200
    locations = models.TextField(blank=True)  # Geographic coordinates and location data
    
    # Partners and Implementation
    executing_agency_partner = models.TextField(blank=True)
    contributing_organization = models.TextField(blank=True)
    reporting_organization = models.CharField(max_length=200, default='Global Affairs Canada')  # Increased from 100
    
    # Financial Information
    maximum_contribution = models.DecimalField(max_digits=15, decimal_places=2)
    budget = models.TextField(blank=True)  # Detailed budget breakdown by year
    
    # Program and Sector Information
    program_name = models.TextField()
    dac_sector = models.TextField()  # Development Assistance Committee sector classification
    
    # Development Aid Classification
    aid_type = models.CharField(max_length=200, blank=True)  # Increased from 100
    collaboration_type = models.CharField(max_length=200, blank=True)  # Increased from 50
    finance_type = models.CharField(max_length=200, blank=True)  # Increased from 100
    flow_type = models.CharField(max_length=200, blank=True)  # Increased from 50
    selection_mechanism = models.CharField(max_length=200, blank=True)  # Increased from 100
    
    # Results and Impact
    expected_results = models.TextField(blank=True)
    progress_and_results_achieved = models.TextField(blank=True)
    
    # Policy and Strategy
    policy_markers = models.TextField(blank=True)  # Cross-cutting themes
    alternate_im_position = models.CharField(max_length=300, blank=True)  # Increased from 100
    other_identifier = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-maximum_contribution', '-start_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['maximum_contribution']),
            models.Index(fields=['start_date']),
            models.Index(fields=['country']),
            models.Index(fields=['region']),
        ]
    
    def __str__(self):
        return f"{self.title[:50]}... - ${self.maximum_contribution:,.2f} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        return reverse('gac_grant_detail', kwargs={'pk': self.pk})
    
    @property
    def formatted_contribution(self):
        return f"${self.maximum_contribution:,.2f}"
    
    @property
    def is_major_funding(self):
        """Check if this is major funding (over $1M)"""
        return self.maximum_contribution >= 1000000
    
    @property
    def duration_years(self):
        """Calculate project duration in years"""
        if self.start_date and self.end_date:
            duration = self.end_date - self.start_date
            return max(1, duration.days / 365.25)
        return None
    
    @property
    def primary_country(self):
        """Extract the primary country from the country field"""
        if ':' in self.country:
            # Handle cases like "Mali: 100.00%" or multiple countries
            countries = self.country.split(';')
            primary = countries[0].strip()
            if ':' in primary:
                return primary.split(':')[0].strip()
            return primary
        return self.country.strip()

    @property
    def formatted_country_distribution(self):
        """Parse and format the country field into a list of dictionaries with clean display"""
        if not self.country:
            return []
            
        countries = []
        
        # Split by comma and parse each country
        for country_part in self.country.split(','):
            country_part = country_part.strip()
            if not country_part:
                continue
                
            if ':' in country_part:
                # Format: "India: 21.00%"
                name, percentage = country_part.split(':', 1)
                countries.append({
                    'name': name.strip(),
                    'percentage': percentage.strip()
                })
            else:
                # Just country name
                countries.append({
                    'name': country_part,
                    'percentage': '100%'
                })
        
        return countries

    @property 
    def clean_country_display(self):
        """Provide a clean single-line display of countries for list views"""
        formatted = self.formatted_country_distribution
        if not formatted:
            return 'Unknown'
            
        if len(formatted) == 1:
            country = formatted[0]
            if country['percentage'] == '100%':
                return country['name']
            else:
                return f"{country['name']} ({country['percentage']})"
        else:
            # Multiple countries - show first few
            country_names = [c['name'] for c in formatted[:3]]
            result = ', '.join(country_names)
            if len(formatted) > 3:
                result += f" +{len(formatted) - 3} more"
            return result
    
    @property
    def has_gender_marker(self):
        """Check if project has gender equality markers"""
        return 'gender equality' in self.policy_markers.lower() if self.policy_markers else False
    
    @property
    def has_environment_marker(self):
        """Check if project has environmental sustainability markers"""
        markers = self.policy_markers.lower() if self.policy_markers else ''
        return 'environmental' in markers or 'sustainability' in markers
    
    @property
    def has_governance_marker(self):
        """Check if project has governance markers"""
        markers = self.policy_markers.lower() if self.policy_markers else ''
        return 'governance' in markers or 'participatory development' in markers
    
    @property
    def formatted_regional_focus(self):
        """Format regional focus data for better display"""
        if not self.region:
            return None
            
        # Parse regional data like "West Indies regional: 10.00%;North and Central America regional: 30.00%"
        regions = []
        parts = self.region.split(';')
        
        for part in parts:
            part = part.strip()
            if ':' in part and '%' in part:
                # Extract region name and percentage
                region_name, percentage_part = part.split(':', 1)
                region_name = region_name.strip()
                percentage = percentage_part.strip()
                
                # Clean up region name (remove "regional" suffix)
                region_name = region_name.replace(' regional', '').strip()
                
                # Format percentage nicely
                if percentage.endswith('%'):
                    try:
                        pct_value = float(percentage[:-1])
                        if pct_value == int(pct_value):
                            percentage = f"{int(pct_value)}%"
                        else:
                            percentage = f"{pct_value:g}%"
                    except ValueError:
                        pass
                
                regions.append({
                    'name': region_name,
                    'percentage': percentage
                })
            elif part:
                # Simple region name without percentage
                regions.append({
                    'name': part.replace(' regional', '').strip(),
                    'percentage': None
                })
        
        return regions if regions else None
    
    @property 
    def clean_regional_focus(self):
        """Clean regional focus for single-line display (e.g., in lists)"""
        formatted = self.formatted_regional_focus
        if not formatted:
            return None
            
        # Create a clean single-line version
        region_parts = []
        for region in formatted:
            if region['percentage']:
                region_parts.append(f"{region['name']} ({region['percentage']})")
            else:
                region_parts.append(region['name'])
                
        return ', '.join(region_parts) if region_parts else None
    
    @property
    def formatted_dac_sector(self):
        """Format DAC sector data for better display"""
        if not self.dac_sector:
            return None
            
        # Parse DAC sector data like "Infectious disease control: 84.00%;Other prevention and treatment of NCDs: 5.00%"
        sectors = []
        parts = self.dac_sector.split(';')
        
        for part in parts:
            part = part.strip()
            if ':' in part and '%' in part:
                # Extract sector name and percentage
                sector_name, percentage_part = part.split(':', 1)
                sector_name = sector_name.strip()
                percentage = percentage_part.strip()
                
                # Format percentage nicely
                if percentage.endswith('%'):
                    try:
                        pct_value = float(percentage[:-1])
                        if pct_value == int(pct_value):
                            percentage = f"{int(pct_value)}%"
                        else:
                            percentage = f"{pct_value:g}%"
                    except ValueError:
                        pass
                
                sectors.append({
                    'name': sector_name,
                    'percentage': percentage
                })
            elif part:
                # Simple sector name without percentage
                sectors.append({
                    'name': part.strip(),
                    'percentage': None
                })
        
        return sectors if sectors else None
    
    @property 
    def clean_dac_sector(self):
        """Clean DAC sector for single-line display (e.g., in lists)"""
        formatted = self.formatted_dac_sector
        if not formatted:
            return None
            
        # Create a clean single-line version
        sector_parts = []
        for sector in formatted:
            if sector['percentage']:
                sector_parts.append(f"{sector['name']} ({sector['percentage']})")
            else:
                sector_parts.append(sector['name'])
                
        return ', '.join(sector_parts) if sector_parts else None
    
    @property
    def formatted_policy_markers(self):
        """Format policy markers data for better display"""
        if not self.policy_markers:
            return None
            
        # Parse policy markers like "1 - Gender equality; 1 - Environmental sustainability (cross-cutting); 2 - Children's issues"
        markers = []
        parts = self.policy_markers.split(';')
        
        for part in parts:
            part = part.strip()
            if ' - ' in part:
                # Extract priority level and marker name
                level_part, marker_name = part.split(' - ', 1)
                level = level_part.strip()
                marker_name = marker_name.strip()
                
                # Map common marker types to icons and colors
                icon_class = 'fas fa-tag'
                badge_class = 'bg-secondary'
                
                marker_lower = marker_name.lower()
                if 'gender' in marker_lower:
                    icon_class = 'fas fa-venus-mars'
                    badge_class = 'bg-warning text-dark'
                elif 'environment' in marker_lower or 'climate' in marker_lower:
                    icon_class = 'fas fa-leaf'
                    badge_class = 'bg-success'
                elif 'governance' in marker_lower or 'participatory' in marker_lower:
                    icon_class = 'fas fa-balance-scale'
                    badge_class = 'bg-primary'
                elif 'children' in marker_lower or 'youth' in marker_lower:
                    icon_class = 'fas fa-child'
                    badge_class = 'bg-info'
                elif 'human rights' in marker_lower:
                    icon_class = 'fas fa-hands-helping'
                    badge_class = 'bg-danger'
                elif 'economic' in marker_lower or 'trade' in marker_lower:
                    icon_class = 'fas fa-chart-line'
                    badge_class = 'bg-success'
                
                markers.append({
                    'level': level,
                    'name': marker_name,
                    'icon_class': icon_class,
                    'badge_class': badge_class
                })
            elif part:
                # Simple marker without level
                markers.append({
                    'level': '',
                    'name': part.strip(),
                    'icon_class': 'fas fa-tag',
                    'badge_class': 'bg-secondary'
                })
        
        return markers if markers else None
    
    @property 
    def clean_policy_markers(self):
        """Clean policy markers for single-line display"""
        formatted = self.formatted_policy_markers
        if not formatted:
            return None
            
        # Create a clean single-line version
        marker_parts = []
        for marker in formatted:
            if marker['level']:
                marker_parts.append(f"{marker['name']} (Level {marker['level']})")
            else:
                marker_parts.append(marker['name'])
                
        return ', '.join(marker_parts) if marker_parts else None
    
    @property
    def clean_reference_id(self):
        """Extract clean reference ID from potentially corrupted other_identifier field"""
        if not self.other_identifier:
            return None
            
        # The reference ID is often corrupted with budget data mixed in
        # Pattern: "Reference:2002000498;Other Identifier Type:CRS Activity identifier"
        # Or corrupted: '000";Budget Type:Original;Start Date:2021-04-01...'
        
        raw_data = self.other_identifier.strip()
        
        # Look for Reference: pattern first
        import re
        ref_match = re.search(r'Reference:([^;]+)', raw_data)
        if ref_match:
            return ref_match.group(1).strip()
        
        # Look for Other Identifier Type pattern
        type_match = re.search(r'Other Identifier Type:([^;]+)', raw_data)
        if type_match:
            return f"Type: {type_match.group(1).strip()}"
        
        # Extract clean part before corruption indicators
        corruption_indicators = [
            ';Budget Type:',
            '";Budget Type:',
            ';Start Date:',
            ';End Date:',
            ';Value Date:'
        ]
        
        clean_part = raw_data
        for indicator in corruption_indicators:
            if indicator in clean_part:
                clean_part = clean_part.split(indicator)[0]
        
        # Remove trailing quotes and semicolons
        clean_part = clean_part.rstrip('";').strip()
        
        # If it's empty, return None
        if not clean_part or clean_part == '':
            return None
            
        # If it's just "000" or similar, it's probably not useful  
        if clean_part in ['000', '0', '00']:
            return None
            
        # If it still looks like budget data, return None  
        if 'Budget Type:' in clean_part or 'Value:' in clean_part:
            return None
            
        return clean_part if clean_part else None
    
    @property
    def clean_budget_info(self):
        """Extract and format clean budget information using correct amounts"""
        if not self.budget or not self.maximum_contribution:
            return None
            
        import re
        budget_entries = []
        
        raw_budget = self.budget.strip()
        
        # Extract date ranges (these are usually intact)
        date_matches = re.findall(r'Start Date:([^;]+).*?End Date:([^;]+)', raw_budget)
        
        if date_matches:
            # Use the correct maximum_contribution amount instead of corrupted values
            total_amount = float(self.maximum_contribution)
            
            if len(date_matches) == 1:
                # Single period - use full amount
                start_date, end_date = date_matches[0]
                budget_entries.append({
                    'period': f"{start_date.strip()} to {end_date.strip()}",
                    'amount': f"${total_amount:,.0f} CAD"
                })
            else:
                # Multiple periods - show total for each (since we don't know the breakdown)
                for i, (start_date, end_date) in enumerate(date_matches, 1):
                    period_label = f"Period {i}: {start_date.strip()} to {end_date.strip()}"
                    budget_entries.append({
                        'period': period_label,
                        'amount': f"${total_amount:,.0f} CAD (total project value)"
                    })
        else:
            # No date info, just show the total amount
            budget_entries.append({
                'period': 'Total Project Budget',
                'amount': f"${float(self.maximum_contribution):,.0f} CAD"
            })
        
        return budget_entries if budget_entries else None


class TaxBracket(models.Model):
    """Canadian federal tax brackets for calculator"""
    year = models.IntegerField()
    min_income = models.DecimalField(max_digits=12, decimal_places=2)
    max_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4)  # e.g., 0.1500 for 15%
    
    class Meta:
        ordering = ['year', 'min_income']
    
    def __str__(self):
        max_str = f"${self.max_income:,.0f}" if self.max_income else "∞"
        return f"{self.year}: ${self.min_income:,.0f} - {max_str} @ {self.tax_rate*100:.1f}%"


class CanadianTaxData(models.Model):
    """Store Canadian tax revenue data for calculations"""
    year = models.IntegerField(unique=True)
    total_federal_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    gst_hst_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    income_tax_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    
    def __str__(self):
        return f"{self.year} - Total Revenue: ${self.total_federal_revenue:,.0f}"