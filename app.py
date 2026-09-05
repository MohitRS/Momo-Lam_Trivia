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
    .stButton>button { background-color: transparent; border: 1px solid #F4C2C2; color: #F4C2C2; border-radius: 30px; }
    .stButton>button:hover { background-color: #F4C2C2; color: #121212; }
</style>
""", unsafe_allow_html=True)

st.title("🤍 How Well Do You Know Us?")
st.write("The transcontinental trivia battle. Werribee vs. Guangzhou.")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the data (ttl=0 ensures it doesn't cache, giving you real-time updates)
try:
    df = conn.read(worksheet="Trivia", ttl=0)
except Exception as e:
    st.error("Waiting for database connection...")
    st.stop()

# --- USER LOGIN ---
user = st.radio("Who is playing right now?", ["Select...", "Mohit 🎾", "Lin 🍵"], horizontal=True)

if user != "Select...":
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🎯 Answer Questions", "🤔 Ask a Question", "🏆 Scoreboard"])
    
    partner = "Lin 🍵" if user == "Mohit 🎾" else "Mohit 🎾"

    # --- TAB 1: ANSWER QUESTIONS ---
    with tab1:
        st.subheader(f"Questions from {partner}")
        
        # Find questions asked by partner that user hasn't answered yet
        pending_mask = (df['Creator'] == partner) & (df['Status'] == 'Unanswered')
        pending_questions = df[pending_mask]
        
        if pending_questions.empty:
            st.write(f"You're all caught up! {partner} hasn't left any new questions for you yet.")
        else:
            for index, row in pending_questions.iterrows():
                with st.expander(f"Question: {row['Question']}"):
                    guess = st.text_input("Your Answer:", key=f"guess_{index}")
                    
                    if st.button("Submit Answer", key=f"btn_{index}"):
                        # Very basic text matching (can be improved!)
                        if guess.strip().lower() == str(row['Correct_Answer']).strip().lower():
                            df.at[index, 'Status'] = 'Correct'
                            st.success("Correct! 🎯")
                            st.balloons()
                        else:
                            df.at[index, 'Status'] = 'Incorrect'
                            st.error(f"Oh no! The correct answer was: {row['Correct_Answer']}")
                        
                        df.at[index, 'Guesser'] = user
                        df.at[index, 'Guessed_Answer'] = guess
                        
                        # Update Google Sheet
                        conn.update(worksheet="Trivia", data=df)
                        st.rerun()

    # --- TAB 2: ASK A QUESTION ---
    with tab2:
        st.subheader("Stump your partner")
        st.write("Ask a question about yourself, our relationship, or an inside joke.")
        
        new_q = st.text_input("The Question:")
        new_a = st.text_input("The Exact Answer (keep it short so it's easy to guess!):")
        
        if st.button("Send to Database"):
            if new_q and new_a:
                new_row = pd.DataFrame([{
                    'Creator': user,
                    'Question': new_q,
                    'Correct_Answer': new_a,
                    'Guesser': '',
                    'Guessed_Answer': '',
                    'Status': 'Unanswered'
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Trivia", data=df)
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
        # Show the last 5 answered questions
        history = df[df['Status'] != 'Unanswered'].tail(5)
        for _, row in history.iterrows():
            icon = "✅" if row['Status'] == 'Correct' else "❌"
            st.write(f"{icon} **{row['Guesser']}** guessed '{row['Guessed_Answer']}' to '{row['Question']}'")