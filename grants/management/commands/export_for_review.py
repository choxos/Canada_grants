import csv
from django.core.management.base import BaseCommand
from grants.models import Grant

class Command(BaseCommand):
    help = 'Export grants to CSV for manual review'
    
    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='grants_for_review.csv',
                          help='Output CSV filename')
        parser.add_argument('--start', type=int, default=0,
                          help='Starting record number')
        parser.add_argument('--limit', type=int, default=100,
                          help='Number of records to export')
    
    def handle(self, *args, **options):
        output_file = options['output']
        start = options['start']
        limit = options['limit']
        
        # Get grants ordered by value (highest first) for priority review
        grants = Grant.objects.all().order_by('-agreement_value')[start:start+limit]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'ID', 
                'Value', 
                'Title', 
                'Recipient', 
                'Province', 
                'City',
                'Program',
                'Description_Preview',
                'Fiscal_Year',
                'Flag_Status'
            ])
            
            for grant in grants:
                writer.writerow([
                    grant.id,
                    f"${grant.agreement_value:,.0f}",
                    grant.agreement_title_en,
                    grant.recipient_legal_name[:100],  # Truncate long names
                    grant.recipient_province,
                    grant.recipient_city_en,
                    grant.program_name_en[:80],  # Truncate long program names
                    grant.description_en[:150] + '...' if len(grant.description_en) > 150 else grant.description_en,
                    grant.fiscal_year,
                    'REVIEW_NEEDED'
                ])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Exported {grants.count()} grants to {output_file} '
                f'(records {start} to {start + grants.count()})'
            )
        )