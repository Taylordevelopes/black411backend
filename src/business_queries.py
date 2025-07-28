from db import get_connection
from datetime import datetime,timezone
from psycopg2.extras import execute_values

def get_city_lat_lon(city, state, conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT latitude, longitude
            FROM city_locations
            WHERE lower(city) = %s AND upper(state) = %s
        """, (city.lower(), state.upper()))
        return cur.fetchone() 

def search_businesses(tag, city, state, radius=50):
    print(f"Searching for: {tag} in {city}, {state}")

    conn = get_connection()
    cur = conn.cursor()

    # STEP 1: Try to get coordinates for the city
    center = get_city_lat_lon(city, state, conn)

    if center:
        center_lat, center_lon = center

        # STEP 2a: Radius-based match (exclude tagname and distance from SELECT)
        query = """
            SELECT 
                b.businessid,
                b.name,
                b.phonenumber,
                b.website,
                a.street,
                a.city,
                a.state,
                a.postalcode
            FROM businesses b
            JOIN addresses a ON b.businessid = a.businessid
            JOIN businesstags bt ON b.businessid = bt.businessid
            JOIN tags t ON bt.tagid = t.tagid
            WHERE lower(t.tagname) = %s
            AND (
                3959 * acos(
                    cos(radians(%s)) * cos(radians(a.latitude)) *
                    cos(radians(a.longitude) - radians(%s)) +
                    sin(radians(%s)) * sin(radians(a.latitude))
                )
            ) <= %s
            ORDER BY b.last_seen_at NULLS FIRST, b.businessid
            LIMIT 3;
        """
        params = (
            tag.lower(),
            center_lat, center_lon, center_lat, radius,  # WHERE
            center_lat, center_lon, center_lat           # ORDER BY
        )
    else:
        print("No city coordinates found — falling back to city/state match.")

        # STEP 2b: City/state fallback (still exclude tagname)
        query = """
            SELECT 
                b.businessid,
                b.name,
                b.phonenumber,
                b.website,
                a.street,
                a.city,
                a.state,
                a.postalcode
            FROM businesses b
            JOIN addresses a ON b.businessid = a.businessid
            JOIN businesstags bt ON b.businessid = bt.businessid
            JOIN tags t ON bt.tagid = t.tagid
            WHERE lower(a.city) = %s
            AND upper(a.state) = %s
            AND lower(t.tagname) = %s;
            ORDER BY b.last_seen_at NULLS FIRST, b.businessid
            LIMIT 3;
        """
        params = (city.lower(), state.upper(), tag.lower())

    # STEP 3: Run the query
    cur.execute(query, params)
    results = cur.fetchall()

    # STEP 4: Update last_seen_at for those results
    business_ids = [row[0] for row in results]
    if business_ids:
        cur.execute(
            "UPDATE businesses SET last_seen_at = %s WHERE businessid = ANY(%s)",
            (datetime.utcnow(), business_ids)  # 👈 wrap list in tuple
        )
        conn.commit()

    # STEP 5: Drop businessid before returning results
    cleaned_results = [row[1:] for row in results]

    cur.close()
    conn.close()

    return cleaned_results
