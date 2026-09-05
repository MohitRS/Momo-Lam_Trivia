import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime
import pytz
import plotly.express as px
import random
import streamlit.components.v1 as components

st.set_page_config(page_title="Lin & Mohit OS", page_icon="🤍", layout="centered")

# --- PREMIUM UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600&family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: #F4C2C2 !important; }
    
    .stButton>button { 
        background-color: transparent; border: 1px solid #F4C2C2; color: #F4C2C2; 
        border-radius: 12px; font-weight: 500; transition: all 0.3s ease; padding: 10px 24px;
    }
    .stButton>button:hover { 
        background-color: #F4C2C2; color: #0E1117; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(244, 194, 194, 0.2); 
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1A1C23; border: 1px solid #2D303E; border-radius: 8px; color: white;
    }
    
    div[data-testid="metric-container"] {
        background-color: #1A1C23; border: 1px solid #2D303E; padding: 15px; border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
sheet_url = "https://docs.google.com/spreadsheets/d/17wg47-a_YxLoLs5dIN1us56qaK3s3CMVGNrr-FlEh6U/edit?gid=0#gid=0"

@st.cache_data(ttl=15)
def load_data():
    return {
        "trivia": conn.read(spreadsheet=sheet_url, worksheet="Trivia").fillna('').astype(str),
        "fridge": conn.read(spreadsheet=sheet_url, worksheet="Fridge").fillna('').astype(str),
        "vibe": conn.read(spreadsheet=sheet_url, worksheet="Vibe").fillna('').astype(str),
        "watch": conn.read(spreadsheet=sheet_url, worksheet="Watchlist").fillna('').astype(str),
        "bucket": conn.read(spreadsheet=sheet_url, worksheet="BucketList").fillna('').astype(str),
        "scores": conn.read(spreadsheet=sheet_url, worksheet="HighScores").fillna('').astype(str),
    }

try:
    db = load_data()
except Exception as e:
    st.error(f"Database sync error: {e}")
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title("🤍 Our Space")
    user = st.radio("User Access:", ["Select...", "Mohit 🎾", "Lin 🍵"])
    st.markdown("---")
    page = st.radio("Menu", ["🏠 Dashboard", "💌 Digital Fridge", "📊 Telemetry", "🎯 Trivia Arena", "🍿 Watchlist", "✈️ Bucket List", "🎲 Date Roulette", "🕹️ The Arcade"])

if user == "Select...":
    st.title("System Locked.")
    st.write("Please authenticate in the sidebar to enter.")
    st.stop()

partner = "Lin 🍵" if user == "Mohit 🎾" else "Mohit 🎾"
melb_tz = pytz.timezone('Australia/Melbourne')
gz_tz = pytz.timezone('Asia/Shanghai')
current_time = datetime.datetime.now(melb_tz if user == "Mohit 🎾" else gz_tz)

# --- PAGE 1: DASHBOARD ---
if page == "🏠 Dashboard":
    st.title(f"Welcome, {user.split()[0]}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Time in Werribee", datetime.datetime.now(melb_tz).strftime('%I:%M %p'))
    with col2:
        st.metric("Time in Guangzhou", datetime.datetime.now(gz_tz).strftime('%I:%M %p'))
        
    grad_date = datetime.date(2026, 12, 15) 
    st.metric(label="Countdown to December", value=f"{(grad_date - datetime.date.today()).days} Days")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚨 Send an 'I Miss You' Ping", use_container_width=True):
        new_ping = pd.DataFrame([{'Author': 'SYSTEM', 'Message': f"*Ping: {user} is missing you.*", 'Timestamp': current_time.strftime("%b %d, %I:%M %p")}])
        conn.update(spreadsheet=sheet_url, worksheet="Fridge", data=pd.concat([new_ping, db['fridge']], ignore_index=True))
        st.cache_data.clear()
        st.toast("Ping delivered! 💌", icon="🚀")

    st.markdown("---")
    st.subheader("Vibe Telemetry")
    if len(db['vibe']) > 1:
        plot_df = db['vibe'][db['vibe']['Date'] != ''].copy()
        plot_df['Miss_Level'] = pd.to_numeric(plot_df['Miss_Level'], errors='coerce')
        fig = px.line(plot_df, x="Date", y="Miss_Level", color="User", markers=True, color_discrete_sequence=['#F4C2C2', '#FFFFFF'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'), margin=dict(l=0, r=0, t=30, b=0))
        fig.update_yaxes(range=[0, 100], showgrid=True, gridcolor='#2D303E')
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

# --- PAGE 2: DIGITAL FRIDGE ---
elif page == "💌 Digital Fridge":
    st.title("Digital Fridge")
    with st.form("new_note", clear_on_submit=True):
        new_msg = st.text_area("Leave a note:", placeholder="Thinking about you...")
        if st.form_submit_button("Post Note") and new_msg:
            new_row = pd.DataFrame([{'Author': user, 'Message': new_msg, 'Timestamp': current_time.strftime("%b %d, %I:%M %p")}])
            conn.update(spreadsheet=sheet_url, worksheet="Fridge", data=pd.concat([new_row, db['fridge']], ignore_index=True))
            st.cache_data.clear()
            st.toast("Note pinned to the fridge! 📌")
            st.rerun()

    for _, row in db['fridge'].iterrows():
        if str(row['Message']).strip() != '':
            with st.container(border=True):
                st.caption(f"**{row['Author']}** • {row['Timestamp']}")
                st.write(row['Message'])

# --- PAGE 3: TELEMETRY ---
elif page == "📊 Telemetry":
    st.title("Vibe Check")
    with st.form("vibe_check"):
        mood = st.slider("Overall Mood", 0, 100, 50)
        energy = st.slider("Energy Level", 0, 100, 50)
        miss = st.slider("Missing Level", 0, 100, 100)
        if st.form_submit_button("Submit"):
            new_vibe = pd.DataFrame([{'Date': current_time.strftime("%Y-%m-%d"), 'User': user, 'Mood': mood, 'Energy': energy, 'Miss_Level': miss}])
            conn.update(spreadsheet=sheet_url, worksheet="Vibe", data=pd.concat([db['vibe'], new_vibe], ignore_index=True))
            st.cache_data.clear()
            st.toast("Telemetry logged successfully! 📡")

# --- PAGE 4: TRIVIA ARENA ---
elif page == "🎯 Trivia Arena":
    st.title("Trivia Arena")
    tab1, tab2 = st.tabs(["Play", "Create"])
    with tab1:
        pending = db['trivia'][(db['trivia']['Creator'] == partner) & (db['trivia']['Status'] == 'Unanswered')]
        if pending.empty:
            st.info("You're all caught up!")
        else:
            for idx, row in pending.iterrows():
                with st.container(border=True):
                    st.write(f"**{row['Question']}**")
                    guess = st.text_input("Your guess:", key=f"g_{idx}")
                    if guess:
                        st.info(f"Their Answer: {row['Correct_Answer']}")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Nailed it", key=f"r_{idx}", use_container_width=True):
                            db['trivia'].at[idx, 'Status'] = 'Correct'
                            db['trivia'].at[idx, 'Guesser'], db['trivia'].at[idx, 'Guessed_Answer'] = user, guess
                            conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=db['trivia'])
                            st.cache_data.clear()
                            st.toast("Point scored! 🎯")
                            st.balloons()
                            st.rerun()
                        if c2.button("❌ Nope", key=f"w_{idx}", use_container_width=True):
                            db['trivia'].at[idx, 'Status'] = 'Incorrect'
                            db['trivia'].at[idx, 'Guesser'], db['trivia'].at[idx, 'Guessed_Answer'] = user, guess
                            conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=db['trivia'])
                            st.cache_data.clear()
                            st.rerun()
    with tab2:
        with st.container(border=True):
            new_q = st.text_input("The Question:")
            new_a = st.text_input("The Answer:")
            if st.button("Submit") and new_q and new_a:
                new_row = pd.DataFrame([{'Creator': user, 'Question': new_q, 'Correct_Answer': new_a, 'Guesser': '', 'Guessed_Answer': '', 'Status': 'Unanswered'}])
                conn.update(spreadsheet=sheet_url, worksheet="Trivia", data=pd.concat([db['trivia'], new_row], ignore_index=True))
                st.cache_data.clear()
                st.toast("Question sent! 📩")
                st.rerun()

# --- PAGE 5: WATCHLIST ---
elif page == "🍿 Watchlist":
    st.title("Watchlist")
    with st.container(border=True):
        new_title = st.text_input("Add a movie/show:")
        if st.button("Add to Queue") and new_title:
            new_watch = pd.DataFrame([{'Title': new_title, 'Added_By': user, 'Status': 'Queued'}])
            conn.update(spreadsheet=sheet_url, worksheet="Watchlist", data=pd.concat([db['watch'], new_watch], ignore_index=True))
            st.cache_data.clear()
            st.toast("Added to queue! 🍿")
            st.rerun()
            
    st.write("### Up Next")
    for idx, row in db['watch'][db['watch']['Status'] == 'Queued'].iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{row['Title']}** ({row['Added_By']})")
            if c2.button("Watched", key=f"w_{idx}", use_container_width=True):
                db['watch'].at[idx, 'Status'] = 'Watched'
                conn.update(spreadsheet=sheet_url, worksheet="Watchlist", data=db['watch'])
                st.cache_data.clear()
                st.rerun()

# --- PAGE 6: BUCKET LIST ---
elif page == "✈️ Bucket List":
    st.title("Bucket List")
    with st.container(border=True):
        item = st.text_input("What are we doing?")
        loc = st.selectbox("Where?", ["Melbourne", "Guangzhou", "Virtual", "Other"])
        if st.button("Add Idea") and item:
            new_plan = pd.DataFrame([{'Item': item, 'Location': loc, 'Added_By': user, 'Status': 'Dreaming'}])
            conn.update(spreadsheet=sheet_url, worksheet="BucketList", data=pd.concat([db['bucket'], new_plan], ignore_index=True))
            st.cache_data.clear()
            st.toast("Added to Bucket List! ✈️")
            st.rerun()
            
    st.write("### Our Plans")
    for idx, row in db['bucket'][db['bucket']['Status'] != 'Completed'].iterrows():
        with st.container(border=True):
            st.write(f"📍 **{row['Location']}**: {row['Item']}")

# --- PAGE 7: DATE ROULETTE ---
elif page == "🎲 Date Roulette":
    st.title("Date Roulette")
    if st.button("Spin the Wheel 🎡", use_container_width=True):
        options = ["Simultaneous matcha delivery.", "Take a shared online personality test.", "Virtual makeup tutorial.", "Browse Sephora together."]
        options.extend([f"Watch: {m}" for m in db['watch'][db['watch']['Status'] == 'Queued']['Title'].tolist()])
        st.success(f"**Result:** {random.choice(options)}")
        st.balloons()

# --- PAGE 8: THE ARCADE ---
elif page == "🕹️ The Arcade":
    st.title("Classic Snake")
    st.write("Desktop: Use arrow keys. Mobile: Tap the buttons below the game!")
    
    # MOBILE-FRIENDLY SNAKE GAME WITH SCROLL FIX
    components.html(
        """
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body { background: #0E1117; color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; margin: 0; font-family: sans-serif; }
            canvas { background: #1A1C23; border: 2px solid #F4C2C2; border-radius: 8px; box-shadow: 0 4px 12px rgba(244,194,194,0.3); margin-top: 40px; }
            #score { position: absolute; top: 10px; font-size: 20px; font-weight: bold; color: #F4C2C2;}
            .controls { display: grid; grid-template-columns: 60px 60px 60px; gap: 10px; margin-top: 20px; }
            .btn { background: #2D303E; border: none; color: white; font-size: 24px; padding: 15px; border-radius: 8px; cursor: pointer; }
            .btn:active { background: #F4C2C2; }
            .up { grid-column: 2; } .left { grid-column: 1; grid-row: 2; } .down { grid-column: 2; grid-row: 2; } .right { grid-column: 3; grid-row: 2; }
          </style>
        </head>
        <body>
          <div id="score">Score: 0</div>
          <canvas width="320" height="320" id="game"></canvas>
          
          <!-- MOBILE BUTTONS -->
          <div class="controls">
            <button class="btn up" onclick="setDir('up')">⬆️</button>
            <button class="btn left" onclick="setDir('left')">⬅️</button>
            <button class="btn down" onclick="setDir('down')">⬇️</button>
            <button class="btn right" onclick="setDir('right')">➡️</button>
          </div>

          <script>
            var canvas = document.getElementById('game');
            var context = canvas.getContext('2d');
            var grid = 16, count = 0, score = 0;
            var snake = { x: 160, y: 160, dx: grid, dy: 0, cells: [], maxCells: 4 };
            var apple = { x: 240, y: 240 };

            // PREVENT SCREEN SCROLLING WITH ARROW KEYS
            window.addEventListener("keydown", function(e) {
                if([37, 38, 39, 40].indexOf(e.keyCode) > -1) { e.preventDefault(); }
            }, false);

            function getRandomInt(min, max) { return Math.floor(Math.random() * (max - min)) + min; }
            
            window.setDir = function(dir) {
                if (dir === 'up' && snake.dy === 0) { snake.dy = -grid; snake.dx = 0; }
                else if (dir === 'down' && snake.dy === 0) { snake.dy = grid; snake.dx = 0; }
                else if (dir === 'left' && snake.dx === 0) { snake.dx = -grid; snake.dy = 0; }
                else if (dir === 'right' && snake.dx === 0) { snake.dx = grid; snake.dy = 0; }
            }

            function loop() {
              requestAnimationFrame(loop);
              if (++count < 6) return;
              count = 0;
              context.clearRect(0,0,canvas.width,canvas.height);
              snake.x += snake.dx; snake.y += snake.dy;
              if (snake.x < 0) { snake.x = canvas.width - grid; } else if (snake.x >= canvas.width) { snake.x = 0; }
              if (snake.y < 0) { snake.y = canvas.height - grid; } else if (snake.y >= canvas.height) { snake.y = 0; }
              snake.cells.unshift({x: snake.x, y: snake.y});
              if (snake.cells.length > snake.maxCells) { snake.cells.pop(); }
              context.fillStyle = '#F4C2C2';
              context.fillRect(apple.x, apple.y, grid-1, grid-1);
              context.fillStyle = '#ffffff';
              snake.cells.forEach(function(cell, index) {
                context.fillRect(cell.x, cell.y, grid-1, grid-1);
                if (cell.x === apple.x && cell.y === apple.y) {
                  snake.maxCells++; score += 10;
                  document.getElementById('score').innerText = 'Score: ' + score;
                  apple.x = getRandomInt(0, 20) * grid; apple.y = getRandomInt(0, 20) * grid;
                }
                for (var i = index + 1; i < snake.cells.length; i++) {
                  if (cell.x === snake.cells[i].x && cell.y === snake.cells[i].y) {
                    snake.x = 160; snake.y = 160; snake.cells = []; snake.maxCells = 4; snake.dx = grid; snake.dy = 0; score = 0;
                    document.getElementById('score').innerText = 'Score: 0';
                  }
                }
              });
            }
            document.addEventListener('keydown', function(e) {
              if (e.which === 37) setDir('left');
              else if (e.which === 38) setDir('up');
              else if (e.which === 39) setDir('right');
              else if (e.which === 40) setDir('down');
            });
            requestAnimationFrame(loop);
          </script>
        </body>
        </html>
        """, height=500
    )
    
    with st.container(border=True):
        st.write("### Log Score")
        new_score = st.number_input("Score", min_value=0, step=10)
        if st.button("Submit", use_container_width=True) and new_score > 0:
            new_log = pd.DataFrame([{'Game': 'Snake', 'Player': user, 'Score': str(new_score), 'Date': current_time.strftime("%b %d")}])
            conn.update(spreadsheet=sheet_url, worksheet="HighScores", data=pd.concat([db['scores'], new_log], ignore_index=True))
            st.cache_data.clear()
            st.toast("High score logged! 🏆")
            st.rerun()

    st.write("### Leaderboard")
    if not db['scores'].empty and db['scores']['Score'].iloc[0] != '':
        db['scores']['Score'] = pd.to_numeric(db['scores']['Score'], errors='coerce')
        for idx, row in db['scores'].sort_values(by="Score", ascending=False).head(5).iterrows():
            with st.container(border=True):
                st.write(f"**{row['Player']}** — {row['Score']} pts")
