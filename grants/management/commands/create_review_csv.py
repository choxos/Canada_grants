import csv
from django.core.management.base import BaseCommand
from grants.models import Grant

class Command(BaseCommand):
    help = 'Create simple 3-column CSV for manual review: ID, Title, Flagged'
    
    def handle(self, *args, **options):
        output_file = 'grants_review.csv'
        
        # Get ALL grants ordered by value (highest first)
        grants = Grant.objects.all().order_by('-agreement_value')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Simple 3-column header
            writer.writerow(['ID', 'Title', 'Flagged'])
            
            for grant in grants:
                writer.writerow([
                    grant.id,
                    grant.agreement_title_en,
                    'FALSE'  # Default to FALSE, we'll manually change to TRUE
                ])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {output_file} with {grants.count()} grants. '
                f'Review 100 at a time and change Flagged column to TRUE for problematic grants.'
            )
        )