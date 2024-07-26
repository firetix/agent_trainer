import streamlit as st
import requests
import json
import logging
import requests
from jinja2 import Template
import time 
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create a logger for the requests library
logger = logging.getLogger("requests")
logger.setLevel(logging.DEBUG)


async def post_data(session, url, payload=None, headers=None):
    async with session.post(url, json=payload, headers=headers) as response:
        return await response.json()
    
class SDRTrainer:
    def __init__(self, config):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        
    def poll_until_ended(call_id, headers):
        url = f"https://api.vapi.ai/call/{call_id}"
        while True:
            response = requests.request("GET", url, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                if response_data["status"] == "ended" :
                    if "ended_reason" in response_data and response_data["ended_reason"] != "unknown-error":
                        continue
                    return response_data
            else:
                print(f'Error: {response.status_code}')
            time.sleep(5)  # Wait for 5 seconds before making the next request

    async def train_sdrs(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            st.subheader("RAG-n-DIAL")
            st.write("Phone call confgiuration")

            name_of_client = st.text_input(
                label="Name your AI?", value="Simo Rachidi"
            )
            
            
            option = st.selectbox(
                "What profession does he have?",
                ("Sales Coach", "Director of human resource", "Director of sales"),
            )
            profession_caption = st.caption("")
            
            
            option_sales_script = st.selectbox(
                "What sales script do you want to follow?",
                ("Cold Call Script for Phone Calls", "Follow Up Script for Phone Calls"),
            )
            st.caption("""This describe to the agent how to evaluate your call for example.""")
            sales_script_caption = st.caption("")
            
            rudeness = st.number_input(label="Rudness level of this AI?", value=5)
            st.caption("Rudeness level should be between 1 to 10. if the rudness is at 0 then be very nice, if the rudness is 10 then you act like you don't have time and are not interested")
            phone_number = st.number_input(value=1234567890, label="Where should the AI call you?")
            prompt_final = self.get_prompt_final(option, name_of_client, rudeness)
            evaluation_prompt = self.get_prompt_final(option_sales_script, name_of_client, rudeness)
            sales_script_caption.caption(evaluation_prompt)
            profession_caption.caption(prompt_final)
            print(evaluation_prompt)
            json_data = self.get_json_data(name_of_client, rudeness, prompt_final,evaluation_prompt)
            print(json_data)
            st.divider()
            submit = st.button("Call me NOW!")
            if submit:
                if not phone_number or phone_number == 1234567890:
                    st.warning("Please enter a phone number")
                    return
                
                response = requests.post(
                    self.config.url, json=json.loads(json_data), headers=self.headers
                )
                
                if response.status_code == 201 or response.status_code == 200:
                    # print(response.json())
                    # print(response.json()["id"])
                    payload_call = self.get_payload_call(response.json()["id"], phone_number)
                    print(payload_call)

                    tasks.append(asyncio.ensure_future(post_data(session, self.config.call_url, json.loads(payload_call),self.headers)))
                    st.write("Call successful")
                    placeholder = st.empty()
                    for task in asyncio.as_completed(tasks):
                        response_call = await task
                        placeholder.write(f"Received data: {response_call}")
                        evaluation = SDRTrainer.poll_until_ended(response_call["id"], self.headers)
                        # print(evaluation)
                        st.divider()
                        st.title("Evaluation Summary")
                        if "analysis" in evaluation:
                            st.caption(evaluation["analysis"]["summary"])
                            st.title("Specific Evaluation")
                            if "successEvaluation" in evaluation["analysis"]:
                                st.caption(evaluation["analysis"]["successEvaluation"])
                    
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
        elif option == "Cold Call Script for Phone Calls":
            prompt_final = SDRTrainer.open_file_and_render_template("local_setup/sales_scripts/cold_call_script_phone_call.txt", name_of_client, rudeness)
        elif option == "Follow Up Script for Phone Calls":
            prompt_final = SDRTrainer.open_file_and_render_template("local_setup/sales_scripts/follow_up_script_phone_call.txt",  name_of_client, rudeness)
        else:
            prompt_final = SDRTrainer.open_file_and_render_template("local_setup/director_sales_prompt.txt", name_of_client, rudeness)

        return prompt_final

    def get_json_data(self, name_of_client, rudeness, prompt_final,evaluation_prompt):
        template = Template(self.config.payload_assistant_template)
        json_data = template.render(
            name=name_of_client,
            rudeness=rudeness,
            geo="New York",
            sdr_prompt_final=prompt_final,
            evaluation_prompt=evaluation_prompt
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
asyncio.run(trainer.train_sdrs())
