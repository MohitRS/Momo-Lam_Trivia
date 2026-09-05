import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime
import pytz
import plotly.express as px

st.set_page_config(page_title="Lin & Mohit OS", page_icon="🤍", layout="wide")

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
    df_vibe = conn.read(spreadsheet=sheet_url, worksheet="Vibe", ttl=0).fillna('').astype(str)
    df_watch = conn.read(spreadsheet=sheet_url, worksheet="Watchlist", ttl=0).fillna('').astype(str)
except Exception as e:
    st.error("Database sync error. Did you add the 'Vibe' and 'Watchlist' tabs?")
    st.stop()

# --- SIDEBAR NAVIGATION & LOGIN ---
with st.sidebar:
    st.title("🤍 Our Space")
    user = st.radio("Access Terminal:", ["Select...", "Mohit 🎾", "Lin 🍵"])
    st.markdown("---")
    page = st.radio("Navigation", [
        "🏠 Command Center", 
        "📊 Telemetry (Vibe Check)",
        "💌 Digital Fridge", 
        "🎯 Trivia Arena",
        "🍿 The Watchlist"
    ])

if user == "Select...":
    st.title("System Locked.")
    st.write("Please authenticate in the sidebar to access the relationship mainframe.")
    st.stop()

partner = "Lin 🍵" if user == "Mohit 🎾" else "Mohit 🎾"
melb_tz = pytz.timezone('Australia/Melbourne')
gz_tz = pytz.timezone('Asia/Shanghai')
current_time = datetime.datetime.now(melb_tz if user == "Mohit 🎾" else gz_tz)

# --- PAGE 1: COMMAND CENTER (DASHBOARD) ---
if page == "🏠 Command Center":
    st.title(f"Welcome back, {user.split()[0]}")
    
    # Top Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Werribee:** {datetime.datetime.now(melb_tz).strftime('%I:%M %p')}")
        st.write(f"**Guangzhou:** {datetime.datetime.now(gz_tz).strftime('%I:%M %p')}")
    with col2:
        grad_date = datetime.date(2026, 12, 15) 
        days_left = (grad_date - datetime.date.today()).days
        st.metric(label="Days to December", value=f"{days_left} Days")
    with col3:
        if st.button("🚨 Send an 'I Miss You' Ping", use_container_width=True):
            timestamp = current_time.strftime("%b %d, %I:%M %p")
            ping_msg = f"*Incoming Ping: {user} was thinking about you right now.*"
            new_ping = pd.DataFrame([{'Author': 'SYSTEM', 'Message': ping_msg, 'Timestamp': timestamp}])
            df_fridge = pd.concat([new_ping, df_fridge], ignore_index=True)
            conn.update(spreadsheet=sheet_url, worksheet="Fridge", data=df_fridge)
            st.success("Ping delivered to the fridge!")
            st.balloons()

    st.markdown("---")
    
    # Telemetry Chart
    st.subheader("Relationship Telemetry")
    if len(df_vibe) > 1:
        # Convert data for plotting
        plot_df = df_vibe[df_vibe['Date'] != ''].copy()
        plot_df['Miss_Level'] = pd.to_numeric(plot_df['Miss_Level'], errors='coerce')
        
        fig = px.line(plot_df, x="Date", y="Miss_Level", color="User", 
                      title="How much we miss each other over time",
                      markers=True, color_discrete_sequence=['#F4C2C2', '#FFFFFF'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#EAEAEA'))
        fig.update_yaxes(range=[0, 100], showgrid=False)
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Not enough telemetry data yet. Submit a daily vibe check!")

# --- PAGE 2: TELEMETRY (VIBE CHECK) ---
elif page == "📊 Telemetry (Vibe Check)":
    st.title("Daily Vibe Check")
    st.write("Log your mental state to update the dashboard timeline.")
    
    with st.form("vibe_check"):
        mood = st.slider("Overall Mood (0 = Rough day, 100 = Incredible)", 0, 100, 50)
        energy = st.slider("Energy Level (0 = Exhausted, 100 = Ready for a marathon)", 0, 100, 50)
        miss = st.slider("How much are you missing them right now?", 0, 100, 100)
        
        if st.form_submit_button("Submit Telemetry"):
            date_str = current_time.strftime("%Y-%m-%d")
            new_vibe = pd.DataFrame([{
                'Date': date_str, 'User': user, 
                'Mood': mood, 'Energy': energy, 'Miss_Level': miss
            }])
            df_vibe = pd.concat([df_vibe, new_vibe], ignore_index=True)
            conn.update(spreadsheet=sheet_url, worksheet="Vibe", data=df_vibe)
            st.success("Telemetry logged successfully.")
            st.rerun()

# --- PAGE 3: THE WATCHLIST ---
elif page == "🍿 The Watchlist":
    st.title("The Watchlist")
    st.write("Queue up movies, YouTube documentaries, or shows for FaceTime dates.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_title = st.text_input("Add a new title:")
    with col2:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Add to Queue", use_container_width=True) and new_title:
            new_watch = pd.DataFrame([{'Title': new_title, 'Added_By': user, 'Status': 'Queued'}])
            df_watch = pd.concat([df_watch, new_watch], ignore_index=True)
            conn.update(spreadsheet=sheet_url, worksheet="Watchlist", data=df_watch)
            st.rerun()
            
    st.markdown("---")
    st.subheader("Currently Queued")
    pending = df_watch[df_watch['Status'] == 'Queued']
    if pending.empty:
        st.write("The queue is empty! Time to add some recommendations.")
    else:
        for idx, row in pending.iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(f"🎥 **{row['Title']}** (Added by {row['Added_By']})")
            with c2:
                if st.button("Mark Watched", key=f"watch_{idx}"):
                    df_watch.at[idx, 'Status'] = 'Watched'
                    conn.update(spreadsheet=sheet_url, worksheet="Watchlist", data=df_watch)
                    st.rerun()

# --- PAGE 4: DIGITAL FRIDGE (EXISTING) ---
elif page == "💌 Digital Fridge":
    st.title("The Digital Fridge")
    with st.form("new_note", clear_on_submit=True):
        new_msg = st.text_area("Write something sweet:")
        if st.form_submit_button("Stick to Fridge") and new_msg:
            timestamp = current_time.strftime("%b %d, %I:%M %p")
            new_row = pd.DataFrame([{'Author': user, 'Message': new_msg, 'Timestamp': timestamp}])
            df_fridge = pd.concat([new_row, df_fridge], ignore_index=True) 
            conn.update(spreadsheet=sheet_url, worksheet="Fridge", data=df_fridge)
            st.success("Note added!")
            st.rerun()

    if df_fridge.empty or df_fridge['Message'].iloc[0] == '':
        st.write("The fridge is empty!")
    else:
        for index, row in df_fridge.iterrows():
            if str(row['Message']).strip() != '':
                st.markdown(f"""
                <div class="note-box">
                    <strong>{row['Author']}</strong> <em>({row['Timestamp']})</em><br>
                    {row['Message']}
                </div>
                """, unsafe_allow_html=True)

# --- PAGE 5: TRIVIA ARENA (EXISTING) ---
elif page == "🎯 Trivia Arena":
    st.title("Trivia Arena")
    tab1, tab2 = st.tabs(["🎯 Play", "🤔 Create"])
    
    with tab1:
        pending_mask = (df_trivia['Creator'] == partner) & (df_trivia['Status'] == 'Unanswered')
        pending_questions = df_trivia[pending_mask]
        
        if pending_questions.empty:
            st.info(f"You're all caught up! {partner} hasn't left any new questions.")
        else:
            for index, row in pending_questions.iterrows():
                with st.expander(f"Question: {row['Question']}", expanded=True):
                    guess = st.text_input("Type your guess:", key=f"guess_{index}")
                    if guess:
                        st.markdown(f"**Their Exact Answer:** `{row['Correct_Answer']}`")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Nailed it", key=f"right_{index}", use_container_width=True):
                            df_trivia.at[index, 'Status'] = 'Correct'
                            df_trivia.at[index, 'Guesser'] = user
                            df_trivia.at[index, 'Guessed_Answer'] = guess
                            conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df_trivia)
                            st.rerun()
                        if c2.button("❌ Not quite", key=f"wrong_{index}", use_container_width=True):
                            df_trivia.at[index, 'Status'] = 'Incorrect'
                            df_trivia.at[index, 'Guesser'] = user
                            df_trivia.at[index, 'Guessed_Answer'] = guess
                            conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df_trivia)
                            st.rerun()

    with tab2:
        new_q = st.text_input("The Question:")
        new_a = st.text_input("The Answer:")
        if st.button("Send to Database") and new_q and new_a:
            new_row = pd.DataFrame([{'Creator': user, 'Question': new_q, 'Correct_Answer': new_a, 'Guesser': '', 'Guessed_Answer': '', 'Status': 'Unanswered'}])
            df_trivia = pd.concat([df_trivia, new_row], ignore_index=True)
            conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=df_trivia)
            st.rerun()
