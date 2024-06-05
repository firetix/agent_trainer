import streamlit as st
import requests
import json

class SDRTrainer:
    def __init__(self, config):
        self.config = config

    def post_agent(self, phone_number):
        response = requests.post(self.config.url, json=self.config.json_file)
        if response.status_code == 200:
            st.write('Post successful call')
            agent_id = response.json()["agent_id"]  # Get the agent ID from the response
            call_payload = {
                "recipient_phone_number": phone_number,
                "agent_id": agent_id
            }
            response = requests.post(self.config.call_url, json=call_payload)  # Make a call using the agent ID
            if response.status_code == 200:
                st.write('Call successful')
            else:
                st.write('Call failed')
                print(f'Status code: {response.status_code}')
                print(f'Error: {response.text}')
        else:
            st.write('Post failed')
            print(f'Status code: {response.status_code}')
            print(f'Error: {response.text}')
        
    def train_sdrs(self):
        st.subheader('SDR training')
        st.write('This is a simple web app that allows you to train your SDRs')

        # job_title = st.text_input(label='What is the job title of the person you are selling to?')
        # rudeness = st.number_input(label='What the rudness level desired?')
        # geo = st.text_input(label='Where are you located?')
        phone_number = st.number_input(label='What is your phonenumber?')

        submit = st.button('Call')
        if submit:
            response = requests.post(self.config.call_url, json=self.config.json_file)
            if response.status_code == 200:
                # self.post_agent(phone_number)  # Create an agent and make a call
                st.write('Post successful')
            else:
                st.write('Post failed')
                print(f'Status code: {response.status_code}')
                print(f'Error: {response.text}')

class SDRConfig:
    def __init__(self, url, call_url, payload_file):
        self.url = url
        self.call_url = call_url
        self.payload_file = payload_file
        self.assistant_id = "f4f8dc10-2b06-4a6d-bfbe-15ac66e3005d"
        self.load_payload()

    def load_payload(self):
        with open(self.payload_file, 'r') as file:
            self.json_file = json.load(file)

# Usage
URL = "http://vapi.ai/agent"  # Updated URL
CALL_URL = "http://vapi.ai/call"  # Updated CALL_URL
payload_file = './local_setup/payload.json'

config = SDRConfig(URL, CALL_URL, payload_file)

trainer = SDRTrainer(config)
trainer.train_sdrs()
