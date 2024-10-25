import streamlit as st
from helper_functions.utility import check_password
import requests
from openai import OpenAI
from datetime import datetime
import pytz

# Retrieve the API key from Streamlit's secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]

# Hardcoded API URLs
api_urls = {
    "Number of CPF Members": "https://api-production.data.gov.sg/v2/public/api/collections/46/metadata",
    "Retirement withdrawals": "https://api-production.data.gov.sg/v2/public/api/collections/43/metadata"
}

# Function to fetch data from a given API URL
def fetch_api_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch data from {url}"}
    except Exception as e:
        return {"error": str(e)}

# About Us page
def about_us():
    st.title("About Us")
    st.write("This project aims to create a government chatbot that provides factual information to users. The chatbot pulls data from various government sources to answer queries.")

# Methodology page
def methodology():
    st.title("Methodology")
    st.write("The chatbot retrieves information based on user queries and fetches data from predefined API sources. The implementation uses OpenAI's language model to process the user's questions and provide accurate responses.")

# Function to handle compliments, feedback, and complaints
def handle_feedback():
    st.title("Feedback")
    feedback_type = st.radio("Select the type of feedback:", 
                              ("Select", "Compliments", "Feedback", "Complaints"), 
                              index=0)

    feedback_message = st.text_area("Please enter your message:")
    
    rating = st.slider("Please rate your experience:", 
                       min_value=1, max_value=5, value=1, step=1)
    
    stars = "⭐" * rating
    st.markdown(f"**Your Rating:** {stars}")

    st.markdown("⭐ - Very Dissatisfied, ⭐⭐ - Dissatisfied, ⭐⭐⭐ - Neutral, ⭐⭐⭐⭐ - Satisfied, ⭐⭐⭐⭐⭐ - Very Satisfied")

    if st.button("Submit"):
        if feedback_message:
            if feedback_type == "Compliments":
                st.success("Thank you for your feedback. We will be sure to pass your compliments to our colleague!")
            elif feedback_type == "Feedback":
                st.success("Thank you for your feedback. Please allow us to investigate and get back to you in 5 working days!")
            elif feedback_type == "Complaints":
                st.success("We apologise for the experience. Please allow us to investigate and get back to you in 5 working days!")
        else:
            st.warning("Please enter a message before submitting.")

    if st.button("Return"):
        for key in ["user_info", "messages", "page", "conversation_chain"]:
            if key in st.session_state:
                del st.session_state[key]
                
        st.session_state.page = "Chatbot"  # Set page to "Chatbot"
        return

# Function to gather user information
def gather_user_info():
    st.subheader("Tell us about yourself")
    st.write("To help us give you a better response, please tell us about yourself and why you are reaching out today. (Optional)")
    
    gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"])
    age_group = st.text_input("Age", "", placeholder="Enter your age")
    
    employment_status = st.selectbox("Employment Status", ["Select", "Employed", "Self-employed", "Unemployed", "Student", "Retired"])
    topic = st.selectbox("What would you like to talk about?", ["Select", "Compliments", "Feedback", "Enquiry", "Complaints", "Appeals"])

    col1, col2 = st.columns([1, 6])

    with col1:
        if st.button("Submit"):
            if age_group and not age_group.isdigit():
                st.error("Please enter a valid number for your age.")
            else:
                st.session_state.user_info = {
                    "gender": gender if gender != "Select" else None,
                    "age_group": age_group,
                    "employment_status": employment_status if employment_status != "Select" else None,
                    "topic": topic if topic != "Select" else None
                }
                st.session_state.submitted = True

    with col2:
        st.markdown("<span style='font-size: 14px; color: gray;'>Please ensure app has stopped 'RUNNING' before clicking SUBMIT</span>", unsafe_allow_html=True)

    if "submitted" in st.session_state and st.session_state.submitted:
        st.success("Thank you for providing your information!")

    if topic in ["Compliments", "Feedback", "Complaints"]:
        st.session_state.page = "Feedback"
        return
    else:
        st.session_state.page = "Chatbot"

# Function to create a structured prompt
def create_structured_prompt(user_info, prompt):
    return (
        f"<User Info>\n"
        f"Gender: {user_info.get('gender', 'unknown')}\n"
        f"Age Group: {user_info.get('age_group', 'unknown')}\n"
        f"Employment Status: {user_info.get('employment_status', 'unknown')}\n"
        f"<User Query>\n"
        f"{prompt}\n"
        "<End of User Input>"
    )

# Main function to control page routing and chatbot logic
def main():
    if "page" not in st.session_state:
        st.session_state.page = "Chatbot"
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ("Chatbot", "About Us", "Methodology"))

    # Manually control redirection using session state
    if st.session_state.page == "Feedback":
        handle_feedback()
        return

    if page == "Chatbot":
        st.title("💬 Retirement Advisor")
        st.write("This is an interactive chatbot that provides personalized information about retirement milestones and preparations related to your CPF.")

        # Display the disclaimer
        with st.expander("IMPORTANT NOTICE", expanded=False):
            st.write(""" 
            This web application is a prototype developed for educational purposes only. 
            The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.
            Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. 
            You assume full responsibility for how you use any generated output.
            Always consult with qualified professionals for accurate and personalized advice.
            """)

        #### Password protection: Check if the password is correct
        if not check_password():
            st.stop()  # Stop the app if the password is incorrect

        # Use the OpenAI client with the secret API key
        client = OpenAI(api_key=openai_api_key)

        # Automatically fetch data from all API URLs (no output displayed)
        for api_url in api_urls.values():
            fetch_api_data(api_url)  # Just fetching without displaying any result

        # Set the timezone to Singapore Time
        sgt = pytz.timezone('Asia/Singapore')
     
        # Add a timestamp message
        current_time = datetime.now(sgt).strftime("%H:%M on %d/%m/%Y")
        st.markdown(
             f'<start> <span style="font-size: smaller;">Our responses are based on historical data from <a href="https://data.gov.sg/" target="_blank">data.gov.sg</a> as at {current_time}. For personalized consultations, please <a href="https://www.cpf.gov.sg/appt/oas/form" target="_blank">schedule an appointment</a> at one of our Service Centres.</span> <end>',
    unsafe_allow_html=True)
     
        # Gather user information if not already collected
        if "user_info" not in st.session_state:
            gather_user_info()

        # Create a session state variable to store the chat messages.
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.conversation_chain = []  # Initialize conversation chain

        # Display all messages in the chat
        if "messages" in st.session_state:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Create a chat input field to allow the user to enter a message.
        if prompt := st.chat_input("Ask a question about government services:"):
            # Store and display the current prompt.
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate a structured prompt based on user information (if provided)
            if "user_info" in st.session_state:
                user_info = st.session_state.user_info
                structured_prompt = create_structured_prompt(user_info, prompt)
            else:
                structured_prompt = f"<User Query>\n{prompt}\n<End of User Input>"

            # Store the structured prompt in session state
            st.session_state.conversation_chain.append(structured_prompt)

            # Call the OpenAI model and get the response
            response = client.Completion.create(
                model="gpt-3.5-turbo",
                prompt=structured_prompt,
                max_tokens=100
            )

            # Store and display the response.
            response_text = response['choices'][0]['text'].strip()
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"):
                st.markdown(response_text)

            # Optionally, reset the user input field.
            st.experimental_rerun()

    elif page == "About Us":
        about_us()
    elif page == "Methodology":
        methodology()

# Run the main function
if __name__ == "__main__":
    main()
