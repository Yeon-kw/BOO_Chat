from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
<<<<<<< Updated upstream
from bs4 import BeautifulSoup
=======
from webdriver_manager.chrome import ChromeDriverManager 
from bs4 import BeautifulSoup
from bs4 import Tag
>>>>>>> Stashed changes
import json
import time

# Culture&Technology융합대학 전용 처리 함수(웹페이지 구성이 타단과대와 다름)
def parse_ct_college(soup, name):
    # 단과대학 전체 소개
    introduction_tag = soup.find("p", class_="con-desc mt30")
    introduction = introduction_tag.get_text(strip=True) if introduction_tag else "소개 정보가 없습니다"

    # 전화번호: 학부명 텍스트 기준으로 수동 매핑
    tel_dict = {
        "글로벌스포츠산업학부": "031-330-4524",
        "디지털콘텐츠학부": "031-330-4067",
        "투어리즘 & 웰니스학부": None  # 없음
    }

    combined_phones = []
    for dept, phone in tel_dict.items():
        if phone:
            combined_phones.append(f"{dept} {phone}")

    return {
        "college": name,
        "introduction": introduction,
        "phone": " / ".join(combined_phones) if combined_phones else "전화번호 없음"
    }

<<<<<<< Updated upstream
# 크롬 드라이버 설정
options = Options()
options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--user-data-dir=C:/temp/chrome_profile")

service = Service("chromedriver.exe")
=======
# 통번역대학, 국제지역대학 전용 함수
def parse_sp_college(soup, college_name):
    intro_tag = soup.find("p", class_="con-desc mt30")
    introduction = intro_tag.get_text(" ", strip=True) if intro_tag else "소개 정보가 없습니다"

    dept_headers = soup.select("div.heading-buttuon.type2")
    phone_entries = []

    for header in dept_headers:
        name_tag = header.find("h2", class_="objHeading_h3")
        if not name_tag:
            continue
        dept_name = name_tag.get_text(strip=True)

        phone = None
        for tag in header.find_all_next():
            if tag.name=="div" and "heading-buttuon" in tag.get("class", []):
                break
            if tag.name=="div" and "location-list" in tag.get("class", []):
                li = tag.find("li", class_="ico2")
                if li and (p:=li.find("p")):
                    phone = p.get_text(strip=True)
                break

        if phone:
            phone_entries.append(f"{dept_name} {phone}")

    return {
        "college": college_name,
        "introduction": introduction,
        "phone": " / ".join(phone_entries) if phone_entries else "전화번호 없음"
    }

#AI융합전공 전용 함수
def parse_ai_college(soup, college_name):
    intro_tag = soup.find("p", class_="con-desc mt30")
    introduction = intro_tag.get_text(" ", strip=True) if intro_tag else "소개 정보가 없습니다"

    phone_entries = []
    for header in soup.select("div.heading-buttuon.type2"):
        name_tag = header.select_one("h2.objHeading_h3")
        if not name_tag:
            continue
        dept_name = name_tag.get_text(strip=True)

        phone = None
        for tag in header.find_all_next():
            if (isinstance(tag, Tag)
                and tag.name == "div"
                and "heading-buttuon" in tag.get("class", [])):
                break

            if (isinstance(tag, Tag)
                and tag.name == "div"
                and "location-list" in tag.get("class", [])):
                p = tag.select_one("li.ico2 p")
                if p:
                    phone = p.get_text(strip=True)
                break

        if phone:
            phone_entries.append(f"{dept_name} {phone}")

    return {
        "college": college_name,
        "introduction": introduction,
        "phone": " / ".join(phone_entries) if phone_entries else "전화번호 없음"
    }


# 크롬 드라이버 설정
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
service = Service(ChromeDriverManager().install())
>>>>>>> Stashed changes
driver = webdriver.Chrome(service=service, options=options)

# 단과대학 리스트
college_urls = [
    {"name": "인문대학", "url": "https://www.hufs.ac.kr/hufs/11240/subview.do"},
    {"name": "통번역대학", "url": "https://www.hufs.ac.kr/hufs/11241/subview.do"},
    {"name": "국가전략언어대학", "url": "https://www.hufs.ac.kr/hufs/11242/subview.do"},
    {"name": "국제지역대학", "url": "https://www.hufs.ac.kr/hufs/11243/subview.do"},
    {"name": "경상대학", "url": "https://www.hufs.ac.kr/hufs/11244/subview.do"},
    {"name": "자연과학대학", "url": "https://www.hufs.ac.kr/hufs/11245/subview.do"},
    {"name": "공과대학", "url": "https://www.hufs.ac.kr/hufs/11246/subview.do"},
    {"name": "융합인재대학", "url": "https://www.hufs.ac.kr/hufs/11247/subview.do"},
    {"name": "Culture&Technology융합대학", "url": "https://www.hufs.ac.kr/hufs/11248/subview.do"},
<<<<<<< Updated upstream
    {"name": "AI융합대학", "url": "https://www.hufs.ac.kr/hufs/11247/subview.do"},
=======
    {"name": "AI융합대학", "url": "https://www.hufs.ac.kr/hufs/11249/subview.do"},
>>>>>>> Stashed changes
    {"name": "바이오메디컬공학부", "url": "https://www.hufs.ac.kr/hufs/11250/subview.do"},
    {"name": "기후변화융합학부", "url": "https://www.hufs.ac.kr/hufs/11252/subview.do"},
    {"name": "자유전공학부", "url": "https://www.hufs.ac.kr/hufs/11251/subview.do"}
]

college_data = []

# 메인 크롤링
for college in college_urls:
    driver.get(college["url"])
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 특수 처리: Culture&Technology융합대학
    if college["name"] == "Culture&Technology융합대학":
<<<<<<< Updated upstream
        print(f"{college['name']} 특수 처리 중...")
        result = parse_ct_college(soup, college["name"])
    else:
        # 일반 단과대학 처리
=======
        result = parse_ct_college(soup, college["name"])
        
    # 특수 처리: 통번역대학, 국제지역대학  
    elif college["name"] == "통번역대학" or college["name"] == "국제지역대학":
        result = parse_sp_college(soup, college["name"])

    # 특수 처리: AI융합대학
    elif college["name"] == "AI융합대학":
        result = parse_ai_college(soup, college["name"])

    # 그 외 다른 단과대학 처리
    else:
>>>>>>> Stashed changes
        introduction_tag = soup.find("p", class_="con-desc mt30")
        introduction = introduction_tag.get_text(strip=True) if introduction_tag else "소개 정보가 없습니다"

        phone = "전화번호 없음"
        tel_block = soup.find("li", class_="ico2")
        if tel_block and "전화번호" in tel_block.get_text():
            full_text = tel_block.get_text(separator=" ", strip=True)
            phone = full_text.replace("전화번호", "").strip()

        result = {
            "college": college["name"],
            "introduction": introduction,
            "phone": phone
        }

    college_data.append(result)

    # 출력
    print(f"\n✅ {result['college']}")
    print(f"소개: {result['introduction'][:60]}...")
    print(f"전화번호: {result['phone']}")

driver.quit()

# JSON 저장
with open("hufs_colleges.json", "w", encoding="utf-8") as f:
    json.dump(college_data, f, ensure_ascii=False, indent=2)

print("모든 단과대학 정보가 'hufs_colleges.json' 파일로 저장 완료되었습니다!")



