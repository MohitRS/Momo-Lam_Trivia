import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Us: Trivia", page_icon="🤍", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Poppins:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; background-color: #121212; color: #EAEAEA; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: #F4C2C2 !important; }
    .stButton>button { background-color: transparent; border: 1px solid #F4C2C2; color: #F4C2C2; border-radius: 8px; font-weight: 500; transition: 0.2s;}
    .stButton>button:hover { background-color: #F4C2C2; color: #121212; border: 1px solid #F4C2C2; }
    div[data-testid="stExpander"] { background-color: rgba(255,255,255,0.03); border: 1px solid rgba(244, 194, 194, 0.2); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🤍 How Well Do You Know Us?")
st.write("The transcontinental trivia battle. Werribee vs. Guangzhou.")

conn = st.connection("gsheets", type=GSheetsConnection)
sheet_url = "https://docs.google.com/spreadsheets/d/17wg47-a_YxLoLs5dIN1us56qaK3s3CMVGNrr-FlEh6U/edit?gid=0#gid=0"

try:
    df = conn.read(spreadsheet=sheet_url, worksheet="Trivia", ttl=0)
    # BUG FIX: Force pandas to treat everything as strings so it doesn't crash on empty columns
    df = df.fillna('').astype(str) 
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

# --- USER LOGIN ---
user = st.radio("Who is playing right now?", ["Select...", "Mohit 🎾", "Lin 🍵"], horizontal=True)

if user != "Select...":
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🎯 Play", "🤔 Create", "🏆 Scoreboard"])
    
    partner = "Lin 🍵" if user == "Mohit 🎾" else "Mohit 🎾"

    # --- TAB 1: ANSWER QUESTIONS (UPGRADED) ---
    with tab1:
        st.subheader(f"Waiting from {partner}")
        
        pending_mask = (df['Creator'] == partner) & (df['Status'] == 'Unanswered')
        pending_questions = df[pending_mask]
        
        if pending_questions.empty:
            st.info(f"You're all caught up! {partner} hasn't left any new questions for you yet.")
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
                                df.at[index, 'Status'] = 'Correct'
                                df.at[index, 'Guesser'] = user
                                df.at[index, 'Guessed_Answer'] = guess
                                conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df)
                                st.balloons()
                                st.rerun()
                        with c2:
                            if st.button("❌ Not quite", key=f"wrong_{index}", use_container_width=True):
                                df.at[index, 'Status'] = 'Incorrect'
                                df.at[index, 'Guesser'] = user
                                df.at[index, 'Guessed_Answer'] = guess
                                conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df)
                                st.rerun()

    # --- TAB 2: ASK A QUESTION ---
    with tab2:
        st.subheader("Stump your partner")
        new_q = st.text_input("The Question:")
        new_a = st.text_input("The Answer:")
        
        if st.button("Send to Database", use_container_width=True):
            if new_q and new_a:
                new_row = pd.DataFrame([{
                    'Creator': user, 'Question': new_q, 'Correct_Answer': new_a,
                    'Guesser': '', 'Guessed_Answer': '', 'Status': 'Unanswered'
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df)
                st.success("Question submitted! It will be waiting for them next time they log in.")
                st.rerun()
            else:
                st.warning("Please fill out both fields.")

    # --- TAB 3: SCOREBOARD ---
    with tab3:
        st.subheader("The Tally")
        
        mohit_score = len(df[(df['Guesser'] == "Mohit 🎾") & (df['Status'] == 'Correct')])
        lin_score = len(df[(df['Guesser'] == "Lin 🍵") & (df['Status'] == 'Correct')])
        
        col1, col2 = st.columns(2)
        col1.metric("Mohit's Score", mohit_score)
        col2.metric("Lin's Score", lin_score)
        
        st.write("---")
        st.write("**Recent Activity:**")
        history = df[df['Status'] != 'Unanswered'].tail(5)
        if history.empty:
            st.write("No questions answered yet. Make the first move!")
        else:
            for _, row in history.iterrows():
                icon = "✅" if row['Status'] == 'Correct' else "❌"
                st.write(f"{icon} **{row['Guesser']}** guessed '{row['Guessed_Answer']}' to '{row['Question']}'")
