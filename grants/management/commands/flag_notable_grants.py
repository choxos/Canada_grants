from django.core.management.base import BaseCommand
from django.db.models import Q
from grants.models import Grant
import re

class Command(BaseCommand):
    help = 'Flag grants that are odd, irrelevant to Canadians, or controversial'
    
    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                          help='Reset all notable flags before processing')
    
    def handle(self, *args, **options):
        if options['reset']:
            Grant.objects.update(is_notable=False, notable_reason='')
            self.stdout.write('Reset all notable flags')
        
        # International/Foreign Projects (often controversial)
        international_keywords = [
            'vietnam', 'china', 'africa', 'bangladesh', 'india', 'pakistan',
            'international development', 'overseas', 'foreign', 'global south',
            'developing countries', 'third world', 'cambodia', 'laos', 'myanmar',
            'ethiopia', 'kenya', 'ghana', 'nigeria', 'haiti', 'jamaica',
            'latin america', 'south america', 'central america', 'caribbean'
        ]
        
        # Gender/Diversity Projects (often debated)
        gender_diversity_keywords = [
            'gender', 'women empowerment', 'feminist', 'lgbtq', 'transgender',
            'diversity', 'inclusion', 'equity', 'dei programs', 'bias training',
            'gender-based', 'women-led', 'gender equality', 'gender justice',
            'intersectional', 'marginalized communities', 'underrepresented'
        ]
        
        # Climate/Environmental (often controversial spending)
        climate_keywords = [
            'climate change', 'carbon neutral', 'net zero', 'green transition',
            'renewable energy', 'solar panels', 'wind energy', 'electric vehicles',
            'carbon capture', 'emissions reduction', 'sustainability',
            'environmental justice', 'clean technology', 'green infrastructure'
        ]
        
        # Arts/Culture (often seen as non-essential)
        arts_culture_keywords = [
            'arts funding', 'cultural project', 'museum', 'theatre', 'dance',
            'music festival', 'art gallery', 'cultural center', 'heritage',
            'artistic expression', 'creative industries', 'film production',
            'documentary', 'cultural preservation', 'indigenous art'
        ]
        
        # Odd/Unusual Projects
        odd_keywords = [
            'rice cultivation', 'beekeeping', 'goat farming', 'chicken raising',
            'mushroom growing', 'fish farming', 'aquaculture', 'seaweed',
            'cricket farming', 'insect protein', 'urban gardening',
            'community composting', 'food waste', 'vertical farming'
        ]
        
        # Academic/Research (sometimes seen as wasteful)
        academic_keywords = [
            'gender studies', 'social justice research', 'decolonization',
            'indigenous knowledge', 'traditional healing', 'storytelling',
            'oral history', 'community engagement', 'participatory research',
            'action research', 'feminist methodology'
        ]
        
        # Process each category
        categories = [
            (international_keywords, "International development project - spending Canadian tax dollars overseas"),
            (gender_diversity_keywords, "Gender/diversity initiative - controversial social programming"),
            (climate_keywords, "Climate change project - expensive environmental initiative"),
            (arts_culture_keywords, "Arts/culture funding - non-essential spending during economic challenges"),
            (odd_keywords, "Unusual/odd project - questionable relevance to Canadian priorities"),
            (academic_keywords, "Academic/research project - theoretical spending with unclear practical benefits")
        ]
        
        total_flagged = 0
        
        for keywords, reason in categories:
            for keyword in keywords:
                grants = Grant.objects.filter(
                    Q(agreement_title_en__icontains=keyword) |
                    Q(description_en__icontains=keyword) |
                    Q(recipient_legal_name__icontains=keyword) |
                    Q(program_name_en__icontains=keyword)
                ).filter(is_notable=False)  # Only flag if not already notable
                
                count = grants.count()
                if count > 0:
                    grants.update(is_notable=True, notable_reason=reason)
                    total_flagged += count
                    self.stdout.write(f'Flagged {count} grants for keyword "{keyword}"')
        
        # Specific high-profile controversial grants
        specific_grants = [
            ("greening our rice", "Controversial Vietnam rice project - criticized for overseas spending"),
            ("gender-just", "Gender justice project - controversial social programming"),
            ("decolonizing", "Decolonization project - divisive academic initiative"),
            ("reconciliation", "Indigenous reconciliation - while important, often debated in scope/cost"),
            ("anti-racism", "Anti-racism training - controversial diversity programming"),
            ("equity training", "Equity training - divisive workplace programming"),
            ("community garden", "Community gardening - questionable use of federal funds for local projects"),
            ("food security", "Food security project - often overlaps with provincial responsibilities"),
        ]
        
        for search_term, reason in specific_grants:
            grants = Grant.objects.filter(
                Q(agreement_title_en__icontains=search_term) |
                Q(description_en__icontains=search_term)
            ).filter(is_notable=False)
            
            count = grants.count()
            if count > 0:
                grants.update(is_notable=True, notable_reason=reason)
                total_flagged += count
                self.stdout.write(f'Flagged {count} grants for specific term "{search_term}"')
        
        # Flag grants to foreign organizations or with foreign addresses
        foreign_grants = Grant.objects.filter(
            Q(recipient_legal_name__icontains='vietnam') |
            Q(recipient_legal_name__icontains='international') |
            Q(recipient_city_en__icontains='hanoi') |
            Q(recipient_city_en__icontains='ho chi minh') |
            Q(recipient_country__isnull=False) & ~Q(recipient_country='CA')
        ).filter(is_notable=False)
        
        foreign_count = foreign_grants.count()
        if foreign_count > 0:
            foreign_grants.update(
                is_notable=True, 
                notable_reason="Foreign recipient - Canadian tax dollars going to overseas organizations"
            )
            total_flagged += foreign_count
            self.stdout.write(f'Flagged {foreign_count} grants to foreign recipients')
        
        # Flag very high value grants (over $10M) as automatically notable
        mega_grants = Grant.objects.filter(
            agreement_value__gte=10000000
        ).filter(is_notable=False)
        
        mega_count = mega_grants.count()
        if mega_count > 0:
            mega_grants.update(
                is_notable=True,
                notable_reason="Mega-grant over $10M - requires public scrutiny due to size"
            )
            total_flagged += mega_count
            self.stdout.write(f'Flagged {mega_count} mega-grants over $10M')
        
        # Summary
        total_notable = Grant.objects.filter(is_notable=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Flagging complete! {total_flagged} new grants flagged. '
                f'Total notable grants: {total_notable}'
            )
        )