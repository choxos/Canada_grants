from django.core.management.base import BaseCommand
from django.db import transaction
from grants.models import GlobalAffairsGrant
import csv
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation


class Command(BaseCommand):
    help = 'Import Global Affairs Canada grants from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-dir',
            type=str,
            default='csv/GFC_data',
            help='Directory containing GAC CSV files (default: csv/GFC_data)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing GAC grants before importing'
        )

    def handle(self, *args, **options):
        csv_dir = options['csv_dir']
        
        if options['clear']:
            self.stdout.write('Clearing existing GAC grants...')
            GlobalAffairsGrant.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing GAC grants'))

        # Expected CSV files
        csv_files = [
            ('GFC_operational.csv', 'operational'),
            ('GFC_closed.csv', 'closed'), 
            ('GFC_terminating.csv', 'terminating')
        ]

        total_imported = 0
        total_errors = 0

        for filename, status in csv_files:
            filepath = os.path.join(csv_dir, filename)
            
            if not os.path.exists(filepath):
                self.stdout.write(
                    self.style.WARNING(f'File not found: {filepath}')
                )
                continue

            self.stdout.write(f'Processing {filename}...')
            
            imported, errors = self.import_csv_file(filepath, status)
            total_imported += imported
            total_errors += errors
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Imported {imported} grants from {filename} '
                    f'({errors} errors)'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete! Total: {total_imported} grants imported, '
                f'{total_errors} errors'
            )
        )

    def import_csv_file(self, filepath, status):
        """Import grants from a single CSV file with standard CSV parsing"""
        imported = 0
        errors = 0
        
        with open(filepath, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    try:
                        grant = self.create_grant_from_row(row, status)
                        if grant:
                            imported += 1
                            if imported % 100 == 0:
                                self.stdout.write(f'  Processed {imported} grants...')
                    except Exception as e:
                        errors += 1
                        if errors <= 10:
                            self.stdout.write(self.style.ERROR(f'Row {row_num}: {e}'))
                        elif errors == 11:
                            self.stdout.write(self.style.WARNING('(suppressing further error details...)'))
        
        return imported, errors

    def create_grant_from_row(self, row, status):
        """Create a GlobalAffairsGrant from CSV row data with better field handling"""
        
        # Handle potential BOM in first column name  
        project_number_key = 'Project Number'
        for key in row.keys():
            if 'Project Number' in key:
                project_number_key = key
                break
        
        # Get project number
        project_number = row.get(project_number_key, '').strip()
        if not project_number:
            return None
            
        # Check if grant already exists
        if GlobalAffairsGrant.objects.filter(project_number=project_number).exists():
            return None

        # Parse monetary value
        max_contribution_str = row.get('Maximum Contribution', '').strip()
        max_contribution = self.parse_currency(max_contribution_str)
        
        if max_contribution is None or max_contribution <= 0:
            return None

        # Parse dates - strip tabs and whitespace
        date_modified = self.parse_date(row.get('Date Modified', '').strip('\t '))
        start_date = self.parse_date(row.get('Start Date', '').strip('\t '))
        end_date = self.parse_date(row.get('End Date', '').strip('\t '))

        # Clean text fields
        title = row.get('Title', '').strip()[:500] or 'Untitled Project'
        description = row.get(' Description', '').strip()[:2000]  # Note the space in column name
        country = row.get('Country', '').strip()[:255]
        executing_agency = row.get('Executing Agency Partner', '').strip()[:500]
        dac_sector = row.get('DAC Sector', '').strip()[:500]  
        policy_markers = row.get('Policy Markers', '').strip()[:1000]
        region = row.get('Region', '').strip()[:255]
        budget = row.get('Budget', '').strip()
        locations = row.get('Locations', '').strip()
        other_identifier = row.get('Other Identifier', '').strip()
        contributing_org = row.get('Contributing Organization', '').strip()[:500]
        expected_results = row.get('Expected Results', '').strip()[:2000]
        progress = row.get('Progress and Results Achieved', '').strip()[:2000]
        aid_type = row.get('Aid Type', '').strip()[:200]

        # Create the grant
        try:
            grant = GlobalAffairsGrant.objects.create(
                project_number=project_number,
                date_modified=date_modified or datetime.now().date(),
                title=title,
                description=description,
                status=status,
                start_date=start_date,
                end_date=end_date,
                country=country,
                region=region,
                locations=locations,
                executing_agency_partner=executing_agency,
                contributing_organization=contributing_org,
                maximum_contribution=max_contribution,
                budget=budget,
                program_name=row.get('Program Name', '').strip()[:500] or 'Unknown Program',
                dac_sector=dac_sector,
                aid_type=aid_type,
                collaboration_type=row.get('Collaboration Type', '').strip()[:255],
                finance_type=row.get('Finance Type', '').strip()[:255],
                flow_type=row.get('Flow Type', '').strip()[:255],
                reporting_organization=row.get('Reporting Organization', '').strip()[:255] or 'Global Affairs Canada',
                selection_mechanism=row.get('Selection Mechanism', '').strip()[:255],
                expected_results=expected_results,
                progress_and_results_achieved=progress,
                policy_markers=policy_markers,
                alternate_im_position=row.get('Alternate IM Position', '').strip()[:255],
                other_identifier=other_identifier,
            )
            return grant
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating grant {project_number}: {e}'))
            return None

    def parse_currency(self, value_str):
        """Parse currency string to Decimal"""
        if not value_str or value_str.strip() == '':
            return None
            
        # Remove currency symbols, commas, and whitespace
        cleaned = value_str.replace('$', '').replace(',', '').strip()
        
        # Handle quoted values
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
            
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str or date_str.strip() == '':
            return None
            
        cleaned = date_str.strip()
        
        # Common date formats in the data
        date_formats = [
            '%Y-%m-%d',     # 2023-04-15
            '%d/%m/%Y',     # 15/04/2023  
            '%m/%d/%Y',     # 04/15/2023
            '%Y-%m-%d\t',   # With tab character
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
                
        return None

    def clean_text_field(self, value, max_length):
        """Clean and truncate text fields"""
        if value is None or value == '':
            return ''
        
        # Convert to string and remove tabs, extra whitespace, and limit length
        import re
        cleaned = re.sub(r'\s+', ' ', str(value).strip())
        return cleaned[:max_length] if cleaned else ''

    def clean_complex_field(self, value):
        """Clean complex fields like Budget, Locations, Other Identifier"""
        if value is None or value == '':
            return ''
        
        # For complex fields, we'll keep them as-is but clean up basic formatting
        cleaned = str(value).strip()
        
        # Remove excessive whitespace but preserve structure
        import re
        cleaned = re.sub(r'\t+', ' ', cleaned)  # Replace tabs with spaces
        cleaned = re.sub(r' {3,}', ' ', cleaned)  # Replace 3+ spaces with single space
        
        return cleaned[:2000]  # Limit to reasonable length
