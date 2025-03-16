"AIzaSyDoGRfFQcpre1nKMR0vv9iiU1Xeogt5tic"

import sqlite3
import re
import textwrap
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify

# 🔹 Configure Google Gemini API
GEMINI_API_KEY = "AIzaSyDoGRfFQcpre1nKMR0vv9iiU1Xeogt5tic"  # Replace with a valid API key
genai.configure(api_key="AIzaSyDoGRfFQcpre1nKMR0vv9iiU1Xeogt5tic")

# 🔹 Initialize Flask app
app = Flask(__name__)

# 🔹 Database setup function
def init_db():
    """Creates a database table if it doesn't exist."""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print("❌ Database initialization failed:", e)

# Initialize the database
init_db()

# 🔹 Function to clean AI response
def clean_response(text):
    """Removes unnecessary Markdown formatting while keeping structure."""
    text = re.sub(r"\*\*(.*?)\*\*", r"**\1:**", text)  # Keep bold for headings
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove *italics*
    text = text.replace(". ", ".\n\n")  # Ensure new lines for readability
    text = text.replace(":*", ":\n")  # Fix bullet point alignment
    formatted_paragraphs = "\n\n".join(textwrap.wrap(text, width=80))
    return formatted_paragraphs

# 🔹 Function to get AI-generated response
def get_ai_response(user_query):
    """Generates response using Google Gemini API"""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(user_query)
        if response and response.text:
            return clean_response(response.text)
        else:
            return "⚠️ No response from AI."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# 🔹 Function to store conversation in database
def store_conversation(user_message, ai_response):
    """Stores user messages and AI responses in the database."""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (user_message, ai_response) VALUES (?, ?)", 
                       (user_message, ai_response))
        conn.commit()
        conn.close()
        print(f"✅ Stored: {user_message} ➡️ {ai_response}")  # Debugging
    except Exception as e:
        print("❌ Database Error:", e)

# 🔹 Function to retrieve chat history
def get_chat_history():
    """Retrieves the last 20 messages from the chat history."""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_message, ai_response, timestamp FROM chat_history ORDER BY timestamp DESC LIMIT 20")
        chat_history = cursor.fetchall()
        conn.close()
        print("🔹 Retrieved Chat History:", chat_history)  # Debugging
        return chat_history
    except Exception as e:
        print("❌ Error retrieving chat history:", e)
        return []

# 🔹 Route for home page
@app.route("/")
def home():
    """Displays the home page with chat history."""
    chat_history = get_chat_history()  # Retrieve chat history
    return render_template("index.html", chat_history=chat_history)

# 🔹 Route for processing user input
@app.route("/ask", methods=["POST"])
def ask():
    """Handles user input, gets AI response, and stores the conversation."""
    try:
        user_message = request.form.get("user_message", "").strip()
        if not user_message:
            return jsonify({"error": "⚠️ Empty message received."}), 400

        ai_response = get_ai_response(user_message)

        # Store conversation in database
        store_conversation(user_message, ai_response)

        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"error": f"❌ Error: {str(e)}"}), 500

# 🔹 Run the app
if __name__ == "__main__":
    app.run(debug=True)
