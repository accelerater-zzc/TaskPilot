#!/usr/bin/env bash
set -e

echo "=== TaskPilot 启动检查 ==="

# Step 1: 基础设施
echo "1. 启动基础设施..."
docker compose up -d postgres redis langfuse
sleep 5

# Step 2: 验证基础设施
echo "2. 验证 postgres + pgvector..."
docker compose exec -T postgres psql -U taskpilot -d taskpilot \
  -c "SELECT extversion FROM pg_extension WHERE extname='vector';" \
  | grep -q "[0-9]" && echo "   ✅ pgvector OK" || echo "   ❌ pgvector 未就绪"

echo "3. 验证 Redis..."
docker compose exec -T redis redis-cli ping | grep -q "PONG" && echo "   ✅ Redis OK" || echo "   ❌ Redis 未就绪"

# Step 3: 安装依赖
echo "4. 安装 Python 依赖..."
pip install -q -r requirements.txt

# Step 4: 运行单元测试
echo "5. 运行单元测试..."
python -m pytest tests/test_skills.py tests/test_memory.py tests/test_router.py -v

echo ""
echo "=== 启动 API 服务 ==="
echo "访问: http://localhost:8000/docs"
uvicorn api.main:api --reload --host 0.0.0.0 --port 8000
