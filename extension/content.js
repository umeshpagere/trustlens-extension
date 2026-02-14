// content.js - TrustLens Content Script
// This script is injected ONLY on user action (clicking extension icon)
// It uses a Shadow DOM to stay isolated and avoid detection by x.com

(function() {
    if (window.__trustlensInjected) {
        console.log('TrustLens: Already active in this tab.');
        return;
    }
    window.__trustlensInjected = true;

    console.log('TrustLens: Content script initialized.');

    // --- Configuration & Selectors ---
    const SHARE_SELECTORS = [
        '[aria-label*="Share"]',
        '[aria-label*="Repost"]',
        '[aria-label*="Forward"]',
        '[data-testid="share"]',
        '[data-testid="retweet"]',
        '.share-button'
    ];

    // --- Core Listener ---
    document.addEventListener('click', (event) => {
        const target = event.target;
        const shareBtn = target.closest(SHARE_SELECTORS.join(','));
        
        if (shareBtn) {
            console.log('TrustLens: Share action detected.');
            handleShareAction(shareBtn);
        }
    }, true); // Capture phase to ensure we see the event

    async function handleShareAction(button) {
        // Find the closest "tweet" or "post" container to extract context
        const container = button.closest('[data-testid="tweet"], article, .post, .feed-item') || document.body;
        const extracted = extractContent(container);

        if (!extracted.text && !extracted.imageUrl) {
            console.log('TrustLens: No content to analyze.');
            return;
        }

        showOverlay('Analyzing credibility...', 'neutral');

        try {
            console.log('TrustLens: Sending content for analysis...');
            const response = await chrome.runtime.sendMessage({
                type: 'ANALYZE_CONTENT',
                payload: extracted
            });

            console.log('TrustLens: Received response:', response);

            if (response && response.success) {
                showOverlay(null, null, null, response.data);
            } else {
                const errorMsg = response ? response.error : 'Unknown error';
                showOverlay('Analysis failed: ' + errorMsg, 'error');
            }
        } catch (error) {
            console.error('TrustLens Connection Error:', error);
            showOverlay('Error connecting to assistant. Please ensure the extension is reloaded and the backend is running.', 'error');
        }
    }

    function extractContent(container) {
        let text = '';
        let imageUrl = null;

        // Try to find tweet text
        const textEl = container.querySelector('[data-testid="tweetText"]') || container.querySelector('[lang]');
        if (textEl) text = textEl.innerText.trim();

        // Try to find images
        const images = container.querySelectorAll('img');
        for (const img of images) {
            if (img.src && !img.src.includes('profile_images') && !img.src.includes('emoji') && img.width > 100) {
                imageUrl = img.src;
                break;
            }
        }

        // Fallback to general text if needed
        if (!text) text = container.innerText.substring(0, 500);

        return { text: text.substring(0, 500), imageUrl };
    }

    // --- Shadow DOM Overlay ---
    let shadowRoot = null;
    let overlayElement = null;
    let detailedModal = null;

    function getPlatformName() {
        const host = window.location.hostname;
        if (host.includes('twitter.com') || host.includes('x.com')) return 'X / Twitter';
        if (host.includes('instagram.com')) return 'Instagram';
        if (host.includes('facebook.com')) return 'Facebook';
        if (host.includes('linkedin.com')) return 'LinkedIn';
        return 'Web Content';
    }

    function showOverlay(message, risk = 'neutral', score = null, data = null) {
        if (!overlayElement) {
            const host = document.createElement('div');
            host.id = 'trustlens-host';
            document.body.appendChild(host);
            shadowRoot = host.attachShadow({ mode: 'open' });

            overlayElement = document.createElement('div');
            overlayElement.id = 'trustlens-overlay';
            shadowRoot.appendChild(overlayElement);

            const style = document.createElement('style');
            style.textContent = `
                #trustlens-overlay {
                    position: fixed;
                    bottom: 24px;
                    left: 24px;
                    width: 320px;
                    background: #F9FAFB;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                    z-index: 2147483647;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    padding: 24px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    border: 1px solid rgba(0,0,0,0.05);
                    transition: all 0.3s ease;
                    color: #111827;
                }
                .header-row {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .app-icon {
                    width: 40px;
                    height: 40px;
                    background: #E5E7EB;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 20px;
                }
                .app-info {
                    display: flex;
                    flex-direction: column;
                }
                .app-name {
                    font-weight: 700;
                    font-size: 18px;
                    color: #111827;
                }
                .app-subtitle {
                    font-size: 12px;
                    color: #6B7280;
                }
                .detected-row {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 14px;
                    color: #374151;
                    margin-top: 4px;
                }
                .score-container {
                    position: relative;
                    width: 160px;
                    height: 160px;
                    margin: 0 auto;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .circular-progress {
                    transform: rotate(-90deg);
                    width: 100%;
                    height: 100%;
                }
                .circle-bg {
                    fill: none;
                    stroke: #E5E7EB;
                    stroke-width: 12;
                }
                .circle-progress {
                    fill: none;
                    stroke: #F59E0B;
                    stroke-width: 12;
                    stroke-linecap: round;
                    stroke-dasharray: 440;
                    stroke-dashoffset: 440;
                    transition: stroke-dashoffset 1s ease-out;
                }
                .score-text {
                    position: absolute;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }
                .score-value {
                    font-size: 36px;
                    font-weight: 800;
                    color: #111827;
                    line-height: 1;
                }
                .score-label {
                    font-size: 12px;
                    color: #6B7280;
                    margin-top: 4px;
                }
                .risk-pill {
                    align-self: center;
                    padding: 6px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                    background: #FEF3C7;
                    color: #92400E;
                }
                .risk-low { background: #D1FAE5; color: #065F46; }
                .risk-medium { background: #FEF3C7; color: #92400E; }
                .risk-high { background: #FEE2E2; color: #991B1B; }
                .risk-neutral { background: #F3F4F6; color: #374151; }
                
                .bullet-points {
                    list-style: none;
                    padding: 0;
                    margin: 0;
                    font-size: 14px;
                    color: #4B5563;
                }
                .bullet-points li {
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    margin-bottom: 6px;
                }
                .bullet-points li::before {
                    content: "•";
                    color: #111827;
                    font-weight: bold;
                }
                .button-row {
                    display: flex;
                    gap: 12px;
                    margin-top: 8px;
                }
                .btn {
                    flex: 1;
                    padding: 10px;
                    border-radius: 12px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    border: none;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    transition: all 0.2s;
                }
                .btn-learn {
                    background: #059669;
                    color: white;
                }
                .btn-learn:hover { background: #047857; }
                .btn-dismiss {
                    background: #E5E7EB;
                    color: #4B5563;
                }
                .btn-dismiss:hover { background: #D1D5DB; }

                /* Detailed Modal */
                #trustlens-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: rgba(0,0,0,0.5);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 2147483647;
                }
                .modal-content {
                    background: white;
                    width: 90%;
                    max-width: 800px;
                    max-height: 90vh;
                    border-radius: 24px;
                    padding: 32px;
                    overflow-y: auto;
                    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
                    display: flex;
                    flex-direction: column;
                    gap: 24px;
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                }
                .modal-title {
                    font-size: 24px;
                    font-weight: 800;
                    color: #111827;
                }
                .modal-close {
                    cursor: pointer;
                    font-size: 24px;
                    color: #9CA3AF;
                }
                .analysis-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 24px;
                }
                @media (max-width: 640px) {
                    .analysis-grid { grid-template-columns: 1fr; }
                }
                .section-card {
                    background: #F9FAFB;
                    border-radius: 16px;
                    padding: 16px;
                    border: 1px solid #F3F4F6;
                }
                .section-title {
                    font-size: 14px;
                    font-weight: 700;
                    color: #6B7280;
                    text-transform: uppercase;
                    margin-bottom: 8px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .section-text {
                    font-size: 15px;
                    line-height: 1.6;
                    color: #374151;
                }
                .preview-img {
                    width: 100%;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    object-fit: cover;
                    max-height: 300px;
                    border: 1px solid #E5E7EB;
                }
                .red-flag-item {
                    color: #991B1B;
                    background: #FEE2E2;
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-size: 13px;
                    display: inline-block;
                    margin: 2px;
                }
            `;
            shadowRoot.appendChild(style);
        }

        let finalScore = score;
        let finalRisk = risk;
        let points = [];

        if (data) {
            finalScore = data.finalResult.finalScore;
            const finalVerdict = data.finalResult.finalVerdict;
            // Map final verdict to risk bucket for overlay styling
            if (typeof finalVerdict === 'string') {
                const v = finalVerdict.toLowerCase();
                if (v.includes('reliable')) finalRisk = 'low';
                else if (v.includes('questionable')) finalRisk = 'medium';
                else if (v.includes('high')) finalRisk = 'high';
                else finalRisk = 'neutral';
            } else {
                finalRisk = 'neutral';
            }
            
            // Collect bullet points
            if (data.textAnalysis && data.textAnalysis.riskKeywordsFound) {
                points = [...points, ...data.textAnalysis.riskKeywordsFound];
            }
            if (data.imageAnalysis && data.imageAnalysis.llmAnalysis && data.imageAnalysis.llmAnalysis.visualRedFlags) {
                points = [...points, ...data.imageAnalysis.llmAnalysis.visualRedFlags];
            }
            
            // If no points but high risk, use common patterns
            if (points.length === 0 && finalRisk !== 'low') {
                if (data.finalResult.explanation) {
                    points = data.finalResult.explanation.split('.').filter(s => s.trim().length > 10).slice(0, 2);
                }
            }
            if (points.length === 0) points = ["Analyzing source credibility", "Verification in progress"];
        }

        const safeRisk = (finalRisk || 'neutral').toLowerCase();
        const scoreClass = ['low', 'medium', 'high', 'neutral'].includes(safeRisk) ? safeRisk : 'medium';
        const colorMap = { low: '#059669', medium: '#F59E0B', high: '#DC2626', neutral: '#6B7280' };
        
        // Circular progress calculation
        const offset = data ? 440 - (440 * finalScore) / 100 : 440;

        overlayElement.innerHTML = `
            <div class="header-row">
                <div class="app-icon">🛡️</div>
                <div class="app-info">
                    <span class="app-name">TrustLens</span>
                    <span class="app-subtitle">AI-powered credibility assistant</span>
                </div>
            </div>

            <div class="detected-row">
                <span>📷 Detected: <strong>${getPlatformName()}</strong></span>
            </div>

            <div class="score-container">
                <svg class="circular-progress" viewBox="0 0 160 160">
                    <circle class="circle-bg" cx="80" cy="80" r="70"></circle>
                    <circle class="circle-progress" cx="80" cy="80" r="70" 
                        style="stroke-dashoffset: ${offset}; stroke: ${colorMap[scoreClass]}"></circle>
                </svg>
                <div class="score-text">
                    <span class="score-value">${data ? finalScore : '...'}</span>
                    <span class="score-label">out of 100</span>
                </div>
            </div>

            <div class="risk-pill risk-${scoreClass}">
                ${safeRisk.toUpperCase()} RISK
            </div>

            <ul class="bullet-points">
                ${points.slice(0, 2).map(p => `<li>${p}</li>`).join('')}
            </ul>

            <div class="button-row">
                <button class="btn btn-learn" id="tl-learn">ℹ️ Learn Why</button>
                <button class="btn btn-dismiss" id="tl-dismiss">✕ Dismiss</button>
            </div>
        `;

        if (message && !data) {
             overlayElement.querySelector('.bullet-points').innerHTML = `<li>${message}</li>`;
        }

        shadowRoot.getElementById('tl-dismiss').onclick = closeOverlay;
        
        if (data) {
            shadowRoot.getElementById('tl-learn').onclick = () => showDetailedPopup(data);
        }

        overlayElement.style.opacity = '1';
        overlayElement.style.transform = 'translateY(0)';
    }

    function showDetailedPopup(data) {
        if (detailedModal) detailedModal.remove();

        detailedModal = document.createElement('div');
        detailedModal.id = 'trustlens-modal-overlay';
        
        const finalResult = data.finalResult;
        const imgAnalysis = data.imageAnalysis && data.imageAnalysis.llmAnalysis ? data.imageAnalysis.llmAnalysis : null;
        const textAnalysis = data.textAnalysis ? data.textAnalysis : null;
        
        detailedModal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title">TrustLens Deep Analysis</div>
                    <div class="modal-close" id="modal-close">✕</div>
                </div>

                <div class="section-card" style="border-left: 6px solid ${
                    (finalResult.finalVerdict || '').toLowerCase().includes('high') ? '#DC2626' :
                    (finalResult.finalVerdict || '').toLowerCase().includes('questionable') ? '#F59E0B' : '#059669'
                }">
                    <div class="section-title">⚖️ Verdict: ${finalResult.finalVerdict} (${finalResult.finalScore}/100)</div>
                    <div class="section-text">${finalResult.explanation || ''}</div>
                </div>

                <div class="analysis-grid">
                    <div class="left-col">
                        ${imgAnalysis ? `
                            <div class="section-card" style="margin-bottom: 20px;">
                                <div class="section-title">🖼️ Analyzed Image</div>
                                <img src="${data.imageAnalysis.imageUrl || ''}" class="preview-img" onerror="this.style.display='none'">
                                <div class="section-text"><strong>Content:</strong> ${imgAnalysis.imageContent}</div>
                                <div style="margin-top: 10px;">
                                    ${imgAnalysis.visualRedFlags.map(f => `<span class="red-flag-item">${f}</span>`).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="section-card">
                            <div class="section-title">📝 Analyzed Text</div>
                            <div class="section-text" style="font-style: italic; color: #4B5563; border-left: 2px solid #D1D5DB; padding-left: 10px;">
                                "${textAnalysis?.extractedText || data.textAnalysis?.text || 'No text extracted'}"
                            </div>
                        </div>
                    </div>

                    <div class="right-col">
                        ${imgAnalysis ? `
                            <div class="section-card" style="margin-bottom: 20px;">
                                <div class="section-title">🔍 Verification</div>
                                <div class="section-text">${imgAnalysis.textVerification}</div>
                            </div>
                            <div class="section-card" style="margin-bottom: 20px;">
                                <div class="section-title">💡 Intent & Message</div>
                                <div class="section-text">${imgAnalysis.conveyedMessage}</div>
                            </div>
                            <div class="section-card">
                                <div class="section-title">🤖 AI Probability</div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div style="flex: 1; height: 10px; background: #E5E7EB; border-radius: 5px; overflow: hidden;">
                                        <div style="width: ${imgAnalysis.aiGeneratedProbability}%; height: 100%; background: #6366F1;"></div>
                                    </div>
                                    <span style="font-weight: bold;">${imgAnalysis.aiGeneratedProbability}%</span>
                                </div>
                            </div>
                        ` : `
                            <div class="section-card">
                                <div class="section-title">🔍 Analysis Details</div>
                                <div class="section-text">${textAnalysis?.explanation || 'No detailed text analysis available.'}</div>
                            </div>
                        `}
                    </div>
                </div>
                
                <button class="btn btn-dismiss" id="modal-close-btn" style="max-width: 200px; align-self: center;">Close Analysis</button>
            </div>
        `;

        shadowRoot.appendChild(detailedModal);

        const closeBtn = () => {
            detailedModal.remove();
            detailedModal = null;
        };

        shadowRoot.getElementById('modal-close').onclick = closeBtn;
        shadowRoot.getElementById('modal-close-btn').onclick = closeBtn;
        detailedModal.onclick = (e) => {
            if (e.target === detailedModal) closeBtn();
        };
    }

    function closeOverlay() {
        if (!overlayElement) return;
        overlayElement.style.opacity = '0';
        overlayElement.style.transform = 'translateY(20px)';
        setTimeout(() => {
            const host = document.getElementById('trustlens-host');
            if (host) host.remove();
            overlayElement = null;
        }, 300);
    }

})();
