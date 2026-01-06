import streamlit as st
import pandas as pd
from logic import create_matches, get_play_stats_snapshot

# Page Config
st.set_page_config(
    page_title="ソフトバレーチーム作成",
    page_icon="🏐", 
    layout="wide"
)

# Custom CSS to mimic the React app aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: linear-gradient(to bottom right, #f0f9ff, #e0e7ff);
    }
    .main {
        background-color: transparent;
    }
    h1 {
        color: #312e81;
        text-align: center;
        font-weight: 700;
    }
    h2, h3 {
        color: #312e81;
    }
    .stButton>button {
        width: 100%;
        background-color: #4f46e5;
        color: white;
        font-weight: bold;
        border-radius: 0.5rem;
        height: 3em;
    }
    .stButton>button:hover {
        background-color: #4338ca;
        color: white;
    }
    .card-male {
        background-color: #dbeafe;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #1e40af;
        margin-bottom: 0.5rem;
    }
    .card-female {
        background-color: #fce7f3;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #9d174d;
        margin-bottom: 0.5rem;
    }
    .waiting-badge-male {
        display: inline-block;
        background-color: #bfdbfe;
        color: #1e3a8a;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: bold;
        font-size: 0.875rem;
        margin: 0.25rem;
    }
    .waiting-badge-female {
        display: inline-block;
        background-color: #fbcfe8;
        color: #831843;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: bold;
        font-size: 0.875rem;
        margin: 0.25rem;
    }
    .match-nav-btn {
        margin: 0 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'matches' not in st.session_state:
    st.session_state.matches = []
if 'current_match_index' not in st.session_state:
    st.session_state.current_match_index = 0
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

def clear_schedule():
    st.session_state.matches = []
    st.session_state.form_submitted = False
    st.session_state.current_match_index = 0

def generate_schedule():
    try:
        matches = create_matches(
            st.session_state.male_count, 
            st.session_state.female_count, 
            st.session_state.match_count,
            st.session_state.get('mode', 'balanced')
        )
        st.session_state.matches = matches
        st.session_state.current_match_index = 0
        st.session_state.form_submitted = True
    except ValueError as e:
        st.error(str(e))

def prev_match():
    if st.session_state.current_match_index > 0:
        st.session_state.current_match_index -= 1

def next_match():
    if st.session_state.current_match_index < len(st.session_state.matches) - 1:
        st.session_state.current_match_index += 1

# Header
st.markdown("<h1>🏐 ソフトバレーチーム作成</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4b5563;'>連続待機なし・同じペア回避でバランスよくローテーション</p>", unsafe_allow_html=True)

# Input Section
with st.container():
    st.markdown("<div style='background-color: white; padding: 2rem; border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 2rem;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-bottom: 1.5rem;'>👥 設定を入力</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.number_input("男性の人数", min_value=0, value=6, key="male_count", help="最低4名", on_change=clear_schedule)
    with col2:
        st.number_input("女性の人数", min_value=0, value=6, key="female_count", help="最低4名", on_change=clear_schedule)
    with col3:
        st.number_input("試合数", min_value=1, value=5, key="match_count", on_change=clear_schedule)

    mode_map = {
        "バランス（推奨）": "balanced",
        "ペア固定（チーム維持）": "fixed_pairs",
        "完全ランダム": "random"
    }
    
    selected_mode_label = st.selectbox(
        "モード選択", 
        options=list(mode_map.keys()),
        index=0,
        help="バランス: 均等にプレイ・ペア替え\nペア固定: ペアを固定してローテーション\n完全ランダム: 毎回ランダムに決定",
        on_change=clear_schedule
    )
    st.session_state.mode = mode_map[selected_mode_label]

    st.button("🔀 試合順を作成", on_click=generate_schedule)
    st.markdown("</div>", unsafe_allow_html=True)

# Match Display
if st.session_state.matches:
    current_idx = st.session_state.current_match_index
    match = st.session_state.matches[current_idx]
    
    # Calculate Play Stats
    stats = get_play_stats_snapshot(
        st.session_state.matches, 
        current_idx, 
        st.session_state.male_count, 
        st.session_state.female_count
    )

    # Navigation
    st.markdown("<div style='background-color: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    
    with nav_col1:
        if current_idx > 0:
            st.button("← 前の試合", on_click=prev_match, key="prev_btn")
            
    with nav_col2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>▶ 第{match['match_number']}試合</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #4b5563; margin: 0;'>全{len(st.session_state.matches)}試合</p>", unsafe_allow_html=True)
        
    with nav_col3:
        if current_idx < len(st.session_state.matches) - 1:
            st.button("次の試合 →", on_click=next_match, key="next_btn")
    st.markdown("</div>", unsafe_allow_html=True)

    # Teams
    teams_col1, teams_col2 = st.columns(2)
    
    # Team A
    with teams_col1:
        st.markdown(f"""
        <div style='background-color: white; border: 4px solid #60a5fa; border-radius: 0.5rem; padding: 1.5rem; height: 100%;'>
            <h3 style='text-align: center; color: #1d4ed8; margin-bottom: 1rem;'>チーム A</h3>
            <div class='card-male'>
                <strong>男性</strong><br>
                { "".join([f"<div>男性{m} <span style='font-size:0.8em'>({stats['male_counts'][m-1]}回出場)</span></div>" for m in match['team1']['males']]) }
            </div>
            <div class='card-female'>
                <strong>女性</strong><br>
                { "".join([f"<div>女性{f} <span style='font-size:0.8em'>({stats['female_counts'][f-1]}回出場)</span></div>" for f in match['team1']['females']]) }
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Team B
    with teams_col2:
        st.markdown(f"""
        <div style='background-color: white; border: 4px solid #f87171; border-radius: 0.5rem; padding: 1.5rem; height: 100%;'>
            <h3 style='text-align: center; color: #b91c1c; margin-bottom: 1rem;'>チーム B</h3>
            <div class='card-male'>
                <strong>男性</strong><br>
                { "".join([f"<div>男性{m} <span style='font-size:0.8em'>({stats['male_counts'][m-1]}回出場)</span></div>" for m in match['team2']['males']]) }
            </div>
            <div class='card-female'>
                <strong>女性</strong><br>
                { "".join([f"<div>女性{f} <span style='font-size:0.8em'>({stats['female_counts'][f-1]}回出場)</span></div>" for f in match['team2']['females']]) }
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Waiting Members
    if match['waiting']['males'] or match['waiting']['females']:
        st.markdown("<div style='margin-top: 1.5rem; background-color: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; margin-bottom: 1rem; color: #374151;'>待機メンバー</h3>", unsafe_allow_html=True)
        
        waiting_col1, waiting_col2 = st.columns(2)
        
        with waiting_col1:
            if match['waiting']['males']:
                st.markdown(f"""
                <div style='background-color: #f3f4f6; padding: 1rem; border-radius: 0.5rem;'>
                    <div style='font-weight: 600; color: #374151; margin-bottom: 0.5rem;'>男性</div>
                    <div>
                        { "".join([f"<span class='waiting-badge-male'>男性{m} ({stats['male_counts'][m-1]}回)</span>" for m in match['waiting']['males']]) }
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        with waiting_col2:
            if match['waiting']['females']:
                st.markdown(f"""
                <div style='background-color: #f3f4f6; padding: 1rem; border-radius: 0.5rem;'>
                    <div style='font-weight: 600; color: #374151; margin-bottom: 0.5rem;'>女性</div>
                    <div>
                         { "".join([f"<span class='waiting-badge-female'>女性{f} ({stats['female_counts'][f-1]}回)</span>" for f in match['waiting']['females']]) }
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
