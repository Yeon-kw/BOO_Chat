import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 유틸 함수: td 내부에 <img> 태그가 존재하면 "Y", 없으면 "N"
def has_img(td):
    return "Y" if td.find("img") else "N"

def extract_and_save_courses(driver, csv_filename,s_path):
    """
    Selenium driver가 현재 body 프레임에 있을 때,
    전공 선택 요소를 순회하며 각 전공의 과목 정보를 파싱하고 CSV 파일로 저장하는 함수입니다.
    
    파싱 순서는:
        - 개설영역: 현재 선택한 전공명
        - 학년: td[2]
        - 학수번호: td[3]
        - 교과목명: td[4] 내부 텍스트
        - 강의계획서: td[5]에 <a> 태그 존재 여부 ("있음"/"없음")
        - 전필: td[6] 내 <img> 유무 ("Y"/"N")
        - 온라인: td[7] 내 <img> 유무 ("Y"/"N")
        - P/F: td[8] 내 <img> 유무 ("Y"/"N")
        - 원어: td[9] 내 <img> 유무 ("Y"/"N")
        - Team Teaching: td[10] 내 <img> 유무 ("Y"/"N")
        - 담당교수: td[11]
        - 학점: td[12]
        - 시간: td[13]
        - 강의시간/강의실: td[14]
        - 신청/제한인원: td[15] (공백 치환)
        - 예비수강신청: td[16]
        - 비고: td[17]
        
    :param driver: Selenium WebDriver (body 프레임에 접근 가능한 상태여야 함)
    :param csv_filename: 저장할 CSV 파일명 (예: "전공_과목정보_전체.csv")
    :return: 추출한 데이터가 담긴 pandas DataFrame
    """
    time.sleep(1)
    # 최종 화면이 body 프레임에 있도록 전환
    driver.switch_to.default_content()
    driver.switch_to.frame("body")
    
    # 전공 선택 요소 찾기
    select_element = driver.find_element(By.XPATH,s_path)
    select = Select(select_element)
    
    all_data = []
    
    # 전공 옵션을 순회하면서 데이터 추출
    for idx in range(len(select.options)):
        select.select_by_index(idx)
        current_major = select.options[idx].text.strip()
        print(f"{idx+1}번째 전공 선택됨: {current_major}")
        
        time.sleep(3)  # 페이지 갱신 시간 확보
        
        # tbody id="lssnlist" 내부의 HTML 추출 및 파싱
        tbody_html = driver.find_element(By.ID, "lssnlist").get_attribute("innerHTML")
        soup = BeautifulSoup(tbody_html, "html.parser")
        rows = soup.find_all("tr")
        
        for row in rows:
            tds = row.find_all("td")
            # 번호 포함 18개 항목이 있어야 파싱 진행
            if len(tds) < 18:
                continue
            
            lecture_plan = "있음" if tds[5].find("a") else "없음"
            row_data = {
                "개설영역": current_major,
                "학년": tds[2].get_text(strip=True),
                "학수번호": tds[3].get_text(strip=True),
                "교과목명": tds[4].get_text(strip=True),
                "강의계획서": lecture_plan,
                "전필": has_img(tds[6]),
                "온라인": has_img(tds[7]),
                "P/F": has_img(tds[8]),
                "원어": has_img(tds[9]),
                "Team Teaching": has_img(tds[10]),
                "담당교수": tds[11].get_text(strip=True),
                "학점": tds[12].get_text(strip=True),
                "시간": tds[13].get_text(strip=True),
                "강의시간/강의실": tds[14].get_text(strip=True),
                "신청/제한인원": tds[15].get_text(strip=True).replace("\xa0", " "),
                "예비수강신청": tds[16].get_text(strip=True),
                "비고": tds[17].get_text(strip=True)
            }
            all_data.append(row_data)
    
    df = pd.DataFrame(all_data)
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    print("CSV 파일 저장 완료:", csv_filename)
    return df

if __name__ == "__main__":
    # Selenium WebDriver 실행 및 초기 작업
    chromedriver = 'chromedriver.exe'
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = 'https://www.hufs.ac.kr/hufs/11422/subview.do?enc=Zm5jdDF8QEB8JTJGc3ViTG9naW4lMkZodWZzJTJGdmlldy5kbyUzRg%3D%3D'
    driver.get(url)
    
    # 로그인 및 초기 클릭 작업
    driver.find_element(By.XPATH, '/html/body/div[4]/div/main/div/article/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/form/div[1]/div[1]/input').send_keys("201902603")
    driver.find_element(By.XPATH, '/html/body/div[4]/div/main/div/article/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/form/div[1]/div[2]/input[1]').send_keys("alsh030815@\n")
    driver.find_element(By.XPATH, "/html/body/div[5]/div/div[3]/div[2]/button").click()
    time.sleep(2)
    driver.fullscreen_window()
    driver.find_element(By.XPATH, "/html/body/header/div/div/div[4]/ul/li[2]/a/span").click()
    driver.find_element(By.XPATH, "/html/body/div[4]/div/main/div[2]/article/div/div[2]/div[1]/div/div[1]/div/div[1]/button").click()
    window_handles = driver.window_handles
    driver.switch_to.window(window_handles[-1])
    driver.find_element(By.XPATH, "/html/body/div[2]/form/div[2]/button[2]").click()
    time.sleep(2)
    # 프레임 전환 (left -> MenuFrame)
    driver.switch_to.frame("left")
    driver.switch_to.frame("MenuFrame")
    driver.find_element(By.XPATH, "/html/body/div/a[3]").click()
    driver.find_element(By.XPATH, "/html/body/div/div[3]/a[3]").click()
    time.sleep(2)
    trash=input("크롤링할 년도,학기 전환후 학기 입력")
    # 최종 화면이 body 프레임에 있도록 전환
    driver.switch_to.default_content()
    driver.switch_to.frame("body")
    
    # 하나의 함수로 데이터 추출 및 CSV 저장
    df_courses = extract_and_save_courses(driver, trash+"전공_과목정보(글로벌).csv","/html/body/div/form/div[1]/table[2]/tbody/tr[1]/td/div[1]/select")
    driver.find_element(By.XPATH, "/html/body/div/form/div[1]/table[2]/tbody/tr[1]/th/div[2]/label").click()
    driver.find_element(By.XPATH, "/html/body/div/form/div[2]/button").click()
    time.sleep(3)
    df_courses = extract_and_save_courses(driver, trash+"교양_과목정보(글로벌).csv","/html/body/div/form/div[1]/table[2]/tbody/tr[1]/td/div[2]/select")
    """driver.find_element(By.XPATH, "/html/body/div/form/div[1]/table[2]/tbody/tr[1]/th/div[3]/label").click()
    driver.find_element(By.XPATH, "/html/body/div/form/div[2]/button").click()
    time.sleep(3)
    df_courses = extract_and_save_courses(driver, trash+"기초_과목정보(글로벌).csv","/html/body/div/form/div[1]/table[2]/tbody/tr[1]/td/div[3]/select")
    driver.find_element(By.XPATH, "/html/body/div/form/div[1]/table[1]/tbody/tr/td[3]/label[1]").click()
    driver.find_element(By.XPATH, "/html/body/div/form/div[2]/button").click()"""
    time.sleep(3)
    driver.find_element(By.XPATH, "/html/body/div/form/div[1]/table[2]/tbody/tr[1]/th/div[1]/label").click()
    driver.find_element(By.XPATH, "/html/body/div/form/div[2]/button").click()
    time.sleep(3)
    df_courses = extract_and_save_courses(driver, trash+"전공_과목정보(서울).csv","/html/body/div/form/div[1]/table[2]/tbody/tr[1]/td/div[1]/select")
    driver.find_element(By.XPATH, "/html/body/div/form/div[1]/table[2]/tbody/tr[1]/th/div[2]/label").click()
    driver.find_element(By.XPATH, "/html/body/div/form/div[2]/button").click()
    time.sleep(3)
    df_courses = extract_and_save_courses(driver, trash+"교양_과목정보(서울).csv","/html/body/div/form/div[1]/table[2]/tbody/tr[1]/td/div[2]/select")
    """driver.find_element(By.XPATH, "/html/body/div/form/div[1]/table[2]/tbody/tr[1]/th/div[3]/label").click()
    driver.find_element(By.XPATH, "/html/body/div/form/div[2]/button").click()
    time.sleep(3)
    df_courses = extract_and_save_courses(driver, trash+"기초_과목정보(서울).csv","/html/body/div/form/div[1]/table[2]/tbody/tr[1]/td/div[3]/select")"""##작년도 기초과목 없음
    
    print(df_courses)
    driver.quit()
