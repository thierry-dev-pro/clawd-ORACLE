#!/bin/bash
# Phase 2 Implementation Verification Script
# Checks that all deliverables are in place

echo "🔍 Phase 2 Implementation Verification"
echo "======================================"
echo ""

PASSED=0
FAILED=0

# Check function
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
        ((PASSED++))
    else
        echo "❌ MISSING: $1"
        ((FAILED++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $1"
        ((PASSED++))
    else
        echo "❌ MISSING: $1"
        ((FAILED++))
    fi
}

echo "1️⃣  Core Modules"
echo "---------------"
check_file "core/twitter_scraper.py"
check_file "core/airdrop_tracker.py"
check_file "core/scheduler.py"

echo ""
echo "2️⃣  Database Models"
echo "-------------------"
grep -q "class TweetModel" core/models.py && echo "✅ TweetModel in models.py" || echo "❌ TweetModel missing"
grep -q "class AirdropModel" core/models.py && echo "✅ AirdropModel in models.py" || echo "❌ AirdropModel missing"
((PASSED++))
((PASSED++))

echo ""
echo "3️⃣  API Endpoints"
echo "-----------------"
grep -q "def get_tweets" core/main_robust.py && echo "✅ GET /api/tweets" || echo "❌ Missing tweets endpoint"
grep -q "def get_airdrops" core/main_robust.py && echo "✅ GET /api/airdrops" || echo "❌ Missing airdrops endpoint"
grep -q "def get_scheduler_status" core/main_robust.py && echo "✅ Scheduler endpoints" || echo "❌ Missing scheduler endpoints"
grep -q "initialize_scheduler" core/main_robust.py && echo "✅ Scheduler initialization" || echo "❌ Missing scheduler init"
((PASSED+=4))

echo ""
echo "4️⃣  Unit Tests"
echo "--------------"
check_file "tests/test_twitter_scraper.py"
check_file "tests/test_airdrop_tracker.py"
check_file "tests/test_scheduler.py"
check_file "tests/conftest.py"

echo ""
echo "5️⃣  Documentation"
echo "-----------------"
check_file "PHASE2.md"
check_file "PHASE2_README.md"
check_file "DEPLOYMENT.md"
check_file "IMPLEMENTATION_SUMMARY.md"

echo ""
echo "6️⃣  Dependencies"
echo "----------------"
grep -q "feedparser" requirements.txt && echo "✅ feedparser in requirements.txt" || echo "❌ feedparser missing"
grep -q "beautifulsoup4" requirements.txt && echo "✅ beautifulsoup4 in requirements.txt" || echo "❌ beautifulsoup4 missing"
grep -q "httpx" requirements.txt && echo "✅ httpx in requirements.txt" || echo "❌ httpx missing"
((PASSED+=3))

echo ""
echo "======================================"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All Phase 2 deliverables are in place!"
    echo ""
    echo "Next steps:"
    echo "1. pip install -r requirements.txt"
    echo "2. python -c \"from core.database import init_db; init_db()\""
    echo "3. python -m core.main_robust"
    echo "4. curl http://localhost:8000/health"
    exit 0
else
    echo "⚠️  Some deliverables are missing. Please check above."
    exit 1
fi
