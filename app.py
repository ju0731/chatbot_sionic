import os
from datetime import datetime
import requests
import json
import pandas as pd

import streamlit as st
from streamlit_chat import message

base_url = "https://live-stargate.sionic.im/api"
api_key = st.secrets["api_key"]

#st.header("Chatbot LMM 🤖")
st.header("Chatbot LMM PoC")


if 'generated' not in st.session_state:
    st.session_state['generated'] = []
 
if 'past' not in st.session_state:
    st.session_state['past'] = []
 
# 파일 업로드 함수
# 디렉토리 이름, 파일 imput
def save_uploaded_file(directory, file):
    # 1. 저장할 디렉토리 있는지 확인
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # 2. 파일 저장
    with open(os.path.join(directory, file.name), 'wb') as f:
        f.write(file.getbuffer())
    return st.success('파일 업로드 성공!')

# Post 호출
def postRequest(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

# 채팅 쓰레드 생성
def create_thread(bucket_id):
    url = base_url + "/v1/threads"
    payload = {"bucketId": bucket_id}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-storm-token": api_key
    }

    response = requests.post(url, json=payload, headers=headers)
    print(response.text)

    thread_id = response.json().get("data").get("threadId")
    print(payload)
    print(f"threadId : {thread_id}")

    return thread_id

#
def send_chat(thread_id, question):
    url = base_url + f"/v1/threads/{thread_id}/chats"
    payload = {
        "question": question,
        "isStreaming": True
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-storm-token": api_key
    }

    response = requests.post(url, json=payload, headers=headers, stream=True)

    text = ""

    for chunk in response.iter_lines(decode_unicode=True):
        if chunk:
            try:
                data = json.loads(chunk)
                content = data.get("content")
                is_final_event = data.get("is_final_event")

                if content:
                    print(content, end="", flush=True)
                    text = text + content

                if is_final_event:
                    break
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue
    return text
 

menu = ['직접 입력', '엑셀 업로드']
choice = st.sidebar.selectbox('메뉴', menu)
#menus = ['직접 입력', '엑셀 업로드']
#choices = st.sidebar.selectbox('메뉴s', menus)

if choice == menu[0]:
    with st.form('form', clear_on_submit=True):
        user_input = st.text_input('TestCase 1 : ', '', key='input1', max_chars=100, help='input message < 100')
        #user_input2 = st.text_input('TestCase 2 : ', '', key='input2', max_chars=100, help='input message < 100')
        submitted = st.form_submit_button('Send')

    if submitted and user_input:
        bucket_id = "7194191884929994753"
        thread_id = create_thread(bucket_id)
        #chaturl = "https://ibot.kt.com/client/v1/talk"
        #chatheader = {"Content-Type":"application/json"}
        #chatpayload = {"sessionKey":"gw32_859b7f89da7f4cf3a2a38fcd9d5a317e","channelToken":"777e7a05a5654253976483a94d20454c","query":user_input,"voice":"false","type":"TALK","id":"hjlv0rN9H3jCGkywO6DU","currentTime":"오전 10:47","className":"name","personalData":"false","displayText":"아이케어"}
        #chatres = requests.post(chaturl, headers=chatheader, json=chatpayload)

        #print(chatres.json()["data"]["messages"][0]["message"])
        #st.session_state.generated.append(chatres.json()["data"]["messages"][0]["message"])

        st.session_state.past.append(user_input)

        st.session_state.generated.append(send_chat(thread_id, user_input))
        
        #st.session_state.past.append(user_input2)
        #st.session_state.generated.append(user_input2+" Answer")

    if st.session_state['generated']:
        for i in range(len(st.session_state['generated'])-1, -1, -1):
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))

elif choice == menu[1]:
    st.subheader('csv 파일 업로드 ')

    csv_file = st.file_uploader('CSV 파일 업로드', type=['csv'])
    print(csv_file)
    if csv_file is not None:
        current_time = datetime.now()
        filename = current_time.isoformat().replace(':', '_') + '.csv'

        csv_file.name = filename

        save_uploaded_file('csv', csv_file)

        # csv를 보여주기 위해 pandas 데이터 프레임으로 만들어야한다.
        df = pd.read_csv('csv/'+filename)
        st.dataframe(df)