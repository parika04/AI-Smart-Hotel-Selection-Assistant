import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

def generate_response(prompt):
    """Generates a response using the Gemini API and formats it into bullet points."""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Convert numbered list into bullet list using simple parsing
        lines = text.split('\n')
        bullet_lines = []
        for line in lines:
            if line.strip().startswith(tuple(str(i) + '.' for i in range(1, 10))):
                # Convert numbered line to bullet point
                bullet_lines.append(f"<li>{line[line.find('.')+1:].strip()}</li>")
            else:
                bullet_lines.append(f"<p>{line}</p>")

        formatted_response = "<ul>" + "".join(bullet_lines) + "</ul>"
        return formatted_response
    except Exception as e:
        return f"<p>Error: {e}</p>"


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
    If the user asks for hotels in a city, provide a list of 3-5 hotels with brief descriptions and approximate price ranges.
    If the user provides specific criteria (e.g., price, amenities, location), use those criteria to filter your recommendations.
    User: {user_input}
    """
    response = generate_response(prompt)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
