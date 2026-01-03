#!/bin/bash

# Check if allure command is available
if ! command -v allure &> /dev/null; then
    echo "Allure command not found. Please install Allure command line tool first."
    echo "You can install it via:"
    echo "  brew install allure  # on macOS"
    echo "  or"
    echo "  npm install -g allure-commandline  # using npm"
    exit 1
fi

# Check if netlify command is available when deploying
if [ "$1" == "deploy" ] && ! command -v netlify &> /dev/null; then
    echo "Netlify CLI not found. Please install it first with:"
    echo "  npm install -g netlify-cli"
    exit 1
fi

# Check if logo exists
if [ ! -f "logo.png" ]; then
    echo "Error: logo.png not found in current directory"
    exit 1
fi

# Check if favicon exists
if [ ! -f "favicon.ico" ]; then
    echo "Error: favicon.ico not found in current directory"
    exit 1
fi

# Function to gather environment information
gather_environment_info() {
    local env_file="$1"
    echo "Gathering environment information..."

    local os_platform
    local os_release
    local os_version
    local python_version
    local pytest_version
    local allure_version
    local requests_version
    local selenium_version

    # Get OS information
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$(uname -s)" == MINGW* ]]; then
        os_platform="Windows"
    else
        os_platform=$(uname -s)
    fi
    os_release=$(uname -r)
    os_version=$(sw_vers -productVersion 2>/dev/null || echo "N/A")

    # Get Python version
    python_version=$(python --version 2>&1 | cut -d' ' -f2)

    # Get package versions
    pytest_version=$(pip freeze | grep "pytest==" | cut -d'=' -f3)
    allure_version=$(pip freeze | grep "allure-pytest==" | cut -d'=' -f3)
    requests_version=$(pip freeze | grep "requests==" | cut -d'=' -f3)
    selenium_version=$(pip freeze | grep "selenium==" | cut -d'=' -f3)

    # Write environment properties
    cat > "$env_file" << EOF
os.platform=${os_platform}
os.release=${os_release}
os.version=${os_version}
python.version=${python_version}
pytest.version=${pytest_version}
allure.pytest.version=${allure_version}
requests.version=${requests_version}
selenium.version=${selenium_version}
EOF
}

# Function to set up test categories
setup_categories() {
    echo "Setting up test categories..."
    mkdir -p allure-results
    cat > allure-results/categories.json << EOF
[
    {
        "name": "QR App UI Issues",
        "messageRegex": ".*qr.*app.*|.*element.*not.*found.*|.*TimeoutException.*|.*StaleElement.*",
        "matchedStatuses": ["failed", "broken"]
    },
    {
        "name": "Authentication Failures",
        "messageRegex": ".*auth.*failed.*|.*unauthorized.*|.*HTTP.*401.*|.*HTTP.*403.*",
        "matchedStatuses": ["failed", "broken"]
    },
    {
        "name": "Data Validation Errors",
        "messageRegex": ".*validation.*error.*|.*invalid.*data.*|.*AssertionError.*|.*ValueError.*",
        "matchedStatuses": ["failed"]
    },
    {
        "name": "Payment Processing Issues",
        "messageRegex": ".*payment.*failed.*|.*transaction.*error.*|.*payment.*timeout.*",
        "matchedStatuses": ["failed", "broken"]
    }
]
EOF
}

# Function to handle test history
setup_history() {
    echo "Setting up test history..."
    mkdir -p allure-results/history

    # Use project-specific history
    PROJECT_HISTORY_DIR=".allure-history/checkout_functionality"
    mkdir -p "$PROJECT_HISTORY_DIR"

    # Copy project-specific history if it exists
    if [ -d "$PROJECT_HISTORY_DIR" ] && [ "$(ls -A $PROJECT_HISTORY_DIR)" ]; then
        echo "Copying project history..."
        cp -r "$PROJECT_HISTORY_DIR"/* allure-results/history/ 2>/dev/null || true
    fi
}

# Function to set up executor information
setup_executor() {
    local build_date
    local build_time
    local build_num

    build_date=$(date "+%Y-%m-%d")
    build_time=$(date "+%H:%M:%S")
    build_num=$(date "+%Y%m%d%H%M%S")

    echo "Setting up executor information..."
    cat << EOF > allure-results/executor.json
{
    "name": "Local Execution",
    "type": "local",
    "reportName": "Internal QR APP TEST",
    "buildName": "${build_date} ${build_time}",
    "buildUrl": "https://internalqrapp.netlify.app",
    "reportUrl": "https://internalqrapp.netlify.app",
    "buildOrder": ${build_num}
}
EOF
}

# Function to preserve history after report generation
preserve_history() {
    local report_dir="$1"
    echo "Preserving test history..."

    PROJECT_HISTORY_DIR=".allure-history/checkout_functionality"
    mkdir -p "$PROJECT_HISTORY_DIR"

    # Save history to project-specific location
    if [ -d "$report_dir/history" ]; then
        echo "Saving history to project folder..."
        cp -r "$report_dir/history"/* "$PROJECT_HISTORY_DIR"/ 2>/dev/null || true
    fi
}

# Function to archive previous report (DEPLOY MODE ONLY)
archive_previous_report() {
    local current_timestamp="$1"

    # Create archives directory structure
    ARCHIVE_DIR="allure-report/archives"
    mkdir -p "$ARCHIVE_DIR"

    # If there's already a current report, archive it
    if [ -f "allure-report/index.html" ]; then
        echo "Archiving previous report..."

        # Create archive subdirectory with timestamp
        local archive_subdir="$ARCHIVE_DIR/run-$current_timestamp"
        mkdir -p "$archive_subdir"

        # Copy current report to archive (excluding the archives folder)
        find allure-report -type f -not -path "*/archives/*" -exec cp --parents {} "$archive_subdir/" \; 2>/dev/null || {
            # Fallback for systems without --parents support
            (cd allure-report && find . -type f -not -path "./archives/*" | while read file; do
                mkdir -p "$archive_subdir/$(dirname "$file")" 2>/dev/null
                cp "$file" "$archive_subdir/$file" 2>/dev/null
            done)
        }

        echo "Previous report archived to: $archive_subdir"
    fi
}

# Function to create trend navigation (CLICKABLE TRENDS)
create_trend_navigation() {
    local dir="$1"
    local archive_dir="$dir/archives"

    echo "Creating trend navigation mapping..."
    mkdir -p "$dir/js"

    # Get list of archived runs sorted by timestamp
    local archived_runs=""
    if [ -d "$archive_dir" ]; then
        archived_runs=$(find "$archive_dir" -name "run-*" -type d | sort)
    fi

    # Create JavaScript with mapping
    cat > "$dir/js/trend-navigation.js" << 'EOF'
// Trend Navigation for Allure Reports
(function() {
    'use strict';

    // Mapping of trend points to archived reports
    const trendMapping = {
EOF

    # Add mapping entries for each archived run
    if [ -n "$archived_runs" ]; then
        local index=0
        while IFS= read -r run_dir; do
            [ -z "$run_dir" ] && continue

            local run_name
            local timestamp

            run_name=$(basename "$run_dir")
            timestamp=${run_name#run-}

            cat >> "$dir/js/trend-navigation.js" << EOF
        ${index}: {
            path: 'archives/${run_name}/index.html',
            timestamp: '${timestamp}',
            displayName: '$(echo "$timestamp" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')'
        },
EOF
            index=$((index + 1))
        done <<< "$archived_runs"
    fi

    # Complete the JavaScript file
    cat >> "$dir/js/trend-navigation.js" << 'EOF'
    };

    // Function to make trend chart clickable
    function makeTrendClickable() {
        setTimeout(function() {
            const trendWidget = document.querySelector('[data-testid="trend"]');
            if (!trendWidget) {
                setTimeout(makeTrendClickable, 500);
                return;
            }

            const chartContainer = trendWidget.querySelector('canvas, svg, .recharts-wrapper');
            if (!chartContainer) {
                setTimeout(makeTrendClickable, 500);
                return;
            }

            // Add click event listener
            chartContainer.addEventListener('click', function(event) {
                const rect = chartContainer.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const width = rect.width;

                // Calculate which trend point was clicked
                const totalPoints = Object.keys(trendMapping).length + 1;
                const pointWidth = width / totalPoints;
                const clickedIndex = Math.floor(x / pointWidth);

                // Check if we have a mapping
                if (trendMapping[clickedIndex]) {
                    const targetReport = trendMapping[clickedIndex];
                    if (confirm(`Navigate to report from ${targetReport.displayName}?`)) {
                        window.location.href = targetReport.path;
                    }
                } else if (clickedIndex === totalPoints - 1) {
                    alert('You are already viewing the current report!');
                }
            });

            // Add hover effect
            chartContainer.style.cursor = 'pointer';
            chartContainer.title = 'Click on trend points to navigate to previous reports';

            // Add visual indicator
            const indicator = document.createElement('div');
            indicator.innerHTML = '💡 Click on trend points to view previous reports';
            indicator.style.cssText = `
                background: linear-gradient(45deg, #2196F3, #21CBF3);
                color: white;
                padding: 8px 12px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
                margin-top: 10px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
                animation: pulse 2s infinite;
            `;

            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.05); opacity: 0.8; }
                }
            `;
            document.head.appendChild(style);

            trendWidget.appendChild(indicator);

        }, 1000);
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', makeTrendClickable);
    } else {
        makeTrendClickable();
    }

})();
EOF

    echo "✓ Trend navigation JavaScript created"
}

# Function to create custom styles
create_custom_styles() {
    local dir=$1
    cat << EOF > "$dir/styles/custom.css"
.side-nav__brand {
    background: url('../plugins/custom-logo/logo.png') no-repeat center !important;
    background-size: contain !important;
    height: 50px !important;
    width: 160px !important;
    margin: 0 auto !important;
    padding: 0 !important;
}

.side-nav__brand span,
.side-nav__brand-text {
    display: none !important;
}

.side-nav__item[href='#executors'],
#executors,
[data-node-id='executors'] {
    display: none !important;
}

.header__title {
    visibility: hidden !important;
    position: relative !important;
}

.header__title::after {
    visibility: visible !important;
    position: absolute !important;
    top: 50% !important;
    left: 0 !important;
    transform: translateY(-50%) !important;
    content: "INTERNAL QR APP TEST" !important;
    font-weight: bold !important;
    color: #1976d2 !important;
}

/* Enhanced trend chart styling - CLICKABLE */
[data-testid="trend"] {
    position: relative !important;
}

[data-testid="trend"] canvas,
[data-testid="trend"] svg,
[data-testid="trend"] .recharts-wrapper {
    cursor: pointer !important;
    transition: transform 0.2s ease, filter 0.2s ease !important;
}

[data-testid="trend"] canvas:hover,
[data-testid="trend"] svg:hover,
[data-testid="trend"] .recharts-wrapper:hover {
    transform: scale(1.02) !important;
    filter: brightness(1.1) drop-shadow(0 4px 8px rgba(33, 150, 243, 0.3)) !important;
}
EOF
}

# Function to inject custom styles
inject_styles() {
    local dir=$1
    local index_file="$dir/index.html"

    if [ -f "$index_file" ]; then
        echo "Injecting styles and updating title..."

        # Create backup
        cp "$index_file" "$index_file.backup"

        # Inject CSS, JavaScript, favicon, update title
        sed -e 's|</head>|    <link rel="stylesheet" href="styles/custom.css">\
        <script src="js/trend-navigation.js"></script>\
        <link rel="icon" type="image/x-icon" href="favicon.ico">\
    <link rel="icon" type="image/png" sizes="32x32" href="favicon.ico">\
    <link rel="shortcut icon" href="favicon.ico">\
</head>|g' \
            -e 's|<title>.*</title>|<title>HMSHost</title>|g' \
            "$index_file.backup" > "$index_file"

        # Clean up backup
        rm "$index_file.backup" 2>/dev/null || true

        # Verify injection worked
        if grep -q "custom.css" "$index_file" && grep -q "trend-navigation.js" "$index_file" && grep -q "HMSHost" "$index_file"; then
            echo "✓ CSS and JavaScript injection successful"
        else
            echo "✗ Injection failed"
        fi
    fi
}

# Function to prepare report directory
prepare_report() {
    local dir=$1
    echo "Preparing report directory: $dir"

    # Create necessary directories
    mkdir -p "$dir/plugins/custom-logo" "$dir/styles" "$dir/js"

    # Copy assets
    cp logo.png "$dir/plugins/custom-logo/logo.png"
    cp favicon.ico "$dir/favicon.ico"

    # Create trend navigation JavaScript
    create_trend_navigation "$dir"

    # Create and inject custom styles
    create_custom_styles "$dir"
    inject_styles "$dir"

    # Verify files
    echo "Verifying report files..."
    for file in plugins/custom-logo/logo.png favicon.ico styles/custom.css js/trend-navigation.js; do
        if [ -f "$dir/$file" ]; then
            echo "✓ $file present"
        else
            echo "✗ $file missing"
        fi
    done
}

case "$1" in
    "serve")
        echo "Starting Allure server with results..."
        rm -rf /tmp/allure-* 2>/dev/null

        # Ensure allure-results directory exists
        mkdir -p allure-results

        # Set up history
        setup_history

        # Generate environment and categories files
        gather_environment_info "allure-results/environment.properties"
        setup_categories
        setup_executor

        # Add unique build identifiers
        echo "build.timestamp=$(date '+%Y-%m-%d %H:%M:%S')" >> allure-results/environment.properties
        echo "build.unique.id=$(date '+%Y%m%d%H%M%S')" >> allure-results/environment.properties

        # Generate the report in temp directory
        TMP_DIR=$(mktemp -d)
        allure generate allure-results -o "$TMP_DIR" --clean

        # Apply customizations
        prepare_report "$TMP_DIR"

        # Open in browser
        allure open "$TMP_DIR" >/dev/null 2>&1
        ;;

    "deploy")
        echo "Generating static report for deployment..."

        # Get current timestamp for archiving
        CURRENT_TIMESTAMP=$(date "+%Y%m%d%H%M%S")

        # Archive previous report if it exists
        if [ -f "allure-report/index.html" ]; then
            archive_previous_report "$CURRENT_TIMESTAMP"
        fi

        # Ensure allure-results directory exists
        mkdir -p allure-results

        # Set up history
        setup_history

        # Generate environment and categories files
        gather_environment_info "allure-results/environment.properties"
        setup_categories
        setup_executor

        # Add unique build identifiers
        echo "build.timestamp=$(date '+%Y-%m-%d %H:%M:%S')" >> allure-results/environment.properties
        echo "build.unique.id=$CURRENT_TIMESTAMP" >> allure-results/environment.properties

        # Generate new report
        allure generate allure-results -o allure-report --clean

        # Apply customizations
        prepare_report "allure-report"

        # Preserve history from this run
        preserve_history "allure-report"

        echo "Deploying to Netlify..."
        netlify deploy --prod --dir=allure-report

        echo "✓ Deployment complete!"
        ;;

    *)
        echo "Usage: $0 [serve|deploy]"
        echo "  serve  - Start local server with the report (no archiving)"
        echo "  deploy - Deploy report to Netlify (with archiving & history)"
        exit 1
        ;;
esac