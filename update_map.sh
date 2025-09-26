#!/bin/bash

# Update Map - Switch from Leaflet to Plotly
# Run this script on your VPS to get the new Plotly choropleth map

echo "🗺️  Updating World Map from Leaflet to Plotly"
echo "============================================="

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
echo "🗺️  New Plotly Features:"
echo "   ✅ Professional choropleth visualization"
echo "   ✅ Built-in country recognition (no external GeoJSON)"
echo "   ✅ Interactive hover tooltips"
echo "   ✅ Export functionality (PNG download)"
echo "   ✅ Responsive design"
echo "   ✅ Better color scale with funding levels"
echo "   ✅ Ocean and coastline styling"
echo ""
echo "🌐 Visit your statistics page: https://cgt.xeradb.com/global-affairs/statistics/"
echo "📊 The map should now load reliably with Plotly!"
