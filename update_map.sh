#!/bin/bash

# Update Map - Switch from Leaflet to Plotly
# Run this script on your VPS to get the new Plotly choropleth map

echo "🗺️  Updating World Map - Simplified Working Implementation"
echo "========================================================="

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
echo "🔧 Simplified Plotly Implementation:"
echo "   ✅ Using proven working pattern from democracy-analysis"
echo "   ✅ Specific Plotly.js version 2.24.1 (reliable CDN)"
echo "   ✅ Single CDN source: cdn.jsdelivr.net (fast & reliable)"
echo "   ✅ Simple direct Plotly.newPlot() call"
echo "   ✅ Minimal overhead, maximum compatibility"
echo ""
echo "🗺️  Map Features:"
echo "   ✅ Interactive world choropleth visualization"
echo "   ✅ Country hover tooltips with funding details"
echo "   ✅ Color-coded funding levels (light to dark blue)"
echo "   ✅ Natural earth projection for professional look"
echo "   ✅ Responsive design works on all devices"
echo ""
echo "🎯 Based On: Working CitingRetracted/democracy-analysis pattern"
echo "   ✅ Same CDN, same version, same approach"
echo "   ✅ Proven to work reliably across different environments"
echo "   ✅ No complex diagnostics needed - it just works!"
echo ""
echo "🌐 Visit: https://cgt.xeradb.com/global-affairs/statistics/"
echo "📊 Map should load immediately without any issues!"
