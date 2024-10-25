import streamlit as st
from helper_functions.utility import check_password
import json
import requests
from openai import OpenAI
from datetime import datetime
import pandas as pd
import altair as alt


# Retrieve the API key from Streamlit's secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]
 

# Hardcoded API URLs
api_urls = {
    "Number of CPF Members & Net Balances by Age Group & Gender as at End of Year": "https://api-production.data.gov.sg/v2/public/api/collections/46/metadata",
    "Retirement withdrawals, Annual": "https://api-production.data.gov.sg/v2/public/api/collections/43/metadata"
     "Full Retirement Sum": "https://data.gov.sg/api/action/datastore_search?resource_id=d_b212dff55c98a4c0b3d3d850bf744ad7"
     "Yearly amount of monthly payout under Retirement Sum Scheme": "https://data.gov.sg/api/action/datastore_search?resource_id=d_c055f39619d2e8a8e0ddf87823b1066d"
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
    st.write(
        "This project aims to create a government chatbot that provides factual information to users. "
        "The chatbot pulls data from various government sources to answer queries."
    )

# Methodology page
def methodology():
    st.title("Methodology")
    st.write(
        "The chatbot retrieves information based on user queries and fetches data from predefined API sources. "
        "The implementation uses OpenAI's language model to process the user's questions and provide accurate responses."
    )

# Function to handle compliments, feedback, and complaints
def handle_feedback():
    st.title("Feedback")
    feedback_type = st.radio("Select the type of feedback:", 
                              ("Select", "Compliments", "Feedback", "Complaints"), 
                              index=0)  # Default to the first option "Select"

    feedback_message = st.text_area("Please enter your message:")
    
    # Add a slider for customer satisfaction rating (1 to 5 stars)
    rating = st.slider("Please rate your experience:", 
                       min_value=1, max_value=5, value=1, step=1)  # Default to 1 star
    
    # Display the selected stars
    stars = "⭐" * rating  # Create a string of stars based on the rating
    st.markdown(f"**Your Rating:** {stars}")

    # Display interval labels
    st.markdown(""" 
        ⭐ - Very Dissatisfied, 
        ⭐⭐ - Dissatisfied, 
        ⭐⭐⭐ - Neutral, 
        ⭐⭐⭐⭐ - Satisfied, 
        ⭐⭐⭐⭐⭐ - Very Satisfied
    """)

    # Check if the feedback has been submitted
    if st.button("Submit"):
        # Only show success message if feedback_message is not empty
        if feedback_message:
            if feedback_type == "Compliments":
                st.success("Thank you for your feedback. We will be sure to pass your compliments to our colleague!")
            elif feedback_type == "Feedback":
                st.success("Thank you for your feedback. Please allow us to investigate and get back to you in 5 working days!")
            elif feedback_type == "Complaints":
                st.success("We apologise for the experience. Please allow us to investigate and get back to you in 5 working days!")
        else:
            st.warning("Please enter a message before submitting.")  # Alert user if message is empty

    if st.button("Return"):
        # Clear session state attributes to reset the session
        for key in ["user_info", "messages", "page", "conversation_chain"]:
            if key in st.session_state:
                del st.session_state[key]  # Remove the keys to reset the session
                
        st.session_state.page = "Chatbot"  # Set page to "Chatbot"
        return  # Exit the function to redirect to the Chatbot page immediately

# Function to gather user information
def gather_user_info():
    st.subheader("Tell us about yourself")
    st.write("To help us give you a better personalised response, please tell us about yourself and why you are reaching out today. (Optional)")
    
    gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"])
    age_group = st.text_input("Age", "", placeholder="Enter your age")
    
    employment_status = st.selectbox("Employment Status", ["Select", "Employed", "Self-employed", "Unemployed", "Student", "Retired"])
    topic = st.selectbox("What would you like to talk about?", ["Select", "Compliments", "Feedback", "Enquiry", "Complaints", "Appeals"])

    # Create two columns for the button and the placeholder message
    col1, col2 = st.columns([1, 6])  # Adjust the ratio as needed

    with col1:
        if st.button("Submit"):
            # Check if age_group is not empty and is numeric
            if age_group and not age_group.isdigit():
                st.error("Please enter a valid number for your age.")  # Show error message if age is invalid
            else:
                # If valid, proceed to save the information
                st.session_state.user_info = {
                    "gender": gender if gender != "Select" else None,
                    "age_group": age_group,
                    "employment_status": employment_status if employment_status != "Select" else None,
                    "topic": topic if topic != "Select" else None
                }
                st.session_state.submitted = True  # Set the flag to True

    with col2:
        # Add a placeholder message next to the submit button
        st.markdown("<span style='font-size: 14px; color: gray;'>Please ensure app has stopped 'RUNNING' before clicking SUBMIT</span>", unsafe_allow_html=True)

    # Display success message below the button if it has been submitted
    if "submitted" in st.session_state and st.session_state.submitted:
        st.success("Thank you for providing your information!")  # Position below the button

    # Redirect to feedback page only if a feedback option is selected
    if topic in ["Compliments", "Feedback", "Complaints"]:
        st.session_state.page = "Feedback"
        return  # Exit the function to redirect to the Feedback page immediately
    else:
        st.session_state.page = "Chatbot"  # Reset if not redirecting

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

    # #### Password protection: Check if the password is correct
    # if not check_password():
    #     st.stop()  # Stop the app if the password is incorrect

    # Initialize page in session state if not already set
    if "page" not in st.session_state:
        st.session_state.page = "Chatbot"
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ("Chatbot", "About Us", "Methodology"))

    # Manually control redirection using session state
    if st.session_state.page == "Feedback":
        handle_feedback()
        return

    if page == "Chatbot":
        # Show title and description.
        st.title("💬 Retirement Advisor")
        st.write(
            "This is an interactive chatbot that provides personalized information about retirement milestones and preparations related to your CPF."
        )

        #### Password protection: Check if the password is correct
        if not check_password():
            st.stop()  # Stop the app if the password is incorrect

        # Display the disclaimer
        with st.expander("IMPORTANT NOTICE", expanded=False):
            st.write(""" 
            This web application is a prototype developed for educational purposes only. 
            The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.
            Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. 
            You assume full responsibility for how you use any generated output.
            Always consult with qualified professionals for accurate and personalized advice.
            """)

        # Use the OpenAI client with the secret API key
        client = OpenAI(api_key=openai_api_key)
 
        # Automatically fetch data from all API URLs (no output displayed)
        for api_url in api_urls.values():
            fetch_api_data(api_url)  # Just fetching without displaying any result

        # Add a timestamp message
        current_time = datetime.now().strftime("%H:%M on %d/%m/%Y")
        st.markdown(f'<start> Responses are based on <a href="https://data.gov.sg/" target="_blank">"https://data.gov.sg/"</a> as at {current_time} <end>', unsafe_allow_html=True)

        # Gather user information if not already collected
        if "user_info" not in st.session_state:
            gather_user_info()
        else:
            # User information has already been collected, no need to gather again
            pass

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
                # If no user info is provided, fallback to a basic prompt
                structured_prompt = f"<User Query>\n{prompt}\n<End of User Input>"

            # Store the structured prompt in session state
            st.session_state.messages.append({"role": "user", "content": structured_prompt})

            # Add structured prompt to the conversation chain
            st.session_state.conversation_chain.append(structured_prompt)

            # Generate a response using the OpenAI API with a factual setting.
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages] + 
                         [{"role": "assistant", "content": step} for step in st.session_state.conversation_chain],
                temperature=0,  # Set temperature to 0 for factual responses
            )

            # Extract and display the response
            answer = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": answer})

            with st.chat_message("assistant"):
                st.markdown(answer)

            # Add assistant response to the conversation chain to continue sequential processing
            st.session_state.conversation_chain.append(answer)

    elif page == "About Us":
        about_us()
    elif page == "Methodology":
        methodology()

if __name__ == "__main__":
    main()
