import csv
from django.core.management.base import BaseCommand
from grants.models import Grant

class Command(BaseCommand):
    help = 'Import flagged results from grants_review.csv'
    
    def handle(self, *args, **options):
        csv_file = 'grants_review.csv'
        
        flagged_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                grant_id = int(row['ID'])
                is_flagged = row['Flagged'].upper() == 'TRUE'
                
                try:
                    grant = Grant.objects.get(id=grant_id)
                    
                    if is_flagged and not grant.is_notable:
                        grant.is_notable = True
                        
                        # Set reason based on title content
                        title_lower = grant.agreement_title_en.lower()
                        
                        if 'international' in title_lower and 'platform' in title_lower:
                            grant.notable_reason = "International platform expansion - Canadian tax dollars for overseas business development"
                        elif 'advertisement' in title_lower or 'omni channel' in title_lower:
                            grant.notable_reason = "Private advertising platform - questionable government funding for marketing technology"
                        elif 'mmorpg' in title_lower or 'game' in title_lower:
                            grant.notable_reason = "Video game development - entertainment industry funding during economic challenges"
                        elif 'customer journey' in title_lower or 'customer retention' in title_lower:
                            grant.notable_reason = "Private business optimization - marketing/sales tools that should be self-funded"
                        elif 'streaming' in title_lower or 'live streaming' in title_lower:
                            grant.notable_reason = "Entertainment streaming platform - non-essential media technology"
                        elif 'pos' in title_lower or 'point of sale' in title_lower:
                            grant.notable_reason = "Private retail technology - commercial POS system development"
                        elif 'led display' in title_lower:
                            grant.notable_reason = "Specialized display technology - niche commercial product with limited public benefit"
                        elif 'container' in title_lower and ('sensor' in title_lower or 'handling' in title_lower):
                            grant.notable_reason = "Specialized logistics technology - narrow commercial application"
                        elif 'hospital bed' in title_lower and 'connectivity' in title_lower:
                            grant.notable_reason = "Medical device networking - specialized healthcare IT project"
                        elif 'laser welding' in title_lower and 'batteries' in title_lower:
                            grant.notable_reason = "Specialized manufacturing process - narrow industrial application"
                        elif 'student' in title_lower and 'analytics' in title_lower:
                            grant.notable_reason = "Educational analytics platform - questionable necessity for government funding"
                        elif 'multi-cloud' in title_lower or 'data distribution' in title_lower:
                            grant.notable_reason = "Private IT infrastructure - commercial cloud services development"
                        elif 'copilot' in title_lower and 'legacy' in title_lower:
                            grant.notable_reason = "Private software modernization - IT consulting that should be self-funded"
                        elif 'salesforce' in title_lower or 'crm platform' in title_lower:
                            grant.notable_reason = "Private CRM development - commercial software platform enhancement"
                        elif 'biometric' in title_lower or 'bioconnect' in title_lower:
                            grant.notable_reason = "Biometric platform - privacy-concerning identity verification technology"
                        elif 'flashfood' in title_lower or 'food waste' in title_lower:
                            grant.notable_reason = "Private food app - commercial mobile application development"
                        elif 'transportation' in title_lower and 'broker' in title_lower:
                            grant.notable_reason = "Private transportation marketplace - ride-sharing platform development"
                        elif 'spoken word' in title_lower or 'meeting' in title_lower:
                            grant.notable_reason = "Meeting productivity software - business tool of questionable government priority"
                        elif 'power grid' in title_lower and 'simulation' in title_lower:
                            grant.notable_reason = "Specialized power grid technology - highly technical project with unclear public benefit"
                        elif 'electronic waste' in title_lower and 'gold' in title_lower:
                            grant.notable_reason = "Specialized recycling technology - niche e-waste processing with limited scope"
                        elif grant.agreement_value >= 10000000:
                            grant.notable_reason = "Major funding over $10M - requires public scrutiny due to massive taxpayer investment"
                        elif 'incubator' in title_lower and 'eastern ontario' in title_lower:
                            grant.notable_reason = "Regional business incubator - $10M+ regional favoritism and questionable effectiveness"
                        elif 'gas oscillation' in title_lower or 'forming technology' in title_lower:
                            grant.notable_reason = "Specialized manufacturing technology - $10M for narrow industrial process"
                        elif 'hybrid integration' in title_lower:
                            grant.notable_reason = "Vague technology platform - $10M for unclear integration project"
                        else:
                            grant.notable_reason = "Questionable government funding priority - private sector development that should be self-funded"
                        
                        grant.save()
                        flagged_count += 1
                        self.stdout.write(f'Flagged: {grant.agreement_title_en[:60]}...')
                
                except Grant.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Grant {grant_id} not found'))
        
        total_notable = Grant.objects.filter(is_notable=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Batch 1 complete! {flagged_count} grants flagged. '
                f'Total notable grants: {total_notable}'
            )
        )