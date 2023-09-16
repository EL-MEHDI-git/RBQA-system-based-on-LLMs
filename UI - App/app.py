import streamlit as st

import streamlit as st
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space

from trubrics.integrations.streamlit import FeedbackCollector

from chain import create_chain, chatGPT

from db_utils import db_session, insert_question_answer_data, insert_feedback_data, send_payload_to_slack

from db_utils import db_session, insert_question_answer_data, insert_feedback_data

import datetime
import json

import requests
import os
from dotenv import load_dotenv
load_dotenv()


# load environment variables
# convert string to boolean
send_chat_data_to_slack_enabled = os.getenv('SEND_CHAT_DATA_TO_SLACK', False).lower() == 'true' # default to False if not set
slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

persist_chat_data_in_db_enabled = os.getenv('PERSIST_CHAT_DATA_IN_DB', False).lower() == 'true' # default to False if not set


if 'openai_key' not in st.session_state:
    st.session_state['openai_key'] = {}

st.set_page_config(page_title ="🦜🔗 RBQA App", layout='wide')



with st.sidebar:
    st.title('🤗💬 Chat App')
    openai_api_key = st.text_input('Enter your OpenAI API KEY', type='password')
    
    if not openai_api_key.startswith('sk-'):
        st.warning('Please enter your OpenAI API key!', icon='⚠')
    

    elif openai_api_key not in st.session_state["openai_key"].keys():
        #qa_chain = create_chain(openai_api_key)
        st.session_state['openai_key'][openai_api_key] = [create_chain(openai_api_key), chatGPT(openai_api_key)]
    
    model = st.radio("choose your bot : ", ['Talend-Docs','ChatGPT'])
    

input_container = st.container()
colored_header(label='', description='', color_name='blue-30')
response_container = st.container()

# User input
## Function for taking user provided prompt as input
def get_text():
    input_text = st.text_input("Enter your question: ", "", key="input")
    return input_text


if model == 'Talend-Docs':

    # allows to persist any Python object for the duration of the session

    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["I'm TalendChat, How may I help you?"]

    if 'past' not in st.session_state:
        st.session_state['past'] = [""]


    ## Applying the user input box
    with input_container:
        user_input = get_text()


        # Response output
        ## Function that takes user's query as input and produces AI generated responses
    def generate_response(prompt):
        qa_chain = st.session_state['openai_key'][openai_api_key][0]
        return qa_chain(prompt)['result']
            

        ## Conditional display of AI generated responses as a function of user provided prompts
    with response_container:
            
        # to avoid re-executing the last query after giving feedback : user_input != st.session_state['past'][-1]
        if user_input not in [st.session_state['past'][-1],""] and openai_api_key.startswith('sk-'):
            response = generate_response(user_input)
            st.session_state.past.append(user_input)
            st.session_state.generated.append(response)
            

            if send_chat_data_to_slack_enabled:
                timestamp_tz = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%z')
                slack_payload = {'timestamp': timestamp_tz,
                                 'model' : 'Talend-Docs',
                                'content': 'Q: '+ user_input + '\nA: ' +response }
                send_payload_to_slack(slack_webhook_url, slack_payload)

            if persist_chat_data_in_db_enabled:
                timestamp_utc = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                insert_question_answer_data(db_session, timestamp_utc, 'Talend-Docs', user_input, response)

        if st.session_state['generated']:
            if len(st.session_state['past'])==1:
                message(st.session_state['generated'][0], key=str(0))
            else:
                message(st.session_state['generated'][0], key=str(0))
                for i in range(1, len(st.session_state['generated'])):
                    message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
                    message(st.session_state['generated'][i], key=str(i))
                    


    # Feedback

    now = datetime.datetime.now()
    filename = now.strftime("%Y-%m-%d_%H-%M-%S")

    collector = FeedbackCollector()
    feedback = collector.st_feedback(
        feedback_type="thumbs",open_feedback_label="Please provide a description",path=f"./feedback/talend-docs/{filename}.json"
    )

    if feedback:

    # open Json file
        with open(f"./feedback/talend-docs/{filename}.json", "r") as file:
            content = json.load(file)

        # add User query & system answer to "user_response"
        content["user_response"]["User Query"] = user_input
        content["user_response"]["System answer"] = st.session_state['generated'][-1]

        # save modifications
        with open(f"./feedback/talend-docs/{filename}.json", "w") as file:
            json.dump(content, file)

        
        if send_chat_data_to_slack_enabled:
            timestamp_tz = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%z')
            slack_payload = {'timestamp': timestamp_tz, 'model' : 'Talend-Docs', 'content': json.dumps(content["user_response"])}
            send_payload_to_slack(slack_webhook_url, slack_payload)

        if persist_chat_data_in_db_enabled:
            timestamp_utc = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            is_useful = True if content["user_response"]["User satisfaction: thumbs"] == ':1 - thumbs up:' else False if content["user_response"]["User satisfaction: thumbs"] == ':2 - thumbs down:' else None
            comment = content["user_response"]["Please provide a description"]
            insert_feedback_data(db_session, timestamp_utc, 'Talend-Docs', user_input, st.session_state['generated'][-1], is_useful, comment, content["user_response"])
    
    db_session.close()
    
else:
    # allows to persist any Python object for the duration of the session


    if 'generated_GPT' not in st.session_state:
        st.session_state['generated_GPT'] = ["I'm TalendChat, How may I help you?"]

    if 'past_GPT' not in st.session_state:
        st.session_state['past_GPT'] = [""]


    ## Applying the user input box
    with input_container:
        user_input = get_text()


        # Response output
        ## Function that takes user's query as input and produces AI generated responses
    def generate_response(prompt):
        qa = st.session_state['openai_key'][openai_api_key][1]
        return qa.run(user_input = prompt)
            

        ## Conditional display of AI generated responses as a function of user provided prompts
    with response_container:
            
        # to avoid re-executing the last query after giving feedback : user_input != st.session_state['past'][-1]
        if user_input not in [st.session_state['past_GPT'][-1],""] and openai_api_key.startswith('sk-'):
            response = generate_response(user_input)
            st.session_state.past_GPT.append(user_input)
            st.session_state.generated_GPT.append(response)

            if send_chat_data_to_slack_enabled:
                timestamp_tz = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%z')
                slack_payload = {'timestamp': timestamp_tz,
                                 'model' : 'ChatGPT',
                                'content': 'Q: '+ user_input + '\nA: ' +response }
                send_payload_to_slack(slack_webhook_url, slack_payload)

            if persist_chat_data_in_db_enabled:
                timestamp_utc = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                insert_question_answer_data(db_session, timestamp_utc, 'ChatGPT', user_input, response)
        
            
        if st.session_state['generated_GPT']:
            if len(st.session_state['past_GPT'])==1:
                message(st.session_state['generated_GPT'][0], key=str(0))
            else:
                message(st.session_state['generated_GPT'][0], key=str(0))
                for i in range(1, len(st.session_state['generated_GPT'])):
                    message(st.session_state['past_GPT'][i], is_user=True, key=str(i) + '_user')
                    message(st.session_state['generated_GPT'][i], key=str(i))


    # Feedback

    now = datetime.datetime.now()
    filename = now.strftime("%Y-%m-%d_%H-%M-%S")

    collector = FeedbackCollector()
    feedback = collector.st_feedback(
        feedback_type="thumbs",open_feedback_label="Please provide a description",path=f"./feedback/ChatGPT/{filename}.json"
    )

    if feedback:

    # open Json file
        with open(f"./feedback/ChatGPT/{filename}.json", "r") as file:
            content = json.load(file)

        # add User query & system answer to "user_response"
        content["user_response"]["User Query"] = user_input
        content["user_response"]["System answer"] = st.session_state['generated'][-1]

        # save modifications
        with open(f"./feedback/ChatGPT/{filename}.json", "w") as file:
            json.dump(content, file)


        if send_chat_data_to_slack_enabled:
            timestamp_tz = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%z')
            slack_payload = {'timestamp': timestamp_tz, 'model' : 'ChatGPT', 'content': json.dumps(content["user_response"])}
            send_payload_to_slack(slack_webhook_url, slack_payload)

        if persist_chat_data_in_db_enabled:
            timestamp_utc = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            is_useful = True if content["user_response"]["User satisfaction: thumbs"] == ':1 - thumbs up:' else False if content["user_response"]["User satisfaction: thumbs"] == ':2 - thumbs down:' else None
            comment = content["user_response"]["Please provide a description"]
            insert_feedback_data(db_session, timestamp_utc, 'ChatGPT', user_input, st.session_state['generated'][-1], is_useful, comment, content["user_response"])

    db_session.close()