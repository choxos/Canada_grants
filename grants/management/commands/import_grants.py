import csv
import os
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models
from grants.models import Grant

class Command(BaseCommand):
    help = 'Import grants data from CSV files'
    
    def add_arguments(self, parser):
        parser.add_argument('--csv-dir', type=str, default='csv', 
                          help='Directory containing CSV files')
        parser.add_argument('--clear', action='store_true',
                          help='Clear existing grants before import')
    
    def handle(self, *args, **options):
        csv_dir = options['csv_dir']
        
        if options['clear']:
            self.stdout.write('Clearing existing grants...')
            Grant.objects.all().delete()
        
        if not os.path.exists(csv_dir):
            self.stdout.write(self.style.ERROR(f'CSV directory {csv_dir} not found'))
            return
        
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
        
        for csv_file in csv_files:
            self.stdout.write(f'Processing {csv_file}...')
            fiscal_year = self.extract_fiscal_year(csv_file)
            self.import_csv_file(os.path.join(csv_dir, csv_file), fiscal_year)
        
        # Flag notable grants
        self.flag_notable_grants()
        
        total_grants = Grant.objects.count()
        total_value = Grant.objects.aggregate(total=models.Sum('agreement_value'))['total'] or 0
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete! {total_grants} grants imported, '
                f'total value: ${total_value:,.2f}'
            )
        )
    
    def extract_fiscal_year(self, filename):
        """Extract fiscal year from filename like '2024_25_grants_and_contributions.csv'"""
        match = re.search(r'(\d{4})_(\d{2})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return "unknown"
    
    def parse_currency(self, value_str):
        """Parse currency string like '$475,000' or '475000' to Decimal"""
        if not value_str or value_str.strip() == '':
            return Decimal('0')
        
        # Remove currency symbols, spaces, and commas
        cleaned = re.sub(r'[\$,\s"]', '', str(value_str))
        
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return Decimal('0')
    
    def parse_date(self, date_str):
        """Parse date string in various formats"""
        if not date_str or date_str.strip() == '':
            return None
        
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        return None
    
    def import_csv_file(self, file_path, fiscal_year):
        """Import a single CSV file"""
        imported_count = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            # Detect if first row is header or data
            first_line = csvfile.readline()
            csvfile.seek(0)
            
            # Skip header if it looks like column names
            if 'Reference Number' in first_line or 'recipient_province' in first_line:
                next(csvfile)
            
            reader = csv.reader(csvfile)
            
            for row_num, row in enumerate(reader, 1):
                if len(row) < 10:  # Skip incomplete rows
                    continue
                
                try:
                    grant_data = self.parse_row(row, fiscal_year)
                    if grant_data:
                        grant, created = Grant.objects.get_or_create(
                            reference_number=grant_data['reference_number'],
                            defaults=grant_data
                        )
                        if created:
                            imported_count += 1
                
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Error processing row {row_num}: {str(e)}'
                        )
                    )
        
        self.stdout.write(f'  Imported {imported_count} grants from {file_path}')
    
    def parse_row(self, row, fiscal_year):
        """Parse a CSV row into grant data"""
        # Handle different CSV formats (2018-19 vs 2024-25)
        if len(row) > 35:  # New format with more columns
            return {
                'reference_number': row[0] or f"auto_{fiscal_year}_{len(row)}",
                'recipient_province': row[1][:50] if row[1] else '',
                'recipient_city_en': row[2][:100] if row[2] else '',
                'recipient_legal_name': row[4][:500] if row[4] else '',
                'recipient_operating_name': row[5][:500] if row[5] else '',
                'recipient_type': row[7][:10] if row[7] else '',
                'recipient_postal_code': row[8][:10] if row[8] else '',
                'agreement_title_en': row[14][:1000] if row[14] else '',
                'agreement_number': row[16][:100] if row[16] else '',
                'agreement_value': self.parse_currency(row[17]),
                'description_en': row[18][:2000] if row[18] else '',
                'expected_results_en': row[20][:2000] if row[20] else '',
                'agreement_start_date': self.parse_date(row[22]),
                'agreement_end_date': self.parse_date(row[23]),
                'naics_identifier': row[24][:20] if row[24] else '',
                'naics_sector_en': row[25][:200] if row[25] else '',
                'program_name_en': row[27][:500] if row[27] else '',
                'program_purpose_en': row[29][:1000] if row[29] else '',
                'fiscal_year': fiscal_year,
            }
        else:  # Older format
            return {
                'reference_number': f"legacy_{fiscal_year}_{row[15]}" if row[15] else f"auto_{fiscal_year}_{hash(str(row))}",
                'recipient_province': row[0][:50] if row[0] else '',
                'recipient_city_en': row[1][:100] if row[1] else '',
                'recipient_legal_name': row[3][:500] if row[3] else '',
                'recipient_operating_name': row[4][:500] if row[4] else '',
                'recipient_type': row[6][:10] if row[6] else '',
                'recipient_postal_code': row[7][:10] if row[7] else '',
                'agreement_title_en': row[13][:1000] if row[13] else '',
                'agreement_number': row[15][:100] if row[15] else '',
                'agreement_value': self.parse_currency(row[16]),
                'description_en': row[17][:2000] if row[17] else '',
                'expected_results_en': row[19][:2000] if row[19] else '',
                'agreement_start_date': self.parse_date(row[21]),
                'agreement_end_date': self.parse_date(row[22]),
                'naics_identifier': row[23][:20] if row[23] else '',
                'naics_sector_en': row[24][:200] if row[24] else '',
                'program_name_en': row[26][:500] if row[26] else '',
                'program_purpose_en': row[28][:1000] if row[28] else '',
                'fiscal_year': fiscal_year,
            }
    
    def flag_notable_grants(self):
        """Flag grants that might be notable or controversial"""
        # Flag major funding (over $1M)
        Grant.objects.filter(agreement_value__gte=1000000).update(is_major_funding=True)
        
        # Flag potentially controversial grants
        controversial_keywords = [
            'gender', 'diversity', 'equity', 'inclusion', 'climate change',
            'carbon', 'indigenous', 'reconciliation', 'international development',
            'arts funding', 'cultural', 'vietnam', 'rice', 'greening'
        ]
        
        for keyword in controversial_keywords:
            grants = Grant.objects.filter(
                models.Q(agreement_title_en__icontains=keyword) |
                models.Q(description_en__icontains=keyword)
            )
            
            for grant in grants:
                if not grant.is_notable:
                    grant.is_notable = True
                    grant.notable_reason = f"Contains keyword: {keyword}"
                    grant.save()
        
        # Specifically flag the "Greening Our Rice" project mentioned
        rice_grants = Grant.objects.filter(
            agreement_title_en__icontains='rice'
        ).filter(
            models.Q(agreement_title_en__icontains='vietnam') |
            models.Q(agreement_title_en__icontains='greening')
        )
        
        for grant in rice_grants:
            grant.is_notable = True
            grant.notable_reason = "Controversial international development project"
            grant.save()
        
        notable_count = Grant.objects.filter(is_notable=True).count()
        major_count = Grant.objects.filter(is_major_funding=True).count()
        
        self.stdout.write(f'Flagged {notable_count} notable grants and {major_count} major funding grants')