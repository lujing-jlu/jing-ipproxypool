# IP代理池

一个基于Python异步编程的高性能IP代理池系统，支持自动爬取、验证和管理代理IP。

## 特性

- 异步并发爬取多个代理源
- 自动验证代理可用性
- 定时更新和清理无效代理
- RESTful API接口
- 支持HTTP/HTTPS/SOCKS4/SOCKS5代理
- Docker一键部署
- 代理质量排序
- 自动去重

## 代理来源

- GitHub优质代理列表
  - TheSpeedX/PROXY-List
  - monosans/proxy-list
  - prxchk/proxy-list
  - hookzof/socks5_list
  - rdavydov/proxy-list
  - jetkai/proxy-list

- 代理API
  - proxyscrape.com
  - proxyspace.pro
  - geonode.com

## 快速开始

### 使用Docker（推荐）

1. 克隆仓库
```bash
git clone https://github.com/yourusername/proxy-pool.git
cd proxy-pool
```

2. 启动服务
```bash
docker-compose up -d
```

### 手动部署

1. 克隆仓库
```bash
git clone https://github.com/yourusername/proxy-pool.git
cd proxy-pool
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动服务
```bash
python run.py
```

## API接口

### 1. 获取单个代理
```
GET /proxy
```
返回响应时间最短的可用代理

### 2. 获取代理列表
```
GET /proxies?valid_only=true
```
参数：
- valid_only: 是否只返回有效代理（默认true）

### 3. 获取统计信息
```
GET /stats
```
返回代理池统计信息：
- total: 总代理数量
- valid: 有效代理数量
- success_rate: 可用率

## 配置说明

### 代理验证
- 验证超时：10秒
- 验证URL：PubChem API
- 失效判定：连续失败3次或1小时未更新
- 更新间隔：5分钟

### 数据存储
- 使用SQLite数据库
- 数据文件：./data/proxies.db

## 开发计划

- [ ] 支持更多代理源
- [ ] 添加代理匿名度检测
- [ ] 支持更多数据库后端
- [ ] 添加Web管理界面
- [ ] 代理评分系统
- [ ] 地理位置分析
- [ ] 导出功能

## 贡献指南

1. Fork 项目
2. 创建新分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目地址：https://github.com/yourusername/proxy-pool
- 作者邮箱：your.email@example.com

## 致谢

感谢以下开源项目提供的代理源：
- [TheSpeedX/PROXY-List](https://github.com/TheSpeedX/PROXY-List)
- [monosans/proxy-list](https://github.com/monosans/proxy-list)
- [prxchk/proxy-list](https://github.com/prxchk/proxy-list)
- [hookzof/socks5_list](https://github.com/hookzof/socks5_list)
- [rdavydov/proxy-list](https://github.com/rdavydov/proxy-list)
- [jetkai/proxy-list](https://github.com/jetkai/proxy-list)
