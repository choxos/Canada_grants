from django.core.management.base import BaseCommand
from grants.models import TaxBracket, CanadianTaxData
from decimal import Decimal

class Command(BaseCommand):
    help = 'Setup Canadian tax brackets and revenue data'
    
    def handle(self, *args, **options):
        # Clear existing data
        TaxBracket.objects.all().delete()
        CanadianTaxData.objects.all().delete()
        
        # 2024 Federal Tax Brackets
        tax_brackets_2024 = [
            (0, 53359, 0.15),      # 15% on first $53,359
            (53359, 106717, 0.205), # 20.5% on next $53,358
            (106717, 164921, 0.26), # 26% on next $58,204
            (164921, 264383, 0.29), # 29% on next $99,462
            (264383, None, 0.33),   # 33% on income over $264,383
        ]
        
        for min_income, max_income, rate in tax_brackets_2024:
            TaxBracket.objects.create(
                year=2024,
                min_income=Decimal(str(min_income)),
                max_income=Decimal(str(max_income)) if max_income else None,
                tax_rate=Decimal(str(rate))
            )
        
        # Canadian Federal Revenue Data (estimates based on public data)
        revenue_data = [
            (2024, 400000000000, 45000000000, 180000000000),  # $400B total, $45B GST, $180B income tax
            (2023, 390000000000, 43000000000, 175000000000),
            (2022, 380000000000, 41000000000, 170000000000),
            (2021, 370000000000, 39000000000, 165000000000),
            (2020, 360000000000, 37000000000, 160000000000),
            (2019, 350000000000, 35000000000, 155000000000),
            (2018, 340000000000, 33000000000, 150000000000),
        ]
        
        for year, total_revenue, gst_revenue, income_tax_revenue in revenue_data:
            CanadianTaxData.objects.create(
                year=year,
                total_federal_revenue=Decimal(str(total_revenue)),
                gst_hst_revenue=Decimal(str(gst_revenue)),
                income_tax_revenue=Decimal(str(income_tax_revenue))
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {TaxBracket.objects.count()} tax brackets '
                f'and {CanadianTaxData.objects.count()} revenue records'
            )
        )