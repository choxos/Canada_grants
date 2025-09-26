from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from decimal import Decimal
import json

from .models import TaxCalculation
from grants.models import Grant, GlobalAffairsGrant

def tax_calculator(request):
    """Tax contribution calculator page"""
    domestic_value = Grant.objects.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0
    domestic_count = Grant.objects.count()
    gac_value = GlobalAffairsGrant.objects.aggregate(Sum('maximum_contribution'))['maximum_contribution__sum'] or 0
    gac_count = GlobalAffairsGrant.objects.count()
    
    context = {
        'total_grants_value': domestic_value + gac_value,
        'total_grants_count': domestic_count + gac_count,
        'domestic_grants_value': domestic_value,
        'domestic_grants_count': domestic_count,
        'gac_grants_value': gac_value,
        'gac_grants_count': gac_count,
    }
    return render(request, 'calculator/tax_calculator.html', context)

@csrf_exempt
def calculate_tax_contribution(request):
    """API endpoint to calculate user's tax contribution"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        annual_income = Decimal(str(data.get('annual_income', 0)))
        gst_eligible_spending = Decimal(str(data.get('gst_eligible_spending', 0)))
        input_mode = data.get('input_mode', 'annual')
        original_income = Decimal(str(data.get('original_income', annual_income)))
        original_spending = Decimal(str(data.get('original_spending', gst_eligible_spending)))
        taxpayer_since_year = int(data.get('taxpayer_since_year', 2018))
        include_gac = data.get('include_gac', True)
        
        # Calculate monthly values
        monthly_income = annual_income / 12
        monthly_gst_spending = gst_eligible_spending / 12
        
        # Calculate taxes
        federal_income_tax = TaxCalculation.calculate_federal_income_tax(annual_income)
        monthly_federal_tax = federal_income_tax / 12
        gst_paid = TaxCalculation.calculate_gst_paid(gst_eligible_spending)
        monthly_gst_paid = gst_paid / 12
        total_tax_contribution = federal_income_tax + gst_paid
        monthly_tax_contribution = total_tax_contribution / 12
        
        # Estimate total federal revenue (2024 data: ~$430B)
        estimated_federal_revenue = Decimal('430000000000')  # $430B
        
        # Calculate user's share of federal revenue
        revenue_share_percentage = (total_tax_contribution / estimated_federal_revenue) * 100
        
        # Estimate what percentage of federal budget goes to grants/contributions
        # Based on federal spending analysis: approximately 2.5% of federal budget
        grants_allocation_percentage = Decimal('2.5')
        
        # Store calculation (optional, for analytics)
        session_key = request.session.session_key or 'anonymous'
        
        calculation = TaxCalculation.objects.create(
            session_key=session_key,
            annual_income=annual_income,
            monthly_income=monthly_income,
            gst_eligible_spending=gst_eligible_spending,
            monthly_gst_spending=monthly_gst_spending,
            taxpayer_since_year=taxpayer_since_year,
            federal_income_tax=federal_income_tax,
            monthly_federal_tax=monthly_federal_tax,
            gst_paid=gst_paid,
            monthly_gst_paid=monthly_gst_paid,
            total_tax_contribution=total_tax_contribution,
            monthly_tax_contribution=monthly_tax_contribution,
            revenue_share_percentage=revenue_share_percentage,
            grants_allocation_percentage=grants_allocation_percentage
        )
        
        # Calculate shares of notable grants (both domestic and GAC)
        grant_shares = []
        
        # Domestic notable grants
        notable_grants = Grant.objects.filter(is_notable=True)[:5]
        for grant in notable_grants:
            user_share = calculation.calculate_grant_share(grant.agreement_value)
            grant_shares.append({
                'id': grant.id,
                'title': grant.agreement_title_en,
                'total_value': float(grant.agreement_value),
                'user_share': float(user_share),
                'user_share_formatted': TaxCalculation.format_currency_amount(float(user_share)),
                'recipient': grant.recipient_legal_name,
                'fiscal_year': grant.fiscal_year,
                'grant_type': 'domestic',
                'category': 'Notable Domestic Grant'
            })
        
        # Major GAC grants if including GAC
        if include_gac:
            major_gac_grants = GlobalAffairsGrant.objects.filter(maximum_contribution__gte=1000000).order_by('-maximum_contribution')[:5]
            for grant in major_gac_grants:
                user_share = calculation.calculate_grant_share(grant.maximum_contribution)
                grant_shares.append({
                    'id': f"gac_{grant.id}",
                    'title': grant.title,
                    'total_value': float(grant.maximum_contribution),
                    'user_share': float(user_share),
                    'user_share_formatted': TaxCalculation.format_currency_amount(float(user_share)),
                    'recipient': grant.primary_country,
                    'fiscal_year': grant.start_date.year if grant.start_date else 'N/A',
                    'grant_type': 'gac',
                    'category': 'Major International Development'
                })
        
        # Sort all grants by user share descending
        grant_shares.sort(key=lambda x: x['user_share'], reverse=True)
        
        # Calculate sophisticated yearly contributions with project duration analysis
        yearly_contributions = calculation.calculate_yearly_contributions(include_gac=include_gac)
        
        # Convert to list format and apply formatting
        yearly_breakdown = []
        for year in sorted(yearly_contributions.keys()):
            data = yearly_contributions[year]
            yearly_breakdown.append({
                'year': year,
                'user_share': float(data['total_contribution']),
                'user_share_formatted': TaxCalculation.format_currency_amount(float(data['total_contribution'])),
                'domestic_share': float(data.get('domestic_contribution', 0)),
                'domestic_share_formatted': TaxCalculation.format_currency_amount(float(data.get('domestic_contribution', 0))),
                'gac_share': float(data.get('gac_contribution', 0)),
                'gac_share_formatted': TaxCalculation.format_currency_amount(float(data.get('gac_contribution', 0))),
                'grant_count': data['grant_count'],
                'domestic_count': data.get('domestic_count', 0),
                'gac_count': data.get('gac_count', 0),
                'top_projects': sorted(data['projects'], key=lambda x: x['user_annual_share'], reverse=True)[:5]
            })
        
        # Calculate future projections
        future_projections = calculation.calculate_future_projections(10)
        
        # Calculate share of total grants spending
        domestic_grants_value = Grant.objects.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0
        gac_grants_value = 0
        if include_gac:
            gac_grants_value = GlobalAffairsGrant.objects.aggregate(Sum('maximum_contribution'))['maximum_contribution__sum'] or 0
        
        total_grants_value = domestic_grants_value + gac_grants_value
        total_grants_share = calculation.calculate_grant_share(total_grants_value)
        monthly_grants_share = calculation.calculate_monthly_grant_share(total_grants_value)
        
        # Calculate separate shares
        domestic_grants_share = calculation.calculate_grant_share(domestic_grants_value)
        gac_grants_share = calculation.calculate_grant_share(gac_grants_value) if include_gac else 0
        
        # Calculate how much of user's taxes actually goes to grants
        grants_portion_of_taxes = total_tax_contribution * grants_allocation_percentage / 100
        monthly_grants_portion = grants_portion_of_taxes / 12
        
        response_data = {
            'success': True,
            'calculation': {
                'annual_income': float(annual_income),
                'monthly_income': float(monthly_income),
                'taxpayer_since_year': taxpayer_since_year,
                'federal_income_tax': float(federal_income_tax),
                'monthly_federal_tax': float(monthly_federal_tax),
                'gst_paid': float(gst_paid),
                'monthly_gst_paid': float(monthly_gst_paid),
                'total_tax_contribution': float(total_tax_contribution),
                'monthly_tax_contribution': float(monthly_tax_contribution),
                'revenue_share_percentage': float(revenue_share_percentage),
                'grants_allocation_percentage': float(grants_allocation_percentage),
                'grants_portion_of_taxes': float(grants_portion_of_taxes),
                'monthly_grants_portion': float(monthly_grants_portion),
                'input_mode': input_mode,
                'original_income': float(original_income),
                'original_spending': float(original_spending),
                # Formatted amounts
                'total_tax_contribution_formatted': TaxCalculation.format_currency_amount(float(total_tax_contribution)),
                'grants_portion_of_taxes_formatted': TaxCalculation.format_currency_amount(float(grants_portion_of_taxes)),
                'monthly_grants_portion_formatted': TaxCalculation.format_currency_amount(float(monthly_grants_portion)),
            },
            'grant_shares': grant_shares,
            'yearly_breakdown': yearly_breakdown,
            'future_projections': future_projections,
            'total_grants_share': float(total_grants_share),
            'total_grants_share_formatted': TaxCalculation.format_currency_amount(float(total_grants_share)),
            'monthly_grants_share': float(monthly_grants_share),
            'monthly_grants_share_formatted': TaxCalculation.format_currency_amount(float(monthly_grants_share)),
            'total_grants_value': float(total_grants_value),
            'include_gac': include_gac,
            'breakdown': {
                'domestic_grants_value': float(domestic_grants_value),
                'domestic_grants_share': float(domestic_grants_share),
                'domestic_grants_share_formatted': TaxCalculation.format_currency_amount(float(domestic_grants_share)),
                'gac_grants_value': float(gac_grants_value),
                'gac_grants_share': float(gac_grants_share),
                'gac_grants_share_formatted': TaxCalculation.format_currency_amount(float(gac_grants_share)),
                'domestic_percentage': float(domestic_grants_share / total_grants_share * 100) if total_grants_share > 0 else 0.0,
                'gac_percentage': float(gac_grants_share / total_grants_share * 100) if total_grants_share > 0 else 0.0,
            },
        }
        
        return JsonResponse(response_data)
        
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid input: {str(e)}',
            'error_type': 'validation'
        }, status=400)
    except ZeroDivisionError as e:
        return JsonResponse({
            'success': False,
            'error': 'Division by zero in calculation - this may indicate missing grant data',
            'error_type': 'calculation'
        }, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': f'Calculation error: {str(e)}',
            'error_type': 'server',
            'debug_info': traceback.format_exc()
        }, status=500)

def grant_share_calculator(request, grant_id):
    """Calculate user's share of a specific grant"""
    try:
        grant = Grant.objects.get(id=grant_id)
        
        # Get the most recent calculation for this session
        session_key = request.session.session_key or 'anonymous'
        calculation = TaxCalculation.objects.filter(session_key=session_key).first()
        
        if not calculation:
            return JsonResponse({'error': 'No tax calculation found. Please use the calculator first.'}, status=400)
        
        user_share = calculation.calculate_grant_share(grant.agreement_value)
        
        response_data = {
            'grant': {
                'id': grant.id,
                'title': grant.agreement_title_en,
                'recipient': grant.recipient_legal_name,
                'total_value': float(grant.agreement_value),
                'description': grant.description_en[:200] + '...' if len(grant.description_en) > 200 else grant.description_en,
            },
            'user_share': float(user_share),
            'percentage_of_income': float((user_share / calculation.annual_income) * 100) if calculation.annual_income > 0 else 0,
        }
        
        return JsonResponse(response_data)
        
    except Grant.DoesNotExist:
        return JsonResponse({'error': 'Grant not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)