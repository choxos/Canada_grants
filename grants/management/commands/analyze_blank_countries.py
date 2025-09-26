from django.core.management.base import BaseCommand
from grants.models import GlobalAffairsGrant
from django.db.models import Sum, Count


class Command(BaseCommand):
    help = 'Analyze grants with blank or empty country fields to understand the data issue'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Analyzing grants with blank country fields...")
        
        # Find grants with blank/empty countries
        blank_country_grants = GlobalAffairsGrant.objects.filter(country__in=['', None])
        blank_count = blank_country_grants.count()
        
        if blank_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No grants found with blank country fields"))
            return
        
        # Basic stats for blank country grants
        blank_stats = blank_country_grants.aggregate(
            total_value=Sum('maximum_contribution'),
            count=Count('id')
        )
        
        self.stdout.write(f"\n🚨 BLANK COUNTRY GRANTS ANALYSIS:")
        self.stdout.write(f"   📊 Total grants: {blank_stats['count']:,}")
        self.stdout.write(f"   💰 Total value: ${blank_stats['total_value']:,}")
        self.stdout.write(f"   💸 Average value: ${blank_stats['total_value']/blank_stats['count']:,.0f}")
        
        # Show sample grants for inspection
        self.stdout.write(f"\n🔍 SAMPLE BLANK COUNTRY GRANTS:")
        sample_grants = blank_country_grants.order_by('-maximum_contribution')[:10]
        
        for i, grant in enumerate(sample_grants, 1):
            self.stdout.write(f"\n{i}. Project: {grant.project_number}")
            self.stdout.write(f"   Title: {grant.title[:80]}...")
            self.stdout.write(f"   Value: ${grant.maximum_contribution:,}")
            self.stdout.write(f"   Status: {grant.status}")
            self.stdout.write(f"   Country field: '{grant.country}'")
            self.stdout.write(f"   Region: '{grant.region}'")
            self.stdout.write(f"   Locations: '{grant.locations[:100] if grant.locations else 'None'}...'")
            
        # Check if they have region or location data
        with_regions = blank_country_grants.exclude(region__in=['', None]).count()
        with_locations = blank_country_grants.exclude(locations__in=['', None]).count()
        
        self.stdout.write(f"\n📍 GEOGRAPHIC DATA ANALYSIS:")
        self.stdout.write(f"   🌍 Grants with region data: {with_regions} ({with_regions/blank_count*100:.1f}%)")
        self.stdout.write(f"   📍 Grants with location data: {with_locations} ({with_locations/blank_count*100:.1f}%)")
        
        # Show status breakdown
        status_breakdown = blank_country_grants.values('status').annotate(
            count=Count('id'),
            total_value=Sum('maximum_contribution')
        ).order_by('-total_value')
        
        self.stdout.write(f"\n📈 STATUS BREAKDOWN:")
        for status in status_breakdown:
            self.stdout.write(f"   {status['status']}: {status['count']} grants, ${status['total_value']:,}")
        
        # Compare to total dataset
        total_grants = GlobalAffairsGrant.objects.count()
        total_value = GlobalAffairsGrant.objects.aggregate(Sum('maximum_contribution'))['maximum_contribution__sum']
        
        self.stdout.write(f"\n🌐 IMPACT ON DATASET:")
        self.stdout.write(f"   📊 Blank countries: {blank_count:,} / {total_grants:,} grants ({blank_count/total_grants*100:.1f}%)")
        self.stdout.write(f"   💰 Blank value: ${blank_stats['total_value']:,} / ${total_value:,} ({blank_stats['total_value']/total_value*100:.1f}%)")
        
        # Recommendations
        self.stdout.write(f"\n💡 RECOMMENDATIONS:")
        if blank_stats['total_value'] / total_value > 0.5:
            self.stdout.write("   ⚠️  HIGH IMPACT: Blank countries represent >50% of total value")
            self.stdout.write("   ⚠️  This will severely skew map visualizations")
            self.stdout.write("   💡 Consider extracting country from region/location fields")
        elif blank_stats['total_value'] / total_value > 0.1:
            self.stdout.write("   ⚠️  MODERATE IMPACT: Blank countries represent >10% of total value")
            self.stdout.write("   💡 Exclude from map or extract from other fields")
        else:
            self.stdout.write("   ✅ LOW IMPACT: Safe to exclude blank countries from visualization")
        
        self.stdout.write(f"\n🔧 SUGGESTED ACTIONS:")
        self.stdout.write("   1. Exclude blank countries from country-based visualizations")
        self.stdout.write("   2. Investigate if region/location fields contain usable country data")
        self.stdout.write("   3. Consider creating separate 'Multi-country' or 'Regional' category")
        self.stdout.write("   4. Review original CSV data for data quality issues")
