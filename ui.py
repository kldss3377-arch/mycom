"""공통 UI 컴포넌트 (CSS, Hero, Metric 카드, 헤더)."""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

CSS_PATH = Path(__file__).resolve().parent / "assets" / "style.css"


def load_css() -> None:
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def hero(title: str, subtitle: str, eyebrow: str = "WELCOME") -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-eyebrow">{html.escape(eyebrow)}</div>
          <h1 class="hero-title">{html.escape(title)}</h1>
          <p class="hero-sub">{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_cards(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="metric-card"><div class="metric-label">{html.escape(str(k))}</div>'
        f'<div class="metric-value">{html.escape(str(v))}</div></div>'
        for k, v in items
    )
    st.markdown(f'<div class="metric-row">{cards}</div>', unsafe_allow_html=True)


def render_modern_header(username: str | None) -> None:
    """Tailwind + Alpine.js 헤더 (iframe 컴포넌트)."""
    if username:
        right = (
            f'<span class="text-sm text-slate-600">👤 {html.escape(username)}님</span>'
            '<a href="?action=logout" target="_top" '
            'class="rounded-lg bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700">로그아웃</a>'
        )
    else:
        right = (
            '<a href="?view=register" target="_top" class="text-sm text-slate-700 hover:text-indigo-600">사용자 등록</a>'
            '<a href="?view=login" target="_top" '
            'class="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-500">로그인</a>'
        )
    components.html(
        f"""
        <script src="https://cdn.tailwindcss.com"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
        <style>[x-cloak]{{display:none !important}}</style>
        <header x-data="{{ open: false }}" class="font-sans">
          <div class="flex items-center justify-between rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 shadow-sm">
            <a href="?view=home" target="_top" class="flex items-center gap-2 font-bold text-slate-900">
              <span class="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-white">🔐</span>
              Streamlit Auth WebApp
            </a>
            <nav class="hidden items-center gap-3 sm:flex">{right}</nav>
            <button @click="open = !open" class="sm:hidden rounded-md border px-2 py-1 text-slate-700">☰</button>
          </div>
          <nav x-cloak x-show="open" x-transition class="mt-2 flex flex-col gap-2 rounded-xl border bg-white p-3 sm:hidden">{right}</nav>
        </header>
        """,
        height=74,
    )
