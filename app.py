from __future__ import annotations

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from auth import authenticate_user, create_user, validate_registration
from database import (
    add_profile,
    get_legacy_profiles,
    get_user_profiles,
    init_db,
    migrate_legacy_csv,
)
from survey import render_survey_page
from ui import hero, load_css, metric_cards, render_modern_header

st.set_page_config(
    page_title="Streamlit Auth WebApp",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()
migrate_legacy_csv()
load_css()


def init_session() -> None:
    defaults = {
        "authenticated": False,
        "user_id": None,
        "userid": None,
        "username": None,
        "email": None,
        "page": "home",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout() -> None:
    for key in ["authenticated", "user_id", "userid", "username", "email"]:
        st.session_state[key] = False if key == "authenticated" else None
    st.session_state.page = "home"


def handle_query_params() -> None:
    action = st.query_params.get("action")
    view = st.query_params.get("view")

    if action == "logout":
        logout()
        st.query_params.clear()
        st.rerun()

    if view in {"home", "register", "login", "mydata", "survey", "pythonide"}:
        st.session_state.page = view
        st.query_params.clear()
        st.rerun()


def sidebar_navigation() -> str:
    st.sidebar.markdown("### ☰ Menu")
    st.sidebar.caption("왼쪽 햄버거 버튼으로 메뉴를 열고 닫을 수 있습니다.")

    if st.session_state.authenticated:
        # 로그아웃 아래에 'Pythonide' 추가
        labels = ["홈", "내 데이터", "설문참여", "로그아웃", "Pythonide"]
        key_map = {
            "홈": "home",
            "내 데이터": "mydata",
            "설문참여": "survey",
            "로그아웃": "logout",
            "Pythonide": "pythonide",
        }
    else:
        labels = ["홈", "사용자 등록", "로그인"]
        key_map = {"홈": "home", "사용자 등록": "register", "로그인": "login"}

    current_key = st.session_state.page
    reverse = {value: key for key, value in key_map.items()}
    default_label = reverse.get(current_key, "홈")
    selected = st.sidebar.radio(
        "Navigation",
        labels,
        index=labels.index(default_label) if default_label in labels else 0,
        label_visibility="collapsed",
    )
    selected_key = key_map[selected]
    if selected_key == "logout":
        logout()
        st.rerun()

    st.session_state.page = selected_key
    return selected_key


def render_public_home() -> None:
    hero(
        "This is my first webapp",
        "첨부한 기본 Streamlit 화면을 바탕으로 SQLite 회원 시스템과 세션 기반 랜딩페이지를 결합한 버전입니다.",
    )
    metric_cards(
        [
            ("Database", "SQLite3"),
            ("DB File", "mycom.db"),
            ("Session", "Streamlit"),
            ("UI", "Modern / Responsive"),
        ]
    )

    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("시작하기")
        st.write("회원가입 후 로그인하면 기존 앱의 콘텐츠, 입력 폼, DB 조회 기능을 사용할 수 있습니다.")
        c1, c2, c3 = st.columns(3)
        if c1.button("사용자 등록", use_container_width=True, type="primary"):
            st.session_state.page = "register"
            st.rerun()
        if c2.button("로그인", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
        if c3.button("파이썬IDE", use_container_width=True):
            st.session_state.page = "pythonide"
            st.rerun()

        components.html(
            "<p><span style='text-decoration: line-through double red;'>Oops</span>!</p>",
            height=40,
        )

    with right:
        with st.container(border=True):
            st.markdown("#### 적용 기능")
            st.markdown(
                "- SQLite `user_table` / `survey_table`\n"
                "- AI 교육효과 인식 설문 (응시·결과·시각화)\n"
                "- 비밀번호 PBKDF2 해시 저장\n"
                "- 로그인 전/후 세션 분리\n"
                "- 접이식 Streamlit Sidebar\n"
                "- Tailwind + Alpine.js 헤더 컴포넌트\n"
                "- Flexbox 기반 반응형 CSS"
            )


def render_register() -> None:
    hero("사용자 등록", "새 계정을 만든 후 로그인 페이지에서 접속할 수 있습니다.", "CREATE ACCOUNT")
    with st.form("register_form", clear_on_submit=False):
        userid = st.text_input("아이디", placeholder="예: cne_user")
        username = st.text_input("사용자 이름", placeholder="예: 홍길동")
        email = st.text_input("이메일", placeholder="name@example.com")
        c1, c2 = st.columns(2)
        password = c1.text_input("비밀번호", type="password")
        password_confirm = c2.text_input("비밀번호 확인", type="password")
        submitted = st.form_submit_button("사용자 등록", type="primary", use_container_width=True)

    if submitted:
        errors = validate_registration(userid, username, password, password_confirm, email)
        if errors:
            for error in errors:
                st.error(error)
            return
        ok, message = create_user(userid, username, password, email)
        if ok:
            st.success(message)
            if st.button("로그인 화면으로 이동", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
        else:
            st.error(message)


def render_login() -> None:
    hero("로그인", "등록한 아이디와 비밀번호로 로그인합니다.", "SIGN IN")
    with st.form("login_form"):
        userid = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", type="primary", use_container_width=True)

    if submitted:
        user = authenticate_user(userid, password)
        if user is None:
            st.error("아이디 또는 비밀번호를 확인해 주세요.")
            return

        st.session_state.authenticated = True
        st.session_state.user_id = user["id_num"]
        st.session_state.userid = user["userid"]
        st.session_state.username = user["username"]
        st.session_state.email = user["email"]
        st.session_state.page = "home"
        st.success(f"{user['username']}님, 로그인되었습니다.")
        st.rerun()


def render_authenticated_home() -> None:
    hero(
        f"{st.session_state.username}님, 환영합니다.",
        "아래 화면은 첨부된 기본 Streamlit 소스의 컬럼·Expander·영상·입력·DB 조회 흐름을 유지해 SQLite 기반으로 확장한 화면입니다.",
        "AUTHENTICATED",
    )

    name = st.text_input("Name?: ", value=st.session_state.username or "")

    if name == "":
        st.error("Please input your name")
        return

    col1, col2 = st.columns((4, 1))
    with col1:
        with st.expander(f"{name}님 여기는 content입니다", expanded=True):
            url = "https://www.youtube.com/watch?v=MHShfgqrUWs"
            st.write("content....")
            st.video(url)
    with col2:
        with st.expander("Tips...", expanded=True):
            st.write("tips...")
            st.caption("로그인 세션이 유지되는 동안 사용자별 데이터가 분리됩니다.")

    col3, col4 = st.columns((4, 1))
    with col3:
        with st.expander("content", expanded=True):
            with st.form("profile_form", clear_on_submit=True):
                age = st.number_input("Age? ", min_value=1, max_value=120, step=1, value=50)
                address = st.text_input("Address? ")
                phone = st.text_input("Phone? ")
                save = st.form_submit_button("Successful Add", type="primary")

            if save:
                if all([name.strip(), age, address.strip(), phone.strip()]):
                    add_profile(
                        int(st.session_state.user_id),
                        name,
                        int(age),
                        address,
                        phone,
                    )
                    st.success("Successful Add!!!")
                else:
                    st.error("Name, Age, Address, Phone을 모두 입력해 주세요.")

        with st.expander("Check my DB"):
            if st.button("Check my db", use_container_width=True):
                rows = get_user_profiles(int(st.session_state.user_id))
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("아직 저장된 데이터가 없습니다.")
    with col4:
        with st.expander("Tips...", expanded=True):
            st.write("tips...")
            st.caption("CSV 대신 mycom.db에 저장됩니다.")


def render_mydata() -> None:
    hero("내 데이터", "현재 로그인한 사용자에게 연결된 데이터만 조회합니다.", "MY DATABASE")
    rows = get_user_profiles(int(st.session_state.user_id))
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("저장된 데이터가 없습니다. 홈에서 데이터를 먼저 등록해 주세요.")

    with st.expander("첨부 CSV 레거시 데이터 보기"):
        st.caption("첨부된 data.csv는 원본 보존을 위해 별도 legacy 데이터로 1회 마이그레이션됩니다.")
        legacy = get_legacy_profiles()
        if legacy:
            st.dataframe(pd.DataFrame(legacy), use_container_width=True, hide_index=True)
        else:
            st.info("레거시 데이터가 없습니다.")


def render_python_ide() -> None:
    """온라인 파이썬 IDE를 iframe으로 렌더링"""
    hero("Python IDE", "브라우저에서 직접 파이썬 코드를 작성하고 실행할 수 있습니다.", "ONLINE IDE")
    components.html(
        '<iframe style="border:1px #FFFFFF none" src="https://www.online-python.com/" title="iFrame" width="100%" height="800px" scrolling="no" frameborder="no" allow="fullscreen"></iframe>',
        height=820,
    )


init_session()
handle_query_params()
render_modern_header(st.session_state.username if st.session_state.authenticated else None)
page = sidebar_navigation()


if not st.session_state.authenticated:
    if page == "register":
        render_register()
    elif page == "login":
        render_login()
    elif page == "pythonide":
        render_python_ide()
    else:
        render_public_home()
else:
    if page == "mydata":
        render_mydata()
    elif page == "survey":
        render_survey_page(hero)
    elif page == "pythonide":
        render_python_ide()
    else:
        render_authenticated_home()