from business_queries import search_businesses
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from utils.state_abbreviations import STATE_ABBREVIATIONS
import re


load_dotenv()

app = Flask(__name__)

def normalize_state(state:str) -> str:
    state = state.strip().lower()
    return STATE_ABBREVIATIONS.get(state, state.upper() if len(state)==2 else "" )


# Parse the text messages spliting before and after 'in' to Grab the Tag, City and State
def parse_search_query(text):
    try:
        parts = text.strip().split(" in ")
        if len(parts) != 2:
            return None, "Please provide the 'in' keyword or and what you are looking for. Remember you can search for anything with The Black 411 (e.g., 'Restaurant in Atlanta GA')."

        tag = parts[0].strip().lower()
        raw_location = parts[1].strip().lower()

        clean_location = re.sub(r'[,\s]+', ' ', raw_location).strip() 
        location_parts = clean_location.rsplit(" ", 1)
        if len(location_parts) != 2:
            return None, "City and state must both be included. Remember you can search for anything with The Black 411 (e.g., 'Restaurant in Atlanta GA')."

        city = location_parts[0].strip().lower()
        raw_state = location_parts[1].strip()

        state = normalize_state(raw_state)

        if not tag:
            return None, "Please include what you're searching for. Remember you can search for anything with The Black 411 (e.g., 'Restaurant in Atlanta GA')."
        
        if not city or not state:
            return None, "City and state must both be included. Remember you can search for anything with The Black 411 (e.g., 'Restaurant in Atlanta GA')."

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
            if len(results) == 1:
                reply = f"Here is a Black Business for your search of '{tag.upper()}' in {city.title()}, {state.upper()}:\n\n"
                for name, phone, website, street, city, state, postalcode in results[:3]:
                    reply += f"📍 {name}\n📞 {phone}\n🔗 {website}\n🏠 {street}, {city}, {state} {postalcode}\n\n"
                reply += "Reply again to search more, Thanks for using The Black 411!"
            else:
                reply = f"Black Businesses for your search of '{tag.upper()}' in {city.title()}, {state.upper()}:\n\n"
                for name, phone, website, street, city, state, postalcode in results[:3]:
                    reply += f"📍 {name}\n📞 {phone}\n🔗 {website}\n🏠 {street}, {city}, {state} {postalcode}\n\n"
                reply += "Reply again to search more, Thanks for using The Black 411!"
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


