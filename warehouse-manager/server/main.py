from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import Material, Inbound, Outbound, LedgerProperty, EncodingRule, MaterialCodeSequence

app = FastAPI(title="仓库管理系统API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册路由
from api import materials, inbounds, outbounds, tools, ai, encoding
app.include_router(materials.router, prefix="/api/materials", tags=["物料"])
app.include_router(inbounds.router, prefix="/api/inbounds", tags=["入库"])
app.include_router(outbounds.router, prefix="/api/outbounds", tags=["出库"])
app.include_router(tools.router, prefix="/api", tags=["工具"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI识别"])
app.include_router(encoding.router, prefix="/api/encoding", tags=["编码"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "仓库管理系统API运行中"}