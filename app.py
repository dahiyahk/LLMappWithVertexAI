import streamlit as st
from google import genai
from google.genai import types
import requests
import logging

# --- Defining variables and parameters  ---
REGION = "global"
PROJECT_ID = "project-8e86e757-90b4-43e7-812" # TODO: Insert Project ID
GEMINI_MODEL_NAME = "gemini-2.5-flash"

temperature = .2
top_p = 0.95

system_instructions = """
You are WanderBot, an expert travel assistant from a world-class travel company. Your mission is to provide exceptional, friendly, and inspiring assistance to users planning their journeys. You are enthusiastic, knowledgeable, and always ready to help someone discover the world.

**Core Directives:**

1.  **Be a World-Class Travel Expert:** Provide accurate, up-to-date, and insightful information about destinations, travel logistics (flights, hotels, transportation), and local culture. Your tone should always be encouraging and helpful.
2.  **Inspire Wanderlust:** Go beyond just answering questions. Offer interesting facts, hidden gems, and travel tips that get users excited about their trip. Use evocative language to describe places and experiences.
3.  **Prioritize the User:** Always be polite, patient, and empathetic. If a user is feeling overwhelmed with planning, offer to break things down into simple, manageable steps.
4.  **Maintain Brand Integrity:** You are a representative of a professional travel company. Your responses should be high-quality, well-structured, and free of errors.

**Functional Capabilities:**

*   **Answering Questions:** Help users with a wide range of travel queries, such as "What are the best beaches in Thailand?", "What is the visa requirement for Brazil?", or "Suggest a 7-day itinerary for Italy."
*   **Booking Assistance:** When a user wants to book something (e.g., "book a flight to Paris" or "find a hotel in New York"), guide them by asking for necessary details like dates, number of travelers, and preferences. Since you cannot complete the booking yourself, your final step should be to summarize their request and state, "I've gathered all the details! You can complete your booking on our secure portal," and you would ideally provide a link.
*   **Personalized Recommendations:** Ask clarifying questions to better understand the user's travel style, budget, and interests to provide tailored recommendations. For example, if they ask for "things to do in London," you can ask, "Are you more interested in history, art, food, or nightlife?"
*   **Problem Solving:** If a user has an issue with existing travel plans, provide helpful information and direct them to the correct customer support channel. For example: "I understand you need to change your flight. The best way to do that is to contact our 24/7 support line at [Phone Number] or visit our support page at [URL]."

**Constraints and Safety Protocols:**

*   **NEVER Ask for PII:** Do not ask for, handle, or store any Personally Identifiable Information (PII). This includes credit card numbers, passport details, home addresses, or any other sensitive personal data. Always direct users to a secure website or official channel for transactions or sharing sensitive information.
*   **Do Not Hallucinate:** If you do not know the answer to a question, admit it. Say something like, "That's a great question, but I don't have the specific information on that. I recommend checking with [Official Tourism Board/Embassy/etc.]."
*   **Stay On-Topic:** Your expertise is travel. Politely decline any requests that are inappropriate, unethical, or completely unrelated to travel planning. You can say, "My expertise is in travel, so I can't help with that. Is there a travel-related question I can answer for you?"
*   **Escalate When Necessary:** If a user is angry, expresses a serious complaint, or you cannot resolve their issue, offer to connect them to a human agent. For example: "I'm sorry I couldn't resolve this for you. Would you like me to connect you with one of our human travel experts?"

**Tone and Style:**

*   **Friendly and Professional:** Be warm and approachable, but maintain a professional demeanor.
*   **Use Emojis Sparingly:** Add a touch of personality with relevant emojis (e.g., ✈️, 🏨, 🗺️, ☀️), but don't overdo it.
*   **Use Formatting:** Use Markdown (like lists and bold text) to make your responses clear and easy to read.
"""

# --- Tooling ---
# TODO: Define the weather tool function declaration
weather_function = {
    "name": "get_current_temperature",
    "description": "Gets the current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
        },
        "required": ["location"],
    },
}

# TODO: Define the get_current_temperature function
def get_current_temperature(location: str) -> str:
    """Gets the current temperature for a given location."""

    try:
        # --- Get Latitude and Longitude for the location ---
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geocode_response = requests.get(geocode_url)
        geocode_data = geocode_response.json()

        if not geocode_data.get("results"):
            return f"Could not find coordinates for {location}."

        lat = geocode_data["results"][0]["latitude"]
        lon = geocode_data["results"][0]["longitude"]

        # --- Get Weather for the coordinates ---
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        temperature = weather_data["current_weather"]["temperature"]
        unit = "°C"

        return f"{temperature}{unit}"

    except Exception as e:
        return f"Error fetching weather: {e}"

# --- Initialize the Vertex AI Client ---
try:
    # TODO: Initialize the Vertex AI client
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=REGION,
    )

    print(f"VertexAI Client initialized successfully with model {GEMINI_MODEL_NAME}")
except Exception as e:
    st.error(f"Error initializing VertexAI client: {e}")
    st.stop()


# TODO: Add the get_chat function here in Task 15.
def get_chat(model_name: str):
    if f"chat-{model_name}" not in st.session_state:

        # TODO: Define the tools configuration for the model
        tools = types.Tool(function_declarations=[weather_function])

        # TODO: Define the generate_content configuration, including tools
        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            system_instruction=[types.Part.from_text(text=system_instructions)],
            tools=[tools] # Pass the tool definition here
        )

        # TODO: Create a new chat session
        chat = client.chats.create(
            model=model_name,
            config=generate_content_config,
        )

        st.session_state[f"chat-{model_name}"] = chat
    return st.session_state[f"chat-{model_name}"]


# --- Call the Model ---
# --- Call the Model ---
def call_model(prompt: str, model_name: str) -> str:
    """
    This function interacts with a large language model (LLM) to generate text based on a given prompt.
    It maintains a chat session and handles function calls from the model to external tools.
    """
    try:
        # TODO: Get the existing chat session or create a new one.
        chat = get_chat(model_name)
        message_content = prompt

        # Start the tool-calling loop
        while True:
            # TODO: Send the message to the model.
            response = chat.send_message(message_content)
            # Check if the model wants to call a tool
            has_tool_calls = False
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_tool_calls = True
                    function_call = part.function_call
                    logging.info(f"Function to call: {function_call.name}")
                    logging.info(f"Arguments: {function_call.args}")

                    # TODO: Call the appropriate function if the model requests it.
                    if function_call.name == "get_current_temperature":
                      result = get_current_temperature(**function_call.args)
                    function_response_part = types.Part.from_function_response(
                        name=function_call.name,
                        response={"result": result},
                    )
                    message_content = [function_response_part]

                elif part.text:
                    logging.info("No function call found in the response.")
                    logging.info(response.text)
            # If no tool call was made, break the loop
            if not has_tool_calls:
                break

        # TODO: Return the model's final text response.
        return response.text
    except Exception as e:
        return f"Error: {e}"


# --- Presentation Tier (Streamlit) ---
# Set the title of the Streamlit application
st.title("Travel Chat Bot")

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    # Initialize the chat history with a welcome message
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you today?"}
    ]

# Display the chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Get user input
if prompt := st.chat_input():
    # Add the user's message to the chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display the user's message
    st.chat_message("user").write(prompt)

    # Show a spinner while waiting for the model's response
    with st.spinner("Thinking..."):
        # Get the model's response using the call_model function
        model_response = call_model(prompt, GEMINI_MODEL_NAME)
        # Add the model's response to the chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": model_response}
        )
        # Display the model's response
        st.chat_message("assistant").write(model_response)
