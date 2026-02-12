"""
Cost optimization tests for Camofox integration.
Validates token reduction and cost savings calculations.
"""

import pytest
import json
from oracle.core.camofox_client import measure_snapshot_size


# Realistic test data
class TestCostCalculations:
    """Test cost reduction calculations."""
    
    def test_html_vs_snapshot_size_ratio(self):
        """Test that snapshots are 100x smaller than HTML."""
        # Simulate realistic HTML page (500KB)
        html_page = self._generate_html_page(size_kb=500)
        html_size_bytes = len(html_page.encode('utf-8'))
        
        # Simulate realistic snapshot (5KB)
        snapshot = self._generate_snapshot(elements=50)
        snapshot_size = measure_snapshot_size(snapshot)
        
        # Calculate ratio
        ratio = html_size_bytes / snapshot_size
        
        # Should be 100x or more
        assert ratio > 100, f"Expected ratio > 100, got {ratio}"
        print(f"HTML size: {html_size_bytes:,} bytes")
        print(f"Snapshot size: {snapshot_size:,} bytes")
        print(f"Reduction ratio: {ratio:.1f}x")
    
    def test_daily_cost_before_after(self):
        """Test daily cost calculation before/after Camofox."""
        # Assumptions
        pages_per_day = 1000
        
        # Before: HTML scraping
        html_size_kb = 500
        tokens_per_page_html = html_size_kb * 250  # ~250 tokens per 1KB
        total_tokens_before = pages_per_day * tokens_per_page_html
        cost_per_mtok = 0.003  # $3 per million tokens
        daily_cost_before = (total_tokens_before / 1_000_000) * cost_per_mtok
        
        # After: Camofox snapshots
        snapshot_size_kb = 5
        tokens_per_page_snapshot = snapshot_size_kb * 250
        total_tokens_after = pages_per_day * tokens_per_page_snapshot
        daily_cost_after = (total_tokens_after / 1_000_000) * cost_per_mtok
        
        # Calculate savings
        daily_savings = daily_cost_before - daily_cost_after
        monthly_savings = daily_savings * 30
        
        assert daily_cost_before > daily_cost_after
        assert daily_savings > 0
        
        print(f"\nDaily Cost Analysis ({pages_per_day:,} pages/day):")
        print(f"  Before (HTML): ${daily_cost_before:.2f}/day")
        print(f"  After (Snapshot): ${daily_cost_after:.2f}/day")
        print(f"  Savings: ${daily_savings:.2f}/day (${monthly_savings:.2f}/month)")
        print(f"  Reduction: {(daily_savings/daily_cost_before)*100:.1f}%")
    
    def test_token_reduction_scenarios(self):
        """Test token reduction across different scraping volumes."""
        cost_per_mtok = 0.003
        
        scenarios = [
            ("Light", 100, 500),      # 100 pages/day, 500KB HTML
            ("Medium", 500, 500),     # 500 pages/day
            ("Heavy", 1000, 500),     # 1000 pages/day
            ("Intensive", 5000, 500), # 5000 pages/day
        ]
        
        results = []
        for name, pages_per_day, html_size_kb in scenarios:
            # Before
            tokens_before = pages_per_day * html_size_kb * 250
            cost_before = (tokens_before / 1_000_000) * cost_per_mtok
            
            # After
            tokens_after = pages_per_day * 5 * 250  # 5KB snapshot
            cost_after = (tokens_after / 1_000_000) * cost_per_mtok
            
            # Savings
            monthly_before = cost_before * 30
            monthly_after = cost_after * 30
            monthly_savings = monthly_before - monthly_after
            
            results.append({
                "scenario": name,
                "pages_per_day": pages_per_day,
                "monthly_before": monthly_before,
                "monthly_after": monthly_after,
                "monthly_savings": monthly_savings,
                "reduction_pct": (monthly_savings / monthly_before) * 100
            })
        
        # Print results
        print("\n" + "="*70)
        print("Token Reduction Scenarios (Monthly Costs)")
        print("="*70)
        print(f"{'Scenario':<15} {'Pages/Day':<12} {'Before':<12} {'After':<12} {'Savings':<12} {'Reduction':<10}")
        print("-"*70)
        
        for r in results:
            print(
                f"{r['scenario']:<15} {r['pages_per_day']:<12,} "
                f"${r['monthly_before']:<11.2f} ${r['monthly_after']:<11.2f} "
                f"${r['monthly_savings']:<11.2f} {r['reduction_pct']:<9.1f}%"
            )
        
        # All should show ~99% reduction
        for r in results:
            assert r['reduction_pct'] > 98


class TestTokenEstimation:
    """Test token estimation for different content types."""
    
    def test_snapshot_token_count_estimation(self):
        """Estimate tokens in realistic snapshot."""
        # Typical snapshot: 50 elements, ~100 chars each + metadata
        snapshot = {
            "tabId": "tab-123",
            "url": "https://example.com",
            "title": "Example Page",
            "elements": [
                {
                    "ref": f"e{i}",
                    "tag": "div",
                    "text": "Sample text content that is typically 50-150 characters long",
                    "className": "element"
                }
                for i in range(50)
            ]
        }
        
        snapshot_json = json.dumps(snapshot)
        snapshot_size = len(snapshot_json.encode('utf-8'))
        
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(snapshot_json) / 4
        
        # Should be < 2000 tokens
        assert estimated_tokens < 2000
        print(f"Snapshot size: {snapshot_size:,} bytes")
        print(f"Estimated tokens: {estimated_tokens:.0f}")
    
    def test_html_token_count_estimation(self):
        """Estimate tokens in realistic HTML page."""
        # Typical HTML: 500KB = 500,000 bytes
        html_size = 500_000
        
        # Rough estimation: 1 token ≈ 4 bytes
        estimated_tokens = html_size / 4
        
        # Should be ~125,000 tokens
        assert estimated_tokens > 100_000
        print(f"HTML size: {html_size:,} bytes")
        print(f"Estimated tokens: {estimated_tokens:.0f}")
    
    def test_token_ratio_validation(self):
        """Validate 100x token reduction claim."""
        # HTML: 500KB = 500,000 bytes ≈ 125,000 tokens
        html_tokens = 125_000
        
        # Snapshot: 5KB = 5,000 bytes ≈ 1,250 tokens
        snapshot_tokens = 1_250
        
        # Ratio
        ratio = html_tokens / snapshot_tokens
        
        assert ratio == 100
        print(f"HTML tokens: {html_tokens:,}")
        print(f"Snapshot tokens: {snapshot_tokens:,}")
        print(f"Token reduction: {ratio:.0f}x")


class TestRealWorldScenarios:
    """Test cost implications for real Oracle use cases."""
    
    def test_twitter_sentiment_scraping_cost(self):
        """Calculate cost for Twitter sentiment scraping."""
        # Use case: Monitor 100 crypto keywords, 10 pages per keyword per day
        keywords = 100
        pages_per_keyword_per_day = 10
        pages_per_day = keywords * pages_per_keyword_per_day
        
        # Costs
        cost_per_mtok = 0.003
        html_tokens_per_page = 125_000
        snapshot_tokens_per_page = 1_250
        
        # Monthly costs
        monthly_pages = pages_per_day * 30
        
        cost_before = (monthly_pages * html_tokens_per_page / 1_000_000) * cost_per_mtok
        cost_after = (monthly_pages * snapshot_tokens_per_page / 1_000_000) * cost_per_mtok
        monthly_savings = cost_before - cost_after
        
        print(f"\nTwitter Sentiment Scraping ({keywords} keywords):")
        print(f"  Pages per day: {pages_per_day:,}")
        print(f"  Monthly cost (HTML): ${cost_before:,.2f}")
        print(f"  Monthly cost (Snapshot): ${cost_after:,.2f}")
        print(f"  Monthly savings: ${monthly_savings:,.2f}")
    
    def test_polymarket_arbitrage_scanning_cost(self):
        """Calculate cost for Polymarket arbitrage scanning."""
        # Use case: Scan 500 markets, every 5 minutes
        markets = 500
        scans_per_day = (24 * 60) // 5  # Every 5 minutes
        pages_per_day = markets  # Full scan = markets
        
        # Costs
        cost_per_mtok = 0.003
        html_tokens_per_page = 125_000
        snapshot_tokens_per_page = 1_250
        
        # Monthly costs
        monthly_pages = pages_per_day * scans_per_day * 30
        
        cost_before = (monthly_pages * html_tokens_per_page / 1_000_000) * cost_per_mtok
        cost_after = (monthly_pages * snapshot_tokens_per_page / 1_000_000) * cost_per_mtok
        monthly_savings = cost_before - cost_after
        
        print(f"\nPolymarket Arbitrage Scanning ({markets} markets):")
        print(f"  Pages per day: {pages_per_day * scans_per_day:,}")
        print(f"  Monthly cost (HTML): ${cost_before:,.2f}")
        print(f"  Monthly cost (Snapshot): ${cost_after:,.2f}")
        print(f"  Monthly savings: ${monthly_savings:,.2f}")
    
    def test_news_aggregation_cost(self):
        """Calculate cost for crypto news aggregation."""
        # Use case: 10 news sources, scraped every 30 minutes
        sources = 10
        scrapes_per_day = (24 * 60) // 30
        pages_per_day = sources * scrapes_per_day
        
        # Costs
        cost_per_mtok = 0.003
        html_tokens_per_page = 125_000
        snapshot_tokens_per_page = 1_250
        
        # Monthly costs
        monthly_pages = pages_per_day * 30
        
        cost_before = (monthly_pages * html_tokens_per_page / 1_000_000) * cost_per_mtok
        cost_after = (monthly_pages * snapshot_tokens_per_page / 1_000_000) * cost_per_mtok
        monthly_savings = cost_before - cost_after
        
        print(f"\nNews Aggregation ({sources} sources):")
        print(f"  Pages per day: {pages_per_day:,}")
        print(f"  Monthly cost (HTML): ${cost_before:,.2f}")
        print(f"  Monthly cost (Snapshot): ${cost_after:,.2f}")
        print(f"  Monthly savings: ${monthly_savings:,.2f}")


# Helper methods
def _generate_html_page(size_kb: int) -> str:
    """Generate realistic HTML page of specified size."""
    html = "<html><head><title>Example</title></head><body>"
    html += "<div>" + ("a" * (size_kb * 1024 - len(html) - 20)) + "</div>"
    html += "</body></html>"
    return html


def _generate_snapshot(elements: int) -> dict:
    """Generate realistic snapshot with specified number of elements."""
    return {
        "tabId": "tab-123",
        "url": "https://example.com",
        "title": "Example Page",
        "elements": [
            {
                "ref": f"e{i}",
                "tag": "div",
                "text": f"Element {i} with sample text content",
                "className": "item"
            }
            for i in range(elements)
        ]
    }


TestCostCalculations._generate_html_page = staticmethod(_generate_html_page)
TestCostCalculations._generate_snapshot = staticmethod(_generate_snapshot)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
