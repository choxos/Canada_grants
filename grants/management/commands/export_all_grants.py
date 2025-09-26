import csv
from django.core.management.base import BaseCommand
from grants.models import Grant

class Command(BaseCommand):
    help = 'Export ALL grants to one big CSV for manual review'
    
    def handle(self, *args, **options):
        output_file = 'all_grants_for_review.csv'
        
        # Get ALL grants ordered by value (highest first)
        grants = Grant.objects.all().order_by('-agreement_value')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'ID', 
                'Value', 
                'FLAGGED',  # This is the column we'll manually edit
                'Title', 
                'Recipient', 
                'Province', 
                'City',
                'Program',
                'Description_Preview',
                'Fiscal_Year'
            ])
            
            for grant in grants:
                writer.writerow([
                    grant.id,
                    f"${grant.agreement_value:,.0f}",
                    'FALSE',  # Default to FALSE, we'll manually change to TRUE
                    grant.agreement_title_en,
                    grant.recipient_legal_name[:100],
                    grant.recipient_province,
                    grant.recipient_city_en,
                    grant.program_name_en[:80],
                    grant.description_en[:150] + '...' if len(grant.description_en) > 150 else grant.description_en,
                    grant.fiscal_year
                ])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Exported {grants.count()} grants to {output_file}. '
                f'Now manually review and change FLAGGED column to TRUE for problematic grants.'
            )
        )