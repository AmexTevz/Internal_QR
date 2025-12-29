// Simple Trend Navigation - Makes trend chart clickable
(function() {
    'use strict';

    console.log('🔵 Trend Navigation: Starting...');

    // Wait for page to load
    function init() {
        setTimeout(function checkForTrend() {
            const trendWidget = document.querySelector('[data-testid="trend"]');

            if (!trendWidget) {
                console.log('⏳ Waiting for trend widget...');
                setTimeout(checkForTrend, 500);
                return;
            }

            console.log('✅ Trend widget found!');

            // Find the chart container
            const chartContainer = trendWidget.querySelector('canvas, svg, .recharts-wrapper, .chart');

            if (!chartContainer) {
                console.log('❌ Chart container not found');
                setTimeout(checkForTrend, 500);
                return;
            }

            console.log('✅ Chart container found:', chartContainer.tagName);

            // Make it clickable
            chartContainer.style.cursor = 'pointer';
            chartContainer.title = 'Click on trend points to navigate to previous reports';

            // Add click handler
            chartContainer.addEventListener('click', function(e) {
                console.log('🖱️ Trend chart clicked!');

                // Get archives
                fetch('archives/')
                    .then(response => response.text())
                    .then(html => {
                        // Parse the HTML to find run folders
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const links = Array.from(doc.querySelectorAll('a'))
                            .map(a => a.getAttribute('href'))
                            .filter(href => href && href.startsWith('run-'))
                            .sort()
                            .reverse(); // Newest first

                        console.log('📁 Found archived runs:', links);

                        if (links.length === 0) {
                            alert('No previous runs available yet. Run tests multiple times to see history!');
                            return;
                        }

                        // Calculate which point was clicked
                        const rect = chartContainer.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const width = rect.width;

                        // Total points = archives + 1 (current)
                        const totalPoints = links.length + 1;
                        const pointWidth = width / totalPoints;
                        const clickedIndex = Math.floor(x / pointWidth);

                        console.log(`📊 Clicked index: ${clickedIndex} of ${totalPoints} points`);

                        if (clickedIndex === totalPoints - 1) {
                            alert('✅ You are already viewing the current report!');
                            return;
                        }

                        if (clickedIndex >= 0 && clickedIndex < links.length) {
                            const targetRun = links[clickedIndex];
                            const timestamp = targetRun.replace('run-', '').replace('/', '');
                            const formatted = formatTimestamp(timestamp);

                            if (confirm(`Navigate to report from ${formatted}?`)) {
                                window.location.href = `archives/${targetRun}/index.html`;
                            }
                        }
                    })
                    .catch(err => {
                        console.error('❌ Error fetching archives:', err);
                        alert('Could not load previous runs. Make sure archives folder exists.');
                    });
            });

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

            trendWidget.appendChild(indicator);

            // Add animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.05); opacity: 0.8; }
                }
            `;
            document.head.appendChild(style);

            console.log('✅ Trend navigation initialized!');

        }, 1000);
    }

    // Format timestamp for display
    function formatTimestamp(timestamp) {
        // Format: YYYYMMDDHHMMSS -> YYYY-MM-DD HH:MM:SS
        if (timestamp.length === 14) {
            return timestamp.replace(
                /(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/,
                '$1-$2-$3 $4:$5:$6'
            );
        }
        return timestamp;
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();