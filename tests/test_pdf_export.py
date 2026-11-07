from datetime import datetime
from pdf_export import build_travel_pdf


def test_pdf_has_magic_header_and_content():
    data = build_travel_pdf(
        user_query='Plan a 3-day Tokyo trip',
        thread_id='test-thread',
        collected={
            'flight_results': 'Airport references only',
            'hotel_results': 'Example hotel search',
            'weather_results': 'Short-range weather only',
            'itinerary': '# Day 1\n- Explore Tokyo',
            'llm_calls': 3,
        },
        generated_at=datetime(2026, 11, 8, 12, 0),
    )
    assert data.startswith(b'%PDF-')
    assert len(data) > 1500
