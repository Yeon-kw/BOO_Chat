from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from config import PINECONE_API_KEY,OPENAI_API_KEY
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Pinecone 설정 (불러오기 전용)
def initialize_pinecone():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "hufs-chatbot"  

    index = pc.Index(index_name)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        api_key=OPENAI_API_KEY
    )

    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="page_content")
    return vectorstore

# OpenAI LLM 로드
def load_model():
    model = ChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-Turbo",  # 테스트용, 향 후 gpt-4o-mini로 변경경
        api_key=OPENAI_API_KEY,
        streaming=True
    )
    print("모델 호출 중...")
    return model

# RAG 체인 구성
def rag_chain(vectorstore):
    llm = load_model()

    # 문서 검색기 (retriever) 구성
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 프롬프트 정의
    prompt = PromptTemplate.from_template("""
    너는 한국외대 학사 관련 질문에 답변하는 챗봇이야.
    다음은 검색된 문서 내용이야. 이 내용을 바탕으로 사용자의 질문에 답변해.
    답을 모르면 모른다고 해. 무조건 한국어로 높임말을 사용해서 답변해.

    #질문:
    {question}

    #문서 내용:
    {context}

    #답변:
    """)

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=OPENAI_API_KEY)

    chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
    )
    
    return chain