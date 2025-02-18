from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import pandas as pd
import os

class EmailNotifier:
    """邮件通知服务抽象层"""
    
    def __init__(self, email_gateway=None):
        self.sender = os.getenv("EMAIL_SENDER")  # 从.env获取，保留默认值
        self.receiver = os.getenv("EMAIL_RECEIVER")  # 从.env获取，保留默认值
        print(f"{self.receiver} is the receiver...")
        self.email_gateway = email_gateway or SMTPEmailGateway()  # 默认使用SMTP
        
    def send_email(self, subject: str, message: str) -> bool:
        # 防御性检查
        assert len(subject) <= 100, "邮件主题过长"
        assert len(message) <= 1000, "邮件内容过长"
        assert "@" in self.receiver, "邮箱格式错误"
        
        return self.email_gateway.send(
            sender=self.sender,
            receiver=self.receiver,
            subject=subject,
            message=message
        )

class SMTPEmailGateway:
    """真实邮件网关实现"""
    def __init__(self):
        import smtplib
        self.server = smtplib.SMTP('smtp.gmail.com', 587)  # 替换为真实SMTP服务器
        self.server.starttls()
        # 改为交互式输入密码
        self.server.login(
            os.getenv("EMAIL_SENDER"), 
            input("Enter SMTP password for email alerts: ")
        )
    
    def send(self, sender: str, receiver: str, subject: str, message: str) -> bool:
        try:
            email_body = f"Subject: {subject}\n\n{message}"
            self.server.sendmail(sender, receiver, email_body)
            return True
        except Exception as e:
            raise RuntimeError(f"邮件发送失败: {str(e)}")

class BlackSwanDetector:
    """黑天鹅事件检测器，使用策略模式便于扩展"""
    
    def __init__(self, threshold: float = -0.07):
        self.threshold = threshold
        self.symbol = "QQQ"
        self.notifier = EmailNotifier()
        self.data_fetcher = MarketDataFetcher()
        
    def _calculate_drop(self) -> float:
        """计算当前跌幅，包含数据校验断言"""
        current_price = self.data_fetcher.get_realtime_price(self.symbol)
        prev_close = self.data_fetcher.get_previous_close(self.symbol)
        
        # 防御性编程断言
        assert prev_close > 0, "前收盘价必须为正数"
        assert current_price >= 0, "当前价格不能为负数"
        assert not pd.isnull(current_price), "实时价格为NaN值"
        assert not pd.isnull(prev_close), "前收盘价为NaN值"
        
        return (current_price - prev_close) / prev_close
    
    def send_alert(self) -> str:
        """主检测逻辑，包含业务规则断言"""
        try:
            price_drop = self._calculate_drop()
            
            # 业务规则验证
            assert -1 <= price_drop <= 1, "价格涨跌幅应在[-1, 1]范围内"
            
            if price_drop <= self.threshold:
                message = f"Black Swam Detected: {self.symbol} dropped {price_drop*100:.2f}%"
                self.notifier.send_email("黑天鹅事件警报", message)
                return message
                
            return "Nothing worth noting in history, do not fooled by randomness, stick to strategy"
            
        except Exception as e:
            self.notifier.send_email(f"Alert system error: {str(e)}", f"Alert system error: {str(e)}")
            raise

class MarketDataFetcher:
    """市场数据获取抽象层，方便模拟测试"""
    
    def __init__(self):
        import yfinance as yf  # 需要先安装 pip install yfinance
        self.yf = yf
    
    def get_realtime_price(self, symbol: str) -> float:
        """获取实时市场价（美东时间9:30后的最新成交价）"""
        try:
            # 获取最近5分钟的交易数据
            data = self.yf.Ticker(symbol).history(period='1d', interval='1m')
            assert not data.empty, "无法获取实时市场数据"
            
            latest_price = data['Close'].iloc[-1]
            assert latest_price > 0, f"无效的实时价格: {latest_price}"
            
            return float(latest_price)
            
        except Exception as e:
            raise RuntimeError(f"实时价格获取失败: {str(e)}") from e
        
    def get_previous_close(self, symbol: str) -> float:
        """获取前收盘价"""
        try:
            data = self.yf.Ticker(symbol).history(period='5d')
            assert not data.empty, "历史数据为空"
            
            # 获取最近一个有效收盘价（排除今日）
            prev_close = data['Close'].iloc[-2]
            assert prev_close > 0, f"无效的前收盘价: {prev_close}"
            
            return float(prev_close)
            
        except Exception as e:
            raise RuntimeError(f"前收盘价获取失败: {str(e)}") from e

# 测试用例增强
def test_normal_market():
    detector = BlackSwanDetector()
    # 模拟正常市场数据
    assert "Nothing worth noting" in detector.send_alert()

def test_black_swan_event():
    detector = BlackSwanDetector(threshold=-0.07)  # 同步修改测试阈值
    # 通过猴子补丁模拟市场数据
    detector.data_fetcher.get_realtime_price = lambda _: 349.0  # 当前价格
    detector.data_fetcher.get_previous_close = lambda _: 376.34  # 修改为下跌7%的测试数据 (350/376.34≈0.93)
    result = detector.send_alert()
    assert "Black Swam" in result

def test_data_validation():
    fetcher = MarketDataFetcher()
    print(fetcher.get_realtime_price("QQQ"))
    print(fetcher.get_previous_close("QQQ"))
    # 验证价格数据假设
    assert fetcher.get_realtime_price("QQQ") > 0
    assert fetcher.get_previous_close("QQQ") > 0

def test_email_notifier():
    # Temporarily set environment variables for this test
    import os
    os.environ['EMAIL_SENDER'] = 'test@example.com'
    os.environ['EMAIL_RECEIVER'] = 'test@example.com'
    
    class MockEmailGateway:
        def __init__(self):
            self.sent_emails = []
        
        def send(self, sender, receiver, subject, message):
            self.sent_emails.append({
                "sender": sender,
                "receiver": receiver,
                "subject": subject,
                "message": message
            })
            return True
    
    mock_gateway = MockEmailGateway()
    notifier = EmailNotifier(email_gateway=mock_gateway)
    
    test_subject = "市场警报"
    test_message = "测试内容"
    notifier.send_email(test_subject, test_message)
    
    assert len(mock_gateway.sent_emails) == 1
    assert test_subject in mock_gateway.sent_emails[0]['subject']
    
    # Clean up environment variables after test
    del os.environ['EMAIL_SENDER']
    del os.environ['EMAIL_RECEIVER']

if __name__ == "__main__":
    pass
    #test_black_swan_event()
    #test_email_notifier()
    #test_data_validation()
    # 生产环境执行
    #detector = BlackSwanDetector()
    #print(detector.send_alert())
    
    #SMTP has authetication error
    #notifier = EmailNotifier(email_gateway=SMTPEmailGateway())
    #notifier.send_email("hello world","hello world")