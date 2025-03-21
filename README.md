# International Shipping Quote Request Agent

This is a multi-agent system that helps collect shipping quote requests through a conversational interface. The system uses Google's Gemini AI model and Langchain to process requests and send the completed form via email using SendGrid.

## Features

- Conversational interface for collecting shipping quote details
- Structured form data collection
- Email notification system
- Powered by Google's Gemini AI

## Prerequisites

- Python 3.8 or higher
- Google API key for Gemini
- SendGrid API key
- Verified sender email address

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
4. Edit the `.env` file with your actual API keys and email address

## Running the Application

To start the application, run:
```bash
streamlit run shipping_quote_agent.py
```

The application will open in your default web browser. You can then interact with the agent to provide shipping quote details.

## Form Structure

The form collects information in the following categories:
1. Shipper & Consignee Details
2. Shipment Details
3. Origin & Destination Details
4. Transportation & Services
5. Additional Information

The agent will guide you through each section and collect the necessary information. 
## APP Link

- https://shhipingquoteagent.streamlit.app/
