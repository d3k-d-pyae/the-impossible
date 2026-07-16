#!/bin/bash
# Render Deployment Script for Impossible Challenge

echo "========================================="
echo "DEPLOYING IMPOSSIBLE CHALLENGE TO RENDER"
echo "========================================="

# Get the Render URL from user
read -p "Enter your Render service URL (e.g., https://impossible-challenge.onrender.com): " RENDER_URL

# Remove trailing slash if present
RENDER_URL="${RENDER_URL%/}"

echo "Using URL: $RENDER_URL"

# Update extension files with new URL
echo ""
echo "Updating extension files..."

# Update background.js
sed -i "s|{{RENDER_URL}}|$RENDER_URL|g" extension/background.js

# Update manifest.json
sed -i "s|{{RENDER_URL}}|$RENDER_URL|g" extension/manifest.json

# Update popup.js
sed -i "s|{{RENDER_URL}}|$RENDER_URL|g" extension/popup.js

# Update content.js
sed -i "s|{{RENDER_URL}}|$RENDER_URL|g" extension/content.js

# Re-package extension
echo ""
echo "Re-packaging extension..."
rm -f static/extension/impossible_ext.zip
cd extension && zip -r ../static/extension/impossible_ext.zip . && cd ..

echo ""
echo "========================================="
echo "DEPLOYMENT PREPARATION COMPLETE!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Push this code to your GitHub repository"
echo "2. Go to https://dashboard.render.com"
echo "3. Click 'New +' -> 'Web Service'"
echo "4. Connect your GitHub repository"
echo "5. Configure:"
echo "   - Name: impossible-challenge"
echo "   - Runtime: Python"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: gunicorn --worker-class eventlet -w 1 server:app"
echo "6. Add Environment Variable:"
echo "   - Key: BASE_URL"
echo "   - Value: $RENDER_URL"
echo "7. Click 'Create Web Service'"
echo ""
echo "Flag: UITCTF{y0u_f0und_th3_h1dd3n_p13c3s_t0g3th3r_w3ll_d0n3!}"
echo "========================================="
