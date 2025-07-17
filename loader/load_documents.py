from langchain.schema import Document
import json
import pandas as pd
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from collections import defaultdict
import os
import re
from typing import List



# 데이터의 불필요한 공백 제거
def clean_page_content(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


# 단과대 정보 1 = 1 document
def load_college_intro(file_path: str, doc_type: str = "단과대정보") -> list[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []
    for entry in data:
        page_content = f"{entry['college']}\n\n{entry['introduction']}\n\n{entry['phone']}"
        metadata = {
            "doc_type": doc_type,
            "college": entry["college"],
            "phone": entry["phone"]
        }
        documents.append(Document(page_content=page_content.strip(), metadata=metadata))

    return documents


# 1 공지 = 1 document
def load_notice_documents(file_path: str, doc_type: str = "학사공지") -> list[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_documents = []
    for entry in data:
        raw_text = clean_page_content(entry["page_content"])
        page_content = f"{entry['title']}\n\n{raw_text}"
        metadata = {
            "doc_type": doc_type,
            "title": entry["title"],
            "author": entry["author"],
            "date": entry["date"],
            "url": entry["url"],
            "ntt_id": entry["ntt_id"]
        }
        raw_documents.append(Document(page_content=page_content, metadata=metadata))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    chunked_documents = splitter.split_documents(raw_documents)

    # 제목을 각 chunk에 반복 삽입 : 하나의 문서가 분할되었을 경우 키워드 역할
    for doc in chunked_documents:
        title = doc.metadata.get("title", "")
        doc.page_content = f"{title}\n\n{doc.page_content.strip()}"

    return chunked_documents


# 전부 "0000년 0월 0일은 (이벤트명) 기간입니다. (요일)" 형식이기 때문에 불필요한 정보 제거 후 (이벤트명)만 추출
def normalize_event_name(text: str) -> str:
    text = re.sub(r"\d{4}년\s*\d{1,2}월\s*\d{1,2}일", "", text)

    # 조사 및 불필요한 표현 제거
    text = re.sub(r"(은|는|이|가)\s*", "", text)
    text = re.sub(r"(입니다|기간입니다|기간|안내)", "", text)

    # 마침표, 특수문자, 공백 정리
    text = re.sub(r"[·\.\-]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

'''
# 학사일정 로드 및 문서 생성 - 이전버전, 제거
def load_academic_schedule(file_path: str, doc_type: str = "학사일정") -> List[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grouped = defaultdict(list)

    for year, semesters in data.items():
        for semester, months in semesters.items():
            for month, days in months.items():
                for date, info in days.items():
                    weekday = info["weekday"]
                    entry = f"{date} ({weekday})"
                    event_name = normalize_event_name(info["text"])

                    # 이벤트 그룹 키: 같은 이벤트 + 학기면 하나로 묶임
                    key = (year, semester, event_name)
                    grouped[key].append(entry)

    documents = []
    for (year, semester, event), date_list in grouped.items():
        date_list.sort()
        page_content = f"{event} 일정 :\n" + "\n".join(date_list)
        metadata = {
            "doc_type": doc_type,
            "event": event,
            "year": year,
            "semester": semester,
            "num_dates": len(date_list),
            "dates": date_list
        }
        documents.append(Document(page_content=page_content.strip(), metadata=metadata))

    return documents
'''
# # 학사일정 로드 및 문서 생성 - 최신버전
def load_academic_schedule(file_path: str, doc_type: str = "학사일정") -> List[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grouped = defaultdict(list)
    metadata_tracker = defaultdict(lambda: {"years": set(), "semesters": set()})

    for year, semesters in data.items():
        for semester, months in semesters.items():
            for month, days in months.items():
                for date, info in days.items():
                    for event in info.get("events", []):
                        weekday = event["weekday"]
                        entry = f"{date} ({weekday})"
                        event_name = normalize_event_name(event["text"])

                        key = event_name  # ✅ 년도 포함하지 않고 순수 이벤트명으로 그룹
                        grouped[key].append(entry)
                        metadata_tracker[key]["years"].add(year)
                        metadata_tracker[key]["semesters"].add(semester)

    documents = []
    for event, date_list in grouped.items():
        date_list.sort()
        meta = metadata_tracker[event]

        page_content = f"{event} 일정:\n" + "\n".join(date_list)
        metadata = {
            "doc_type": doc_type,
            "event": event,
            "years": sorted(meta["years"]),
            "semesters": sorted(meta["semesters"]),
            "num_dates": len(date_list),
            "dates": date_list
        }
        documents.append(Document(page_content=page_content.strip(), metadata=metadata))

    return documents

# 교수진 정보
def load_professor_documents(json_path: str, doc_type: str = "교수진 정보") -> List[Document]:
    """
    교수진 JSON 파일을 로드하여 LangChain Document로 변환합니다.
    """
    documents = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n", ".", " "]
    )

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    i = 0
    while i < len(data):
        meta_block = data[i]
        prof_list = data[i + 1] if (i + 1 < len(data)) and isinstance(data[i + 1], list) else []

        if isinstance(meta_block, dict):
            meta_key = list(meta_block.keys())[0]
            meta_value = meta_block[meta_key]
        else:
            i += 2
            continue

        for prof in prof_list:
            name = prof.get("이름", "정보없음")
            phrases = [f"{name} 교수님은 {meta_value} {meta_key} 소속입니다."]

            if prof.get("직위") and prof.get("직위") != "정보없음":
                phrases.append(f"{prof['직위']} 직위를 맡고 있습니다.")
            if prof.get("학위") and prof.get("학위") != "정보없음":
                phrases.append(f"{prof['학위']} 학위를 가지고 있습니다.")
            if prof.get("연구분야") and prof.get("연구분야") != "정보없음":
                phrases.append(f"연구분야는 {prof['연구분야']}입니다.")
            if prof.get("이메일") and prof.get("이메일") != "정보없음":
                phrases.append(f"이메일은 {prof['이메일']}입니다.")
            if prof.get("연구실") and prof.get("연구실") != "정보없음":
                phrases.append(f"연구실은 {prof['연구실']}입니다.")

            page_text = " ".join(phrases)

            # 메타데이터 구성
            base_metadata = {
                meta_key: meta_value,
                "doc_type": doc_type
            }
            base_metadata.update({
                "이름": prof.get("이름", "정보없음"),
                "직위": prof.get("직위", "정보없음"),
                "학위": prof.get("학위", "정보없음"),
                "연구분야": prof.get("연구분야", "정보없음"),
                "전화번호": prof.get("전화번호", "정보없음"),
                "이메일": prof.get("이메일", "정보없음"),
                "연구실": prof.get("연구실", "정보없음")
            })

            # 자동 청킹
            if len(page_text) > 300:
                chunks = splitter.split_text(page_text)
                for chunk in chunks:
                    documents.append(Document(page_content=chunk, metadata=base_metadata))
            else:
                documents.append(Document(page_content=page_text, metadata=base_metadata))

        i += 2

    return documents

# 강의시간표 document load - 개설 영역별로 문서 분할, 자연어 형태의 문서로 생성, load_all_subject_documents에 종속

def load_subject_by_area(filepath: str, filename: str) -> list[Document]:
    df = pd.read_csv(filepath)
    documents = []

    # Yes/No 변환 대상 컬럼
    #yn_cols = ['전필', '온라인', 'P/F', '원어', 'Team Teaching']
    day_map = {'월': '월요일', '화': '화요일', '수': '수요일', '목': '목요일', '금': '금요일'}

    #def convert_yes_no(val):
    #    return 'Yes' if val == 'Y' else 'No'

    def parse_time_room(info):
        try:
            time_part, room_part = info.split('(')
            room = room_part.strip(')')
            day = day_map.get(time_part.strip()[0], time_part.strip()[0])
            hours = time_part.strip()[2:].replace(" ", ",")
            return f"{day} {hours}교시 / 강의실 {room}호"
        except:
            return info.strip()
        
    def build_extra_info(row):
        return " / ".join([
            "전공필수 과목 맞음" if row['전필'] == 'Y' else "전공필수 과목 아님",
            "온라인강의 맞음" if row['온라인'] == 'Y' else "온라인강의 아님",
            "P/F 평가 과목 맞음" if row['P/F'] == 'Y' else "P/F 평가 과목 아님"
            #"Team Teaching 과목 맞음" if row['Team Teaching'] == 'Y' else "Team Teaching 과목 아님"
        ])

    grouped = df.groupby("개설영역")

    for area, group_df in grouped:
        contents = []
        for _, row in group_df.iterrows():
            year_text = f"{int(float(row['학년']))}학년 대상" if pd.notna(row["학년"]) else "전체 학년 대상"
            time_room_text = parse_time_room(str(row['강의시간/강의실']))
            extra_info = build_extra_info(row)

            '''
            row_text = (
                f"[{row['교과목명']}] {year_text} / 교수: {row['담당교수']} / "
                f"강의시간: {time_room_text} / 학점: {row['학점']} / {extra_info}"
            )
            '''
            row_text = (
                f"[{area} /{filename[3:5]}/ {row['교과목명']}] / 교수: {row['담당교수']} / "
                f"{time_room_text} / 학점: {row['학점']} / {extra_info}"
            )
            
            contents.append(row_text)

        page_content = "\n\n".join(contents)
        metadata = {
            "filename": filename,
            "개설영역": area,
            "doc_type": "강의시간표"
        }
        documents.append(Document(page_content=page_content.strip(), metadata=metadata))

    return documents

# 강의시간표 파일들 읽어오는 함수
def load_all_subject_documents(directory: str) -> list[Document]:
    all_documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            documents = load_subject_by_area(filepath, filename)
            all_documents.extend(documents)
    return all_documents

# 전공 가이드북 PDF 로드 + 청킹
def load_major_guidebook(pdf_path: str) -> list[Document]:
    """
    전공 가이드북 PDF를 로드하여 페이지별로 청킹한 Document 리스트 반환
    - 페이지별 Document를 청킹하여 세부 정보 유지
    - metadata에는 source 경로만 포함
    """
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()  # 페이지별 Document 리스트

     # metadata에 doc_type 삽입
    for page in pages:
        page.metadata["doc_type"] = "전공가이드북"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(pages)
    return chunks


#  수강편람 JSON 로드 → 페이지별 Document 분리 → 청킹 적용
def load_sugang_pram(json_path: str, doc_type: str = "수강편람") -> list[Document]:
    with open(json_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    elements = result["elements"]
    page_chunks = defaultdict(list)

    for el in elements:
        page = el.get("page", 0)
        content = el.get("content", {}).get("markdown", "").strip()
        if content:
            page_chunks[page].append((el["category"], content, el))

    docs = []
    for page, items in page_chunks.items():
        combined_text = "\n\n".join(f"## [{cat}] ##\n{txt}" for cat, txt, _ in items)
        metadata = {
            "doc_type": doc_type,
            "page": page,
            "num_elements": len(items),
            "categories": list(set(cat for cat, _, _ in items)),
        }
        docs.append(Document(page_content=combined_text, metadata=metadata))

    # 청킹
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(docs)
    return chunks