import streamlit as st
import requests
import json
import logging
import requests
from jinja2 import Template

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create a logger for the requests library
logger = logging.getLogger("requests")
logger.setLevel(logging.DEBUG)


class SDRTrainer:
    def __init__(self, config):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def train_sdrs(self):
        st.subheader("Talk to AI")
        st.write("Simulate a call to a potential customer")

        name_of_client = st.text_input(
            label="Name your AI?", value="Alex PeterSon"
        )
        rudeness = st.number_input(label="Rudness level of this AI?", value=5)
        phone_number = st.number_input(value=None, label="Your phone number?")
        option = st.selectbox(
            "Who is the AI ?",
            ("Director of human resource", "Director of sales", "Sales Coach"),
        )
        prompt_final = self.get_prompt_final(option, name_of_client, rudeness)
        print(prompt_final)
        json_data = self.get_json_data(name_of_client, rudeness, prompt_final)
        print(json_data)
        submit = st.button("Call me NOW!")
        if submit:
            response = requests.post(
                self.config.url, json=json.loads(json_data), headers=self.headers
            )
            if response.status_code == 201 or response.status_code == 200:
                print(response.json())
                print(response.json()["id"])
                payload_call = self.get_payload_call(response.json()["id"], phone_number)
                print(payload_call)
                response_call = requests.post(
                    self.config.call_url,
                    json=json.loads(payload_call),
                    headers=self.headers,
                )
                if response_call.status_code == 200 or response_call.status_code == 201:
                    st.write("Call successful")
                else:
                    st.write("Call failed")
                    print(f"Status code: {response_call.status_code}")
                    print(f"Error: {response_call.text}")

                st.write("Post successful")
            else:
                st.write("Post failed")
                print(f"Status code: {response.status_code}")
                print(f"Error: {response.text}")
                
    def open_file_and_render_template(file_path, name_of_client, rudeness):
        with open(file_path, "r") as agent_prompt:
            agent_prompt_txt = agent_prompt.read()
            agent_prompt_template = Template(agent_prompt_txt)
            prompt_final = agent_prompt_template.render(
                name=name_of_client,
                rudeness=rudeness,
                geo="New York",
            )
        return prompt_final
    
    def get_prompt_final(self, option, name_of_client, rudeness):

        if option == "Sales Coach":
            prompt_final = SDRTrainer.open_file_and_render_template("local_setup/agent_prompt.txt", name_of_client, rudeness)
        elif option == "Director of human resource":
            prompt_final = SDRTrainer.open_file_and_render_template("local_setup/director_hr_prompt.txt", name_of_client, rudeness)
        else:
            prompt_final = SDRTrainer.open_file_and_render_template("local_setup/director_sales_prompt.txt", name_of_client, rudeness)

        return prompt_final

    def get_json_data(self, name_of_client, rudeness, prompt_final):
        template = Template(self.config.payload_assistant_template)
        json_data = template.render(
            name=name_of_client,
            rudeness=rudeness,
            geo="New York",
            sdr_prompt_final=prompt_final,
        )
        return json_data

    def get_payload_call(self, assistant_id, phone_number):
        template = Template(self.config.payload_call_template)
        payload_call = template.render(
            assistant_id=assistant_id,
            customer_number=int(phone_number),
        )
        return payload_call


class SDRConfig:
    def __init__(self, url, call_url, payload_file, payload_call_file):
        self.url = url
        self.call_url = call_url
        self.payload_file = payload_file
        self.payload_call_file = payload_call_file
        self.payload_assistant_template = SDRConfig.load_payload(payload_file)
        self.payload_call_template = SDRConfig.load_payload(payload_call_file)
        self.api_key = st.secrets["vapi_api_key"]

    @staticmethod
    def load_payload(payload_file):
        with open(payload_file, "r") as file:
            return file.read()


# Usage
URL = "https://api.vapi.ai/assistant"  # Updated URL
CALL_URL = "https://api.vapi.ai/call/phone"  # Updated CALL_URL
payload_call_file = "./local_setup/payload_call.json"
payload_file = "./local_setup/payload_assistant.json"

config = SDRConfig(URL, CALL_URL, payload_file, payload_call_file)

trainer = SDRTrainer(config)
trainer.train_sdrs()
