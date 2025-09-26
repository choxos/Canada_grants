from django.core.management.base import BaseCommand
from django.db.models import Q
from grants.models import Grant

class Command(BaseCommand):
    help = 'Flag all grants related to foreign countries, especially developing nations'
    
    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                          help='Reset all notable flags before processing')
    
    def handle(self, *args, **options):
        if options['reset']:
            Grant.objects.update(is_notable=False, notable_reason='')
            self.stdout.write('Reset all notable flags')
        
        # Comprehensive list of foreign countries and regions
        # Prioritizing developing/third-world countries that often receive Canadian aid
        
        developing_countries = [
            # Asia-Pacific Developing Countries
            'vietnam', 'cambodia', 'laos', 'myanmar', 'bangladesh', 'nepal', 'bhutan',
            'sri lanka', 'maldives', 'afghanistan', 'pakistan', 'india', 'philippines',
            'indonesia', 'thailand', 'malaysia', 'papua new guinea', 'fiji', 'vanuatu',
            'solomon islands', 'timor-leste', 'mongolia', 'north korea',
            
            # Africa
            'nigeria', 'kenya', 'ethiopia', 'ghana', 'uganda', 'tanzania', 'rwanda',
            'burundi', 'democratic republic of congo', 'congo', 'cameroon', 'chad',
            'central african republic', 'sudan', 'south sudan', 'somalia', 'eritrea',
            'djibouti', 'madagascar', 'malawi', 'mozambique', 'zambia', 'zimbabwe',
            'botswana', 'namibia', 'angola', 'gabon', 'equatorial guinea', 'sao tome',
            'cape verde', 'guinea-bissau', 'guinea', 'sierra leone', 'liberia',
            'ivory coast', 'burkina faso', 'mali', 'niger', 'senegal', 'gambia',
            'mauritania', 'morocco', 'algeria', 'tunisia', 'libya', 'egypt',
            'lesotho', 'swaziland', 'comoros', 'seychelles', 'mauritius',
            
            # Latin America & Caribbean
            'haiti', 'jamaica', 'dominican republic', 'cuba', 'puerto rico',
            'guatemala', 'belize', 'honduras', 'el salvador', 'nicaragua',
            'costa rica', 'panama', 'colombia', 'venezuela', 'guyana', 'suriname',
            'brazil', 'ecuador', 'peru', 'bolivia', 'paraguay', 'uruguay',
            'argentina', 'chile', 'barbados', 'trinidad and tobago', 'grenada',
            'st lucia', 'st vincent', 'dominica', 'antigua', 'st kitts',
            
            # Middle East
            'iraq', 'syria', 'lebanon', 'jordan', 'palestine', 'yemen', 'oman',
            'bahrain', 'qatar', 'kuwait', 'saudi arabia', 'iran', 'turkey',
            
            # Eastern Europe & Former Soviet
            'ukraine', 'moldova', 'belarus', 'georgia', 'armenia', 'azerbaijan',
            'kazakhstan', 'kyrgyzstan', 'tajikistan', 'turkmenistan', 'uzbekistan',
            'albania', 'bosnia', 'serbia', 'montenegro', 'north macedonia',
            'kosovo', 'bulgaria', 'romania',
            
            # Pacific Islands
            'samoa', 'tonga', 'kiribati', 'tuvalu', 'nauru', 'palau', 'marshall islands',
            'micronesia',
        ]
        
        # Broader regional terms
        regional_terms = [
            'africa', 'african', 'sub-saharan', 'west africa', 'east africa',
            'central africa', 'southern africa', 'north africa', 'sahel',
            'asia-pacific', 'southeast asia', 'south asia', 'central asia',
            'latin america', 'south america', 'central america', 'caribbean',
            'middle east', 'gulf states', 'arab world', 'maghreb',
            'developing countries', 'third world', 'global south', 'emerging markets',
            'least developed countries', 'low-income countries', 'fragile states',
            'post-conflict', 'humanitarian', 'refugee', 'displaced persons',
        ]
        
        # Development/aid related terms
        development_terms = [
            'international development', 'foreign aid', 'development assistance',
            'humanitarian aid', 'emergency relief', 'disaster response',
            'capacity building', 'technical assistance', 'knowledge transfer',
            'south-south cooperation', 'triangular cooperation',
            'development cooperation', 'overseas development',
            'global development', 'international cooperation',
            'cross-border', 'transnational', 'multinational',
            'bilateral cooperation', 'multilateral', 'regional cooperation',
        ]
        
        # Combine all terms
        all_foreign_terms = developing_countries + regional_terms + development_terms
        
        total_flagged = 0
        
        # Search in all relevant fields
        for term in all_foreign_terms:
            grants = Grant.objects.filter(
                Q(agreement_title_en__icontains=term) |
                Q(description_en__icontains=term) |
                Q(recipient_legal_name__icontains=term) |
                Q(program_name_en__icontains=term) |
                Q(expected_results_en__icontains=term) |
                Q(recipient_city_en__icontains=term)
            ).filter(is_notable=False)  # Only flag if not already notable
            
            count = grants.count()
            if count > 0:
                # Determine the reason based on the term type
                if term in developing_countries:
                    reason = f"Foreign spending in {term.title()} - Canadian tax dollars going to developing country"
                elif term in regional_terms:
                    reason = f"International development in {term} - overseas spending of Canadian funds"
                else:
                    reason = f"Foreign aid/development project - Canadian tax dollars for overseas assistance"
                
                grants.update(is_notable=True, notable_reason=reason)
                total_flagged += count
                
                if count > 0:
                    self.stdout.write(f'Flagged {count} grants for term "{term}"')
        
        # Check for foreign organizations by name patterns
        foreign_org_patterns = [
            'university of', 'instituto', 'universidade', 'université',
            'college of', 'school of', 'academy of', 'institute of technology',
            'national university', 'state university', 'federal university',
            'ministry of', 'government of', 'department of',
        ]
        
        foreign_org_count = 0
        for pattern in foreign_org_patterns:
            # Look for organizations that might be foreign
            foreign_orgs = Grant.objects.filter(
                recipient_legal_name__icontains=pattern
            ).exclude(
                # Exclude clearly Canadian institutions
                Q(recipient_legal_name__icontains='canada') |
                Q(recipient_legal_name__icontains='canadian') |
                Q(recipient_legal_name__icontains='ontario') |
                Q(recipient_legal_name__icontains='quebec') |
                Q(recipient_legal_name__icontains='british columbia') |
                Q(recipient_legal_name__icontains='alberta') |
                Q(recipient_legal_name__icontains='manitoba') |
                Q(recipient_legal_name__icontains='saskatchewan') |
                Q(recipient_legal_name__icontains='nova scotia') |
                Q(recipient_legal_name__icontains='new brunswick') |
                Q(recipient_legal_name__icontains='newfoundland') |
                Q(recipient_legal_name__icontains='prince edward island') |
                Q(recipient_legal_name__icontains='northwest territories') |
                Q(recipient_legal_name__icontains='nunavut') |
                Q(recipient_legal_name__icontains='yukon')
            ).filter(is_notable=False)
            
            count = foreign_orgs.count()
            if count > 0:
                foreign_orgs.update(
                    is_notable=True,
                    notable_reason=f"Potentially foreign organization - {pattern} pattern suggests overseas institution"
                )
                foreign_org_count += count
        
        if foreign_org_count > 0:
            total_flagged += foreign_org_count
            self.stdout.write(f'Flagged {foreign_org_count} grants to potentially foreign organizations')
        
        # Flag grants with foreign postal codes (non-Canadian format)
        # Canadian postal codes follow A1A 1A1 format
        import re
        all_grants = Grant.objects.filter(is_notable=False)
        foreign_postal_count = 0
        
        for grant in all_grants:
            if grant.recipient_postal_code:
                # Canadian postal code pattern: Letter-Number-Letter Number-Letter-Number
                canadian_pattern = r'^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$'
                if not re.match(canadian_pattern, grant.recipient_postal_code.replace(' ', '')):
                    # This might be a foreign postal code
                    grant.is_notable = True
                    grant.notable_reason = f"Foreign postal code ({grant.recipient_postal_code}) - likely overseas recipient"
                    grant.save()
                    foreign_postal_count += 1
        
        if foreign_postal_count > 0:
            total_flagged += foreign_postal_count
            self.stdout.write(f'Flagged {foreign_postal_count} grants with foreign postal codes')
        
        # Special focus on specific controversial international projects
        controversial_international = [
            ('rice', 'vietnam', "Rice cultivation in Vietnam - controversial overseas agricultural project"),
            ('shrimp', 'vietnam', "Shrimp farming in Vietnam - questionable use of Canadian funds for foreign aquaculture"),
            ('moringa', 'africa', "African Moringa project - overseas agricultural development"),
            ('refugee camp', '', "Refugee camp assistance - foreign humanitarian spending"),
            ('food dispensing', 'refugee', "Refugee food systems - overseas humanitarian aid"),
        ]
        
        for term1, term2, reason in controversial_international:
            if term2:
                grants = Grant.objects.filter(
                    (Q(agreement_title_en__icontains=term1) | Q(description_en__icontains=term1)) &
                    (Q(agreement_title_en__icontains=term2) | Q(description_en__icontains=term2))
                ).filter(is_notable=False)
            else:
                grants = Grant.objects.filter(
                    Q(agreement_title_en__icontains=term1) | Q(description_en__icontains=term1)
                ).filter(is_notable=False)
            
            count = grants.count()
            if count > 0:
                grants.update(is_notable=True, notable_reason=reason)
                total_flagged += count
                self.stdout.write(f'Flagged {count} controversial international grants for "{term1}"')
        
        # Summary
        total_notable = Grant.objects.filter(is_notable=True).count()
        from django.db import models
        total_value = Grant.objects.filter(is_notable=True).aggregate(
            total=models.Sum('agreement_value')
        )['total'] or 0
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Foreign grant flagging complete! '
                f'{total_flagged} new grants flagged for foreign/international spending. '
                f'Total notable grants: {total_notable} '
                f'Total value of notable grants: ${total_value:,.2f}'
            )
        )