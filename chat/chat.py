import streamlit as st
from streamlit_chat import message

from database import get_redis_connection
from chatbot import RetrievalAssistant, Message

from setup import setup_and_ingest
import openai
openai.api_key = st.secrets["OPENAI_API_KEY"]
# Initialise database

## Initialise Redis connection
redis_client = get_redis_connection()

# Set instruction

# System prompt requiring Question and Year to be extracted from the user
system_prompt = '''
You are a helpful business assistant who knows about the for Foxylight products in great detail. You need to capture a FAQ style Question and any detail user might be seeking about Foxylight product.
If user has already made purchase and seeking further assitant try to capture order ID as well.
Once you have the order ID, say "Looking into your order".

when providing dimentions please 
Example 1:

User: I'd like to know about my order delivery date.

Assistant: Certainly, what is your order ID that I can assit you with?

User: FX-0012344 please.

Assistant: Looking into your order.
'''


### CHATBOT APP

st.set_page_config(
    page_title="Streamlit Chat - Demo",
    page_icon=":robot:"
)

st.title('Foxylight assistant')
st.subheader("I can help you with any query regarding Foxylight products.")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

def query(question):
    response = st.session_state['chat'].ask_assistant(question)
    return response

prompt = st.text_input(f"What do you want to know: ", key="input")

if st.button('Submit', key='generationSubmit'):

    # Initialization
    if 'chat' not in st.session_state:
        st.session_state['chat'] = RetrievalAssistant()
        messages = []
        system_message = Message('system',system_prompt)
        messages.append(system_message.message())
    else:
        messages = []


    user_message = Message('user',prompt)
    messages.append(user_message.message())

    response = query(messages)

    # Debugging step to print the whole response
    #st.write(response)

    st.session_state.past.append(prompt)
    st.session_state.generated.append(response['content'])

if st.session_state['generated']:

    for i in range(len(st.session_state['generated'])-1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')


setup_and_ingest()