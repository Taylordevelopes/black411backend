from db import get_connection

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
            ORDER BY (
                3959 * acos(
                    cos(radians(%s)) * cos(radians(a.latitude)) *
                    cos(radians(a.longitude) - radians(%s)) +
                    sin(radians(%s)) * sin(radians(a.latitude))
                )
            ) ASC;
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
        """
        params = (city.lower(), state.upper(), tag.lower())

    # STEP 3: Run the query
    cur.execute(query, params)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results
