from django.core.management.base import BaseCommand
from grants.models import Grant

class Command(BaseCommand):
    help = 'Manually flag specific grants from batch 1 review'
    
    def handle(self, *args, **options):
        # Manually reviewed grants that should be flagged as notable
        # Based on careful review of batch_1.csv
        
        flagged_grants = [
            # International/Foreign Platform Scaling - Canadian tax dollars for overseas expansion
            (16070, "International platform scaling - Canadian funds used for overseas business expansion"),
            (6325, "International platform scaling - Canadian funds used for overseas business expansion"),
            
            # Questionable relevance to Canadian priorities
            (15714, "World's Largest Learning MMORPG - video game development, questionable priority during economic challenges"),
            (9498, "Student journey analytics platform - educational software of questionable necessity"),
            (14865, "Customer journey mapping for advertising - private sector marketing tool development"),
            (18955, "Transportation broker marketplace - private ride-sharing platform development"),
            (19083, "Live streaming ad delivery platform - entertainment/advertising technology"),
            (20707, "Food waste app scaling - private app development with limited scope"),
            
            # Expensive technology projects with unclear Canadian benefit
            (13177, "Power grid simulation technology - highly specialized technical project"),
            (12365, "Meeting automation AI - productivity software of questionable government priority"),
            (21168, "Legacy software modernization - private sector IT consulting"),
            (20882, "Biometric platform build-out - privacy-concerning identity verification system"),
            
            # Private sector business development that should be self-funded
            (18880, "Customer retention optimization - private business consulting"),
            (21085, "CRM platform modularization - private software development"),
            (9154, "Point of sale operating system - private retail technology"),
            (1905, "Multi-cloud data distribution - private IT infrastructure"),
            
            # Specialized industrial projects with limited broad benefit
            (13643, "Electronic waste gold recovery - highly specialized recycling technology"),
            (11229, "Laser welding for batteries - specialized manufacturing process"),
            (9476, "Hospital bed connectivity - medical device networking"),
            (3575, "Container handling sensors - specialized logistics technology"),
            
            # High-value projects requiring extra scrutiny due to cost
            (4485, "Eastern Ontario Business Incubator - $10M+ regional favoritism"),
            (20498, "Advertisement platform enablement - $10M for private advertising technology"),
            (19480, "Hybrid integration platform - $10M for vague technology project"),
            (11623, "Gas oscillation forming technology - $10M for specialized manufacturing"),
        ]
        
        flagged_count = 0
        for grant_id, reason in flagged_grants:
            try:
                grant = Grant.objects.get(id=grant_id)
                grant.is_notable = True
                grant.notable_reason = reason
                grant.save()
                flagged_count += 1
                self.stdout.write(f'Flagged grant {grant_id}: {grant.agreement_title_en[:60]}...')
            except Grant.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Grant {grant_id} not found'))
        
        # Also flag all grants over $8M as requiring scrutiny due to high taxpayer cost
        mega_grants = Grant.objects.filter(agreement_value__gte=8000000, is_notable=False)
        mega_count = mega_grants.count()
        mega_grants.update(
            is_notable=True,
            notable_reason="Major funding over $8M - requires public scrutiny due to significant taxpayer investment"
        )
        
        total_notable = Grant.objects.filter(is_notable=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Batch 1 manual flagging complete! '
                f'{flagged_count} specifically flagged grants + {mega_count} mega-grants. '
                f'Total notable grants: {total_notable}'
            )
        )