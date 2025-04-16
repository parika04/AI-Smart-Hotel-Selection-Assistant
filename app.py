import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

def generate_response(prompt):
    """Generates a response using the Gemini API."""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        lines = text.split('\n')
        hotel_data = []
        formatted_lines = []

        for line in lines:
            line = line.strip()
            # Extract hotel name and description, more robustly
            if re.match(r'^\d+\.\s*(.+?)\s*:\s*(.*)$', line):  # Changed separator to ":"
                match = re.match(r'^\d+\.\s*(.+?)\s*:\s*(.*)$', line)  # Changed separator to ":"
                hotel_name = match.group(1).strip()
                description = match.group(2).strip()
                # Further extraction of location from description, if present
                location_match = re.search(r'\b(?:in|near|at)\s+([A-Za-z\s]+(?:, [A-Za-z\s]+)?)\b', description)
                location = location_match.group(1).strip() if location_match else ""
                hotel_data.append({'name': hotel_name, 'description': description, 'location': location})
                formatted_lines.append(
                    f"<li><a href='#' target='_blank'>{hotel_name}</a>: {description}</li>")  # Placeholder
            elif re.search(r"Hotel:\s*(.+)", line):
                hotel_name = re.search(r"Hotel:\s*(.+)", line).group(1).strip()
                hotel_data.append({'name': hotel_name, 'description': '', 'location': ''})
                formatted_lines.append(f"<li><a href='#' target='_blank'>{hotel_name}</a></li>")
            else:
                formatted_lines.append(f"<p>{line}</p>")

        formatted_response = "<ul>" + "".join(formatted_lines) + "</ul>"
        return formatted_response, hotel_data
    except Exception as e:
        return f"<p>Error: {e}</p>", []



@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat requests and returns Gemini's response."""
    user_input = request.json['message']
    prompt = f"""
    You are a helpful AI Hotel Selection Assistant. Help the user find suitable hotels.
    Provide specific hotel recommendations based on the user's preferences.
    When the user asks for hotels in a city,  provide a list of 3-5 hotels with brief descriptions and approximate price ranges.  Do not include booking links in this initial response.  Make sure the descriptions include the city.
    If the user provides specific criteria (e.g., price, amenities, location), use those criteria to filter your recommendations.  Make sure the descriptions include the city.
    Focus on providing the hotel names and brief descriptions, including the city, in this first response.
    User: {user_input}
    """
    response, hotel_data = generate_response(prompt)

    # Replace this with a robust hotel-to-link mapping (e.g., from a database)
    hotel_links = {
        ("Ritz-Carlton", "New York"): "https://www.ritzcarlton.com/en/hotels/new-york/central-park",
        ("Ritz-Carlton", "Chicago"): "https://www.ritzcarlton.com/en/hotels/chicago",
        ("Four Seasons", "New York"): "https://www.fourseasons.com/newyork/",
        ("Four Seasons", "Paris"): "https://www.fourseasons.com/paris/",
        ("Hilton", "London"): "https://www.hilton.com/en/hotels/united-kingdom/london/",
        ("Hilton", "Tokyo"): "https://www.hilton.com/en/hotels/japan/tokyo/",
        ("Marriott", "Rome"): "https://www.marriott.com/en-us/hotels/italy/rome/",
        ("Marriott", "Bangkok"): "https://www.marriott.com/en-us/hotels/thailand/bangkok/",
        ("Hyatt", "Sydney"): "https://www.hyatt.com/en-US/hotel/australia/sydney/",
        ("Hyatt", "Toronto"): "https://www.hyatt.com/en-US/hotel/canada/toronto/",
    }

    # Update the response with clickable links
    for i, hotel in enumerate(hotel_data):
        link_key = (hotel['name'], hotel['location'])  # Use a tuple of (name, location)
        if link_key in hotel_links:
            response = response.replace(f"<li><a href='#' target='_blank'>{hotel['name']}</a>: {hotel['description']}</li>",
                                        f"<li><a href='{hotel_links[link_key]}' target='_blank'>{hotel['name']}</a>: {hotel['description']}</li>")
        else:
            response = response.replace(f"<li><a href='#' target='_blank'>{hotel['name']}</a>: {hotel['description']}</li>",
                                        f"<li><a href='https://www.google.com/search?q={hotel['name'].replace(' ', '+')}+{hotel['location'].replace(' ', '+')}' target='_blank'>{hotel['name']}</a>: {hotel['description']}</li>") # Added location to the google search.


    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
