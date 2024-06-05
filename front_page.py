import streamlit as st
import requests
import json

import logging
import requests
import streamlit.components.v1 as components
from jinja2 import Template

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a logger for the requests library
logger = logging.getLogger('requests')
logger.setLevel(logging.DEBUG)


class SDRTrainer:
    def __init__(self, config):
        self.config = config
        self.headers = {"Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"}

    # def post_agent(self, phone_number, agent_id):
    #     response = requests.post(self.config.call_url, json=self.config.json_file, headers=self.headers)
    #     if response.status_code == 200:
    #         st.write('Post successful call')
    #         call_payload = {
    #             "recipient_phone_number": phone_number,
    #             "agent_id": agent_id
    #         }
    #         response = requests.post(self.config.call_url, json=call_payload, headers=self.headers)  # Make a call using the agent ID
    #         if response.status_code == 200:
    #             st.write('Call successful')
    #         else:
    #             st.write('Call failed')
    #             print(f'Status code: {response.status_code}')
    #             print(f'Error: {response.text}')
    #     else:
    #         st.write('Post failed')
    #         print(f'Status code: {response.status_code}')
    #         print(f'Error: {response.text}')

    def train_sdrs(self):
        st.subheader('SDR training')
        st.write('This is a simple web app that allows you to train your SDRs')

        name_of_client = st.text_input(label='What name of the person you want to call?', value='Superman')
        job_title = st.text_input(label='What is the job title of the person you are selling to?', value='Director of Pharmacy at CVS')
        rudeness = st.number_input(label='What the rudness level desired?', value=0.5)
        phone_number = st.number_input(value=None, label='What is your phone number?')
        
        
        template = Template(self.config.payload_assistant_template)
        json_data = template.render(name=name_of_client, job_title=job_title, rudeness=rudeness, geo="New York")
        submit = st.button('Call')
        if submit:
            response = requests.post(self.config.url,
                                     json=json.loads(json_data),
                                     headers=self.headers)
            if response.status_code == 201 or response.status_code == 200:
                print(response.json())
                print(response.json()["id"])
                template = Template(self.config.payload_call_template)
                payload_call = template.render(assistant_id=response.json()["id"], customer_number=int(phone_number))
                print(payload_call)
                response_call = requests.post(self.config.call_url,
                                     json=json.loads(payload_call),
                                     headers=self.headers)
                if response_call.status_code == 200 or response_call.status_code == 201:
                    st.write('Call successful')
                else:
                    st.write('Call failed')
                    print(f'Status code: {response_call.status_code}')
                    print(f'Error: {response_call.text}')
                              
                st.write('Post successful')
            else:
                st.write('Post failed')
                print(f'Status code: {response.status_code}')
                print(f'Error: {response.text}')

class SDRConfig:
    def __init__(self, url, call_url, payload_file, payload_call_file):
        self.url = url
        self.call_url = call_url
        self.payload_file = payload_file
        self.payload_call_file = payload_call_file
        self.assistant_id = "f4f8dc10-2b06-4a6d-bfbe-15ac66e3005d"
        self.payload_assistant_template = SDRConfig.load_payload(payload_file)
        self.payload_call_template = SDRConfig.load_payload(payload_call_file)
        self.api_key = "01644691-33bc-44e0-8778-4d369d4d7a5b"

    def load_payload(payload_file):
        with open(payload_file, 'r') as file:
            return file.read()


# Usage
URL = "https://api.vapi.ai/assistant"  # Updated URL
CALL_URL = "https://api.vapi.ai/call/phone"  # Updated CALL_URL
payload_call_file = './local_setup/payload_call.json'
payload_file = './local_setup/payload_assistant.json'

config = SDRConfig(URL, CALL_URL, payload_file, payload_call_file)

trainer = SDRTrainer(config)
trainer.train_sdrs()


