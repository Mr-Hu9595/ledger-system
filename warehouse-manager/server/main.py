from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import Material, Inbound, Outbound, LedgerProperty

app = FastAPI(title="仓库管理系统API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册路由
from api import materials, inbounds, outbounds, tools, ai
app.include_router(materials.router, prefix="/api/materials", tags=["物料"])
app.include_router(inbounds.router, prefix="/api/inbounds", tags=["入库"])
app.include_router(outbounds.router, prefix="/api/outbounds", tags=["出库"])
app.include_router(tools.router, prefix="/api", tags=["工具"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI识别"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "仓库管理系统API运行中"}