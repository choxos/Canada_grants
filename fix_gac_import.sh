#!/bin/bash

# Fix GAC Import - Field Length Issues
# Run this script on your VPS to fix the database field length errors

echo "🔧 Fixing GAC Grant Import Field Length Issues"
echo "=============================================="

# Make sure we're in the right directory
cd /home/cgt/Canada_grants
source venv/bin/activate

echo "1️⃣  Pulling latest code changes..."
git pull origin main

echo "2️⃣  Applying database migrations (increasing field lengths)..."
python manage.py migrate grants

echo "3️⃣  Clearing existing GAC grants (to fix corrupted transaction)..."
python manage.py shell -c "
from grants.models import GlobalAffairsGrant
print(f'Clearing {GlobalAffairsGrant.objects.count()} existing GAC grants...')
GlobalAffairsGrant.objects.all().delete()
print('✅ GAC grants cleared')
"

echo "4️⃣  Re-importing GAC grants with fixed field lengths..."
python manage.py import_gac_grants --csv-dir csv/GFC_data

echo "5️⃣  Checking import results..."
python manage.py shell -c "
from grants.models import GlobalAffairsGrant
total = GlobalAffairsGrant.objects.count()
print(f'✅ Successfully imported {total:,} GAC grants')

by_status = GlobalAffairsGrant.objects.values('status').annotate(
    count=models.Count('id')
).order_by('status')

print()
print('Breakdown by status:')
for item in by_status:
    print(f'  {item[\"status\"].title()}: {item[\"count\"]:,} grants')
"

echo "6️⃣  Restarting application..."
sudo supervisorctl restart cgt

echo ""
echo "🎉 GAC Import Fix Complete!"
echo ""
echo "📊 Summary of changes:"
echo "   ✅ Increased project_number: 50 → 100 characters"
echo "   ✅ Increased region: 200 → 500 characters"
echo "   ✅ Increased aid_type: 100 → 200 characters"
echo "   ✅ Increased collaboration_type: 50 → 200 characters"
echo "   ✅ Increased finance_type: 100 → 200 characters"
echo "   ✅ Increased flow_type: 50 → 200 characters"
echo "   ✅ Increased selection_mechanism: 100 → 200 characters"
echo "   ✅ Increased alternate_im_position: 100 → 300 characters"
echo "   ✅ Increased reporting_organization: 100 → 200 characters"
echo ""
echo "🌐 Your application should now be working at: https://cgt.xeradb.com"
echo "📋 Check status with: sudo supervisorctl status cgt"
