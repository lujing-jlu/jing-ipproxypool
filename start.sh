#!/bin/bash

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装Docker，请先安装Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未安装docker-compose，请先安装docker-compose"
    exit 1
fi

# 停止并删除旧容器
echo "停止并删除旧容器..."
docker-compose down

# 构建新镜像
echo "构建新镜像..."
docker-compose build

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查服务状态
if curl -s "http://localhost:8000/stats" > /dev/null; then
    echo "服务启动成功！"
    echo "API地址: http://localhost:8000"
    echo "查看代理统计: http://localhost:8000/stats"
    echo "获取单个代理: http://localhost:8000/proxy"
    echo "获取所有代理: http://localhost:8000/proxies"
else
    echo "服务启动失败，请检查日志:"
    docker-compose logs
fi 