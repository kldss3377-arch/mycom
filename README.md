# Streamlit Auth WebApp + AI 교육효과 인식 설문

## 실행 방법
```bash
pip install -r requirements.txt
streamlit run app.py
```
처음 실행하면 같은 폴더에 `mycom.db`(SQLite3)가 자동으로 만들어집니다.

## 파일 구성
| 파일 | 역할 |
|---|---|
| app.py | 메인 화면과 메뉴 (기존 코드 유지 + `설문참여` 메뉴 추가) |
| survey.py | **신규** 설문참여 화면 (설문응시 / 설문 결과 / 시각화 탭) |
| database.py | SQLite 연결, 테이블 생성(user_table, survey_table 등), 설문 저장·조회 |
| auth.py | 회원가입 검증, PBKDF2 비밀번호 해시, 로그인 |
| ui.py | Hero, Metric 카드, Tailwind + Alpine.js 헤더 |
| assets/style.css | 반응형 공통 CSS |
| scripts/mycom.sql | 테이블 생성 SQL (참고용) |
| data/ | `data.csv`를 넣으면 레거시 데이터로 1회 옮겨 저장 |

## 설문 기능
- 로그인 → 사이드바 → **설문참여**
- **설문응시**: Q1~Q10 (5점 척도: 1 전혀 아니다 ~ 5 매우 그렇다). 10문항에 모두 답해야 저장됩니다.
  - `survey_table.user_id` = 로그인 아이디, `created_at` = 응답 시각(한국시간, `YYYY-MM-DD HH:MM:SS`)
  - 다시 제출하면 새 응답으로 추가 저장됩니다.
- **설문 결과**: 총 응답 수, 참여자 수, 전체 평균, 긍정률, 문항별 평균·표준편차·척도별 빈도·긍정률·부정률, CSV 다운로드
- **시각화**: 문항별 평균, 100% 누적 분포, 레이더 차트, 문항별 도넛 차트, 일자별 응답 추이

설문 문항을 바꾸려면 `survey.py` 맨 위의 `QUESTIONS`(문항 전문)와 `SHORT`(차트용 짧은 이름)만 고치면 됩니다.
