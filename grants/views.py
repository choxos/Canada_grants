from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Max, Min, Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db import models
import json
from decimal import Decimal
from .models import Grant, GlobalAffairsGrant


def home(request):
    """Homepage with overview stats"""
    # Domestic grants stats
    domestic_total_value = Grant.objects.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0
    domestic_count = Grant.objects.count()
    
    # GAC grants stats  
    gac_total_value = GlobalAffairsGrant.objects.aggregate(Sum('maximum_contribution'))['maximum_contribution__sum'] or 0
    gac_count = GlobalAffairsGrant.objects.count()
    
    # Combined stats
    total_value = domestic_total_value + gac_total_value
    total_count = domestic_count + gac_count
    
    # Recent Major Funding - combine domestic and GAC
    recent_major = []
    
    # Get major domestic grants (over $1M)
    domestic_major = Grant.objects.filter(
        agreement_value__gte=1000000
    ).order_by('-agreement_value')[:3]
    
    for grant in domestic_major:
        recent_major.append({
            'id': grant.id,
            'title': grant.agreement_title_en,
            'recipient': grant.recipient_legal_name,
            'value': grant.agreement_value,
            'type': 'domestic',
            'url': grant.get_absolute_url(),
            'badge_class': 'major-funding-badge'
        })
    
    # Get major GAC grants (over $1M)
    gac_major = GlobalAffairsGrant.objects.filter(
        maximum_contribution__gte=1000000
    ).order_by('-maximum_contribution')[:3]
    
    for grant in gac_major:
        recent_major.append({
            'id': f"gac_{grant.id}",
            'title': grant.title,
            'recipient': grant.primary_country,
            'value': grant.maximum_contribution,
            'type': 'gac',
            'url': grant.get_absolute_url(),
            'badge_class': 'bg-info text-white'
        })
    
    # Sort all major grants by value and take top 5
    recent_major.sort(key=lambda x: x['value'], reverse=True)
    recent_major = recent_major[:5]
    
    # Notable Grants - combine notable domestic and special GAC grants
    notable_grants = []
    
    # Get notable domestic grants
    domestic_notable = Grant.objects.filter(is_notable=True).order_by('-agreement_value')[:3]
    
    for grant in domestic_notable:
        notable_grants.append({
            'id': grant.id,
            'title': grant.agreement_title_en,
            'reason': grant.notable_reason or 'Notable grant',
            'value': grant.agreement_value,
            'type': 'domestic',
            'url': grant.get_absolute_url(),
            'badge_class': 'notable-badge'
        })
    
    # Get GAC grants with special policy markers
    gac_notable = GlobalAffairsGrant.objects.filter(
        Q(policy_markers__icontains='gender') |
        Q(policy_markers__icontains='environmental') |
        Q(maximum_contribution__gte=5000000)  # Very large international grants
    ).order_by('-maximum_contribution')[:3]
    
    for grant in gac_notable:
        reason = "International development"
        if grant.policy_markers and 'gender' in grant.policy_markers.lower():
            reason = "Gender equality focus"
        elif grant.policy_markers and 'environmental' in grant.policy_markers.lower():
            reason = "Environmental sustainability"
        elif grant.maximum_contribution >= 5000000:
            reason = "Major international funding"
            
        notable_grants.append({
            'id': f"gac_{grant.id}",
            'title': grant.title,
            'reason': reason,
            'value': grant.maximum_contribution,
            'type': 'gac',
            'url': grant.get_absolute_url(),
            'badge_class': 'bg-success text-white'
        })
    
    # Sort notable grants by value and take top 5
    notable_grants.sort(key=lambda x: x['value'], reverse=True)
    notable_grants = notable_grants[:5]
    
    context = {
        'total_count': total_count,
        'total_value': total_value,
        'domestic_grants': domestic_count,
        'domestic_value': domestic_total_value,
        'gac_grants': gac_count, 
        'gac_value': gac_total_value,
        'avg_grant_value': total_value / total_count if total_count > 0 else 0,
        'recent_major': recent_major,
        'notable_grants': notable_grants,
    }
    return render(request, 'grants/home.html', context)


def grant_list(request):
    """List domestic grants with search and filtering"""
    grants = Grant.objects.all()
    
    # Search
    query = request.GET.get('q')
    if query:
        grants = grants.filter(
            Q(agreement_title_en__icontains=query) |
            Q(recipient_legal_name__icontains=query) |
            Q(description_en__icontains=query)
        )
    
    # Filters
    province = request.GET.get('province')
    if province:
        grants = grants.filter(recipient_province=province)
        
    year = request.GET.get('year')
    if year:
        grants = grants.filter(fiscal_year=year)
        
    min_value = request.GET.get('min_value')
    if min_value:
        try:
            grants = grants.filter(agreement_value__gte=Decimal(min_value))
        except:
            pass
            
    max_value = request.GET.get('max_value')
    if max_value:
        try:
            grants = grants.filter(agreement_value__lte=Decimal(max_value))
        except:
            pass

    # Sorting
    sort_by = request.GET.get('sort', '-agreement_value')
    grants = grants.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(grants, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    provinces = Grant.objects.values_list('recipient_province', flat=True).distinct().order_by('recipient_province')
    years = Grant.objects.values_list('fiscal_year', flat=True).distinct().order_by('-fiscal_year')
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'provinces': provinces,
        'years': years,
        'current_filters': {
            'province': province,
            'year': year,
            'min_value': min_value,
            'max_value': max_value,
            'sort': sort_by,
        }
    }
    return render(request, 'grants/grant_list.html', context)


def grant_detail(request, pk):
    """Detailed view of a single domestic grant"""
    grant = get_object_or_404(Grant, pk=pk)
    return render(request, 'grants/grant_detail.html', {'grant': grant})


def major_funding(request):
    """List major funding grants (over $1M)"""
    grants = Grant.objects.filter(is_major_funding=True).order_by('-agreement_value')
    
    paginator = Paginator(grants, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_value = grants.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'total_value': total_value,
        'grant_count': grants.count(),
    }
    return render(request, 'grants/major_funding.html', context)


def notable_grants(request):
    """List notable/controversial grants"""
    grants = Grant.objects.filter(is_notable=True).order_by('-agreement_value')
    
    paginator = Paginator(grants, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'grant_count': grants.count(),
    }
    return render(request, 'grants/notable_grants.html', context)


# =============================================================================
# GLOBAL AFFAIRS CANADA (GAC) VIEWS
# =============================================================================

def gac_grant_list(request):
    """List GAC international development grants"""
    grants = GlobalAffairsGrant.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        grants = grants.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(executing_agency_partner__icontains=search_query) |
            Q(program_name__icontains=search_query)
        )
    
    # Filters
    status = request.GET.get('status')
    if status:
        grants = grants.filter(status=status)
        
    country = request.GET.get('country')
    if country:
        grants = grants.filter(country__icontains=country)
        
    region = request.GET.get('region')
    if region:
        grants = grants.filter(region__icontains=region)
        
    program = request.GET.get('program')
    if program:
        grants = grants.filter(program_name__icontains=program)
        
    dac_sector = request.GET.get('dac_sector')
    if dac_sector:
        grants = grants.filter(dac_sector__icontains=dac_sector)
        
    min_value = request.GET.get('min_value')
    if min_value:
        try:
            grants = grants.filter(maximum_contribution__gte=Decimal(min_value))
        except:
            pass
            
    max_value = request.GET.get('max_value')
    if max_value:
        try:
            grants = grants.filter(maximum_contribution__lte=Decimal(max_value))
        except:
            pass

    # Special filters
    major_only = request.GET.get('major_only')
    if major_only:
        grants = grants.filter(maximum_contribution__gte=1000000)
        
    policy_marker = request.GET.get('policy_marker')
    if policy_marker == 'gender':
        grants = grants.filter(policy_markers__icontains='gender')
    elif policy_marker == 'environment':
        grants = grants.filter(policy_markers__icontains='environmental')
    elif policy_marker == 'governance':
        grants = grants.filter(policy_markers__icontains='governance')

    # Sorting
    sort_by = request.GET.get('sort', '-maximum_contribution')
    grants = grants.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(grants, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options for dropdowns
    status_choices = GlobalAffairsGrant.STATUS_CHOICES
    
    # Get unique countries (cleaned)
    countries = list(GlobalAffairsGrant.objects.exclude(country='').values_list('country', flat=True).distinct())
    cleaned_countries = []
    for country in countries:
        if ':' in country:
            clean_country = country.split(':')[0].strip()
        else:
            clean_country = country.strip()
        if clean_country and clean_country not in cleaned_countries:
            cleaned_countries.append(clean_country)
    countries = sorted(cleaned_countries)[:30]  # Top 30 countries
    
    # Get unique regions
    regions = list(GlobalAffairsGrant.objects.exclude(region='').values_list('region', flat=True).distinct().order_by('region')[:25])
    
    # Get unique programs
    programs = list(GlobalAffairsGrant.objects.exclude(program_name='').values_list('program_name', flat=True).distinct().order_by('program_name')[:30])
    
    # Get unique DAC sectors
    dac_sectors = []
    for sector in GlobalAffairsGrant.objects.exclude(dac_sector='').values_list('dac_sector', flat=True).distinct():
        # Split by semicolon and take first part
        if ':' in sector:
            clean_sector = sector.split(':')[0].strip()
            if clean_sector and clean_sector not in dac_sectors:
                dac_sectors.append(clean_sector)
    dac_sectors = sorted(dac_sectors)[:20]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_choices': status_choices,
        'countries': countries,
        'regions': regions,
        'programs': programs,
        'dac_sectors': dac_sectors,
        'current_filters': {
            'status': status,
            'country': country,
            'region': region,
            'program': program,
            'dac_sector': dac_sector,
            'min_value': min_value,
            'max_value': max_value,
            'major_only': major_only,
            'policy_marker': policy_marker,
            'sort': sort_by,
        }
    }
    return render(request, 'grants/gac_grant_list.html', context)


def gac_grant_detail(request, pk):
    """Detailed view of a single GAC grant"""
    grant = get_object_or_404(GlobalAffairsGrant, pk=pk)
    return render(request, 'grants/gac_grant_detail.html', {'grant': grant})


def gac_statistics(request):
    """Statistics page for GAC grants"""
    grants = GlobalAffairsGrant.objects.all()
    
    # Basic stats
    total_grants = grants.count()
    total_value = grants.aggregate(Sum('maximum_contribution'))['maximum_contribution__sum'] or 0
    avg_value = grants.aggregate(Avg('maximum_contribution'))['maximum_contribution__avg'] or 0
    
    # Status breakdown
    status_data = list(grants.values('status').annotate(
        count=Count('id'),
        total_value=Sum('maximum_contribution'),
        avg_value=Avg('maximum_contribution')
    ).order_by('status'))
    
    # Convert Decimal to float for JSON serialization
    for item in status_data:
        item['total_value'] = float(item['total_value'] or 0)
        item['avg_value'] = float(item['avg_value'] or 0)
    
    # Top countries (temporarily include blank to diagnose the issue)
    country_data = list(grants.values('country').annotate(
        count=Count('id'),
        total_value=Sum('maximum_contribution')
    ).order_by('-total_value')[:20])
    
    for item in country_data:
        item['total_value'] = float(item['total_value'] or 0)
        # Clean up country names (remove percentages)
        country = item['country'].split(':')[0].strip() if ':' in item['country'] else item['country']
        item['country'] = country[:30]  # Truncate long names
    
    # Top regions
    region_data = list(grants.exclude(region='').values('region').annotate(
        count=Count('id'),
        total_value=Sum('maximum_contribution')
    ).order_by('-total_value')[:15])
    
    for item in region_data:
        item['total_value'] = float(item['total_value'] or 0)
    
    # Major funding (over $1M)
    major_funding = grants.filter(maximum_contribution__gte=1000000)
    major_count = major_funding.count()
    major_value = major_funding.aggregate(Sum('maximum_contribution'))['maximum_contribution__sum'] or 0
    
    # Policy markers analysis
    gender_grants = grants.filter(policy_markers__icontains='gender').count()
    env_grants = grants.filter(policy_markers__icontains='environmental').count()
    governance_grants = grants.filter(policy_markers__icontains='governance').count()
    
    context = {
        'total_grants': total_grants,
        'total_value': float(total_value),
        'avg_value': float(avg_value),
        'major_count': major_count,
        'major_value': float(major_value),
        'status_data': json.dumps(status_data),
        'country_data': json.dumps(country_data),
        'region_data': json.dumps(region_data),
        'gender_grants': gender_grants,
        'env_grants': env_grants,
        'governance_grants': governance_grants,
    }
    return render(request, 'grants/gac_statistics.html', context)


# =============================================================================
# EXISTING DOMESTIC GRANTS VIEWS
# =============================================================================

def statistics_page(request):
    """Comprehensive statistics dashboard for domestic grants"""
    grants = Grant.objects.all()
    
    # Basic statistics
    total_grants = grants.count()
    total_value = grants.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0
    avg_value = grants.aggregate(Avg('agreement_value'))['agreement_value__avg'] or 0
    median_value = grants.order_by('agreement_value')[total_grants//2].agreement_value if total_grants > 0 else 0
    
    # Top grants
    top_grants = grants.order_by('-agreement_value')[:10]
    
    # Yearly data for charts
    yearly_data_raw = list(
        grants.values('fiscal_year')
        .annotate(
            count=Count('id'),
            total_value=Sum('agreement_value'),
            avg_value=Avg('agreement_value'),
            major_count=Count('id', filter=Q(is_major_funding=True)),
            notable_count=Count('id', filter=Q(is_notable=True))
        )
        .order_by('fiscal_year')
    )
    
    # Convert Decimal values to float for JavaScript
    yearly_data = []
    for year in yearly_data_raw:
        yearly_data.append({
            'fiscal_year': year['fiscal_year'],
            'count': year['count'],
            'total_value': float(year['total_value'] or 0),
            'avg_value': float(year['avg_value'] or 0),
            'major_count': year['major_count'],
            'notable_count': year['notable_count']
        })
    
    # Provincial data
    provincial_data_raw = list(
        grants.values('recipient_province')
        .annotate(
            count=Count('id'),
            total_value=Sum('agreement_value'),
            avg_value=Avg('agreement_value'),
            unique_recipients=Count('recipient_legal_name', distinct=True)
        )
        .order_by('-total_value')
    )
    
    # Convert Decimal values and calculate value_per_recipient
    provincial_data = []
    for province in provincial_data_raw:
        total_val = float(province['total_value'] or 0)
        unique_recip = province['unique_recipients'] or 1
        provincial_data.append({
            'recipient_province': province['recipient_province'],
            'count': province['count'],
            'total_value': total_val,
            'avg_value': float(province['avg_value'] or 0),
            'unique_recipients': unique_recip,
            'value_per_recipient': total_val / unique_recip
        })
    
    # Top recipients
    top_recipients_raw = list(
        grants.values('recipient_legal_name')
        .annotate(
            count=Count('id'),
            total_value=Sum('agreement_value')
        )
        .order_by('-total_value')[:20]
    )
    
    top_recipients = []
    for recipient in top_recipients_raw:
        top_recipients.append({
            'recipient_legal_name': recipient['recipient_legal_name'],
            'count': recipient['count'],
            'total_value': float(recipient['total_value'] or 0)
        })
    
    # Sector analysis
    sector_data_raw = list(
        grants.exclude(naics_sector_en='')
        .values('naics_sector_en')
        .annotate(
            count=Count('id'),
            total_value=Sum('agreement_value')
        )
        .order_by('-total_value')[:15]
    )
    
    sector_data = []
    for sector in sector_data_raw:
        sector_data.append({
            'naics_sector_en': sector['naics_sector_en'],
            'count': sector['count'],
            'total_value': float(sector['total_value'] or 0)
        })
    
    # Program analysis
    program_data_raw = list(
        grants.values('program_name_en')
        .annotate(
            count=Count('id'),
            total_value=Sum('agreement_value')
        )
        .order_by('-total_value')[:15]
    )
    
    program_data = []
    for program in program_data_raw:
        program_data.append({
            'program_name_en': program['program_name_en'],
            'count': program['count'],
            'total_value': float(program['total_value'] or 0)
        })
    
    # Value distribution
    value_ranges = [
        ('Under $10K', 0, 10000),
        ('$10K - $50K', 10000, 50000),
        ('$50K - $100K', 50000, 100000),
        ('$100K - $500K', 100000, 500000),
        ('$500K - $1M', 500000, 1000000),
        ('$1M - $10M', 1000000, 10000000),
        ('Over $10M', 10000000, float('inf'))
    ]
    
    value_distribution = []
    for range_name, min_val, max_val in value_ranges:
        if max_val == float('inf'):
            range_grants = grants.filter(agreement_value__gte=min_val)
        else:
            range_grants = grants.filter(agreement_value__gte=min_val, agreement_value__lt=max_val)
        
        count = range_grants.count()
        total_val = range_grants.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0
        percentage = (count / total_grants * 100) if total_grants > 0 else 0
        
        value_distribution.append({
            'range': range_name,
            'count': count,
            'total_value': float(total_val),
            'percentage': round(percentage, 1)
        })
    
    # Recipient type analysis
    recipient_type_data_raw = list(
        grants.values('recipient_type')
        .annotate(
            count=Count('id'),
            total_value=Sum('agreement_value')
        )
        .order_by('-total_value')
    )
    
    recipient_type_data = []
    for rtype in recipient_type_data_raw:
        recipient_type_data.append({
            'recipient_type': rtype['recipient_type'],
            'count': rtype['count'],
            'total_value': float(rtype['total_value'] or 0)
        })
    
    # Notable category breakdown
    notable_breakdown = {
        'controversial': {
            'count': grants.filter(is_controversial=True).count(),
            'total_value': float(grants.filter(is_controversial=True).aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0)
        },
        'major_funding': {
            'count': grants.filter(is_major_funding=True).count(),
            'total_value': float(grants.filter(is_major_funding=True).aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0)
        },
        'notable': {
            'count': grants.filter(is_notable=True).count(),
            'total_value': float(grants.filter(is_notable=True).aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0)
        }
    }
    
    context = {
        'total_grants': total_grants,
        'total_value': total_value,
        'avg_value': avg_value,
        'median_value': median_value,
        'top_grants': top_grants,
        'yearly_data': json.dumps(yearly_data),
        'provincial_data': provincial_data,
        'top_recipients': top_recipients,
        'sector_data': json.dumps(sector_data),
        'program_data': json.dumps(program_data),
        'value_distribution': json.dumps(value_distribution),
        'recipient_type_data': json.dumps(recipient_type_data),
        'notable_breakdown': json.dumps(notable_breakdown),
    }
    return render(request, 'grants/statistics.html', context)


def api_documentation(request):
    """API documentation page"""
    return render(request, 'grants/api_documentation.html')


# =============================================================================
# API ENDPOINTS 
# =============================================================================

def grant_stats_api(request):
    """Basic grant statistics API"""
    grants = Grant.objects.all()
    
    stats = {
        'total_grants': grants.count(),
        'total_value': float(grants.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0),
        'avg_value': float(grants.aggregate(Avg('agreement_value'))['agreement_value__avg'] or 0),
        'provinces': grants.values_list('recipient_province', flat=True).distinct().count(),
        'major_funding_count': grants.filter(is_major_funding=True).count(),
        'notable_count': grants.filter(is_notable=True).count(),
    }
    
    return JsonResponse(stats)


def grants_search_api(request):
    """Advanced grants search API"""
    grants = Grant.objects.all()
    
    # Search parameters
    query = request.GET.get('q', '')
    province = request.GET.get('province', '')
    year = request.GET.get('year', '')
    min_value = request.GET.get('min_value', '')
    max_value = request.GET.get('max_value', '')
    recipient_type = request.GET.get('recipient_type', '')
    sort_by = request.GET.get('sort', '-agreement_value')
    limit = min(int(request.GET.get('limit', 100)), 1000)  # Max 1000 results
    
    # Apply filters
    if query:
        grants = grants.filter(
            Q(agreement_title_en__icontains=query) |
            Q(recipient_legal_name__icontains=query) |
            Q(description_en__icontains=query)
        )
    
    if province:
        grants = grants.filter(recipient_province__iexact=province)
    
    if year:
        grants = grants.filter(fiscal_year=year)
        
    if min_value:
        try:
            grants = grants.filter(agreement_value__gte=Decimal(min_value))
        except:
            pass
    
    if max_value:
        try:
            grants = grants.filter(agreement_value__lte=Decimal(max_value))
        except:
            pass
            
    if recipient_type:
        grants = grants.filter(recipient_type=recipient_type)
    
    # Sort and limit
    grants = grants.order_by(sort_by)[:limit]
    
    # Serialize results
    results = []
    for grant in grants:
        results.append({
            'id': grant.id,
            'title': grant.agreement_title_en,
            'recipient': grant.recipient_legal_name,
            'value': float(grant.agreement_value),
            'province': grant.recipient_province,
            'fiscal_year': grant.fiscal_year,
            'is_major_funding': grant.is_major_funding,
            'is_notable': grant.is_notable,
            'program': grant.program_name_en,
        })
    
    return JsonResponse({
        'count': len(results),
        'results': results
    })


def recipients_api(request):
    """Top recipients analysis API"""
    limit = min(int(request.GET.get('limit', 50)), 200)
    
    recipients = Grant.objects.values('recipient_legal_name', 'recipient_type').annotate(
        grant_count=Count('id'),
        total_value=Sum('agreement_value'),
        avg_value=Avg('agreement_value')
    ).order_by('-total_value')[:limit]
    
    results = []
    for recipient in recipients:
        results.append({
            'name': recipient['recipient_legal_name'],
            'type': recipient['recipient_type'],
            'grant_count': recipient['grant_count'],
            'total_value': float(recipient['total_value']),
            'avg_value': float(recipient['avg_value']),
        })
    
    return JsonResponse({
        'count': len(results),
        'recipients': results
    })


def comprehensive_stats_api(request):
    """Comprehensive statistics API"""
    grants = Grant.objects.all()
    
    # Basic stats
    basic_stats = {
        'total_grants': grants.count(),
        'total_value': float(grants.aggregate(Sum('agreement_value'))['agreement_value__sum'] or 0),
        'avg_value': float(grants.aggregate(Avg('agreement_value'))['agreement_value__avg'] or 0),
        'max_value': float(grants.aggregate(Max('agreement_value'))['agreement_value__max'] or 0),
        'min_value': float(grants.aggregate(Min('agreement_value'))['agreement_value__min'] or 0),
    }
    
    # Provincial breakdown
    provincial_stats = list(grants.values('recipient_province').annotate(
        count=Count('id'),
        total_value=Sum('agreement_value'),
        avg_value=Avg('agreement_value')
    ).order_by('-total_value'))
    
    for province in provincial_stats:
        province['total_value'] = float(province['total_value'])
        province['avg_value'] = float(province['avg_value'])
    
    # Yearly trends
    yearly_stats = list(grants.values('fiscal_year').annotate(
        count=Count('id'),
        total_value=Sum('agreement_value')
    ).order_by('fiscal_year'))
    
    for year in yearly_stats:
        year['total_value'] = float(year['total_value'])
    
    return JsonResponse({
        'basic_stats': basic_stats,
        'provincial_breakdown': provincial_stats[:10],
        'yearly_trends': yearly_stats,
        'top_sectors': list(grants.exclude(naics_sector_en='').values('naics_sector_en').annotate(
            count=Count('id'),
            total_value=Sum('agreement_value')
        ).order_by('-total_value')[:10])
    })


# =============================================================================
# GAC API ENDPOINTS
# =============================================================================

def gac_stats_api(request):
    """GAC grants statistics API"""
    grants = GlobalAffairsGrant.objects.all()
    
    stats = {
        'total_grants': grants.count(),
        'total_value': float(grants.aggregate(Sum('maximum_contribution'))['maximum_contribution__sum'] or 0),
        'avg_value': float(grants.aggregate(Avg('maximum_contribution'))['maximum_contribution__avg'] or 0),
        'operational_count': grants.filter(status='operational').count(),
        'closed_count': grants.filter(status='closed').count(),
        'terminating_count': grants.filter(status='terminating').count(),
        'countries_count': grants.values('country').distinct().count(),
    }
    
    return JsonResponse(stats)


def gac_search_api(request):
    """GAC grants search API"""
    grants = GlobalAffairsGrant.objects.all()
    
    # Search parameters
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    country = request.GET.get('country', '')
    min_value = request.GET.get('min_value', '')
    max_value = request.GET.get('max_value', '')
    sort_by = request.GET.get('sort', '-maximum_contribution')
    limit = min(int(request.GET.get('limit', 100)), 1000)
    
    # Apply filters
    if query:
        grants = grants.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(country__icontains=query)
        )
    
    if status:
        grants = grants.filter(status=status)
    
    if country:
        grants = grants.filter(country__icontains=country)
        
    if min_value:
        try:
            grants = grants.filter(maximum_contribution__gte=Decimal(min_value))
        except:
            pass
    
    if max_value:
        try:
            grants = grants.filter(maximum_contribution__lte=Decimal(max_value))
        except:
            pass
    
    # Sort and limit
    grants = grants.order_by(sort_by)[:limit]
    
    # Serialize results
    results = []
    for grant in grants:
        results.append({
            'id': grant.id,
            'project_number': grant.project_number,
            'title': grant.title,
            'country': grant.primary_country,
            'value': float(grant.maximum_contribution),
            'status': grant.status,
            'start_date': grant.start_date.isoformat() if grant.start_date else None,
            'end_date': grant.end_date.isoformat() if grant.end_date else None,
        })
    
    return JsonResponse({
        'count': len(results),
        'results': results
    })