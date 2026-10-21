"""설문참여 메뉴: AI의 교육적 효과에 대한 인식 설문 (설문응시 / 설문 결과 / 시각화)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import QUESTION_COLS, add_survey, get_surveys, get_user_surveys

# ------------------------------------------------------------------ 설문 정의
QUESTIONS: dict[str, str] = {
    "q1": "AI 도구는 학습 내용을 더 쉽게 이해하는 데 도움이 된다.",
    "q2": "AI를 활용하면 개인의 수준과 속도에 맞춘 맞춤형 학습이 가능하다.",
    "q3": "AI 활용 수업(교육)은 학습에 대한 흥미와 동기를 높여 준다.",
    "q4": "AI가 제공하는 즉각적인 피드백은 학습 효과를 높인다.",
    "q5": "AI를 활용하면 학습 시간을 더 효율적으로 사용할 수 있다.",
    "q6": "AI는 창의적 사고와 문제해결 능력 향상에 도움이 된다.",
    "q7": "AI 활용 교육은 실제 업무(직무) 역량 향상에 도움이 된다.",
    "q8": "AI가 제공한 정보를 비판적으로 검토하는 능력도 함께 기를 수 있다.",
    "q9": "교육 현장에서 AI 활용을 더 확대할 필요가 있다.",
    "q10": "앞으로도 AI를 학습 도구로 계속 활용할 의향이 있다.",
}
SHORT: dict[str, str] = {
    "q1": "이해도 향상", "q2": "맞춤형 학습", "q3": "흥미·동기", "q4": "즉각 피드백",
    "q5": "시간 효율", "q6": "창의·문제해결", "q7": "직무역량", "q8": "비판적 사고",
    "q9": "활용 확대 필요", "q10": "지속 활용 의향",
}
SCALE: dict[int, str] = {1: "전혀 아니다", 2: "아니다", 3: "보통이다", 4: "그렇다", 5: "매우 그렇다"}
SCALE_COLORS = {
    "전혀 아니다": "#dc2626", "아니다": "#f97316", "보통이다": "#a3a3a3",
    "그렇다": "#60a5fa", "매우 그렇다": "#1d4ed8",
}


def _label(q: str) -> str:
    return f"Q{q[1:]}. {SHORT[q]}"


def _load_df() -> pd.DataFrame:
    df = pd.DataFrame(get_surveys())
    if df.empty:
        return df
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df


# ------------------------------------------------------------------ 통계 계산
def build_stats(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for q in QUESTION_COLS:
        s = df[q].dropna().astype(int)
        n = len(s)
        counts = s.value_counts().reindex(range(1, 6), fill_value=0)
        row = {
            "문항": f"Q{q[1:]}",
            "내용": QUESTIONS[q],
            "응답수": n,
            "평균": round(s.mean(), 2) if n else None,
            "표준편차": round(s.std(ddof=0), 2) if n else None,
        }
        for k, name in SCALE.items():
            row[f"{name}({k})"] = int(counts[k])
        row["긍정률(%)"] = round((counts[4] + counts[5]) / n * 100, 1) if n else None
        row["부정률(%)"] = round((counts[1] + counts[2]) / n * 100, 1) if n else None
        rows.append(row)
    return pd.DataFrame(rows)


def distribution_long(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for q in QUESTION_COLS:
        s = df[q].dropna().astype(int)
        n = len(s) or 1
        counts = s.value_counts().reindex(range(1, 6), fill_value=0)
        for k, name in SCALE.items():
            rows.append({"문항": _label(q), "응답": name, "응답수": int(counts[k]),
                         "비율(%)": round(counts[k] / n * 100, 1)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ Tab 1: 설문응시
def tab_take_survey() -> None:
    userid = st.session_state.userid
    mine = get_user_surveys(userid)
    if mine:
        st.info(f"이미 {len(mine)}회 응답하셨습니다. (최근 응답: {mine[0]['created_at']}) "
                "다시 제출하면 새 응답으로 추가 저장됩니다.")

    st.markdown("**AI의 교육적 효과에 대한 인식 설문**  \n"
                "각 문항을 읽고 본인의 생각과 가장 가까운 답을 선택해 주세요. (5점 척도)")

    # 저장 완료 메시지 (rerun 후 표시)
    done = st.session_state.pop("survey_done_msg", None)
    if done:
        st.success(done)
        st.balloons()

    ver = st.session_state.setdefault("survey_form_ver", 0)  # 제출 성공 시 폼 초기화용
    with st.form("survey_form", clear_on_submit=False):
        answers: dict[str, int | None] = {}
        for q, text in QUESTIONS.items():
            st.markdown(f'<div class="q-card"><span class="q-no">Q{q[1:]}.</span>{text}</div>',
                        unsafe_allow_html=True)
            answers[q] = st.radio(
                text, options=list(SCALE.keys()), format_func=lambda v: f"{v}. {SCALE[v]}",
                index=None, horizontal=True, key=f"survey_{q}_{ver}", label_visibility="collapsed",
            )
        submitted = st.form_submit_button("설문 제출", type="primary", use_container_width=True)

    if submitted:
        missing = [f"Q{q[1:]}" for q, v in answers.items() if v is None]
        if missing:
            st.error(f"응답하지 않은 문항이 있습니다: {', '.join(missing)}")
            return
        created_at = add_survey(userid, [int(answers[q]) for q in QUESTION_COLS])
        st.session_state.survey_done_msg = f"설문이 저장되었습니다. 참여해 주셔서 감사합니다! (응답일시: {created_at})"
        st.session_state.survey_form_ver = ver + 1
        st.rerun()


# ------------------------------------------------------------------ Tab 2: 설문 결과
def tab_results(df: pd.DataFrame) -> None:
    stats = build_stats(df)
    all_vals = df[QUESTION_COLS].stack()
    pos_rate = (all_vals >= 4).mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 응답 건수", f"{len(df)}건")
    c2.metric("참여 사용자", f"{df['user_id'].nunique()}명")
    c3.metric("전체 평균", f"{all_vals.mean():.2f} / 5")
    c4.metric("전체 긍정률", f"{pos_rate:.1f}%")

    st.subheader("문항별 통계")
    st.dataframe(
        stats,
        use_container_width=True,
        hide_index=True,
        column_config={
            "내용": st.column_config.TextColumn(width="large"),
            "평균": st.column_config.ProgressColumn(format="%.2f", min_value=1, max_value=5),
            "긍정률(%)": st.column_config.NumberColumn(format="%.1f%%"),
            "부정률(%)": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )
    st.caption("긍정률 = (그렇다 + 매우 그렇다) / 응답수 · 부정률 = (전혀 아니다 + 아니다) / 응답수")

    best = stats.loc[stats["평균"].idxmax()]
    worst = stats.loc[stats["평균"].idxmin()]
    st.markdown(
        f"- 가장 높게 인식된 항목: **{best['문항']} {best['내용']}** (평균 {best['평균']})\n"
        f"- 가장 낮게 인식된 항목: **{worst['문항']} {worst['내용']}** (평균 {worst['평균']})"
    )

    with st.expander("응답 원자료 보기 / 다운로드"):
        raw = df.copy()
        raw["created_at"] = raw["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(raw, use_container_width=True, hide_index=True)
        d1, d2 = st.columns(2)
        d1.download_button("문항별 통계 CSV", stats.to_csv(index=False).encode("utf-8-sig"),
                           "survey_stats.csv", "text/csv", use_container_width=True)
        d2.download_button("응답 원자료 CSV", raw.to_csv(index=False).encode("utf-8-sig"),
                           "survey_raw.csv", "text/csv", use_container_width=True)


# ------------------------------------------------------------------ Tab 3: 시각화
def tab_visualize(df: pd.DataFrame) -> None:
    stats = build_stats(df)
    stats["라벨"] = [_label(q) for q in QUESTION_COLS]
    dist = distribution_long(df)

    # 1) 문항별 평균
    st.subheader("① 문항별 평균 점수")
    fig = px.bar(stats, x="평균", y="라벨", orientation="h", text="평균",
                 range_x=[0, 5], color_discrete_sequence=["#4f46e5"],
                 hover_data={"내용": True, "라벨": False})
    fig.update_layout(yaxis={"categoryorder": "array", "categoryarray": stats["라벨"][::-1]},
                      yaxis_title=None, height=420, margin=dict(l=0, r=10, t=10, b=0))
    fig.add_vline(x=3, line_dash="dot", line_color="gray", annotation_text="보통(3)")
    st.plotly_chart(fig, use_container_width=True)

    # 2) 응답 분포 (100% 누적 막대)
    st.subheader("② 문항별 응답 분포 (100% 누적)")
    fig = px.bar(dist, x="비율(%)", y="문항", color="응답", orientation="h", text="비율(%)",
                 category_orders={"응답": list(SCALE.values()), "문항": stats["라벨"].tolist()},
                 color_discrete_map=SCALE_COLORS, hover_data=["응답수"])
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="inside", insidetextanchor="middle")
    fig.update_layout(barmode="stack", xaxis_range=[0, 100], yaxis_title=None, height=440,
                      legend=dict(orientation="h", y=-0.15, title=None), margin=dict(l=0, r=10, t=10, b=0))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    # 3) 레이더 차트
    with left:
        st.subheader("③ 인식 프로파일 (레이더)")
        theta = stats["라벨"].tolist() + [stats["라벨"].iloc[0]]
        r = stats["평균"].tolist() + [stats["평균"].iloc[0]]
        fig = go.Figure(go.Scatterpolar(r=r, theta=theta, fill="toself", name="평균",
                                        line_color="#4f46e5"))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5], dtick=1)), showlegend=False,
                          height=420, margin=dict(l=80, r=80, t=30, b=30))
        st.plotly_chart(fig, use_container_width=True)

    # 4) 선택 문항 상세
    with right:
        st.subheader("④ 문항별 상세 분포")
        q = st.selectbox("문항 선택", QUESTION_COLS, format_func=lambda x: f"Q{x[1:]}. {QUESTIONS[x]}")
        one = dist[dist["문항"] == _label(q)]
        fig = px.pie(one, names="응답", values="응답수", hole=0.45, color="응답",
                     color_discrete_map=SCALE_COLORS, category_orders={"응답": list(SCALE.values())})
        fig.update_traces(textinfo="percent+label", sort=False)
        fig.update_layout(height=360, showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # 5) 일자별 참여 추이
    st.subheader("⑤ 일자별 응답 건수 추이")
    daily = df.dropna(subset=["created_at"]).groupby(df["created_at"].dt.date).size().reset_index(name="응답수")
    daily.columns = ["날짜", "응답수"]
    fig = px.bar(daily, x="날짜", y="응답수", text="응답수")
    fig.update_layout(height=300, xaxis_title=None, margin=dict(l=0, r=10, t=10, b=0))
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------ 진입점
def render_survey_page(hero_fn) -> None:
    hero_fn("설문참여", "AI의 교육적 효과에 대한 인식 설문에 참여하고, 전체 결과를 확인합니다.", "SURVEY")
    t1, t2, t3 = st.tabs(["📝 설문응시", "📊 설문 결과", "📈 시각화"])
    with t1:
        tab_take_survey()

    df = _load_df()
    with t2:
        if df.empty:
            st.info("아직 응답 데이터가 없습니다. '설문응시' 탭에서 첫 응답을 남겨 주세요.")
        else:
            tab_results(df)
    with t3:
        if df.empty:
            st.info("시각화할 응답 데이터가 없습니다.")
        else:
            tab_visualize(df)
