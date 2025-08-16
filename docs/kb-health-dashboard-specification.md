# KB Health Dashboard Specification

## Overview

Browser-based dashboard for monitoring knowledge base query engine quality, performance, and usage patterns with real-time data collection and async processing to maintain MCP server performance.

## Success Criteria & KPIs

### Primary KPIs (Must Meet)

#### 1. User Satisfaction Rate > 80%
- **Metric**: Percentage of 4+ star user ratings
- **Collection**: User feedback after query responses
- **Target**: 80% of rated queries receive 4-5 stars
- **Alert Threshold**: < 75% satisfaction rate

#### 2. Query Success Rate > 90%
- **Metric**: Percentage of queries returning meaningful results
- **Collection**: Automated based on result count and similarity scores
- **Target**: 90% of queries return >0 results with similarity > 0.3
- **Alert Threshold**: < 85% success rate

#### 3. Average Response Time < 2 seconds
- **Metric**: End-to-end query processing time
- **Collection**: Measured from query submission to result delivery
- **Target**: Mean response time under 2000ms
- **Alert Threshold**: > 3000ms average over 1-hour window

#### 4. Source Diversity Index > 0.7
- **Metric**: Variety of documents referenced in query results
- **Calculation**: `unique_documents / total_documents_in_kb`
- **Target**: Results draw from at least 70% of available source diversity
- **Alert Threshold**: < 0.5 diversity index

### Secondary Metrics (Nice to Have)

#### Performance Metrics
- **P95 Response Time**: < 5 seconds
- **Query Throughput**: Queries per minute capacity
- **Error Rate**: < 1% of queries result in system errors
- **Memory Usage**: Stable memory consumption during query processing

#### Content Quality Metrics
- **Answer Completeness**: Estimated coverage of query intent
- **Chunk Coherence**: Overlap and relevance between returned chunks
- **Recency Score**: Average age of documents in results
- **Knowledge Coverage**: Percentage of knowledge base actively used

#### Usage Analytics
- **Query Pattern Trends**: Most common query types and topics
- **Peak Usage Times**: Traffic patterns and load distribution
- **Knowledge Gap Identification**: Queries with consistently poor results
- **Content Utilization**: Which documents are most/least accessed

## Implementation Details

### Phase 1: Core Analytics Infrastructure

#### 1.1 Analytics Data Model

```python
@dataclass
class QueryAnalytics:
    query_id: str
    query_text: str
    timestamp: datetime
    result_count: int
    response_time: float
    avg_similarity_score: float
    max_similarity_score: float
    source_documents: List[str]
    chunk_positions: List[int]
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class DocumentAnalytics:
    document_id: str
    filename: str
    access_count: int
    last_accessed: datetime
    avg_relevance_score: float
    unique_queries_served: int

@dataclass
class SystemMetrics:
    timestamp: datetime
    active_queries: int
    memory_usage: float
    cpu_usage: float
    vector_db_latency: float
    embedding_service_latency: float
```

#### 1.2 Database Schema (SQLite)

```sql
-- Query analytics table
CREATE TABLE query_analytics (
    query_id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    result_count INTEGER,
    response_time REAL,
    avg_similarity_score REAL,
    max_similarity_score REAL,
    source_document_count INTEGER,
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    error_message TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_rating (user_rating),
    INDEX idx_response_time (response_time)
);

-- Document usage tracking
CREATE TABLE document_analytics (
    document_id TEXT,
    query_id TEXT,
    relevance_score REAL,
    chunk_position INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES query_analytics(query_id),
    INDEX idx_document_id (document_id),
    INDEX idx_timestamp (timestamp)
);

-- System performance metrics
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_name TEXT,
    metric_value REAL,
    INDEX idx_timestamp_metric (timestamp, metric_name)
);

-- User feedback details
CREATE TABLE user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id TEXT,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES query_analytics(query_id)
);
```

#### 1.3 Async Analytics Service

```python
# mcp_rag_playground/analytics/analytics_service.py
import asyncio
import sqlite3
from datetime import datetime
from typing import List, Optional
from dataclasses import asdict

class AnalyticsService:
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.query_queue = asyncio.Queue()
        self._initialize_db()
        
    async def log_query_async(self, analytics: QueryAnalytics):
        """Non-blocking query logging"""
        await self.query_queue.put(analytics)
        
    async def log_user_feedback(self, query_id: str, rating: int, feedback: str = ""):
        """Log user feedback for query quality"""
        feedback_data = {
            'query_id': query_id,
            'rating': rating,
            'feedback_text': feedback,
            'timestamp': datetime.now()
        }
        await self.query_queue.put(('feedback', feedback_data))
        
    async def process_analytics_queue(self):
        """Background processor for analytics data"""
        while True:
            try:
                item = await self.query_queue.get()
                if isinstance(item, QueryAnalytics):
                    self._store_query_analytics(item)
                elif isinstance(item, tuple) and item[0] == 'feedback':
                    self._store_user_feedback(item[1])
                self.query_queue.task_done()
            except Exception as e:
                print(f"Analytics processing error: {e}")
                
    def calculate_kpis(self, time_window_hours: int = 24) -> dict:
        """Calculate primary KPIs for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User Satisfaction Rate
        cursor.execute("""
            SELECT AVG(CASE WHEN user_rating >= 4 THEN 1.0 ELSE 0.0 END) * 100
            FROM query_analytics 
            WHERE timestamp >= datetime('now', '-{} hours')
            AND user_rating IS NOT NULL
        """.format(time_window_hours))
        satisfaction_rate = cursor.fetchone()[0] or 0
        
        # Query Success Rate
        cursor.execute("""
            SELECT AVG(CASE WHEN result_count > 0 AND avg_similarity_score > 0.3 
                           THEN 1.0 ELSE 0.0 END) * 100
            FROM query_analytics 
            WHERE timestamp >= datetime('now', '-{} hours')
        """.format(time_window_hours))
        success_rate = cursor.fetchone()[0] or 0
        
        # Average Response Time
        cursor.execute("""
            SELECT AVG(response_time)
            FROM query_analytics 
            WHERE timestamp >= datetime('now', '-{} hours')
        """.format(time_window_hours))
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Source Diversity Index
        cursor.execute("""
            SELECT COUNT(DISTINCT document_id) as unique_docs,
                   (SELECT COUNT(*) FROM (
                       SELECT DISTINCT document_id FROM document_analytics
                   )) as total_docs
            FROM document_analytics da
            JOIN query_analytics qa ON da.query_id = qa.query_id
            WHERE qa.timestamp >= datetime('now', '-{} hours')
        """.format(time_window_hours))
        diversity_data = cursor.fetchone()
        diversity_index = (diversity_data[0] / diversity_data[1]) if diversity_data[1] > 0 else 0
        
        conn.close()
        
        return {
            'user_satisfaction_rate': round(satisfaction_rate, 2),
            'query_success_rate': round(success_rate, 2),
            'avg_response_time': round(avg_response_time, 3),
            'source_diversity_index': round(diversity_index, 3),
            'timestamp': datetime.now().isoformat()
        }
```

### Phase 2: MCP Tool Integration

#### 2.1 Enhanced MCP Tools with Analytics

```python
# Modify existing mcp_rag_playground/mcp/rag_server.py
from mcp_rag_playground.analytics.analytics_service import AnalyticsService
import uuid
import time

analytics_service = AnalyticsService()

@mcp.tool()
def search_knowledge_base_with_analytics(
    ctx: Context, 
    query: str, 
    limit: int = 10, 
    min_score: float = 0.7
) -> Dict[str, Any]:
    """Enhanced search with analytics tracking"""
    query_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Existing search logic
        results = rag_api.search(query, limit, min_score)
        response_time = time.time() - start_time
        
        # Collect analytics data
        analytics_data = QueryAnalytics(
            query_id=query_id,
            query_text=query,
            timestamp=datetime.now(),
            result_count=len(results),
            response_time=response_time,
            avg_similarity_score=sum(r.score for r in results) / len(results) if results else 0,
            max_similarity_score=max(r.score for r in results) if results else 0,
            source_documents=[r.document.filename for r in results],
            chunk_positions=[r.document.chunk_position for r in results]
        )
        
        # Async logging (non-blocking)
        asyncio.create_task(analytics_service.log_query_async(analytics_data))
        
        # Return results with query_id for feedback
        return {
            "query_id": query_id,
            "results": [{"document": r.document.dict(), "score": r.score} for r in results],
            "metadata": {
                "result_count": len(results),
                "response_time": response_time,
                "query_processed_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        # Log error analytics
        error_analytics = QueryAnalytics(
            query_id=query_id,
            query_text=query,
            timestamp=datetime.now(),
            result_count=0,
            response_time=time.time() - start_time,
            avg_similarity_score=0,
            max_similarity_score=0,
            source_documents=[],
            chunk_positions=[],
            error_message=str(e)
        )
        asyncio.create_task(analytics_service.log_query_async(error_analytics))
        raise

@mcp.tool()
def rate_query_response(ctx: Context, query_id: str, rating: int, feedback: str = "") -> Dict[str, Any]:
    """Allow users to rate query response quality"""
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5")
        
    asyncio.create_task(analytics_service.log_user_feedback(query_id, rating, feedback))
    
    return {
        "status": "success",
        "message": f"Feedback recorded for query {query_id}",
        "rating": rating
    }
```

### Phase 3: Dashboard Implementation

#### 3.1 FastAPI Dashboard Endpoints

```python
# mcp_rag_playground/api/dashboard.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, List
from datetime import datetime, timedelta

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Serve dashboard HTML interface"""
    with open("static/dashboard.html", "r") as f:
        return HTMLResponse(f.read())

@dashboard_router.get("/api/kpis")
async def get_kpis(hours: int = 24) -> Dict:
    """Get primary KPIs for dashboard"""
    return analytics_service.calculate_kpis(hours)

@dashboard_router.get("/api/query-trends")
async def get_query_trends(days: int = 7) -> Dict:
    """Get query volume and success trends"""
    conn = sqlite3.connect(analytics_service.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DATE(timestamp) as date,
               COUNT(*) as total_queries,
               AVG(CASE WHEN result_count > 0 THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
               AVG(response_time) as avg_response_time
        FROM query_analytics 
        WHERE timestamp >= datetime('now', '-{} days')
        GROUP BY DATE(timestamp)
        ORDER BY date
    """.format(days))
    
    results = cursor.fetchall()
    conn.close()
    
    return {
        "dates": [r[0] for r in results],
        "query_volumes": [r[1] for r in results],
        "success_rates": [round(r[2], 2) for r in results],
        "response_times": [round(r[3], 3) for r in results]
    }

@dashboard_router.get("/api/top-queries")
async def get_top_queries(limit: int = 10) -> List[Dict]:
    """Get most frequent queries and their performance"""
    conn = sqlite3.connect(analytics_service.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT query_text,
               COUNT(*) as frequency,
               AVG(result_count) as avg_results,
               AVG(user_rating) as avg_rating,
               AVG(response_time) as avg_response_time
        FROM query_analytics 
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY query_text
        ORDER BY frequency DESC
        LIMIT ?
    """, (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            "query": r[0],
            "frequency": r[1],
            "avg_results": round(r[2], 1),
            "avg_rating": round(r[3], 1) if r[3] else None,
            "avg_response_time": round(r[4], 3)
        }
        for r in results
    ]

@dashboard_router.get("/api/alerts")
async def get_alerts() -> List[Dict]:
    """Check for KPI violations and generate alerts"""
    kpis = analytics_service.calculate_kpis()
    alerts = []
    
    if kpis['user_satisfaction_rate'] < 75:
        alerts.append({
            "level": "warning",
            "message": f"User satisfaction below threshold: {kpis['user_satisfaction_rate']}%",
            "metric": "satisfaction_rate",
            "current_value": kpis['user_satisfaction_rate'],
            "threshold": 75
        })
        
    if kpis['query_success_rate'] < 85:
        alerts.append({
            "level": "critical",
            "message": f"Query success rate below threshold: {kpis['query_success_rate']}%",
            "metric": "success_rate", 
            "current_value": kpis['query_success_rate'],
            "threshold": 85
        })
        
    if kpis['avg_response_time'] > 3.0:
        alerts.append({
            "level": "warning",
            "message": f"Response time above threshold: {kpis['avg_response_time']}s",
            "metric": "response_time",
            "current_value": kpis['avg_response_time'],
            "threshold": 3.0
        })
        
    if kpis['source_diversity_index'] < 0.5:
        alerts.append({
            "level": "info",
            "message": f"Low source diversity: {kpis['source_diversity_index']}",
            "metric": "diversity_index",
            "current_value": kpis['source_diversity_index'],
            "threshold": 0.5
        })
    
    return alerts
```

#### 3.2 Dashboard HTML Interface

```html
<!-- static/dashboard.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KB Health Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .kpi-card { min-height: 120px; }
        .alert-badge { position: absolute; top: 10px; right: 10px; }
        .metric-good { color: #28a745; }
        .metric-warning { color: #ffc107; }
        .metric-critical { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <h1 class="my-4">Knowledge Base Health Dashboard</h1>
                
                <!-- Alerts Section -->
                <div id="alerts-container" class="mb-4"></div>
                
                <!-- Primary KPIs -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card kpi-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">User Satisfaction</h5>
                                <h2 id="satisfaction-rate" class="metric-good">--%</h2>
                                <small class="text-muted">Target: >80%</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card kpi-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Query Success</h5>
                                <h2 id="success-rate" class="metric-good">--%</h2>
                                <small class="text-muted">Target: >90%</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card kpi-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Avg Response Time</h5>
                                <h2 id="response-time" class="metric-good">--s</h2>
                                <small class="text-muted">Target: <2s</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card kpi-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Source Diversity</h5>
                                <h2 id="diversity-index" class="metric-good">--</h2>
                                <small class="text-muted">Target: >0.7</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Charts Row -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Query Trends (7 days)</h5>
                                <canvas id="query-trends-chart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Response Time Distribution</h5>
                                <canvas id="response-time-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Top Queries Table -->
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Top Queries (Last 7 Days)</h5>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Query</th>
                                        <th>Frequency</th>
                                        <th>Avg Results</th>
                                        <th>Avg Rating</th>
                                        <th>Avg Response Time</th>
                                    </tr>
                                </thead>
                                <tbody id="top-queries-table">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Dashboard JavaScript implementation
        class DashboardManager {
            constructor() {
                this.refreshInterval = 30000; // 30 seconds
                this.charts = {};
                this.init();
            }
            
            async init() {
                await this.loadKPIs();
                await this.loadQueryTrends();
                await this.loadTopQueries();
                await this.loadAlerts();
                
                // Auto-refresh
                setInterval(() => {
                    this.loadKPIs();
                    this.loadAlerts();
                }, this.refreshInterval);
            }
            
            async loadKPIs() {
                try {
                    const response = await fetch('/dashboard/api/kpis');
                    const kpis = await response.json();
                    
                    this.updateKPI('satisfaction-rate', kpis.user_satisfaction_rate, 80, '%');
                    this.updateKPI('success-rate', kpis.query_success_rate, 90, '%');
                    this.updateKPI('response-time', kpis.avg_response_time, 2, 's');
                    this.updateKPI('diversity-index', kpis.source_diversity_index, 0.7);
                } catch (error) {
                    console.error('Failed to load KPIs:', error);
                }
            }
            
            updateKPI(elementId, value, threshold, suffix = '') {
                const element = document.getElementById(elementId);
                const displayValue = suffix === '%' ? value.toFixed(1) : value.toFixed(2);
                element.textContent = displayValue + suffix;
                
                // Update color based on threshold
                element.className = this.getMetricClass(value, threshold, elementId);
            }
            
            getMetricClass(value, threshold, metricType) {
                if (metricType === 'response-time') {
                    // Lower is better for response time
                    return value <= threshold ? 'metric-good' : 
                           value <= threshold * 1.5 ? 'metric-warning' : 'metric-critical';
                } else {
                    // Higher is better for other metrics
                    return value >= threshold ? 'metric-good' :
                           value >= threshold * 0.8 ? 'metric-warning' : 'metric-critical';
                }
            }
            
            async loadQueryTrends() {
                try {
                    const response = await fetch('/dashboard/api/query-trends');
                    const trends = await response.json();
                    
                    const ctx = document.getElementById('query-trends-chart').getContext('2d');
                    
                    if (this.charts.queryTrends) {
                        this.charts.queryTrends.destroy();
                    }
                    
                    this.charts.queryTrends = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: trends.dates,
                            datasets: [{
                                label: 'Query Volume',
                                data: trends.query_volumes,
                                borderColor: 'rgb(75, 192, 192)',
                                yAxisID: 'y'
                            }, {
                                label: 'Success Rate (%)',
                                data: trends.success_rates,
                                borderColor: 'rgb(255, 99, 132)',
                                yAxisID: 'y1'
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    type: 'linear',
                                    display: true,
                                    position: 'left',
                                    title: {
                                        display: true,
                                        text: 'Query Volume'
                                    }
                                },
                                y1: {
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: {
                                        display: true,
                                        text: 'Success Rate (%)'
                                    },
                                    grid: {
                                        drawOnChartArea: false
                                    }
                                }
                            }
                        }
                    });
                } catch (error) {
                    console.error('Failed to load query trends:', error);
                }
            }
            
            async loadTopQueries() {
                try {
                    const response = await fetch('/dashboard/api/top-queries');
                    const queries = await response.json();
                    
                    const tbody = document.getElementById('top-queries-table');
                    tbody.innerHTML = queries.map(q => `
                        <tr>
                            <td>${q.query}</td>
                            <td><span class="badge bg-primary">${q.frequency}</span></td>
                            <td>${q.avg_results}</td>
                            <td>${q.avg_rating ? q.avg_rating + ' ⭐' : 'No ratings'}</td>
                            <td>${q.avg_response_time}s</td>
                        </tr>
                    `).join('');
                } catch (error) {
                    console.error('Failed to load top queries:', error);
                }
            }
            
            async loadAlerts() {
                try {
                    const response = await fetch('/dashboard/api/alerts');
                    const alerts = await response.json();
                    
                    const container = document.getElementById('alerts-container');
                    container.innerHTML = alerts.map(alert => `
                        <div class="alert alert-${alert.level === 'critical' ? 'danger' : 
                                                   alert.level === 'warning' ? 'warning' : 'info'} 
                                                   alert-dismissible fade show" role="alert">
                            <strong>${alert.level.toUpperCase()}:</strong> ${alert.message}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Failed to load alerts:', error);
                }
            }
        }
        
        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new DashboardManager();
        });
    </script>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

## Deployment & Integration

### Configuration

```python
# mcp_rag_playground/config/analytics_config.py
@dataclass
class AnalyticsConfig:
    enabled: bool = True
    db_path: str = "analytics.db"
    collection_interval: int = 30  # seconds
    retention_days: int = 90
    alert_thresholds: dict = field(default_factory=lambda: {
        'satisfaction_rate': 75,
        'success_rate': 85,
        'response_time': 3.0,
        'diversity_index': 0.5
    })
```

### Container Integration

```python
# Update mcp_rag_playground/container/container.py
from .analytics.analytics_service import AnalyticsService

class Container:
    # ... existing code ...
    
    analytics_service = providers.Singleton(
        AnalyticsService,
        db_path=providers.Configuration.analytics.db_path
    )
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Document KB Health Dashboard success criteria and quality metrics", "status": "completed", "id": "9"}, {"content": "Create implementation plan for response quality monitoring", "status": "completed", "id": "10"}, {"content": "Design analytics data model and storage schema", "status": "completed", "id": "11"}, {"content": "Plan dashboard visualization components", "status": "completed", "id": "12"}]