from business_queries import search_businesses
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)


# Parse the text messages spliting before and after 'in' to Grab the Tag, City and State
def parse_search_query(text):
    try:
        parts = text.strip().split(" in ")
        if len(parts) != 2:
            return None, "Missing 'in' keyword or tag before it (e.g., 'BBQ in Atlanta GA')."

        tag = parts[0].strip().lower()
        location_parts = parts[1].rsplit(" ", 1)

        if len(location_parts) != 2:
            return None, "City and state must both be included (e.g., 'BBQ in Atlanta GA')."

        city = location_parts[0].strip().lower()
        state = location_parts[1].strip().upper()

        if not tag:
            return None, "Please include what you're searching for (e.g., 'BBQ in Atlanta GA')."
        
        if not city or not state:
            return None, "City and state must both be included (e.g., 'BBQ in Atlanta GA')."

        return (tag, city, state), None

    except Exception as e:
        return None, "There was a problem processing your search. Try again."
    

@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body", "").strip()
    resp = MessagingResponse()

    parsed, error = parse_search_query(incoming_msg)

    if error:
        resp.message(error)
        return str(resp)

    tag, city, state = parsed

    try:
        results = search_businesses(tag, city, state)

        if results:
            reply = f"Black Businesses in {city.title()}, {state.upper()}:\n\n"
            for name, phone, website, street, city, state, postalcode in results[:5]:
                reply += f"📍 {name}\n📞 {phone}\n🔗 {website}\n🏠 {street}, {city}, {state} {postalcode}\n\n"
            reply += "Reply again to search more!"
        else:
            reply = f"No results found for '{tag}' in {city.title()}, {state.upper()}."

    except Exception as e:
        print("Error:", e)
        reply = "Oops! Something went wrong. Please try again later."

    resp.message(reply)
    return str(resp)


# def main():
#     print("Welcome to The Black 411")

#     query = "restaurant in Miami fl"
#     parsed, error = parse_search_query(query)

#     if error:
#         print("Error:", error)
#         return

#     tag, city, state = parsed

#     results = search_businesses(tag, city, state)

#     if results:
#         print("\nMatching businesses:\n")
#         for row in results:
#             print(f"- {row[0]} | {row[1]} ({row[2]}, {row[3]}) - Category: {row[4]}")
#     else:
#         print("No businesses found matching your search.")

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5000)


