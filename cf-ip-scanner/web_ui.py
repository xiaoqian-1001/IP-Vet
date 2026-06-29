WEB_UI_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CF 三方 IP</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;min-height:100vh}
::selection{background:#58a6ff;color:#fff}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:#0d1117}
::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#484f58}

.container{max-width:720px;margin:0 auto;padding:24px 20px}

.header{padding:16px 0;border-bottom:1px solid #21262d;margin-bottom:24px}
.header h1{font-size:22px;font-weight:600;color:#f0f6fc;display:flex;align-items:center;gap:10px}
.header h1 .dot{width:10px;height:10px;background:#238636;border-radius:50%;display:inline-block;box-shadow:0 0 8px #238636}
.header .subtitle{font-size:12px;color:#8b949e;margin-top:4px}

.card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:20px 24px;margin-bottom:20px}
.card-title{font-size:15px;font-weight:600;color:#f0f6fc;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid #21262d}
.card-title::before{content:"";display:inline-block;width:4px;height:16px;background:#58a6ff;border-radius:2px;margin-right:8px;vertical-align:-2px}

.form-row{display:flex;align-items:center;margin-bottom:14px;gap:12px}
.form-label{width:100px;flex-shrink:0;font-size:13px;color:#8b949e;text-align:right}
.form-control{flex:1;display:flex;align-items:center;gap:8px}
.form-control select,.form-control input{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:7px 12px;border-radius:6px;font-size:13px;outline:none;transition:border-color .2s;width:100%}
.form-control select:focus,.form-control input:focus{border-color:#58a6ff;box-shadow:0 0 0 3px rgba(88,166,255,0.15)}
.form-control select{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%238b949e' d='M6 8.825L1.175 4 2.238 2.938 6 6.7l3.763-3.762L10.825 4z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center;padding-right:30px;cursor:pointer}
.form-control select option{background:#161b22;color:#c9d1d9}
.form-control .unit{font-size:12px;color:#8b949e;white-space:nowrap;flex-shrink:0}

.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:6px 14px;border-radius:6px;font-size:13px;font-weight:500;cursor:pointer;border:1px solid transparent;transition:all .2s;white-space:nowrap}
.btn-sm{padding:5px 10px;font-size:12px}
.btn-secondary{background:#21262d;color:#c9d1d9;border-color:#30363d}
.btn-secondary:hover{background:#30363d}
.btn-primary{width:100%;padding:12px 24px;background:linear-gradient(135deg,#1f6feb,#388bfd);color:#fff;border:none;font-size:15px;font-weight:600;border-radius:8px;cursor:pointer;transition:all .2s;margin-top:4px}
.btn-primary:hover{background:linear-gradient(135deg,#388bfd,#58a6ff);transform:translateY(-1px);box-shadow:0 4px 16px rgba(31,111,235,0.3)}
.btn-primary:active{transform:translateY(0)}
.btn-primary:disabled{opacity:0.5;cursor:not-allowed;pointer-events:none}

.progress-card{display:none}
.progress-card.active{display:block}
.progress-bar-wrap{height:6px;background:#21262d;border-radius:3px;overflow:hidden;margin:12px 0}
.progress-bar{height:100%;background:linear-gradient(90deg,#1f6feb,#58a6ff);border-radius:3px;transition:width .3s;width:0}
.progress-info{display:flex;justify-content:space-between;font-size:12px;color:#8b949e}
.progress-status{font-size:13px;color:#c9d1d9;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.spinner{width:14px;height:14px;border:2px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin .8s linear infinite;flex-shrink:0}
@keyframes spin{to{transform:rotate(360deg)}}

.result-table{width:100%;border-collapse:collapse;display:none}
.result-table.active{display:table}
.result-table th{font-size:12px;color:#8b949e;font-weight:500;text-align:left;padding:8px 12px;border-bottom:1px solid #21262d;text-transform:uppercase;letter-spacing:.5px}
.result-table td{font-size:13px;color:#c9d1d9;padding:10px 12px;border-bottom:1px solid #21262d}
.result-table tr:hover td{background:rgba(88,166,255,0.05)}
.result-table .ip{font-family:"SF Mono",Consolas,monospace;color:#58a6ff;font-size:12px}
.result-table .bw{color:#3fb950;font-weight:600}
.result-table .lat{color:#d29922}
.result-table .dc{font-size:11px;color:#8b949e;background:#21262d;padding:2px 6px;border-radius:3px}
.rank{width:28px;height:28px;background:#21262d;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:#8b949e}
.rank.top{background:rgba(31,111,235,0.15);color:#58a6ff}

.status-badge{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:500}
.status-badge.success{background:rgba(35,134,54,0.15);color:#3fb950}
.status-badge.fail{background:rgba(218,54,51,0.15);color:#f85149}

.empty-state{text-align:center;padding:40px 20px;color:#484f58;display:none}
.empty-state.active{display:block}
.empty-icon{font-size:40px;margin-bottom:12px;opacity:0.4}

.footer{text-align:center;padding:20px;color:#484f58;font-size:11px}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1><span class="dot"></span>CF 三方 IP</h1>
    <div class="subtitle">第三方反代 IP 严选工具 | 本地 http://127.0.0.1:29999</div>
  </div>

  <div class="card">
    <div class="card-title">扫描设置</div>
    <div class="form-row">
      <span class="form-label">IP 版本</span>
      <div class="form-control">
        <select id="ipVersion">
          <option value="ipv4">IPv4</option>
          <option value="ipv6">IPv6</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <span class="form-label">TLS</span>
      <div class="form-control">
        <select id="tls">
          <option value="true">开启</option>
          <option value="false">关闭</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <span class="form-label">数据中心</span>
      <div class="form-control">
        <select id="datacenter">
          <option value="all">全部</option>
        </select>
        <button class="btn btn-secondary btn-sm" id="btnRefreshDC" title="刷新数据中心列表">刷新</button>
      </div>
    </div>
    <div class="form-row">
      <span class="form-label">端口</span>
      <div class="form-control">
        <select id="portMode">
          <option value="default">列表端口</option>
          <option value="custom">指定端口</option>
        </select>
        <input type="number" id="customPort" placeholder="443" style="display:none;width:100px;flex-shrink:0" min="1" max="65535" value="443">
      </div>
    </div>
    <div class="form-row">
      <span class="form-label">期望带宽</span>
      <div class="form-control">
        <input type="number" id="minBandwidth" value="50" min="0" max="10000">
        <span class="unit">Mbps</span>
      </div>
    </div>
    <div class="form-row">
      <span class="form-label">结果数</span>
      <div class="form-control">
        <select id="resultCount">
          <option value="3">3 个</option>
          <option value="5" selected>5 个</option>
          <option value="10">10 个</option>
          <option value="20">20 个</option>
          <option value="50">50 个</option>
        </select>
      </div>
    </div>
    <button class="btn-primary" id="btnScan">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      开始扫描
    </button>
  </div>

  <div class="card progress-card" id="progressCard">
    <div class="card-title">扫描进度</div>
    <div class="progress-status" id="progressStatus">
      <span class="spinner"></span>
      <span id="progressText">准备中...</span>
    </div>
    <div class="progress-bar-wrap">
      <div class="progress-bar" id="progressBar"></div>
    </div>
    <div class="progress-info">
      <span id="progressDetail">0 / 0</span>
      <span id="progressSpeed">--</span>
    </div>
  </div>

  <div class="card" id="resultCard" style="display:none">
    <div class="card-title">扫描结果 <span id="resultSummary" style="font-size:12px;color:#8b949e;font-weight:400"></span></div>
    <table class="result-table active" id="resultTable">
      <thead>
        <tr><th>#</th><th>IP 地址</th><th>端口</th><th>带宽</th><th>延迟</th><th>数据中心</th></tr>
      </thead>
      <tbody id="resultBody"></tbody>
    </table>
    <div class="empty-state active" id="emptyState">
      <div class="empty-icon">--</div>
      <div>暂无扫描结果</div>
    </div>
  </div>

  <div class="footer">CF 三方 IP &copy; 本地严选工具 | 127.0.0.1:29999</div>
</div>

<script>
(function(){
  var ws = null;
  var scanning = false;

  var progressCard = document.getElementById("progressCard");
  var progressBar = document.getElementById("progressBar");
  var progressText = document.getElementById("progressText");
  var progressDetail = document.getElementById("progressDetail");
  var progressSpeed = document.getElementById("progressSpeed");
  var progressStatus = document.getElementById("progressStatus");
  var resultCard = document.getElementById("resultCard");
  var resultTable = document.getElementById("resultTable");
  var resultBody = document.getElementById("resultBody");
  var resultSummary = document.getElementById("resultSummary");
  var emptyState = document.getElementById("emptyState");
  var btnScan = document.getElementById("btnScan");
  var btnRefreshDC = document.getElementById("btnRefreshDC");
  var portMode = document.getElementById("portMode");
  var customPort = document.getElementById("customPort");
  var dcSelect = document.getElementById("datacenter");

  var startTime = 0;

  function showProgress(show) {
    progressCard.className = show ? "card progress-card active" : "card progress-card";
  }

  function setProgress(phase, data) {
    showProgress(true);

    if (phase === "fetching" || phase === "parsing") {
      progressText.textContent = data;
      progressBar.style.width = "0%";
      progressDetail.textContent = "--";
      progressSpeed.textContent = "--";
    } else if (phase === "status") {
      progressText.textContent = data;
    } else if (phase === "error") {
      progressText.textContent = data;
      progressStatus.innerHTML = '<span style="color:#f85149">&#10007;</span><span>' + data + '</span>';
      scanning = false;
      btnScan.disabled = false;
      btnScan.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>开始扫描';
    } else if (phase === "scanning") {
      progressText.textContent = data;
      progressBar.style.width = "0%";
      progressDetail.textContent = "已收集 0 / 0";
      progressSpeed.textContent = "--";
      startTime = Date.now();
    } else if (phase === "progress") {
      var pct = data.pool_size > 0 ? Math.round(data.scanned / data.pool_size * 100) : 0;
      progressBar.style.width = Math.min(pct, 100) + "%";
      progressText.textContent = "已扫描 " + (data.scanned || 0) + " 个, 合格 " + (data.found || 0) + " 个";
      progressDetail.textContent = "已收集 " + (data.found || 0) + " / " + (data.target || 0);
      progressSpeed.textContent = "候选池 " + (data.pool_size || 0) + " 个";
    } else if (phase === "found") {
      progressText.textContent = data.ip + ":" + data.port + "  带宽 " + (data.bandwidth || 0).toFixed(1) + " Mbps";
      progressDetail.textContent = "已收集 " + (data.found || 0) + " / " + (data.target || 0);
      progressSpeed.textContent = "DC: " + (data.datacenter || "UNK") + " | 已扫描 " + (data.scanned || 0);
      var pct = data.pool_size > 0 ? Math.round(data.scanned / data.pool_size * 100) : 0;
      progressBar.style.width = Math.min(pct, 100) + "%";
    } else if (phase === "complete") {
      var elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      progressBar.style.width = "100%";
      progressText.textContent = "扫描完成";
      progressStatus.innerHTML = '<span style="color:#3fb950">&#10003;</span><span>扫描完成 (' + elapsed + 's)</span>';
      progressDetail.textContent = "共扫描 " + (data.scanned || 0) + " 个目标, 收集 " + ((data.results || []).length) + " 个优质 IP";
      progressSpeed.textContent = "";

      scanning = false;
      btnScan.disabled = false;
      btnScan.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>开始扫描';

      showResults(data.results || []);
    }
  }

  function showResults(results) {
    resultCard.style.display = "block";
    resultBody.innerHTML = "";

    if (results.length === 0) {
      resultTable.classList.remove("active");
      emptyState.classList.add("active");
      resultSummary.textContent = "";
      return;
    }

    resultTable.classList.add("active");
    emptyState.classList.remove("active");
    resultSummary.textContent = "(" + results.length + " 个优质 IP)";

    results.forEach(function(r, i) {
      var rankClass = i < 3 ? " top" : "";
      var row = document.createElement("tr");
      row.innerHTML =
        '<td><span class="rank' + rankClass + '">' + (i + 1) + '</span></td>' +
        '<td><span class="ip">' + (r.ip || "-") + '</span></td>' +
        '<td>' + (r.port || "-") + '</td>' +
        '<td><span class="bw">' + (r.bandwidth || 0).toFixed(1) + ' Mbps</span></td>' +
        '<td><span class="lat">' + (r.latency || 0).toFixed(1) + ' ms</span></td>' +
        '<td><span class="dc">' + (r.datacenter || "UNK") + '</span></td>';
      resultBody.appendChild(row);
    });
  }

  function connectWS() {
    var proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(proto + "//" + window.location.host + "/ws");

    ws.onopen = function() {
      console.log("[WS] Connected");
    };

    ws.onmessage = function(e) {
      try {
        var msg = JSON.parse(e.data);
        setProgress(msg.type, msg.data);
      } catch(err) {
        console.error("[WS] Parse error:", err);
      }
    };

    ws.onclose = function() {
      console.log("[WS] Disconnected");
      ws = null;
    };

    ws.onerror = function(err) {
      console.error("[WS] Error:", err);
    };
  }

  function startScan() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      connectWS();
      setTimeout(function(){ startScan(); }, 500);
      return;
    }

    scanning = true;
    btnScan.disabled = true;
    btnScan.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px"></span>扫描中...';
    resultCard.style.display = "none";
    resultBody.innerHTML = "";
    resultSummary.textContent = "";
    progressBar.style.width = "0%";

    var config = {
      ipVersion: document.getElementById("ipVersion").value,
      tls: document.getElementById("tls").value === "true",
      datacenter: dcSelect.value,
      minBandwidth: parseFloat(document.getElementById("minBandwidth").value) || 50,
      resultCount: parseInt(document.getElementById("resultCount").value) || 5,
      portMode: portMode.value,
    };

    if (portMode.value === "custom") {
      config.customPort = parseInt(customPort.value) || 443;
    }

    ws.send(JSON.stringify({type: "start_scan", config: config}));
  }

  function stopScan() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({type: "stop_scan"}));
    }
    scanning = false;
    btnScan.disabled = false;
    btnScan.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>开始扫描';
  }

  btnScan.addEventListener("click", function() {
    if (scanning) {
      stopScan();
    } else {
      startScan();
    }
  });

  portMode.addEventListener("change", function() {
    customPort.style.display = portMode.value === "custom" ? "inline-block" : "none";
  });

  function loadDatacenters() {
    fetch("/api/datacenters")
      .then(function(r){ return r.json(); })
      .then(function(data){
        dcSelect.innerHTML = '<option value="all">全部</option>';
        (data.datacenters || []).forEach(function(dc){
          var opt = document.createElement("option");
          opt.value = dc;
          opt.textContent = dc;
          dcSelect.appendChild(opt);
        });
      })
      .catch(function(){});
  }

  btnRefreshDC.addEventListener("click", function() {
    btnRefreshDC.disabled = true;
    btnRefreshDC.textContent = "刷新中...";
    loadDatacenters();
    setTimeout(function(){
      btnRefreshDC.textContent = "刷新";
      btnRefreshDC.disabled = false;
    }, 3000);
  });

  loadDatacenters();
  connectWS();
})();
</script>
</body>
</html>"""
