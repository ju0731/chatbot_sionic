import os
from datetime import datetime
import requests
import json
import pandas as pd
import csv
import asyncio
import streamlit as st
from streamlit_chat import message

base_url = "https://live-stargate.sionic.im/api"
api_key = st.secrets["api_key"]


#st.header("Chatbot LMM 🤖")
st.header("Chatbot LMM PoC")

q_list = []
r_list = []

if 'generated' not in st.session_state:
    st.session_state['generated'] = []
 
if 'past' not in st.session_state:
    st.session_state['past'] = []
 
# 파일 업로드 함수
# 디렉토리 이름, 파일 input
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

async def process(thread_list, question_list):
    tasks = []
    for i in range(0, len(thread_list)):
        tasks.append(asyncio.create_task(send_chat(thread_list[i], question_list[i])))

    await asyncio.wait(tasks)

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

# 채팅 전송 비동기
async def send_chat(thread_id, question):
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
                    #print(content, end="", flush=True)
                    text = text + content

                if is_final_event:
                    break
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue
    q_list.append(question)
    r_list.append(text)
    return text

def send_chat_sync(thread_id, question):
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
                    #print(content, end="", flush=True)
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

        st.session_state.past.append(user_input)
        st.session_state.generated.append(send_chat_sync(thread_id, user_input))

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

    if st.button('SEND'):
        if csv_file is not None:
            current_time = datetime.now()
            filename = current_time.isoformat().replace(':', '_') + '.csv'

            csv_file.name = filename

            save_uploaded_file('csv', csv_file)

            df = pd.read_csv('csv/'+filename)
            rf = open('csv/'+filename,'rt', encoding='UTF8')
            reader = csv.reader(rf)

            cnt = 0;
            task_thread_list = [];
            task_question_list = [];

            for line in reader:
                if cnt > 0:
                    print(line[0])

                    if line:
                        bucket_id = "7194191884929994753"
                        thread_id = create_thread(bucket_id)
                        task_thread_list.append(thread_id)
                        task_question_list.append(line[0])
                        
                cnt = cnt + 1

            asyncio.run(process(task_thread_list, task_question_list))
                
            rf.close()
            os.remove('csv/'+filename)

            df = pd.DataFrame()
            df['Question'] = q_list
            df['Answer'] = r_list
            st.dataframe(df)
            r_list = []


            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')

            csv = convert_df(df)

            st.download_button(
                "Press to Download",
                csv,
                "result.csv",
                "text/csv",
                key='download-csv'
            )

        else: st.warning('CSV 파일을 업로드 해주세요', icon="⚠️")
        
        