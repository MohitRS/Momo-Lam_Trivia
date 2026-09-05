import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime
import pytz

st.set_page_config(page_title="Lin & Mohit Hub", page_icon="🤍", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Poppins:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; background-color: #121212; color: #EAEAEA; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: #F4C2C2 !important; }
    .stButton>button { background-color: transparent; border: 1px solid #F4C2C2; color: #F4C2C2; border-radius: 8px; font-weight: 500; transition: 0.2s;}
    .stButton>button:hover { background-color: #F4C2C2; color: #121212; border: 1px solid #F4C2C2; }
    div[data-testid="stExpander"] { background-color: rgba(255,255,255,0.03); border: 1px solid rgba(244, 194, 194, 0.2); border-radius: 10px; }
    .note-box { background-color: rgba(244, 194, 194, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #F4C2C2; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
sheet_url = "https://docs.google.com/spreadsheets/d/17wg47-a_YxLoLs5dIN1us56qaK3s3CMVGNrr-FlEh6U/edit?gid=0#gid=0"

try:
    df_trivia = conn.read(spreadsheet=sheet_url, worksheet="Trivia", ttl=0).fillna('').astype(str)
    df_fridge = conn.read(spreadsheet=sheet_url, worksheet="Fridge", ttl=0).fillna('').astype(str)
except Exception as e:
    st.error(f"Database error: {e}")
    st.info("Did you remember to create the 'Fridge' tab in your Google Sheet?")
    st.stop()

# --- SIDEBAR NAVIGATION & LOGIN ---
with st.sidebar:
    st.title("🤍 Our Space")
    user = st.radio("Who is logging in?", ["Select...", "Mohit 🎾", "Lin 🍵"])
    st.markdown("---")
    page = st.radio("Navigation", ["🏠 Dashboard", "💌 Digital Fridge", "🎯 Trivia Arena"])

if user == "Select...":
    st.title("Welcome Home.")
    st.write("Please select your profile in the sidebar menu to unlock the app.")
    st.stop()

partner = "Lin 🍵" if user == "Mohit 🎾" else "Mohit 🎾"

# --- PAGE 1: DASHBOARD ---
if page == "🏠 Dashboard":
    st.title(f"Welcome back, {user.split()[0]}")
    st.write("Here is the current state of us.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Time Zones")
        melb_tz = pytz.timezone('Australia/Melbourne')
        gz_tz = pytz.timezone('Asia/Shanghai')
        
        st.write(f"**Werribee:** {datetime.datetime.now(melb_tz).strftime('%I:%M %p')}")
        st.write(f"**Guangzhou:** {datetime.datetime.now(gz_tz).strftime('%I:%M %p')}")
    
    with col2:
        st.subheader("Countdown")
        # Update this to her actual grad date when you know it!
        grad_date = datetime.date(2026, 12, 15) 
        days_left = (grad_date - datetime.date.today()).days
        st.metric(label="Days until December Grad", value=f"{days_left} Days")

    st.markdown("---")
    st.subheader("Trivia Tally")
    mohit_score = len(df_trivia[(df_trivia['Guesser'] == "Mohit 🎾") & (df_trivia['Status'] == 'Correct')])
    lin_score = len(df_trivia[(df_trivia['Guesser'] == "Lin 🍵") & (df_trivia['Status'] == 'Correct')])
    
    c1, c2 = st.columns(2)
    c1.metric("Mohit's Score", mohit_score)
    c2.metric("Lin's Score", lin_score)

# --- PAGE 2: DIGITAL FRIDGE ---
elif page == "💌 Digital Fridge":
    st.title("The Digital Fridge")
    st.write("Leave a note, a joke, or a reminder.")
    
    # Form to add a new note
    with st.form("new_note", clear_on_submit=True):
        new_msg = st.text_area("Write something sweet:")
        submitted = st.form_submit_button("Stick to Fridge")
        if submitted and new_msg:
            timestamp = datetime.datetime.now(pytz.timezone('Australia/Melbourne')).strftime("%b %d, %I:%M %p")
            new_row = pd.DataFrame([{'Author': user, 'Message': new_msg, 'Timestamp': timestamp}])
            df_fridge = pd.concat([new_row, df_fridge], ignore_index=True) # Put new notes at the top
            conn.update(spreadsheet=sheet_url, worksheet="Fridge", data=df_fridge)
            st.success("Note added!")
            st.rerun()

    st.markdown("---")
    
    # Display notes
    if df_fridge.empty or df_fridge['Message'].iloc[0] == '':
        st.write("The fridge is empty! Leave the first note.")
    else:
        for index, row in df_fridge.iterrows():
            if str(row['Message']).strip() != '':
                st.markdown(f"""
                <div class="note-box">
                    <strong>{row['Author']}</strong> <em>({row['Timestamp']})</em><br>
                    {row['Message']}
                </div>
                """, unsafe_allow_html=True)

# --- PAGE 3: TRIVIA ARENA ---
elif page == "🎯 Trivia Arena":
    st.title("Trivia Arena")
    tab1, tab2 = st.tabs(["🎯 Play", "🤔 Create"])
    
    with tab1:
        st.subheader(f"Waiting from {partner}")
        pending_mask = (df_trivia['Creator'] == partner) & (df_trivia['Status'] == 'Unanswered')
        pending_questions = df_trivia[pending_mask]
        
        if pending_questions.empty:
            st.info(f"You're all caught up! {partner} hasn't left any new questions.")
        else:
            for index, row in pending_questions.iterrows():
                with st.expander(f"Question: {row['Question']}", expanded=True):
                    guess = st.text_input("Type your guess to reveal the answer:", key=f"guess_{index}")
                    
                    if guess:
                        st.markdown(f"**Their Exact Answer:** `{row['Correct_Answer']}`")
                        st.write("Were you close enough?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Nailed it", key=f"right_{index}", use_container_width=True):
                                df_trivia.at[index, 'Status'] = 'Correct'
                                df_trivia.at[index, 'Guesser'] = user
                                df_trivia.at[index, 'Guessed_Answer'] = guess
                                conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df_trivia)
                                st.balloons()
                                st.rerun()
                        with c2:
                            if st.button("❌ Not quite", key=f"wrong_{index}", use_container_width=True):
                                df_trivia.at[index, 'Status'] = 'Incorrect'
                                df_trivia.at[index, 'Guesser'] = user
                                df_trivia.at[index, 'Guessed_Answer'] = guess
                                conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df_trivia)
                                st.rerun()

    with tab2:
        st.subheader("Stump your partner")
        new_q = st.text_input("The Question:")
        new_a = st.text_input("The Answer:")
        
        if st.button("Send to Database", use_container_width=True):
            if new_q and new_a:
                new_row = pd.DataFrame([{'Creator': user, 'Question': new_q, 'Correct_Answer': new_a, 'Guesser': '', 'Guessed_Answer': '', 'Status': 'Unanswered'}])
                df_trivia = pd.concat([df_trivia, new_row], ignore_index=True)
                conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df_trivia)
                st.success("Question submitted!")
                st.rerun()
