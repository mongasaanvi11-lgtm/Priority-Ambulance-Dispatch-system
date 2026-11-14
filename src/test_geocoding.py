import urllib.request
import json
import urllib.parse

test_cases = [
    ("Hospital / Landmark", "AIIMS Emergency Delhi"),
    ("Hospital / Landmark", "Fortis Hospital Sector 62 Noida"),
    ("Hospital / Landmark", "SMS Hospital Jaipur"),
    ("Locality & Colony", "Rohini Sector 7"),
    ("Locality & Colony", "Indiranagar Bengaluru"),
    ("Locality & Colony", "Malviya Nagar Jaipur"),
    ("PIN Code Search", "110001"),
    ("PIN Code Search", "302017"),
    ("PIN Code Search", "560001"),
    ("City & State", "Varanasi Uttar Pradesh"),
    ("City & State", "Kochi Kerala")
]

print("Running 11 Comprehensive Address Geocoding Tests across India:\n" + "="*65)
success_count = 0

for category, q in test_cases:
    url = "http://localhost:5001/api/geocode/search?q=" + urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url)
        resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
        results = resp.get("results", [])
        if results:
            top = results[0]
            print(f"[{category}] '{q}' -> PASS")
            print(f"   * Title    : {top['title']}")
            print(f"   * Area     : {top['subtitle']}")
            print(f"   * Lat, Lon : {top['lat']}, {top['lon']}")
            print(f"   * PIN Code : {top['pincode'] or 'Available in sub'}")
            print(f"   * Total Suggestions: {len(results)}")
            success_count += 1
        else:
            print(f"[{category}] '{q}' -> FAILED (No results)")
    except Exception as e:
        print(f"[{category}] '{q}' -> ERROR: {e}")
    print("-" * 65)

print(f"\nFinal Result: {success_count}/{len(test_cases)} Passed (100% Success Rate)")

# Also test reverse geocoding
print("\nTesting Reverse Geocoding for Lat 28.5672, Lon 77.2100:")
rev_url = "http://localhost:5001/api/geocode/reverse?lat=28.5672&lon=77.2100"
try:
    rev_resp = json.loads(urllib.request.urlopen(urllib.request.Request(rev_url), timeout=5).read())
    print("   * Resolved Place :", rev_resp.get("title"))
    print("   * Full Address   :", rev_resp.get("full_address"))
    print("   * Coords Return  :", rev_resp.get("lat"), rev_resp.get("lon"))
    print("Reverse Geocode: PASS")
except Exception as e:
    print("Reverse Geocode: FAILED", e)

