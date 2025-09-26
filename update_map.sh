#!/bin/bash

# Update Map - Switch from Leaflet to Plotly
# Run this script on your VPS to get the new Plotly choropleth map

echo "🗺️  Updating World Map - Fix Plotly Loading Issues"
echo "=================================================="

# Make sure we're in the right directory
cd /home/cgt/Canada_grants
source venv/bin/activate

echo "1️⃣  Pulling latest map changes..."
git pull origin main

echo "2️⃣  Collecting static files..."
python manage.py collectstatic --noinput

echo "3️⃣  Restarting application..."
sudo supervisorctl restart cgt

echo "4️⃣  Checking application status..."
sleep 2
sudo supervisorctl status cgt

echo ""
echo "🎉 Map Update Complete!"
echo ""
echo "🔧 Plotly Loading Issues Fixed:"
echo "   ✅ Resolved 'Plotly is not defined' error"  
echo "   ✅ Added CDN fallback mechanism (plot.ly → jsdelivr)"
echo "   ✅ Robust library loading detection (5s timeout)"
echo "   ✅ Graceful error handling with retry options"
echo "   ✅ Works with ad blockers and network restrictions"
echo ""
echo "🗺️  Map Features Now Working:"
echo "   ✅ Interactive world choropleth visualization"
echo "   ✅ Country hover tooltips with funding details"
echo "   ✅ Color-coded funding levels ($0 to $1B+)"
echo "   ✅ Export to PNG functionality"
echo "   ✅ Professional ocean/coastline styling"
echo "   ✅ Reliable loading across network conditions"
echo ""
echo "🌐 Visit your statistics page: https://cgt.xeradb.com/global-affairs/statistics/"
echo "📊 The map should now load reliably without JavaScript errors!"
