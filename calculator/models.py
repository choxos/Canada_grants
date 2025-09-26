from django.db import models
from decimal import Decimal

class TaxCalculation(models.Model):
    """Store user tax calculations for reference"""
    session_key = models.CharField(max_length=40)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_eligible_spending = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_gst_spending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # When user started being a Canadian taxpayer
    taxpayer_since_year = models.IntegerField(default=2018)
    
    # Calculated values
    federal_income_tax = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_federal_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_paid = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_gst_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax_contribution = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_tax_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # User's share of total federal revenue (as percentage)
    revenue_share_percentage = models.DecimalField(max_digits=10, decimal_places=8)
    
    # Grant spending allocation percentage (what % of federal budget goes to grants)
    grants_allocation_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.5'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Income: ${self.annual_income:,.0f} - Tax: ${self.total_tax_contribution:,.0f}"
    
    @staticmethod
    def calculate_federal_income_tax(annual_income):
        """Calculate federal income tax based on 2024 brackets"""
        # 2024 Federal tax brackets
        brackets = [
            (53359, 0.15),    # 15% on first $53,359
            (53358, 0.205),   # 20.5% on next $53,358 ($53,359 to $106,717)
            (58204, 0.26),    # 26% on next $58,204 ($106,717 to $164,921)
            (99462, 0.29),    # 29% on next $99,462 ($164,921 to $264,383)
            (float('inf'), 0.33)  # 33% on income over $264,383
        ]
        
        tax = Decimal('0')
        remaining_income = Decimal(str(annual_income))
        
        for bracket_limit, rate in brackets:
            if remaining_income <= 0:
                break
                
            taxable_in_bracket = min(remaining_income, Decimal(str(bracket_limit)))
            tax += taxable_in_bracket * Decimal(str(rate))
            remaining_income -= taxable_in_bracket
        
        return tax
    
    @staticmethod
    def calculate_gst_paid(gst_eligible_spending):
        """Calculate GST paid (5% on eligible spending)"""
        return Decimal(str(gst_eligible_spending)) * Decimal('0.05')
    
    def calculate_grant_share(self, grant_value):
        """Calculate user's personal share of a specific grant"""
        # Only the portion of taxes that goes to grants should be considered
        effective_share = self.revenue_share_percentage * self.grants_allocation_percentage / 100
        return Decimal(str(grant_value)) * effective_share / 100
    
    def calculate_monthly_grant_share(self, grant_value):
        """Calculate user's monthly share of a specific grant"""
        annual_share = self.calculate_grant_share(grant_value)
        return annual_share / 12
    
    def calculate_yearly_contributions(self, include_gac=True):
        """Calculate year-by-year contribution breakdown with project duration analysis"""
        from grants.models import Grant, GlobalAffairsGrant
        from datetime import datetime
        import re
        
        yearly_contributions = {}
        
        # Process domestic grants
        grants = Grant.objects.all()
        for grant in grants:
            # Parse fiscal year to get actual years
            if grant.fiscal_year:
                # Handle fiscal years like "2023-24" or "2023-2024"
                year_match = re.match(r'(\d{4})', grant.fiscal_year)
                if year_match:
                    fiscal_year = int(year_match.group(1))
                else:
                    continue
            else:
                continue
                
            # Determine project duration
            start_year = fiscal_year
            end_year = fiscal_year  # Default to single year
            
            if grant.agreement_start_date and grant.agreement_end_date:
                start_year = grant.agreement_start_date.year
                end_year = grant.agreement_end_date.year
            elif grant.agreement_start_date:
                start_year = grant.agreement_start_date.year
                # Estimate end year based on fiscal year if no end date
                if fiscal_year > start_year:
                    end_year = fiscal_year
                else:
                    end_year = start_year + 2  # Assume 3-year project if unclear
            
            # Calculate duration and annual amount
            duration_years = max(1, end_year - start_year + 1)
            annual_amount = grant.agreement_value / duration_years
            
            # Calculate user's annual share of this grant
            annual_user_share = self.calculate_grant_share(annual_amount)
            
            # Add to yearly totals for years when user was taxpayer
            for year in range(start_year, end_year + 1):
                if year >= self.taxpayer_since_year:
                    if year not in yearly_contributions:
                        yearly_contributions[year] = {
                            'total_contribution': Decimal('0'),
                            'grant_count': 0,
                            'projects': [],
                            'domestic_contribution': Decimal('0'),
                            'gac_contribution': Decimal('0'),
                            'domestic_count': 0,
                            'gac_count': 0
                        }
                    
                    yearly_contributions[year]['total_contribution'] += annual_user_share
                    yearly_contributions[year]['domestic_contribution'] += annual_user_share
                    yearly_contributions[year]['grant_count'] += 1
                    yearly_contributions[year]['domestic_count'] += 1
                    yearly_contributions[year]['projects'].append({
                        'title': grant.agreement_title_en[:50] + ('...' if len(grant.agreement_title_en) > 50 else ''),
                        'recipient': grant.recipient_legal_name[:40] + ('...' if len(grant.recipient_legal_name) > 40 else ''),
                        'annual_value': float(annual_amount),
                        'user_annual_share': float(annual_user_share),
                        'total_value': float(grant.agreement_value),
                        'duration_years': duration_years,
                        'start_year': start_year,
                        'end_year': end_year,
                        'grant_type': 'domestic'
                    })
        
        # Process GAC grants if requested
        if include_gac:
            gac_grants = GlobalAffairsGrant.objects.all()
            for grant in gac_grants:
                # Determine project duration from actual dates
                start_year = None
                end_year = None
                
                if grant.start_date:
                    start_year = grant.start_date.year
                if grant.end_date:
                    end_year = grant.end_date.year
                    
                # If no dates available, estimate based on status
                if not start_year or not end_year:
                    current_year = datetime.now().year
                    if grant.status == 'operational':
                        start_year = start_year or 2018  # Conservative estimate
                        end_year = end_year or current_year + 2
                    elif grant.status == 'closed':
                        start_year = start_year or 2015
                        end_year = end_year or current_year - 1
                    elif grant.status == 'terminating':
                        start_year = start_year or 2018
                        end_year = end_year or current_year
                
                # Skip if we still don't have valid years
                if not start_year or not end_year or start_year > end_year:
                    continue
                    
                # Calculate duration and annual amount
                duration_years = max(1, end_year - start_year + 1)
                annual_amount = grant.maximum_contribution / duration_years
                
                # Calculate user's annual share of this grant
                annual_user_share = self.calculate_grant_share(annual_amount)
                
                # Add to yearly totals for years when user was taxpayer
                for year in range(start_year, end_year + 1):
                    if year >= self.taxpayer_since_year:
                        if year not in yearly_contributions:
                            yearly_contributions[year] = {
                                'total_contribution': Decimal('0'),
                                'grant_count': 0,
                                'projects': [],
                                'domestic_contribution': Decimal('0'),
                                'gac_contribution': Decimal('0'),
                                'domestic_count': 0,
                                'gac_count': 0
                            }
                        
                        yearly_contributions[year]['total_contribution'] += annual_user_share
                        yearly_contributions[year]['gac_contribution'] += annual_user_share
                        yearly_contributions[year]['grant_count'] += 1
                        yearly_contributions[year]['gac_count'] += 1
                        yearly_contributions[year]['projects'].append({
                            'title': grant.title[:50] + ('...' if len(grant.title) > 50 else ''),
                            'recipient': grant.primary_country[:40] + ('...' if len(grant.primary_country) > 40 else ''),
                            'annual_value': float(annual_amount),
                            'user_annual_share': float(annual_user_share),
                            'total_value': float(grant.maximum_contribution),
                            'duration_years': duration_years,
                            'start_year': start_year,
                            'end_year': end_year,
                            'grant_type': 'gac'
                        })
        
        return yearly_contributions
    
    def calculate_future_projections(self, projection_years=10):
        """Calculate future projections with and without new projects"""
        from datetime import datetime
        
        yearly_contributions = self.calculate_yearly_contributions()
        current_year = datetime.now().year
        
        # Scenario 1: Only continuing existing projects
        continuing_projects = {}
        
        # Find projects that extend beyond current year
        for year, data in yearly_contributions.items():
            if year > current_year:
                continuing_projects[year] = {
                    'total_contribution': data['total_contribution'],
                    'grant_count': data['grant_count'],
                    'scenario': 'continuing_only'
                }
        
        # Scenario 2: Add estimated new projects based on historical averages
        with_new_projects = continuing_projects.copy()
        
        # Calculate historical average yearly contribution (excluding future years)
        historical_years = [year for year in yearly_contributions.keys() if year <= current_year]
        if historical_years:
            total_historical_contribution = sum(
                yearly_contributions[year]['total_contribution'] 
                for year in historical_years
            )
            avg_yearly_contribution = total_historical_contribution / len(historical_years)
            avg_grant_count = sum(
                yearly_contributions[year]['grant_count'] 
                for year in historical_years
            ) / len(historical_years)
        else:
            avg_yearly_contribution = Decimal('0')
            avg_grant_count = 0
        
        # Project future years with estimated new projects
        for future_year in range(current_year + 1, current_year + projection_years + 1):
            existing_contribution = continuing_projects.get(future_year, {}).get('total_contribution', Decimal('0'))
            
            with_new_projects[future_year] = {
                'total_contribution': existing_contribution + avg_yearly_contribution,
                'grant_count': continuing_projects.get(future_year, {}).get('grant_count', 0) + int(avg_grant_count),
                'scenario': 'with_new_projects',
                'estimated_new_contribution': float(avg_yearly_contribution),
                'continuing_contribution': float(existing_contribution)
            }
        
        return {
            'continuing_only': continuing_projects,
            'with_new_projects': with_new_projects,
            'historical_average': float(avg_yearly_contribution)
        }
    
    @staticmethod
    def format_currency_amount(amount):
        """Format currency amounts, showing <$0.01 for very small amounts"""
        if amount < 0.01:
            return "<$0.01"
        else:
            return f"${amount:,.2f}"
    
    @property
    def monthly_calculations(self):
        """Return monthly breakdown of all calculations"""
        return {
            'monthly_income': self.monthly_income,
            'monthly_federal_tax': self.monthly_federal_tax,
            'monthly_gst_paid': self.monthly_gst_paid,
            'monthly_tax_contribution': self.monthly_tax_contribution,
            'monthly_grants_contribution': self.monthly_tax_contribution * self.grants_allocation_percentage / 100,
        }