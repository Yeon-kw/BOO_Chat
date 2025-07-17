from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient
import os, time
from dotenv import load_dotenv
from uuid import uuid4
from operator import itemgetter

from pinecone import Pinecone
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.document_transformers import LongContextReorder
from langchain.chains import create_history_aware_retriever
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.chains import create_retrieval_chain

# .env 파일에서 API 키 로드
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def normalize_query(query: str) -> str:
    abbreviation_map = {
        "글스산": "글로벌스포츠산업전공",
        "바메공": "바이오메디컬공학전공",
        "BME": "바이오메디컬공학전공",
        "이중": "이중전공",
        "통대": "통번역대학",
        "공대": "공과대학",
        "일통": "일본어통번역학과",
        "영통": "영어통번역학과",
        "독통": "독일어통번역학과",
        "스통": "스페인어통번역학과",
        "마인어":"말레이시아인도네시아통번역학과",
        "GBT": "Global Business&Technology",
        "융인": "융합인재학과",
        "중통": "중국어통번역학과",
        "국금": "국제금융학과",
        "이통": "이탈리아어통번역학과",
        "태통": "태국어통번역학과",
        "정통": "정보통신공학과",
        "산공": "산업경영공학과",
        "산경공": "산업경영공학과",
        "파에": "Finance&AI융합학부",
        "데융": "AI데이터융합학부",
        "글자전": "글로벌자유전공학부",
        "자전": "글로벌자유전공학부",
        "대영": "대학영어",
        "데사":"데이터사이언스",
        "국리":"국가리더전공",
        "세크": "세르비아·크로아티아",
        "그불": "그리스·불가리아",
        "전물": "전자물리학과",
        "생공": "생명공학과",
        "디콘": "디지털콘텐츠학부",
        "자대": "자연과학대학",
        "인경관": "인문경상관",
        "국지대": "국제지역대학",
        "전언대": "국가전략언어대학",
        "전언": "국가전략언어",
        "국전언": "국가전략언어대학",
        "융소": "융복합소프트웨어전공"
        # 필요시 추가
    }
    
    for short, full in abbreviation_map.items():
        query = query.replace(short, full)
    return query

#from langchain.vectorstores import Pinecone as PineconeVectorStore
#from langchain.embeddings import OpenAIEmbeddings

def initialize_pinecone() -> PineconeVectorStore:
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=OPENAI_API_KEY)
    
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name="hufs-chatbot",
        embedding=embedding,
        text_key="page_content"
    )
    return vectorstore

# OpenAI LLM 모델 로드
def load_model():
    return ChatOpenAI(temperature=0, model_name="gpt-4o-mini", api_key=OPENAI_API_KEY, streaming=True)

# RAG 체인 구성 함수 (BM25 + Pinecone 앙상블)
def rag_chain(vectorstore):
    llm = load_model()
    doc_list = load_all_documents()
    texts = [doc.page_content for doc in doc_list]
    bm25_retriever = BM25Retriever.from_texts(texts)
    bm25_retriever.k = 30

    pinecone_retriever = vectorstore.as_retriever(search_kwargs={"k": 30})
    ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever, pinecone_retriever], weights=[0.3, 0.7])

    reranker_model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
    reranker = CrossEncoderReranker(model=reranker_model, top_n=15)
    compression_retriever = ContextualCompressionRetriever(base_compressor=reranker, base_retriever=ensemble_retriever)

    system_prompt = (
        "주어진 대화 기록과 최근 질문을 바탕으로, 이전 대화 내용을 참고하여 "
        "독립적으로 이해 가능한 질문으로 재구성하거나 그대로 사용하세요."
    )

    contextual_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware = create_history_aware_retriever(llm, compression_retriever, contextual_prompt)
    reorder = LongContextReorder()

    my_retriever = ({"input": itemgetter("input"), "chat_history": itemgetter("chat_history")} |
                     history_aware |
                     RunnableLambda(lambda docs: reorder.transform_documents(docs)))

     # QA 프롬프트
    qa_system_prompt = """
        너는 한국외국어대학교 학생들의 학사 관련 질문에 답변하는 AI 챗봇이야.
        
        - 사용자는 일상적인 표현, 축약어, 은어 등을 쓸 수 있어.
        - 항상 문서에서 제공한 정보에 기반하여 '정확하고 공손하게' 답변해.
        - 질문자의 핵심 의도에 집중해, 관련 없는 부가정보는 생략해.
        - 질문을 받으면 먼저 '의미를 해석하고', 관련 문서에서 '어떤 근거로 어떤 판단을 할 수 있는지' 논리적으로 연결해서 답변해.
        - 문서에 정보가 부족하면 "담당 교수님께 문의하라"는 안내로 마무리해.
        - 항상 끝에 "혹시 더 도와드릴까요?" 와 비슷한 '부드러운 후속 안내'를 덧붙여.
        - 질문에 포함된 표현이 한국어일 경우, 동일한 의미의 영어 표현도 함께 고려해해  
        예: “딥러닝” → “Deep Learning”, “데베” → “데이터베이스” →  “Data Base ”
        가능하면 질문에서 추출된 의미를 한국어/영어 키워드 모두로 확장해서 관련 문서를 찾아봐봐.
        
        ---
        
        [축약어 해석 규칙]
        - "일통" → "일본어통번역학과"
        - "글스산" → "글로벌스포츠산업학부"
        - "전필" → "전공필수", "전선" → "전공선택"
        - "유고" → "유고결석", "공결" → "공식결석"
        - "[언어명]통" → "[언어명]어통번역학과"로 일반화 가능
                                            
        ---
        
        [예시 응답 패턴]: (생각)은 답변 내용에 포함하지 말 것
        
        Q: 감기로 병원 다녀왔는데 진료확인서로 유고결석 가능해?  
        (생각) ‘감기’는 병결 사유이고, '진료확인서'는 증빙 서류임. 유고결석은 병원급 이상 서류를 요구함.  
        감기로 병원에 다녀오신 경우, 일반 의원에서 발급한 진료확인서는 인정되지 않을 수 있습니다.  
        병원급 이상의 의료기관에서 받은 진료확인서를 제출하시면 유고결석 처리가 가능할 수 있습니다.  
        정확한 기준은 과목 담당 교수님께 확인해 주세요. 혹시 더 도와드릴까요?
        
        Q: 일통 전필 뭐야?  
         (생각) '일통'은 '일본어통번역학과', '전필'은 전공필수 과목을 의미함.  
         일본어통번역학과의 전공필수 과목은 다음과 같습니다...
        
        Q: 취업계 내면 결석 인정되나요?  
         (생각) 취업계는 공결 사유에 해당되기도 하지만, 교수 재량에 따라 달라질 수 있음.  
        일부 과목에서는 취업계 제출 시 공결로 인정되기도 합니다.  
        다만 교수님에 따라 판단 기준이 다르니 꼭 수업 담당 교수님께 먼저 문의하시기 바랍니다. 혹시 더 도와드릴까요?
        
        ---
        
        #사용자 질문:  
        {input}
        
        #참고 문서:  
        {context}

        #답변: 
        """
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    qa_chain = create_stuff_documents_chain(llm, qa_prompt)

    return create_retrieval_chain(my_retriever, qa_chain)

# 세션 기반 체인 래핑
def get_session_history(session_id):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

store = {}

def initialize_conversation(vectorstore):
    chain = rag_chain(vectorstore)
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )

def load_all_documents():
    import pickle, os
    from loader.load_documents import (
        load_all_subject_documents,
        load_major_guidebook,
        load_sugang_pram,
        load_professor_documents,
        load_college_intro,
        load_notice_documents,
        load_academic_schedule,
    )

    # 캐시 우선
    if os.path.exists("data/cached_docs.pkl"):
        with open("data/cached_docs.pkl", "rb") as f:
            return pickle.load(f)

    # 새로 로드
    subject_docs = load_all_subject_documents("data/Timetable_Crawling_Data")
    guidebook_docs = load_major_guidebook("data/major_guide_2025.pdf")
    pram_docs = load_sugang_pram("data/pram_2025_1.json")
    prof_docs = load_professor_documents("data/hufs_professor.json")
    college_docs = load_college_intro("data/hufs_colleges.json")
    notice_docs = load_notice_documents("data/hufs_notice.json")
    schedule_docs = load_academic_schedule("data/hufs_schedule.json")

    doc_list = subject_docs + guidebook_docs + pram_docs + prof_docs + college_docs + notice_docs + schedule_docs

    # 저장
    with open("data/cached_docs.pkl", "wb") as f:
        pickle.dump(doc_list, f)

    return doc_list