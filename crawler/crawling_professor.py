from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json

# 브라우저 설정
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 드라이버 실행
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 💡 URL: 교수진 페이지
url = "https://sw.hufs.ac.kr/sw/14987/subview.do"
driver.get(url)

# 로딩 기다림
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "_prFlLi"))
)

# HTML 파싱
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# 교수 리스트 블록
professor_blocks = soup.select("li._prFlLi")
print(f"🔍 총 교수 수: {len(professor_blocks)}명")

professors = []

for i, prof in enumerate(professor_blocks, 1):
    name = prof.select_one(".artclTitle strong").text.strip()

    dls = prof.select(".artclInfo dl")
    info = {}
    for dl in dls:
        dt = dl.select_one("dt")
        dd = dl.select_one("dd")
        if dt and dd:
            key = dt.text.strip()
            value = dd.text.strip()
            # 빈 값이면 "정보없음"으로 처리
            info[key] = value if value != "" else "정보없음"

    # 교수 데이터 정리
    data = {
        "이름": name,
        "직위": info.get("직위(직급)", "정보없음"),
        "학위": info.get("학위", "정보없음"),
        "연구분야": info.get("연구분야", "정보없음"),
        "전화번호": info.get("전화번호", "정보없음"),
        "이메일": info.get("이메일", "정보없음"),
        "연구실": info.get("연구실", "정보없음")
    }

    professors.append(data)

    # 디버깅 출력
    print(f"\n[{i}] {name}")
    for k, v in data.items():
        print(f"  {k}: {v}")

# JSON 저장
with open("professors.json", "w", encoding="utf-8") as f:
    json.dump(professors, f, ensure_ascii=False, indent=4)

driver.quit()
print("\n✅ professors.json 저장 완료 (빈 값은 '정보없음'으로 대체됨)!")
