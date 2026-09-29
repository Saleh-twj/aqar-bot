import json, urllib.request

API = "https://backend.aqaralmuhaysini.com/api/properties/list?page={}"
SITE = "https://aqaralmuhaysini.com/propertydetails/{}"

def get(page):
    req = urllib.request.Request(API.format(page), headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=30)).get("properties") or []

def num(v):
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return None

results, seen, page = [], set(), 1
while page <= 1000:
    items = get(page)
    new = [p for p in items if p["id"] not in seen]
    if not new:
        break
    for p in new:
        seen.add(p["id"])
        if p.get("status") != "available":
            continue
        results.append({
            "id": p["id"],
            "url": SITE.format(p["id"]),
            "title": p.get("title"),
            "type": (p.get("PropertyType") or {}).get("name"),
            "purpose": "بيع" if p.get("purpose") == "for_sale" else "إيجار",
            "city": (p.get("City") or {}).get("name"),
            "hood": (p.get("Neighborhood") or {}).get("name"),
            "price": num(p.get("price")),
            "area": num(p.get("area")),
            "rooms": p.get("roomsCount"),
        })
    print(f"صفحة {page}: {len(seen)} عقار")
    page += 1

json.dump(results, open("properties.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"تم: {len(results)} عقار متاح من أصل {len(seen)}")
