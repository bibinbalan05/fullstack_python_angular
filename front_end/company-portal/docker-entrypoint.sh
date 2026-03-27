#!/bin/sh
set -e  # Exit on any error

# Replace environment variables in the built Angular files
# This allows us to inject API URLs and other config at runtime

echo "Injecting environment variables..."

# Define the main.js file (Angular build output)
MAIN_JS_FILE=$(find /usr/share/nginx/html -name "main*.js" | head -1)

if [ -f "$MAIN_JS_FILE" ]; then
    echo "Found main.js file: $MAIN_JS_FILE"
    
    # Replace placeholder with actual API URL (validate URL format)
    if [ ! -z "$API_URL" ]; then
        # Basic URL validation
        case "$API_URL" in
            https://*)
                echo "Setting API_URL to: $API_URL"
                sed -i "s|API_URL_PLACEHOLDER|$API_URL|g" "$MAIN_JS_FILE"
                ;;
            *)
                echo "Error: API_URL must use HTTPS protocol"
                exit 1
                ;;
        esac
    else
        echo "Warning: API_URL not set, using default"
        sed -i "s|API_URL_PLACEHOLDER|https://api.archr.se|g" "$MAIN_JS_FILE"
    fi
    
    echo "Environment variable injection complete"
else
    echo "Warning: main.js file not found"
fi

# Start nginx
exec "$@"
