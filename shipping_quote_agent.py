import os
from typing import Dict, List
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import json

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Define the shipping quote form structure
SHIPPING_QUOTE_FORM = {
    "shipper_consignee": {
        "company_name": "",
        "contact_person": "",
        "email": "",
        "phone_number": "",
        "pickup_address": "",
        "delivery_address": "",
        "consignee_name_address": ""
    },
    "shipment_details": {
        "type_of_shipment": "",
        "container_type": "",
        "number_of_containers": "",
        "cargo_type": "",
        "hs_code": "",
        "weight": "",
        "volume": "",
        "number_of_packages": "",
        "packaging_type": ""
    },
    "origin_destination": {
        "port_of_loading": "",
        "port_of_discharge": "",
        "customs_clearance_required": "",
        "special_handling": ""
    },
    "transportation_services": {
        "door_to_door": "",
        "port_to_port": "",
        "customs_brokerage": "",
        "inland_transportation": "",
        "warehousing": ""
    },
    "additional_info": {
        "expected_date": "",
        "incoterms": "",
        "insurance_required": "",
        "preferred_carrier": "",
        "special_instructions": ""
    }
}

class ShippingQuoteAssistant:
    def __init__(self):
        self.form_data = SHIPPING_QUOTE_FORM.copy()
        self.current_section = "shipper_consignee"
        self.chat = model.start_chat(history=[])
        self.email_sent = False  # Track if email has been sent
        
        # Set up the initial context
        self.chat.send_message("""You are a helpful shipping quote assistant. Help users fill out their shipping quote form by asking relevant questions and collecting information.
        The form has the following sections:
        1. Shipper & Consignee Details
        2. Shipment Details
        3. Origin & Destination Details
        4. Transportation & Services
        5. Additional Information
        
        Ask questions one at a time and keep track of which sections are completed. When all information is collected, offer to send the form via email.
        
        When you receive information, respond with a confirmation and then ask for the next piece of information.
        """)

    def update_form(self, section: str, field: str, value: str) -> str:
        """Updates the form with the provided information"""
        if section in self.form_data and field in self.form_data[section]:
            self.form_data[section][field] = value
            return f"Updated {field} in {section} with {value}"
        return f"Could not update {field} in {section}"

    def extract_information(self, message: str) -> List[tuple]:
        """Extract information from user message and return list of (section, field, value) tuples"""
        # Define patterns for information extraction
        patterns = {
            "shipper_consignee": {
                "company_name": r"company name is (.*?)(?=\s+and\s+I'm|$)",
                "contact_person": r"I'm\s+(.*?)(?=\s+and|$)",
                "email": r"email is\s+(.*?)(?=\s+and|$)",
                "phone_number": r"phone is\s+([+\d-]+)",
                "pickup_address": r"pickup address is\s+(.*?)(?=\.\s+The|$)",
                "delivery_address": r"delivery address is\s+(.*?)(?=\.\s+The|$)",
                "consignee_name_address": r"consignee is\s+(.*?)(?=\.\s+|$)"
            },
            "shipment_details": {
                "type_of_shipment": r"ship (\d+) (\d+)' containers",
                "container_type": r"(\d+)' containers",
                "number_of_containers": r"(\d+) containers",
                "cargo_type": r"cargo type is ([^,]+)",
                "hs_code": r"HS code is ([^,]+)",
                "weight": r"weight is ([^,]+)",
                "volume": r"volume is ([^,]+)",
                "number_of_packages": r"(\d+) pallets",
                "packaging_type": r"(\d+) pallets"
            },
            "origin_destination": {
                "port_of_loading": r"Port of loading is ([^,]+)",
                "port_of_discharge": r"port of discharge is ([^,]+)",
                "customs_clearance_required": r"customs clearance",
                "special_handling": r"special handling for ([^,]+)"
            },
            "transportation_services": {
                "door_to_door": r"door-to-door service",
                "port_to_port": r"port-to-port",
                "customs_brokerage": r"customs brokerage",
                "inland_transportation": r"inland transportation",
                "warehousing": r"warehousing"
            },
            "additional_info": {
                "expected_date": r"ship this on ([^,]+)",
                "incoterms": r"using ([^,]+) terms",
                "insurance_required": r"need insurance",
                "preferred_carrier": r"prefer ([^,]+) as our carrier",
                "special_instructions": r"Please handle with care as ([^,]+)"
            }
        }

        updates = []
        for section, fields in patterns.items():
            for field, pattern in fields.items():
                import re
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    value = match.group(1) if len(match.groups()) > 0 else "Yes"
                    updates.append((section, field, value))
        return updates

    def send_email(self, recipient_email: str) -> str:
        """Sends the completed form via email using SendGrid"""
        try:
            # Get configuration
            api_key = os.getenv('SENDGRID_API_KEY')
            from_email = os.getenv('SENDGRID_FROM_EMAIL')
            
            # Validate configuration
            if not api_key:
                return "Error: SendGrid API key is missing. Please check your .env file"
            if not from_email:
                return "Error: Sender email is missing. Please check your .env file"
            if not recipient_email:
                return "Error: Recipient email is required"

            # Create message with form data
            email_content = "Shipping Quote Request Details:\n\n"
            for section, fields in self.form_data.items():
                email_content += f"\n{section.replace('_', ' ').title()}:\n"
                for field, value in fields.items():
                    if value:  # Only include non-empty fields
                        email_content += f"{field.replace('_', ' ').title()}: {value}\n"
            
            # Print debug info (remove in production)
            print(f"Sending email to: {recipient_email}")
            print(f"From email: {from_email}")
            print(f"API Key present: {'Yes' if api_key else 'No'}")
            
            message = Mail(
                from_email=from_email,
                to_emails=recipient_email,
                subject='Shipping Quote Request',
                plain_text_content=email_content
            )
            
            # Send email
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                return f"✉️ Email sent successfully to {recipient_email}"
            else:
                return f"❌ Error sending email. Status code: {response.status_code}"
            
        except Exception as e:
            print(f"Error details: {str(e)}")  # Debug info
            return f"❌ Error sending email: {str(e)}"

    def process_message(self, user_message: str) -> str:
        """Process user message and return response"""
        try:
            # Check for various email sending phrases
            email_triggers = [
                "send email to",
                "send the form to",
                "send quote to",
                "send to",
                "email to",
                "please send",
                "send email",
                "send form"
            ]
            
            if any(trigger in user_message.lower() for trigger in email_triggers):
                # Try to extract email from the current message
                import re
                # Look for email pattern
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
                
                if email_match:
                    # Use email found in message
                    recipient_email = email_match.group(0)
                else:
                    # Use email from form data
                    recipient_email = self.form_data["shipper_consignee"]["email"]
                    
                if not recipient_email:
                    return "I don't have an email address. Please provide an email address to send the quote to."
                
                return self.send_email(recipient_email)
            
            # Extract and update form data
            updates = self.extract_information(user_message)
            for section, field, value in updates:
                self.update_form(section, field, value)
            
            # Get AI response
            response = self.chat.send_message(user_message)
            return response.text
        except Exception as e:
            return f"Error processing message: {str(e)}"

def main():
    st.title("International Shipping Quote Request")
    
    # Initialize session state
    if "assistant" not in st.session_state:
        st.session_state.assistant = ShippingQuoteAssistant()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display environment status in sidebar (keeping only the essential info)
    with st.sidebar:
        st.subheader("Environment Status")
        sendgrid_key = os.getenv("SENDGRID_API_KEY")
        sender_email = os.getenv("SENDGRID_FROM_EMAIL")
        st.write(f"SendGrid API Key: {'Configured' if sendgrid_key else 'Not Configured'}")
        st.write(f"Sender Email: {'Configured' if sender_email else 'Not Configured'}")
        
        # Removed the form data display from sidebar

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Please provide your shipping quote request details"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            response = st.session_state.assistant.process_message(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 