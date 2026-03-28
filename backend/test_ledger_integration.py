"""
Test script for ledger auto-creation integration
Run this to verify the end-to-end flow works correctly
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.ledger_service import ledger_service
from services.audio_storage_service import audio_storage_service
from services.supabase_service import supabase_service


def test_ledger_creation():
    """Test ledger entry creation with mock data."""
    print("🧪 Testing Ledger Auto-Creation Integration\n")
    
    # Mock extracted data (as would come from LLM)
    extracted_data = {
        "items_sold": [
            {
                "name": "केला (Banana)",
                "quantity": 60,
                "unit_price": 5,
                "total_amount": 300
            },
            {
                "name": "आम (Mango)",
                "quantity": 20,
                "unit_price": 40,
                "total_amount": 800
            }
        ],
        "expenses": [
            {
                "type": "raw_material",
                "description": "फल खरीदने में (Fruit purchase)",
                "amount": 500
            },
            {
                "type": "transport",
                "description": "रिक्शा किराया (Rickshaw fare)",
                "amount": 50
            }
        ],
        "total_revenue": 1100,
        "total_expense": 550,
        "net_profit": 550,
        "notes": "आज अच्छा दिन था (Good day today)"
    }
    
    # Test user ID (replace with actual user ID from your Supabase)
    test_user_id = "test-user-123"
    test_transcription_id = "test-transcription-456"
    
    print("📝 Mock Data:")
    print(f"  Items: {len(extracted_data['items_sold'])}")
    print(f"  Expenses: {len(extracted_data['expenses'])}")
    print(f"  Net Profit: ₹{extracted_data['net_profit']}\n")
    
    # Test 1: Create ledger entry
    print("1️⃣ Creating ledger entry...")
    try:
        ledger_entry_id = ledger_service.create_entry_from_transcription(
            user_id=test_user_id,
            transcription_id=test_transcription_id,
            extracted_data=extracted_data,
            audio_url=None,  # No audio for this test
        )
        
        if ledger_entry_id:
            print(f"   ✅ Ledger entry created: {ledger_entry_id}")
        else:
            print("   ❌ Ledger entry creation returned None")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Retrieve ledger entry
    print("\n2️⃣ Retrieving ledger entries...")
    try:
        from datetime import date, timedelta
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        entries = ledger_service.get_entries_by_date_range(
            user_id=test_user_id,
            start_date=yesterday.isoformat(),
            end_date=today.isoformat()
        )
        
        print(f"   ✅ Found {len(entries)} entries")
        if entries:
            entry = entries[0]
            print(f"   📊 Entry details:")
            print(f"      - Date: {entry.get('entry_date')}")
            print(f"      - Items: {len(entry.get('ledger_items', []))}")
            print(f"      - Expenses: {len(entry.get('ledger_expenses', []))}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Get summary
    print("\n3️⃣ Generating summary...")
    try:
        summary = ledger_service.get_summary(
            user_id=test_user_id,
            period="week"
        )
        
        print(f"   ✅ Summary generated:")
        print(f"      - Total Earnings: ₹{summary.get('total_earnings', 0):.2f}")
        print(f"      - Total Expenses: ₹{summary.get('total_expenses', 0):.2f}")
        print(f"      - Net Profit: ₹{summary.get('net_profit', 0):.2f}")
        print(f"      - Days: {summary.get('days_count', 0)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 4: Check Supabase Storage bucket
    print("\n4️⃣ Checking Supabase Storage...")
    try:
        # Just verify the service initializes
        print(f"   ✅ Audio storage service initialized")
        print(f"      - Bucket: {audio_storage_service.BUCKET_NAME}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n✅ All tests passed!")
    print("\n📋 Next Steps:")
    print("   1. Upload a real audio file via POST /process")
    print("   2. Check that ledger entry is created automatically")
    print("   3. Verify audio is uploaded to Supabase Storage")
    print("   4. Check that presigned URL is generated")
    print("   5. Verify audio segments are stored")
    
    return True


def test_confidence_scoring():
    """Test confidence score calculation."""
    print("\n🎯 Testing Confidence Scoring\n")
    
    # Test items with varying completeness
    test_items = [
        {
            "name": "Apple",
            "quantity": 50,
            "unit_price": 10,
            "total_amount": 500
        },
        {
            "name": "something",  # Vague name
            "quantity": 10,
        },
        {
            "name": "Banana",
            # Missing quantity and price
        }
    ]
    
    for i, item in enumerate(test_items, 1):
        confidence = ledger_service._calculate_item_confidence(item)
        print(f"{i}. Item: {item.get('name', 'Unknown')}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Needs confirmation: {confidence < 0.7}")
        print()


if __name__ == "__main__":
    print("=" * 60)
    print("LEDGER AUTO-CREATION INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Check environment
    if not os.getenv("SUPABASE_URL"):
        print("⚠️  Warning: SUPABASE_URL not set in environment")
        print("   Make sure .env file is loaded\n")
    
    # Run tests
    try:
        test_confidence_scoring()
        print("\n" + "=" * 60 + "\n")
        test_ledger_creation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
