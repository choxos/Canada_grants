import csv
from django.core.management.base import BaseCommand
from grants.models import Grant

class Command(BaseCommand):
    help = 'Import flagged results from CSV back to database'
    
    def add_arguments(self, parser):
        parser.add_argument('--csv-file', type=str, required=True,
                          help='CSV file with flagged results')
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        flagged_count = 0
        not_found_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                grant_id = int(row['ID'])
                is_flagged = row['FLAGGED'].upper() == 'TRUE'
                
                try:
                    grant = Grant.objects.get(id=grant_id)
                    
                    if is_flagged:
                        grant.is_notable = True
                        # Set a reason based on the grant characteristics
                        if 'international' in grant.agreement_title_en.lower():
                            grant.notable_reason = "International platform/expansion - Canadian tax dollars for overseas business development"
                        elif 'advertisement' in grant.agreement_title_en.lower() or 'marketing' in grant.agreement_title_en.lower():
                            grant.notable_reason = "Private advertising/marketing platform - questionable government funding priority"
                        elif 'game' in grant.agreement_title_en.lower() or 'mmorpg' in grant.agreement_title_en.lower():
                            grant.notable_reason = "Video game development - entertainment industry funding during economic challenges"
                        elif 'customer journey' in grant.agreement_title_en.lower() or 'customer retention' in grant.agreement_title_en.lower():
                            grant.notable_reason = "Private business consulting/optimization - should be self-funded by companies"
                        elif 'streaming' in grant.agreement_title_en.lower() or 'media' in grant.agreement_title_en.lower():
                            grant.notable_reason = "Entertainment/media platform - non-essential industry funding"
                        elif 'pos' in grant.agreement_title_en.lower() or 'point of sale' in grant.agreement_title_en.lower():
                            grant.notable_reason = "Private retail technology - commercial software development"
                        elif 'led display' in grant.agreement_title_en.lower():
                            grant.notable_reason = "Specialized display technology - niche commercial product development"
                        elif 'container' in grant.agreement_title_en.lower() and 'sensor' in grant.agreement_title_en.lower():
                            grant.notable_reason = "Specialized logistics sensors - narrow commercial application"
                        elif grant.agreement_value >= 10000000:
                            grant.notable_reason = "Major funding over $10M - requires public scrutiny due to massive taxpayer investment"
                        elif grant.agreement_value >= 5000000:
                            grant.notable_reason = "Large funding over $5M - significant taxpayer investment requiring justification"
                        else:
                            grant.notable_reason = "Questionable government funding priority - private sector development that should be self-funded"
                        
                        grant.save()
                        flagged_count += 1
                        self.stdout.write(f'Flagged grant {grant_id}: {grant.agreement_title_en[:60]}...')
                    else:
                        # Ensure it's not flagged if marked as FALSE
                        if grant.is_notable:
                            grant.is_notable = False
                            grant.notable_reason = ''
                            grant.save()
                
                except Grant.DoesNotExist:
                    not_found_count += 1
                    self.stdout.write(self.style.WARNING(f'Grant {grant_id} not found'))
        
        total_notable = Grant.objects.filter(is_notable=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete! {flagged_count} grants flagged. '
                f'{not_found_count} grants not found. '
                f'Total notable grants in database: {total_notable}'
            )
        )