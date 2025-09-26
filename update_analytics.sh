#!/bin/bash

# Update Analytics Configuration
# Run this script on your VPS to add Google Analytics with environment variable configuration

echo "📊 Updating Google Analytics Configuration"
echo "========================================"

# Make sure we're in the right directory
cd /home/cgt/Canada_grants
source venv/bin/activate

echo "1️⃣  Pulling latest code from GitHub..."
git pull origin main

echo "2️⃣  Adding Google Analytics ID to .env file..."
# Check if GOOGLE_ANALYTICS_ID already exists in .env
if grep -q "GOOGLE_ANALYTICS_ID" .env; then
    echo "   ✅ GOOGLE_ANALYTICS_ID already exists in .env"
else
    echo "" >> .env
    echo "# Analytics" >> .env
    echo "GOOGLE_ANALYTICS_ID=G-C4H8V6WDDG" >> .env
    echo "   ✅ Added GOOGLE_ANALYTICS_ID to .env"
fi

echo "3️⃣  Collecting static files..."
python manage.py collectstatic --noinput

echo "4️⃣  Restarting application..."
sudo supervisorctl restart cgt

echo "5️⃣  Checking application status..."
sleep 2
sudo supervisorctl status cgt

echo ""
echo "🎉 Analytics Configuration Update Complete!"
echo ""
echo "📊 Google Analytics Setup:"
echo "   ✅ ID stored securely in environment variable"
echo "   ✅ Only loads when GOOGLE_ANALYTICS_ID is set"
echo "   ✅ Template updated to use dynamic ID"
echo "   ✅ Context processor provides ID to all pages"
echo ""
echo "🔐 Security Benefits:"
echo "   ✅ No hardcoded tracking ID in code"
echo "   ✅ Can be disabled by removing from .env"
echo "   ✅ Different IDs for different environments"
echo ""
echo "🌐 Visit your site and check Google Analytics for tracking data!"
echo "📈 Analytics should now be active on all pages."
