OAuth(ADC) 전환 완료
변경 내용:

항목 이전 변경 후
인증 방식 .env의 GEMINI_API_KEY Google OAuth (ADC) 우선, API Key 폴백
쿼터 API Key 무료 할당량 Google Cloud 프로젝트 할당량 (별도)
코드 3개 파일에서 각각 genai.configure(api_key=...)
data/gemini_config.py
에서 중앙 관리
구성:

data/gemini_config.py
— ADC 자동 감지 → 실패 시 API Key 폴백
인증 순서: OAuth (ADC) → API Key → 경고
Quota project: gen-lang-client-0731404465 (Gemini 프로젝트)
참고: ADC 토큰이 만료되면 gcloud auth application-default login을 다시 실행하면 됩니다.
