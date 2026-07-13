const DATA = __JSON_DATA__;
    
    function renderDashboard() {
        // Tab 1 Metrics
        const metrics = document.querySelectorAll('#content1 .mc-val');
        if(metrics.length >= 4) {
            metrics[0].innerHTML = DATA.metrics.total;
            metrics[0].nextElementSibling.innerHTML = 'Tổng số aspect được trích xuất';
            
            metrics[1].innerHTML = DATA.metrics.nps;
            metrics[1].nextElementSibling.innerHTML = DATA.metrics.nps >= 0 ? 'Thuộc nhóm Tốt trong ngành' : 'Cần cải thiện ngay';
            metrics[1].className = DATA.metrics.nps >= 0 ? 'mc-val green' : 'mc-val red';
            
            metrics[2].innerHTML = DATA.metrics.neg_rate + '%';
            metrics[2].nextElementSibling.innerHTML = DATA.metrics.neg_count + ' đánh giá tiêu cực';
            
            metrics[3].innerHTML = DATA.metrics.pos_rate + '%';
            metrics[3].nextElementSibling.innerHTML = DATA.metrics.pos_count + ' đánh giá tích cực';
        }
        
        // Tab 1 Trend Line
        const svgTrend = document.querySelector('#content1 svg[preserveAspectRatio="none"]');
        if(svgTrend) {
            const polylines = svgTrend.querySelectorAll('polyline');
            const polygon = svgTrend.querySelector('polygon');
            if(polylines.length >= 2) {
                polylines[0].setAttribute('points', DATA.trend.pos_pts);
                polylines[1].setAttribute('points', DATA.trend.neg_pts);
            }
            if(polygon) polygon.setAttribute('points', DATA.trend.pos_poly);
        }

        // Tab 1 Drivers & Donut
        const cardTitles = document.querySelectorAll('#content1 .card-title');
        cardTitles.forEach(t => {
            if(t.innerHTML.includes('Mức độ ảnh hưởng lên Sự hài lòng')) {
                const driverContainer = t.parentElement.querySelector('div[style*="display:flex; flex-direction:column; gap:16px; margin-top:10px;"]');
                if(driverContainer) {
                    let driverHtml = '';
                    DATA.drivers.pos.forEach(d => {
                        driverHtml += `
                        <div>
                            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;">
                                <span style="font-weight:500">${d.name}</span> <span style="color:var(--pos); font-weight:600;">+${d.rate}% NPS</span>
                            </div>
                            <div style="height:6px; background:var(--surface2); border-radius:3px;">
                                <div style="width:${d.rate}%; height:100%; background:var(--pos); border-radius:3px;"></div>
                            </div>
                        </div>`;
                    });
                    driverHtml += `<div style="height:1px; background:var(--border); margin:4px 0;"></div>`;
                    DATA.drivers.neg.forEach(d => {
                        driverHtml += `
                        <div>
                            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;">
                                <span style="font-weight:500">${d.name}</span> <span style="color:var(--neg); font-weight:600;">-${d.rate}% NPS</span>
                            </div>
                            <div style="height:6px; background:var(--surface2); border-radius:3px; display:flex; justify-content:flex-end;">
                                <div style="width:${d.rate}%; height:100%; background:var(--neg); border-radius:3px;"></div>
                            </div>
                        </div>`;
                    });
                    driverContainer.innerHTML = driverHtml;
                }
            }
            if(t.innerHTML.includes('Cảm xúc tổng hợp (Toàn bộ Brand)')) {
                const parent = t.parentElement;
                const donut = parent.querySelector('.donut-mock');
                if(donut) {
                    donut.className = 'donut-real';
                    donut.style.width = '240px';
                    donut.style.height = '240px';
                    donut.style.borderRadius = '50%';
                    donut.style.margin = '30px auto 10px';
                    donut.style.background = `conic-gradient(var(--pos) 0% ${DATA.metrics.pos_rate}%, var(--neg) ${DATA.metrics.pos_rate}% 100%)`;
                    donut.style.position = 'relative';
                    donut.innerHTML = `<div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); background:white; border-radius:50%; width:65%; height:65%; display:flex; align-items:center; justify-content:center; font-size:36px; font-weight:bold; color:var(--text-primary);">${DATA.metrics.pos_rate}%</div>`;
                }
                const textWrap = parent.querySelector('div[style*="text-align:center; margin-top:12px"]');
                if(textWrap) textWrap.innerHTML = `Dữ liệu tổng hợp từ ${DATA.metrics.total} khía cạnh đánh giá.`;
                
                const legendWrap = parent.querySelector('div[style*="display:flex; justify-content:center; gap: 16px; margin-top: 24px;"]');
                if(legendWrap) {
                    legendWrap.innerHTML = `
                        <span style="font-size:12px;"><span style="color:var(--pos)">●</span> Tích cực (${DATA.metrics.pos_rate}%)</span>
                        <span style="font-size:12px;"><span style="color:var(--neg)">●</span> Tiêu cực (${DATA.metrics.neg_rate}%)</span>
                    `;
                }
            }
        });
        
        // Tab 1 Smart Alerts
        const smartAlertsList = document.querySelector('.smart-alerts-list');
        if (smartAlertsList && DATA.feed && DATA.feed.length > 0) {
            let negMap = {};
            let posMap = {};
            
            DATA.feed.forEach(f => {
                let prod = f.product || 'Sản phẩm chung';
                f.tags.forEach(t => {
                    let key = prod + '::' + t.aspect;
                    if (t.polarity === 'neg') {
                        if (!negMap[key]) negMap[key] = { prod: prod, aspect: t.aspect, count: 0 };
                        negMap[key].count++;
                    } else if (t.polarity === 'pos') {
                        if (!posMap[key]) posMap[key] = { prod: prod, aspect: t.aspect, count: 0 };
                        posMap[key].count++;
                    }
                });
            });
            
            let negAlerts = Object.values(negMap).sort((a,b) => b.count - a.count);
            let posAlerts = Object.values(posMap).sort((a,b) => b.count - a.count);
            
            let alertHtml = '';
            
            if (negAlerts.length > 0) {
                let worst = negAlerts[0];
                let prodText = worst.prod !== 'Sản phẩm chung' ? ` của ${worst.prod}` : '';
                alertHtml += `
                    <div class="alert-item" style="background:var(--neg-bg); margin-bottom:10px; border-left: 3px solid var(--neg);">
                      <div class="alert-icon" style="background:transparent; font-size:18px;">⚠️</div>
                      <div class="alert-text-wrap">
                        <div class="alert-title" style="font-size:13px; color:var(--neg); font-weight:600;">
                            Cảnh báo chất lượng: Khía cạnh "${worst.aspect}"${prodText} bị phàn nàn nhiều
                        </div>
                        <div class="alert-desc">
                            Phát hiện ${worst.count} đánh giá nhắc tới phản hồi tiêu cực về "${worst.aspect}". Đề xuất bộ phận vận hành/R&D kiểm tra ngay.
                        </div>
                      </div>
                    </div>
                `;
            }
            
            if (posAlerts.length > 0) {
                let best = posAlerts[0];
                let prodText = best.prod !== 'Sản phẩm chung' ? ` của ${best.prod}` : '';
                alertHtml += `
                    <div class="alert-item" style="background:var(--pos-bg); border-left: 3px solid var(--pos);">
                      <div class="alert-icon" style="background:transparent; font-size:18px;">💡</div>
                      <div class="alert-text-wrap">
                        <div class="alert-title" style="font-size:13px; color:var(--pos); font-weight:600;">
                            Cơ hội truyền thông: Khía cạnh "${best.aspect}"${prodText} được đánh giá tốt
                        </div>
                        <div class="alert-desc">
                            Khía cạnh "${best.aspect}" nhận được ${best.count} lượt khen ngợi từ khách hàng. Phù hợp đẩy mạnh làm USP trong chiến dịch truyền thông.
                        </div>
                      </div>
                    </div>
                `;
            }
            
            if (alertHtml) {
                smartAlertsList.innerHTML = alertHtml;
            } else {
                smartAlertsList.innerHTML = '<div style="font-size:11px;color:#999;padding:10px 0;">Không phát hiện cảnh báo hoặc cơ hội đặc biệt trong dữ liệu này.</div>';
            }
        }
        
        // Tab 1 Ranking
        const rankingList = document.querySelector('.ranking-list');
        if(rankingList) {
            let rankHtml = '';
            DATA.products.forEach((p, idx) => {
                let rankClass = idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : idx === 2 ? 'rank-3' : 'rank-other';
                let stars = p.score >= 4.5 ? '★★★★★' : p.score >= 3.5 ? '★★★★☆' : '★★★☆☆';
                let safeTooltip = (p.tooltip || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                rankHtml += `
                    <div class="ranking-item" style="position:relative; cursor:pointer; display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid var(--border);">
                        <div class="rank-badge ${rankClass}">${idx + 1}</div>
                        <div class="rank-info" style="flex:1; min-width:0;">
                            <div class="rank-name" style="font-weight:600; font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${p.name}</div>
                            <div class="rank-stars">
                                <span class="stars-visual">${stars}</span>
                                <span class="stars-score">${p.score}</span>
                                <span class="reviews-count">• ${p.total} khía cạnh</span>
                            </div>
                        </div>
                        <div class="custom-tooltip" style="display:none !important; position:absolute; top:100%; left:10%; z-index:1000; background:#222; color:#fff; padding:10px 14px; border-radius:8px; font-size:11px; white-space:pre-wrap; width:max-content; max-width:400px; box-shadow:0 4px 12px rgba(0,0,0,0.15); pointer-events:none; line-height:1.5;">${safeTooltip}</div>
                    </div>
                `;
            });
            rankingList.innerHTML = rankHtml;
            rankingList.style.maxHeight = '350px';
            rankingList.style.overflowY = 'auto';
            rankingList.style.paddingRight = '4px';
            rankingList.querySelectorAll('.ranking-item').forEach(item => {
                const tt = item.querySelector('.custom-tooltip');
                if (!tt) return;
                item.addEventListener('mouseenter', () => { tt.style.setProperty('display', 'block', 'important'); });
                item.addEventListener('mouseleave', () => { tt.style.setProperty('display', 'none', 'important'); });
            });
        }


        // Tab 1 Heatmap — top 10 aspects, scroll ngang
        const heatmapTable = document.querySelector('#content1 table');
        if(heatmapTable && DATA.heatmap.columns.length > 0) {
            // Wrap bảng trong container scroll ngang
            const heatmapCard = heatmapTable.closest('.card');
            let wrapper = heatmapTable.parentElement;
            if (!wrapper.classList.contains('heatmap-scroll-wrap')) {
                wrapper = document.createElement('div');
                wrapper.className = 'heatmap-scroll-wrap';
                wrapper.style.cssText = 'overflow-x: auto; overflow-y: auto; max-height: 360px; margin-top: 12px;';
                heatmapTable.parentNode.insertBefore(wrapper, heatmapTable);
                wrapper.appendChild(heatmapTable);
            }
            
            // Thead sticky
            let thead = `<tr style="position:sticky; top:0; z-index:5; background:var(--surface);
                border-bottom:1px solid var(--border); color:var(--text-muted); font-size:11px;">
                <th style="padding:8px 12px; min-width:130px; white-space:nowrap;">Sản phẩm</th>`;
            DATA.heatmap.columns.forEach(c => {
                thead += `<th style="padding:8px 12px; min-width:120px; white-space:nowrap;">${c}</th>`;
            });
            thead += '</tr>';
            heatmapTable.querySelector('thead').innerHTML = thead;
            heatmapTable.style.cssText = 'width: max-content; min-width: 100%; border-collapse: collapse; text-align: left;';
            
            let tbody = '';
            DATA.heatmap.data.forEach(row => {
                let tr = `<tr><td style="padding:12px; font-weight:500; font-size:12px; border-bottom:1px solid var(--border); min-width:130px; white-space:nowrap;">${row.product}</td>`;
                DATA.heatmap.columns.forEach(c => {
                    let d = row.aspects[c] || {pos_pct: 0, neg_pct: 0};
                    let dominantClass = d.pos_pct >= d.neg_pct ? 'pos' : 'neg';
                    let dominantVal = Math.max(d.pos_pct, d.neg_pct);
                    if (dominantVal === 0) {
                        tr += `<td style="padding:12px; border-bottom:1px solid var(--border); min-width:120px;">–</td>`;
                    } else {
                        tr += `<td style="padding:12px; border-bottom:1px solid var(--border); min-width:120px;">
                            <div style="display:flex; align-items:center; gap:6px;">
                                <div class="asp-bar-track" style="flex:1;">
                                    <div class="asp-bar-fill" style="width:${dominantVal}%; background:var(--${dominantClass})"></div>
                                </div>
                                <span style="font-size:10px; font-weight:600; font-family:'DM Mono',monospace; color:var(--${dominantClass}); width:28px; text-align:right;">${dominantVal}%</span>
                            </div>
                        </td>`;
                    }
                });
                tr += '</tr>';
                tbody += tr;
            });
            heatmapTable.querySelector('tbody').innerHTML = tbody;
        }

        // Tab 2 Metrics
        const t2Metrics = document.querySelectorAll('#content2 .mc-val');
        
        // Swap Ranking and Donut cards
        try {
            const rankingCard = document.querySelector('#content1 .ranking-list').closest('.card');
            const donutCard = rankingCard.nextElementSibling;
            if (rankingCard && donutCard && donutCard.querySelector('.donut-real')) {
                rankingCard.parentNode.insertBefore(donutCard, rankingCard);
            }
        } catch (e) {}
        
        if(t2Metrics.length >= 4) {
            t2Metrics[0].innerHTML = DATA.metrics.total;
            t2Metrics[0].nextElementSibling.innerHTML = DATA.feed.length + ' câu → ' + DATA.metrics.total + ' khía cạnh';
            
            t2Metrics[1].innerHTML = DATA.metrics.neg_rate + '%';
            t2Metrics[1].nextElementSibling.innerHTML = DATA.metrics.neg_count + ' khía cạnh tiêu cực';
            
            t2Metrics[2].innerHTML = DATA.metrics.pos_rate + '%';
            t2Metrics[2].nextElementSibling.innerHTML = DATA.metrics.pos_count + ' khía cạnh tích cực';
            
            t2Metrics[3].innerHTML = DATA.metrics.top_aspect;
            t2Metrics[3].nextElementSibling.innerHTML = DATA.metrics.top_aspect_count + ' lần nhắc đến';
        }
        
        // Tab 2 Metrics
        const t2MetricsRow = document.querySelector('#content2 .metrics-row');
        if(t2MetricsRow && !document.querySelector('#t2-charts-row')) {
            // 1. Grouped bar data
            let gbarHtml = '';
            let sortedProds = [...DATA.products].sort((a,b) => b.total - a.total);
            const topProds = sortedProds.slice(0, 15);
            topProds.forEach(p => {
                let safeName = (p.name || '').replace(/"/g, '&quot;').replace(/</g, '&lt;');
                let escapedName = (p.name || '').replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/</g, '&lt;');
                
                let pTtInner = `<div style=&quot;color:#fff; font-weight:600; font-size:13px; margin-bottom:6px;&quot;>${escapedName}</div><div style=&quot;display:flex; align-items:center; gap:6px; font-size:11px; color:#ccc;&quot;><span style=&quot;display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--pos);&quot;></span>Tích cực: ${p.pos} (${p.pos_rate}%)</div><div style=&quot;display:flex; align-items:center; gap:6px; font-size:11px; color:#ccc; margin-top:3px;&quot;><span style=&quot;display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--neg);&quot;></span>Tiêu cực: ${p.neg} (${p.neg_rate}%)</div><div style=&quot;font-size:11px; color:#888; margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.1);&quot;>Tổng nhắc đến: ${p.total} lần</div>`;
                
                gbarHtml += `
                <div style="display:flex; flex-direction:column; align-items:center; flex: 0 0 80px; gap:8px; cursor:pointer;"
                     onmouseover="let tt = document.getElementById('stacked-tt'); tt.innerHTML='${pTtInner}'; tt.style.opacity=1; tt.style.display='block';" 
                     onmouseout="let tt = document.getElementById('stacked-tt'); tt.style.opacity=0; tt.style.display='none';"
                     onmousemove="let tt = document.getElementById('stacked-tt'); tt.style.left = (event.clientX + 15) + 'px'; tt.style.top = (event.clientY + 15) + 'px';">
                    <div style="display:flex; align-items:flex-end; gap:3px; height:180px; width:100%; justify-content:center;">
                        <div style="width:20px; background:var(--pos); height:${p.pos_rate}%; border-radius:3px 3px 0 0; transition: opacity 0.2s;" onmouseover="this.style.opacity=0.7" onmouseout="this.style.opacity=1"></div>
                        <div style="width:20px; background:var(--neg); height:${p.neg_rate}%; border-radius:3px 3px 0 0; transition: opacity 0.2s;" onmouseover="this.style.opacity=0.7" onmouseout="this.style.opacity=1"></div>
                    </div>
                    <div style="font-size:9px; color:var(--text-muted); text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; width:100%;" title="${safeName}">${safeName}</div>
                </div>`;
            });

            // 2. Stacked Horizontal Bar for Aspects
            let aspectHtml = '';
            let sortedAsps = [...DATA.aspects].sort((a,b) => b.total - a.total).slice(0, 10);
            let maxAspTotal = sortedAsps.length > 0 ? sortedAsps[0].total : 1;
            
            sortedAsps.forEach(a => {
                let safeName = (a.name || '').replace(/"/g, '&quot;').replace(/</g, '&lt;');
                let escapedName = (a.name || '').replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/</g, '&lt;');
                let barWidth = (a.total / maxAspTotal) * 100;
                
                let ttInner = `<div style=&quot;color:#fff; font-weight:600; font-size:13px; margin-bottom:6px;&quot;>${escapedName}</div><div style=&quot;display:flex; align-items:center; gap:6px; font-size:11px; color:#ccc;&quot;><span style=&quot;display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--pos);&quot;></span>Tích cực: ${a.pos} (${a.pos_rate}%)</div><div style=&quot;display:flex; align-items:center; gap:6px; font-size:11px; color:#ccc; margin-top:3px;&quot;><span style=&quot;display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--neg);&quot;></span>Tiêu cực: ${a.neg} (${a.neg_rate}%)</div><div style=&quot;font-size:11px; color:#888; margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.1);&quot;>Tổng nhắc đến: ${a.total} lần</div>`;
                
                aspectHtml += `
                <div style="display:flex; align-items:center; gap:10px; margin-bottom: 8px;">
                    <div style="font-size:10px; width:75px; text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${safeName}">${safeName}</div>
                    <div style="flex:1; display:flex; align-items:center; gap:8px;">
                        <div style="width:${barWidth}%; display:flex; height:18px; border-radius:3px; overflow:hidden; background:var(--surface2); cursor:pointer; transition: opacity 0.2s;"
                             onmouseover="this.style.opacity=0.8; let tt = document.getElementById('stacked-tt'); tt.innerHTML='${ttInner}'; tt.style.opacity=1; tt.style.display='block';" 
                             onmouseout="this.style.opacity=1; let tt = document.getElementById('stacked-tt'); tt.style.opacity=0; tt.style.display='none';"
                             onmousemove="let tt = document.getElementById('stacked-tt'); tt.style.left = (event.clientX + 15) + 'px'; tt.style.top = (event.clientY + 15) + 'px';">
                            <div style="width:${a.pos_rate}%; background:var(--pos); height:100%;"></div>
                            <div style="width:${a.neg_rate}%; background:var(--neg); height:100%;"></div>
                        </div>
                    </div>
                </div>`;
            });
            aspectHtml += `<div id="stacked-tt" style="position:fixed; background:rgba(20,20,20,0.95); border:1px solid rgba(255,255,255,0.1); box-shadow:0 8px 24px rgba(0,0,0,0.3); padding:10px 14px; border-radius:8px; font-family:sans-serif; pointer-events:none; opacity:0; z-index:99999; display:none; line-height:1.4; text-align:left;"></div>`;

            const chartsHTML = `
            <div id="t2-charts-row" class="dashboard-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 24px; margin-top: 24px;">
                <div class="card" style="min-width:0;">
                    <div class="card-title" style="display:flex; justify-content:space-between; margin-bottom:10px;">
                        <div>
                            Sentiment theo sản phẩm<br>
                            <span style="font-size:10px; font-weight:normal; color:var(--text-muted)">Positive vs Negative rate mỗi sản phẩm</span>
                        </div>
                        <div style="font-size:10px; display:flex; gap:10px; align-items:flex-start">
                            <span><span style="color:var(--pos)">■</span> Positive</span>
                            <span><span style="color:var(--neg)">■</span> Negative</span>
                        </div>
                    </div>
                    <div style="display:flex; align-items:flex-end; gap:10px; height:240px; border-bottom:1px solid var(--border); padding-bottom:10px; padding-top:10px; overflow-x:auto; overflow-y:hidden;">
                        ${gbarHtml}
                    </div>
                </div>
                <div class="card" style="min-width:0;">
                    <div class="card-title" style="display:flex; justify-content:space-between; margin-bottom:15px;">
                        <div>
                            Sentiment theo khía cạnh (Aspect)<br>
                            <span style="font-size:10px; font-weight:normal; color:var(--text-muted)">Positive vs Negative theo mức độ nhắc đến </span>
                        </div>
                        <div style="font-size:10px; display:flex; gap:10px; align-items:flex-start">
                            <span><span style="color:var(--pos)">■</span> Positive</span>
                            <span><span style="color:var(--neg)">■</span> Negative</span>
                        </div>
                    </div>
                    <div style="display:flex; flex-direction:column; padding-right:10px; overflow-y:auto; max-height:240px;">
                        ${aspectHtml}
                    </div>
                </div>
            </div>`;
            
            t2MetricsRow.insertAdjacentHTML('afterend', chartsHTML);
        }

        // Tab 2 Feed & Filtering Logic
        const feedCol = document.querySelector('.feed-col');
        const sidebar = document.querySelector('.sidebar');
        
        if(feedCol && sidebar) {
            window.dashboardFilter = {
                aspect: 'Tất cả aspect',
                product: 'Tất cả',
                searchQuery: ''
            };
            
            const searchInput = document.querySelector('.search-wrap input');
            if(searchInput) {
                searchInput.addEventListener('input', function(e) {
                    window.dashboardFilter.searchQuery = e.target.value.toLowerCase();
                    window.renderFeedList();
                });
            }
            
            let aspCounts = {};
            let prodCounts = {};
            
            DATA.feed.forEach(f => {
                prodCounts[f.product] = (prodCounts[f.product] || 0) + 1;
                
                let uniqueAspects = new Set(f.tags.map(t => t.aspect));
                uniqueAspects.forEach(a => {
                    aspCounts[a] = (aspCounts[a] || 0) + 1;
                });
            });
            
            function getAspectColor(aspName) {
                const colors = ['#D85A30', '#BA7517', '#1D9E75', '#D4537E', '#3A6B10', '#888780', '#378ADD', '#E24B4A', '#534AB7'];
                let hash = 0;
                for (let i = 0; i < aspName.length; i++) { hash = aspName.charCodeAt(i) + ((hash << 5) - hash); }
                return colors[Math.abs(hash) % colors.length];
            }

            window.renderSidebar = function() {
                let aspectHtml = `
                    <div>
                        <div class="s-section-label">Aspect category</div>
                        <div class="s-item ${window.dashboardFilter.aspect === 'Tất cả aspect' ? 'active' : ''}" data-cat="aspect" data-val="Tất cả aspect">
                            <div class="s-dot" style="background:#888"></div>Tất cả aspect
                        </div>
                `;
                let sortedAspects = Object.keys(aspCounts).sort((a,b) => aspCounts[b] - aspCounts[a]);
                sortedAspects.forEach(asp => {
                    let activeClass = window.dashboardFilter.aspect === asp ? 'active' : '';
                    aspectHtml += `
                        <div class="s-item ${activeClass}" data-cat="aspect" data-val="${asp}">
                            <div class="s-dot" style="background:${getAspectColor(asp)}"></div>${asp}<span class="s-count">${aspCounts[asp]}</span>
                        </div>
                    `;
                });
                aspectHtml += `</div><div class="s-divider"></div>`;
                
                const PRODS_PER_PAGE = 20;
                window.prodPage = window.prodPage || 1;

                let sortedProds = Object.keys(prodCounts).sort((a,b) => prodCounts[b] - prodCounts[a]);
                let totalProdPages = Math.max(1, Math.ceil(sortedProds.length / PRODS_PER_PAGE));
                if (window.prodPage > totalProdPages) window.prodPage = 1;
                let prodStart = (window.prodPage - 1) * PRODS_PER_PAGE;
                let pagedProds = sortedProds.slice(prodStart, prodStart + PRODS_PER_PAGE);

                let prodHtml = `
                    <div>
                        <div class="s-section-label">Sản phẩm
                            ${totalProdPages > 1 ? `<span style="float:right;font-size:10px;color:var(--text-muted);font-weight:400">${window.prodPage}/${totalProdPages}</span>` : ''}
                        </div>
                        <div class="s-item ${window.dashboardFilter.product === 'Tất cả' ? 'active' : ''}" data-cat="product" data-val="Tất cả">
                            <div class="s-dot" style="background:#888"></div>Tất cả
                        </div>
                `;
                pagedProds.forEach(prod => {
                    let activeClass = window.dashboardFilter.product === prod ? 'active' : '';
                    prodHtml += `
                        <div class="s-item ${activeClass}" data-cat="product" data-val="${prod}">
                            <div class="s-dot" style="background:var(--accent-mid)"></div>
                            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px" title="${prod}">${prod}</span>
                            <span class="s-count">${prodCounts[prod]}</span>
                        </div>
                    `;
                });
                // Nút chuyển trang sản phẩm
                if (totalProdPages > 1) {
                    prodHtml += `
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;padding:0 2px">
                            <button class="prod-page-btn" data-dir="-1" style="font-size:11px;padding:3px 8px;border:1px solid var(--border);border-radius:4px;background:var(--surface);cursor:pointer;color:var(--text-secondary)" ${window.prodPage === 1 ? 'disabled style="opacity:0.4;cursor:default"' : ''}>←</button>
                            <span style="font-size:10px;color:var(--text-muted)">${prodStart+1}–${Math.min(prodStart+PRODS_PER_PAGE, sortedProds.length)} / ${sortedProds.length}</span>
                            <button class="prod-page-btn" data-dir="1" style="font-size:11px;padding:3px 8px;border:1px solid var(--border);border-radius:4px;background:var(--surface);cursor:pointer;color:var(--text-secondary)" ${window.prodPage === totalProdPages ? 'disabled style="opacity:0.4;cursor:default"' : ''}>→</button>
                        </div>
                    `;
                }
                prodHtml += `</div>`;
                
                sidebar.innerHTML = aspectHtml + prodHtml;
                
                sidebar.querySelectorAll('.s-item').forEach(item => {
                    item.addEventListener('click', function() {
                        let cat = this.getAttribute('data-cat');
                        let val = this.getAttribute('data-val');
                        if (cat === 'aspect') window.dashboardFilter.aspect = val;
                        if (cat === 'product') window.dashboardFilter.product = val;
                        
                        window.renderSidebar();
                        window.renderFeedList();
                    });
                });

                sidebar.querySelectorAll('.prod-page-btn').forEach(btn => {
                    btn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        if (this.disabled) return;
                        window.prodPage = (window.prodPage || 1) + parseInt(this.getAttribute('data-dir'));
                        window.renderSidebar();
                    });
                });
            };

            const ITEMS_PER_PAGE = 10;
            window.currentPage = window.currentPage || 1;

            window.renderFeedList = function() {
                window.currentPage = 1; // reset về trang 1 khi filter thay đổi
                window.renderFeedPage();
            };

            window.renderFeedPage = function() {
                let filteredFeed = DATA.feed.filter(f => {
                    if (window.dashboardFilter.product !== 'Tất cả' && f.product !== window.dashboardFilter.product) return false;
                    
                    let reqAsp = window.dashboardFilter.aspect !== 'Tất cả aspect' ? window.dashboardFilter.aspect : null;
                    
                    if (reqAsp) {
                        let matchAsp = f.tags.some(t => t.aspect === reqAsp);
                        if (!matchAsp) return false;
                    }
                    
                    if (window.dashboardFilter.searchQuery) {
                        let q = window.dashboardFilter.searchQuery;
                        let textMatch = f.text.toLowerCase().includes(q);
                        let prodMatch = f.product.toLowerCase().includes(q);
                        let tagMatch = f.tags.some(t => t.aspect.toLowerCase().includes(q));
                        if (!textMatch && !prodMatch && !tagMatch) return false;
                    }
                    
                    return true;
                });
                
                // Phân trang
                let totalPages = Math.max(1, Math.ceil(filteredFeed.length / ITEMS_PER_PAGE));
                if (window.currentPage > totalPages) window.currentPage = totalPages;
                let start = (window.currentPage - 1) * ITEMS_PER_PAGE;
                let pageFeed = filteredFeed.slice(start, start + ITEMS_PER_PAGE);

                let feedHtml = `
                    <div class="feed-header">
                        Danh sách đánh giá
                        <span class="feed-count">${filteredFeed.length}</span>
                    </div>
                `;
                feedHtml += `<div class="feed-body">`;
                pageFeed.forEach(f => {
                    let tagsHtml = '';
                    f.tags.forEach(t => {
                        let cls = t.polarity === 'pos' ? 'pos' : t.polarity === 'neg' ? 'neg' : '';
                        tagsHtml += `<span class="asp-pill ${cls}"><span class="asp-dot"></span>${t.aspect}</span>`;
                    });
                    tagsHtml += `<span class="prod-pill">${f.product}</span>`;
                    
                    feedHtml += `
                        <div class="review-card">
                            <div class="rc-top">
                                <div class="rc-sentence">${f.text}</div>
                            </div>
                            <div class="rc-tags">${tagsHtml}</div>
                        </div>
                    `;
                });
                feedHtml += `</div>`;

                // ── Build pagination HTML ──
                if (totalPages > 1) {
                    let pages = [];
                    if (totalPages <= 7) {
                        for (let i = 1; i <= totalPages; i++) pages.push(i);
                    } else {
                        pages.push(1);
                        if (window.currentPage > 3) pages.push('...');
                        let lo = Math.max(2, window.currentPage - 1);
                        let hi = Math.min(totalPages - 1, window.currentPage + 1);
                        for (let i = lo; i <= hi; i++) pages.push(i);
                        if (window.currentPage < totalPages - 2) pages.push('...');
                        pages.push(totalPages);
                    }
                    let btnHtml = pages.map(p =>
                        p === '...'
                        ? `<span style="padding:5px 4px;font-size:11px;color:var(--text-muted)">...</span>`
                        : `<button class="page-btn ${p === window.currentPage ? 'active' : ''}" data-page="${p}">${p}</button>`
                    ).join('');
                    feedHtml += `
                        <div class="pagination">
                            <span class="page-info">Trang ${window.currentPage} / ${totalPages}</span>
                            <div class="page-btns">
                                <button class="page-btn" data-page="${window.currentPage - 1}" ${window.currentPage === 1 ? 'disabled' : ''}>←</button>
                                ${btnHtml}
                                <button class="page-btn" data-page="${window.currentPage + 1}" ${window.currentPage === totalPages ? 'disabled' : ''}>→</button>
                            </div>
                        </div>
                    `;
                }

                feedCol.innerHTML = feedHtml;

                // Gắn sự kiện click pagination
                feedCol.querySelectorAll('.page-btn[data-page]').forEach(btn => {
                    btn.addEventListener('click', function() {
                        if (this.disabled) return;
                        let pg = parseInt(this.getAttribute('data-page'));
                        if (!pg || pg < 1 || pg > totalPages) return;
                        window.currentPage = pg;
                        window.renderFeedPage();
                        feedCol.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                });

                updateChartPanel(filteredFeed);
            };
            
            function updateChartPanel(filteredData) {
                const chartPanel = document.querySelector('.chart-panel');
                if(!chartPanel) return;
                
                let localAspCounts = {};
                let localPosCount = 0;
                let localNegCount = 0;
                
                filteredData.forEach(f => {
                    f.tags.forEach(t => {
                        if (window.dashboardFilter.aspect !== 'Tất cả aspect' && t.aspect !== window.dashboardFilter.aspect) return;
                        
                        if (!localAspCounts[t.aspect]) localAspCounts[t.aspect] = { total: 0, pos: 0, neg: 0 };
                        localAspCounts[t.aspect].total++;
                        if (t.polarity === 'pos') { localAspCounts[t.aspect].pos++; localPosCount++; }
                        else if (t.polarity === 'neg') { localAspCounts[t.aspect].neg++; localNegCount++; }
                    });
                });
                
                let sortedAsps = Object.keys(localAspCounts).map(k => ({
                    name: k,
                    total: localAspCounts[k].total,
                    pos: localAspCounts[k].pos,
                    neg: localAspCounts[k].neg
                })).sort((a,b) => b.total - a.total).slice(0, 10);
                
                let maxVal = sortedAsps.length > 0 ? sortedAsps[0].total : 1;
                
                let aspectBars = '<div><div class="cp-title">Aspect nhắc đến nhiều nhất</div><div>';
                if (sortedAsps.length === 0) aspectBars += '<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">Không có dữ liệu phù hợp</div>';
                
                sortedAsps.forEach(a => {
                    let width = (a.total / maxVal * 100);
                    let safeName = a.name.replace(/"/g, '&quot;').replace(/</g, '&lt;');
                    aspectBars += `
                        <div class="asp-bar-row">
                            <div class="asp-bar-name" title="${safeName}">${safeName}</div>
                            <div class="asp-bar-track">
                                <div class="asp-bar-fill" style="width:${width}%;background:var(--accent-mid)"></div>
                            </div>
                            <div class="asp-bar-val">${a.total}</div>
                        </div>
                    `;
                });
                aspectBars += '</div></div>';
                
                let totalPol = localPosCount + localNegCount;
                let pRate = totalPol > 0 ? Math.round((localPosCount/totalPol)*100) : 0;
                let nRate = totalPol > 0 ? Math.round((localNegCount/totalPol)*100) : 0;
                
                let sentimentHtml = `
                    <div>
                        <div class="cp-title">Sentiment tổng quan</div>
                        <div style="display:flex; justify-content:space-between; margin-top:8px;">
                            <span style="font-size:10px; font-weight:600; color:var(--pos)">Tích cực (${pRate}%)</span>
                            <span style="font-size:10px; font-weight:600; color:var(--neg)">Tiêu cực (${nRate}%)</span>
                        </div>
                        <div class="sentiment-stack">
                            <div style="width:${pRate}%;background:var(--pos)"></div>
                            <div style="width:${nRate}%;background:var(--neg)"></div>
                        </div>
                        <div class="sentiment-labels">
                            <span style="color:var(--pos)">${pRate}%</span>
                            <span style="color:var(--neg)">${nRate}%</span>
                        </div>
                    </div>
                `;
                
                let allAsps = Object.keys(localAspCounts).map(k => ({
                    name: k,
                    total: localAspCounts[k].total,
                    pos: localAspCounts[k].pos,
                    neg: localAspCounts[k].neg,
                    neg_rate: localAspCounts[k].total > 0 ? Math.round((localAspCounts[k].neg/localAspCounts[k].total)*100) : 0
                }));
                
                let alerts = allAsps.filter(a => a.neg > 0)
                                    .sort((a, b) => b.neg - a.neg)
                                    .slice(0, 5);
                
                let alertsHtml = `<div><div class="cp-title">Cần cải thiện ngay</div><div style="display:flex;flex-direction:column;gap:8px">`;
                if(alerts.length === 0) alertsHtml += '<div style="font-size:11px;color:#999">Không có dữ liệu phù hợp</div>';
                alerts.forEach(a => {
                    alertsHtml += `
                        <div class="alert-item">
                            <div class="alert-icon" style="background:var(--neg-bg);font-size:12px">⚡</div>
                            <div class="alert-text-wrap">
                                <div class="alert-title">${a.name}</div>
                                <div class="alert-desc">${a.neg_rate}% negative rate</div>
                            </div>
                        </div>
                    `;
                });
                alertsHtml += `</div></div>`;
                
                let localProdCounts = {};
                filteredData.forEach(f => {
                    if (!localProdCounts[f.product]) localProdCounts[f.product] = { total: 0, pos: 0 };
                    f.tags.forEach(t => {
                        if (window.dashboardFilter.aspect !== 'Tất cả aspect' && t.aspect !== window.dashboardFilter.aspect) return;
                        
                        localProdCounts[f.product].total++;
                        if (t.polarity === 'pos') localProdCounts[f.product].pos++;
                    });
                });
                
                let bestProds = Object.keys(localProdCounts).map(k => {
                    let tot = localProdCounts[k].total;
                    return { name: k, total: tot, pos_rate: tot > 0 ? Math.round((localProdCounts[k].pos/tot)*100) : 0 };
                }).filter(p => p.total > 0).sort((a,b) => b.pos_rate - a.pos_rate).slice(0, 3);
                
                let bestProdsHtml = `<div><div class="cp-title">Sản phẩm tốt nhất</div><div style="display:flex;flex-direction:column;gap:8px">`;
                if(bestProds.length === 0) bestProdsHtml += '<div style="font-size:11px;color:#999">Không có dữ liệu phù hợp</div>';
                bestProds.forEach((bp, idx) => {
                    bestProdsHtml += `
                        <div style="display:flex;align-items:center;gap:6px">
                            <span style="font-size:11px;color:var(--text-muted);width:14px;text-align:center;font-family:'DM Mono',monospace">${idx + 1}</span>
                            <span style="font-size:11px;color:var(--text-secondary);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${bp.name}</span>
                            <span style="font-size:11px;font-weight:500;color:var(--pos);font-family:'DM Mono',monospace">${bp.pos_rate}%</span>
                        </div>
                    `;
                });
                bestProdsHtml += `</div></div>`;
                
                chartPanel.innerHTML = aspectBars + '<div class="cp-divider"></div>' + sentimentHtml + '<div class="cp-divider"></div>' + alertsHtml + '<div class="cp-divider"></div>' + bestProdsHtml;
                if(typeof syncHeights === 'function') syncHeights();
            }

            // Lần render đầu tiên
            window.renderSidebar();
            window.renderFeedList();
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        renderDashboard();
        syncHeights();
        renderUploadHistory();
        initLiveInference();
        initUploadActions();
        
        // Nếu Streamlit đã chạy model và có kết quả → tự động hiển thị
        if (DATA.inferResult !== null && DATA.inferResult !== undefined && DATA.inferText) {
            const textarea = document.querySelector('#content3 textarea');
            const resultContainer = document.querySelector('#inference-result');
            const runBtn = document.querySelector('#content3 .run-btn');
            if (textarea) textarea.value = DATA.inferText;
            if (resultContainer && runBtn) {
                renderInferResult(DATA.inferResult, resultContainer, runBtn);
                // Chuyển sang tab 3 tự động
                const t3 = document.getElementById('t3');
                if (t3) t3.checked = true;
            }
        }
    });
    renderDashboard();
    setTimeout(syncHeights, 100);
    renderUploadHistory();

    // Nếu backend gửi kèm openTab (VD sau khi click "Xem chi tiết") → tick radio tương ứng
    if (DATA.openTab) {
        const tRadio = document.getElementById('t' + DATA.openTab);
        if (tRadio) tRadio.checked = true;
    }
    
    function renderUploadHistory() {
        if(DATA.uploadHistory && DATA.uploadHistory.length > 0) {
            const tbody = document.querySelector('#content4 table tbody');
            if(tbody) {
                let historyHtml = '';
                [...DATA.uploadHistory].reverse().forEach(file => {
                    // Escape hash để tránh XSS (dù hash là md5 nên không thực sự nguy hiểm)
                    const safeHash = (file.hash || '').replace(/[^a-zA-Z0-9_-]/g, '');
                    const action = safeHash
                        ? `<a href="#" data-hash="${safeHash}" onclick="return loadHistoryFile(this)"
                             style="color:var(--accent-mid); text-decoration:none; font-weight:500;">Xem chi tiết →</a>`
                        : `<span style="color:var(--text-muted);">—</span>`;
                    historyHtml += `
                      <tr style="border-bottom: 1px solid var(--border);">
                        <td style="padding: 12px 10px; font-weight: 500;">${file.name}</td>
                        <td style="padding: 12px 10px; color:var(--text-secondary);">${file.date}</td>
                        <td style="padding: 12px 10px; font-family:'DM Mono',monospace; font-size:11px;">${file.rows.toLocaleString()}</td>
                        <td style="padding: 12px 10px;"><span class="asp-pill pos" style="background:var(--pos-bg); color:var(--pos);">Hoàn thành</span></td>
                        <td style="padding: 12px 10px;">${action}</td>
                      </tr>
                    `;
                });
                tbody.innerHTML = historyHtml;
            }
        }
    }

    // Click "Xem chi tiết" → chuyển tab Phân tích dữ liệu + báo backend load file tương ứng.
    // Backend sẽ đọc cache_data/<hash>.csv, thay analyzed_df, rerun. Dashboard tự re-render.
    window.loadHistoryFile = function(el) {
        const hash = el.getAttribute('data-hash');
        if (!hash) return false;
        // Switch tab 2 ngay để feedback tức thì (Streamlit rerun mất ~1s)
        const t2 = document.getElementById('t2');
        if (t2) t2.checked = true;
        // Báo backend Python nạp file cụ thể
        if (typeof sendToStreamlit === 'function') {
            sendToStreamlit("LOAD_HISTORY:" + hash);
        }
        return false;   // huỷ mặc định href="#" (không nhảy lên đầu trang)
    };
    
    // ── HELPER: render kết quả inference vào DOM ──────────────────────
    function renderInferResult(extracted, resultContainer, runBtn) {
        runBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 12 12" fill="none" style="margin-right:6px;">
              <polygon points="2,1 11,6 2,11" fill="currentColor" />
            </svg>
            Chạy `;
        runBtn.style.opacity = '1';

        let resHtml = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <span style="font-weight:600; font-size:12px; color:var(--text-secondary);">KẾT QUẢ TRÍCH XUẤT TỪ MÔ HÌNH:</span>
              <span class="asp-pill pos" style="background:var(--accent); color:#fff; border:none;">Hoàn thành</span>
            </div>`;

        if (!extracted || extracted.length === 0) {
            resHtml += `<div style="text-align:center; padding:20px; color:var(--text-muted);">Không tìm thấy khía cạnh nào trong câu này.</div>`;
        } else if (extracted[0] && extracted[0].error) {
            resHtml += `<div style="padding:14px; background:#FEE2E2; border-radius:8px; color:#991B1B;">
                ⚠ Lỗi mô hình: ${extracted[0].error}</div>`;
        } else {
            extracted.forEach(item => {
                const polarity = item['Cảm xúc (Polarity)'] || '';
                const aspect   = item['Khía cạnh (Aspect)']  || '';
                const isPos = polarity.includes('Tích cực');
                const isNeg = polarity.includes('Tiêu cực');
                const polColor = isPos ? 'var(--pos)' : (isNeg ? 'var(--neg)' : '#6b7280');
                const polBg    = isPos ? 'var(--pos-bg)' : (isNeg ? 'var(--neg-bg)' : '#f3f4f6');
                resHtml += `
                    <div style="display:flex; gap:12px; margin-bottom:12px;">
                      <div style="flex:1; background:var(--surface2); padding:16px; border-radius:var(--radius-sm); text-align:center;">
                        <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase; margin-bottom:6px;">Khía cạnh (Aspect)</div>
                        <div style="font-weight:600; color:var(--accent); font-size:15px;">${aspect}</div>
                      </div>
                      <div style="flex:1; background:${polBg}; padding:16px; border-radius:var(--radius-sm); text-align:center;">
                        <div style="font-size:10px; color:${polColor}; text-transform:uppercase; margin-bottom:6px;">Cảm xúc (Polarity)</div>
                        <div style="font-weight:600; color:${polColor}; font-size:15px;">${polarity}</div>
                      </div>
                    </div>`;
            });
        }
        resultContainer.innerHTML = resHtml;
        resultContainer.style.display = 'block';
    }

    function initLiveInference() {
        const runBtn = document.querySelector('#content3 .run-btn');
        const textarea = document.querySelector('#content3 textarea');
        const resultContainer = document.querySelector('#inference-result');
        
        if(runBtn && textarea && resultContainer) {
            runBtn.addEventListener('click', async function() {
                const text = textarea.value.trim();
                if(!text) return;
                
                runBtn.innerHTML = 'Đang phân tích...';
                runBtn.style.opacity = '0.7';
                
                // ── GIẢI PHÁP 2 CHIỀU: NATIVE STREAMLIT COMPONENT ──────────────────────────
                // Gọi thẳng hàm sendToStreamlit() đã được tiêm vào cuối file HTML
                // để đẩy text ngược về biến Python mà không vi phạm Sandbox Security.
                
                if (DATA.inferResult !== undefined && DATA.inferResult !== null && DATA.inferText === text) {
                    renderInferResult(DATA.inferResult, resultContainer, runBtn);
                } else {
                    runBtn.innerHTML = '⏳ Đang chạy mô hình...';
                    runBtn.style.opacity = '0.7';
                    resultContainer.innerHTML = `
                        <div style="padding:16px; background:#EFF6FF; border-radius:8px; color:#1E40AF; font-size:13px; text-align:center;">
                          <div style="font-size:22px; margin-bottom:8px;">⚙️</div>
                          <strong>Đang gửi đến mô hình AI...</strong><br/>
                          <span style="font-size:11px; opacity:.7; margin-top:4px; display:block;">Xin vui lòng chờ trong giây lát</span>
                        </div>`;
                    resultContainer.style.display = 'block';
                    
                    // Gửi text thẳng về Python!
                    if (typeof sendToStreamlit === 'function') {
                        sendToStreamlit(text);
                    } else {
                        console.error("Hàm sendToStreamlit chưa được khởi tạo!");
                    }
                }
            });
        }
    }
    
    function initUploadActions() {
        const uploadZone = document.querySelector('#upload-zone');
        const uploadBtn = document.querySelector('.upload-btn');
        
        const handleUploadClick = () => {
            if (typeof sendToStreamlit === 'function') {
                sendToStreamlit("RESET_UPLOAD");
            }
        };
        
        if(uploadZone) uploadZone.addEventListener('click', handleUploadClick);
        if(uploadBtn) uploadBtn.addEventListener('click', handleUploadClick);
    }
    
    // Đã chuyển vào DOMContentLoaded ở trên


    function syncHeights() {
        const cp = document.querySelector('.chart-panel');
        const fcw = document.querySelector('.feed-col-wrap');
        if(cp && fcw) {
            fcw.style.maxHeight = cp.scrollHeight + 'px';
            fcw.style.overflowY = 'auto';
        }
    }
    
    // CSS bổ sung — body scroll tự nhiên theo chiều cao nội dung (chart-panel quyết định)
    const scrollStyle = document.createElement('style');
    scrollStyle.innerHTML = `
        body, html { overflow-y: auto !important; height: auto !important; }
        .layout { height: auto !important; min-height: 0; padding-top: var(--topbar-h); }
        #content2 { height: auto !important; overflow: visible !important; }
        .sidebar { overflow-y: auto; max-height: calc(100vh - var(--topbar-h)); position: sticky; top: var(--topbar-h); align-self: start; }
        .main { overflow: visible !important; height: auto !important; }
        .content-area { align-items: start; overflow: visible !important; }
        .feed-col-wrap { overflow: visible !important; }
        .feed-col { overflow: visible !important; max-height: none !important; }
        .chart-panel { position: sticky; top: var(--topbar-h); align-self: start; overflow: visible !important; max-height: none; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ddd; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #bbb; }
    `;
    document.head.appendChild(scrollStyle);
</script>
<!-- DASH_INJECT_END -->