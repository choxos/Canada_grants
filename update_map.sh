#!/bin/bash

# Update Map - Switch from Leaflet to Plotly
# Run this script on your VPS to get the new Plotly choropleth map

echo "🗺️  Updating World Map - Fix JavaScript Scope Error"
echo "===================================================="

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
echo "🐛 JavaScript Error Fixed:"
echo "   ✅ Resolved 'countryData is not defined' error"
echo "   ✅ Fixed function scope issue with Plotly map"
echo "   ✅ Map now loads without console errors"
echo ""
echo "🗺️  Plotly Map Features:"
echo "   ✅ Interactive choropleth visualization"
echo "   ✅ Hover tooltips with funding details"
echo "   ✅ Color-coded countries by funding level"
echo "   ✅ Export functionality (PNG download)"
echo "   ✅ Professional styling with ocean/land contrast"
echo ""
echo "🌐 Visit your statistics page: https://cgt.xeradb.com/global-affairs/statistics/"
echo "📊 The map should now display properly without errors!"
