#!/bin/bash

# Update Map - Switch from Leaflet to Plotly
# Run this script on your VPS to get the new Plotly choropleth map

echo "🗺️  Updating World Map - Enhanced Diagnostics & 4 CDN Fallback"
echo "==============================================================="

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
echo "🔧 Enhanced Plotly Loading System:"
echo "   ✅ 4 CDN fallback sources (plot.ly → jsdelivr → unpkg → cdnjs)"
echo "   ✅ Real-time loading diagnostics with detailed timing"
echo "   ✅ Network connectivity testing (httpbin.org)"
echo "   ✅ Comprehensive error reporting with solutions"
echo "   ✅ Interactive diagnostics panel for troubleshooting"
echo "   ✅ 10-second timeout with detailed failure analysis"
echo ""
echo "🗺️  Map Features When Loaded:"
echo "   ✅ Interactive world choropleth visualization"
echo "   ✅ Country hover tooltips with funding details"
echo "   ✅ Color-coded funding levels ($0 to $1B+)"
echo "   ✅ Export to PNG functionality"
echo "   ✅ Professional ocean/coastline styling"
echo ""
echo "🔍 Diagnostic Features:"
echo "   ✅ Shows which CDNs were attempted and their status"
echo "   ✅ Reports network connectivity issues"
echo "   ✅ Provides troubleshooting steps for ad blockers/firewalls"
echo "   ✅ Console logging for technical debugging"
echo ""
echo "🌐 Visit: https://cgt.xeradb.com/global-affairs/statistics/"
echo "📊 Check browser console for detailed loading diagnostics!"
echo ""
echo "💡 If map still doesn't load, click 'Show Diagnostics' button"
echo "   to see exactly which CDNs failed and why."
