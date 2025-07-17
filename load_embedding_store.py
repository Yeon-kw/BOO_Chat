from loader.load_documents import *
from loader.vectorstore import store_documents_to_pinecone, delete_documents_by_metadata

from config import INDEX_NAME, PINECONE_API_KEY, OPENAI_API_KEY,EMBEDDING_DIM

def main():
    # 1. 경로 설정
    timetable_path = "data/Timetable_Crawling_Data"
    guidebook_path = "data/major_guide_2025.pdf"
    pram_path = "data/pram_2025_1.json"
    prof_path = "data/hufs_professor.json"
    college_path = "data/hufs_colleges.json"
    notice_path = "data/hufs_notice.json"
    schedule_path = "data/hufs_schedule.json"
    '''
    # 2. 문서 로드
    print("강의시간표 로드 중...")
    subject_docs = load_all_subject_documents(timetable_path)

    print("전공가이드북 로드 중...")
    guidebook_docs = load_major_guidebook(guidebook_path)

    print("수강편람 로드 중...")
    pram_docs = load_sugang_pram(pram_path)

    print("교수진 정보 로드 중...")
    prof_docs = load_professor_documents(prof_path)

    print("단과대 정보 로드 중...")
    college_docs = load_college_intro(college_path)

    print("학사공지 로드 중...")
    notice_docs = load_notice_documents(notice_path)

    print("학사일정 로드 중...")
    schedule_docs = load_academic_schedule(schedule_path)

    # 3. 벡터스토어 저장 (하나의 통합 인덱스 사용)

    print("Pinecone에 문서 저장 시작...")
    store_documents_to_pinecone(subject_docs, index_name=INDEX_NAME, openai_api_key=OPENAI_API_KEY, 
                                pinecone_api_key=PINECONE_API_KEY, embedding_dim = EMBEDDING_DIM)
    store_documents_to_pinecone(guidebook_docs, index_name=INDEX_NAME, openai_api_key=OPENAI_API_KEY,
                                 pinecone_api_key=PINECONE_API_KEY, embedding_dim = EMBEDDING_DIM)
    store_documents_to_pinecone(pram_docs, index_name=INDEX_NAME, openai_api_key=OPENAI_API_KEY,
                                 pinecone_api_key=PINECONE_API_KEY, embedding_dim = EMBEDDING_DIM)
    store_documents_to_pinecone(prof_docs, index_name=INDEX_NAME, openai_api_key=OPENAI_API_KEY, 
                                pinecone_api_key=PINECONE_API_KEY, embedding_dim = EMBEDDING_DIM)
    store_documents_to_pinecone(college_docs, index_name=INDEX_NAME, openai_api_key=OPENAI_API_KEY,
                                 pinecone_api_key=PINECONE_API_KEY, embedding_dim = EMBEDDING_DIM)
    store_documents_to_pinecone(notice_docs, index_name=INDEX_NAME, openai_api_key=OPENAI_API_KEY,
                                 pinecone_api_key=PINECONE_API_KEY, embedding_dim = EMBEDDING_DIM)
    store_documents_to_pinecone(schedule_docs, index_name=INDEX_NAME, openai_api_key=OPENAI_API_KEY,
                                 pinecone_api_key=PINECONE_API_KEY, embedding_dim = EMBEDDING_DIM)
    print("모든 문서 저장 완료.")
    '''
    # 4. 수정문서 적용
    for doc_type, loader_func, path in [
    ("학사공지", load_notice_documents, notice_path)
    ]:
        print(f"📌 '{doc_type}' 기존 벡터 삭제 중...")
        delete_documents_by_metadata(INDEX_NAME, PINECONE_API_KEY, "doc_type", doc_type)
        print(f"{doc_type} 로드 중...")
        docs = loader_func(path)
        store_documents_to_pinecone(docs, INDEX_NAME, OPENAI_API_KEY, PINECONE_API_KEY, EMBEDDING_DIM)

if __name__ == "__main__":
    main()
