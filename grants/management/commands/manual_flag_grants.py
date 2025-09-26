from django.core.management.base import BaseCommand
from grants.models import Grant

class Command(BaseCommand):
    help = 'Manually flag specific grants as notable based on review'
    
    def handle(self, *args, **options):
        # Reset all notable flags first
        Grant.objects.update(is_notable=False, notable_reason='')
        
        # Manually identified controversial/odd grants
        notable_grants = [
            # International Development / Foreign Spending
            (4509, "International business development - Canadian tax dollars for overseas business advisory"),
            (311, "Energy access in developing countries - foreign aid spending"),
            (2270, "South Africa commercialization - Canadian funds for foreign market development"),
            (1217, "South Africa expansion - Canadian tax dollars for overseas business expansion"),
            (16860, "African Moringa development - questionable relevance to Canadian priorities"),
            (18084, "African food ingredients - overseas agricultural development"),
            (4694, "GCC/APAC expansion - Middle East/Asia business development with Canadian funds"),
            
            # Gender/Diversity/Equity Programs
            (19869, "Women-led ventures catalyst - controversial gender-based funding criteria"),
            (9541, "Women-owned business integration - gender-specific business support"),
            (8040, "Women-owned business integration - gender-specific business support"),
            (13166, "Gender and DEI service delivery - divisive diversity programming"),
            (10542, "Diversity, Equity and Inclusion collaboration - controversial DEI initiatives"),
            (17594, "Diversity and Inclusion Initiative - divisive social programming"),
            (16372, "Diversity and Inclusion Initiative - divisive social programming"),
            (21327, "Equity, Diversity, and Inclusion product enhancements - forced DEI integration"),
            
            # Indigenous/Reconciliation Projects
            (17367, "Indigenous Community KnowledgeKeeper - expensive cultural preservation project"),
            (19818, "Indigenous & Women-Led manufacturing - identity-based funding criteria"),
            (2621, "Indigenous Knowledge Keeper Portal - costly cultural digitization project"),
            (9509, "Indigenous small business mentoring - race-based business support"),
            
            # Climate/Environmental Projects (often controversial)
            (17839, "Energy transition optimization - expensive climate change initiative"),
            (1459, "Energy transition optimization - expensive climate change initiative"),
            (12716, "Greening of manufacturing equipment - costly environmental retrofitting"),
            (246, "Youth Green hiring - climate activism job creation"),
            (112, "Green Youth development - environmental activism funding"),
            
            # Arts/Culture/Non-Essential Projects
            (8808, "Stop motion animation optimization - non-essential arts funding during economic hardship"),
            (9732, "Interior design recommendation engine - luxury service development"),
            
            # Questionable Agriculture Projects
            (8876, "Bulk food dispensing for refugee camps - foreign aid spending"),
            (14171, "Shrimp farm production in Vietnam - overseas agricultural development"),
            
            # High-Value Projects Requiring Scrutiny
            (4485, "Eastern Ontario Business Incubator - $10M+ regional favoritism"),
            (20498, "SMB advertisement platform - $10M for private advertising technology"),
            (20430, "COVID-19 vaccine trial - $10M for single vaccine candidate"),
            (19480, "Hybrid Integration Platform - $10M for vague technology project"),
            (11623, "Gas Oscillation forming technology - $10M for specialized manufacturing"),
            
            # Odd/Unusual Projects
            (20466, "Made-To-Order Pricing Application - questionable need for government funding"),
            (3555, "Voice/Chat project TAIGA - unclear purpose and relevance"),
            (786, "Autonomous Networking Platform - vague technology project"),
            (123, "Remote Psychometric Assessment trading signals - bizarre combination of concepts"),
        ]
        
        flagged_count = 0
        for grant_id, reason in notable_grants:
            try:
                grant = Grant.objects.get(id=grant_id)
                grant.is_notable = True
                grant.notable_reason = reason
                grant.save()
                flagged_count += 1
                self.stdout.write(f'Flagged grant {grant_id}: {grant.agreement_title_en[:60]}...')
            except Grant.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Grant {grant_id} not found'))
        
        # Also flag all grants over $5M as requiring scrutiny
        mega_grants = Grant.objects.filter(agreement_value__gte=5000000, is_notable=False)
        mega_count = mega_grants.count()
        mega_grants.update(
            is_notable=True,
            notable_reason="Major funding over $5M - requires public scrutiny due to significant taxpayer investment"
        )
        
        total_notable = Grant.objects.filter(is_notable=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Manual flagging complete! '
                f'{flagged_count} specifically flagged grants + {mega_count} mega-grants. '
                f'Total notable grants: {total_notable}'
            )
        )