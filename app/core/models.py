from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Proxy(Base):
    __tablename__ = 'proxies'
    
    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(String, nullable=False)  # http/https/socks5
    last_check = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float)  # 响应时间(秒)
    is_valid = Column(Boolean, default=True)
    fail_count = Column(Integer, default=0)  # 连续失败次数
    source = Column(String)  # 代理来源
    
    def to_dict(self):
        return {
            'id': self.id,
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'last_check': self.last_check.isoformat(),
            'response_time': self.response_time,
            'is_valid': self.is_valid,
            'fail_count': self.fail_count,
            'source': self.source
        }
    
    @property
    def url(self):
        return f"{self.protocol}://{self.host}:{self.port}"

def init_db(db_url='sqlite:///proxies.db'):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal 