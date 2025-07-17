# vectorstore.py
import os
import json
import time
from uuid import uuid4
from dotenv import load_dotenv
from typing import List
from tqdm import tqdm
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from config import EMBEDDING_DIM

# 환경 변수 불러오기
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 파라미터 설정
INDEX_NAME = "hufs-chatbot"
EMBEDDING_DIM = 1536


### 3. 벡터 DB 초기화 및 임베딩 저장
def store_documents_to_pinecone(docs: List[Document], index_name: str, openai_api_key,pinecone_api_key,embedding_dim):
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=openai_api_key)
    pc = Pinecone(api_key=pinecone_api_key)

    if index_name not in pc.list_indexes().names():
        print(f"🔧 인덱스 '{index_name}' 생성 중...")
        pc.create_index(
            name=index_name,
            dimension=embedding_dim,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
    else:
        print(f"✅ 인덱스 '{index_name}' 이미 존재")

    index = pc.Index(index_name)
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="page_content")

    if docs and isinstance(docs[0], Document):
        doc_type = docs[0].metadata.get("type") or docs[0].metadata.get("doc_type") or "unknown"
        print(f"📤 '{index_name}'로 문서 업로드 시작 - 문서 유형: '{doc_type}' ({len(docs)}개)")
    else:
        print(f"📤 '{index_name}'로 문서 업로드 시작 ({len(docs)}개)")
    for doc, doc_id in tqdm(zip(docs, [str(uuid4()) for _ in docs]), total=len(docs)):
        vectorstore.add_documents([doc], ids=[doc_id])

    print(f"✅ 저장 완료: {index_name}")


### 2. 필터 기반 문서 삭제 함수 추가
def delete_documents_by_metadata(index_name: str, pinecone_api_key: str, field: str, value: str):
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(index_name)

    # dummy vector는 쿼리 조건용
    dummy_vector = [0.0] * EMBEDDING_DIM

    result = index.query(
        vector=dummy_vector,
        top_k=1000,
        include_metadata=True,
        filter={field: {"$eq": value}},
    )
    ids_to_delete = [match["id"] for match in result["matches"]]
    if ids_to_delete:
        print(f"🗑️ '{value}'로 식별된 {len(ids_to_delete)}개 벡터 삭제 중...")
        index.delete(ids=ids_to_delete)
    else:
        print(f"⚠️ 삭제할 벡터가 없음: {value}")
