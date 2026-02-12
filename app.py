import streamlit as st
import pandas as pd
import plotly.express as px
from ydata_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report

# 페이지 설정
st.set_page_config(page_title="데이터 만능 분석기", layout="wide")

st.title("📊 데이터 자동 분석 및 종합 리포트")

uploaded_file = st.file_uploader("데이터 파일 업로드 (csv, xlsx)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 1. 파일 확장자 확인 및 데이터 로드 방식 결정
    try:
        df = None
        
        # [CASE A] 엑셀 파일일 경우: 시트 선택 기능 추가
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            # 엑셀 파일 자체를 로드 (데이터는 아직 안 읽음)
            xl_file = pd.ExcelFile(uploaded_file)
            sheet_names = xl_file.sheet_names
            
            # 시트가 여러 개라면 선택박스 표시
            if len(sheet_names) > 1:
                st.info(f"💡 이 엑셀 파일에는 {len(sheet_names)}개의 시트가 있습니다.")
                selected_sheet = st.selectbox("분석할 시트를 선택하세요:", sheet_names)
                # 선택한 시트만 데이터프레임으로 변환
                df = xl_file.parse(selected_sheet)
            else:
                # 시트가 1개뿐이면 바로 로드
                df = xl_file.parse(sheet_names[0])

        # [CASE B] CSV 파일일 경우: 인코딩 자동 처리
        elif uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0) # 커서 초기화
                df = pd.read_csv(uploaded_file, encoding='cp949')

        else:
            st.error("지원하지 않는 파일 형식입니다.")

        # 2. 데이터가 정상적으로 로드되었다면 분석 시작
        if df is not None:
            st.success(f"✅ 데이터 로드 성공! ({df.shape[0]}행, {df.shape[1]}열)")
            
            # ... (이후 탭(Tab) 생성 및 시각화 코드는 기존과 동일하게 유지) ...
            
            # 여기에 아까 작성한 tab1, tab2, tab3 코드가 이어지면 됩니다.

    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")

    df = load_data(uploaded_file)

    if df is not None:
        # 탭 구성: 미리보기 / 내 마음대로 시각화 / AI 종합 리포트
        tab1, tab2, tab3 = st.tabs(["📄 데이터 미리보기", "🎨 내 마음대로 시각화", "🤖 AI 종합 리포트"])

        # Tab 1: 기본 데이터 확인
        with tab1:
            st.dataframe(df.head())
            st.write(f"데이터 크기: {df.shape}")

        # Tab 2: 기존의 인터랙티브 시각화 (사용자가 직접 선택)
        with tab2:
            st.subheader("원하는 컬럼을 선택해 그래프 그리기")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                x_col = st.selectbox("X축 선택", numeric_cols)
                y_col = st.selectbox("Y축 선택", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                
                fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("수치형 데이터가 없어 산점도를 그릴 수 없습니다.")

        # Tab 3: ydata-profiling (수정된 버전)
        with tab3:
            st.write("데이터의 기초 통계, 결측치, 상관관계 등을 한 번에 분석합니다.")
            
            if st.button("종합 분석 리포트 생성하기"):
                with st.spinner("리포트를 생성 중입니다... 잠시만 기다려주세요."):
                    
                    # 1. 리포트 생성
                    pr = ProfileReport(df, minimal=True)
                    
                    # 2. HTML로 변환하여 화면에 표시 (이 방식이 더 안정적임)
                    report_html = pr.to_html()
                    components.html(report_html, height=800, scrolling=True)