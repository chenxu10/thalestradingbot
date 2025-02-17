import pandas as pd

class BlackSwanDetector:
    """黑天鹅事件检测器，使用策略模式便于扩展"""
    
    def __init__(self, threshold: float = -0.07):
        self.threshold = threshold
        self.symbol = "QQQ"
        self.notifier = SMSNotifier()
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
                self.notifier.send_sms(message)
                return message
                
            return "Nothing worth noting in history, do not fooled by randomness, stick to strategy"
            
        except Exception as e:
            self.notifier.send_sms(f"Alert system error: {str(e)}")
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

class SMSNotifier:
    """短信通知服务抽象层"""
    
    def __init__(self):
        self.recipient = "+1234567890"  # 应来自配置文件
        
    def send_sms(self, message: str) -> bool:
        # 实际应集成短信网关API
        # 添加发送断言
        assert len(message) <= 160, "短信内容不得超过160字符"
        assert self.recipient.startswith("+"), "国际号码格式错误"
        return True  # 模拟发送成功

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

def test_sms_notifier():
    """测试短信通知服务的边界条件"""
    notifier = SMSNotifier()
    
    # 测试正常短信
    normal_msg = "Test message " * 10  # 140字符
    assert notifier.send_sms(normal_msg) is True
    
    # 测试边界长度
    edge_msg = "a" * 160
    assert notifier.send_sms(edge_msg) is True
    
    # 测试过长消息应触发断言
    import pytest
    with pytest.raises(AssertionError):
        notifier.send_sms("a" * 161)
    
    # 测试错误号码格式
    invalid_notifier = SMSNotifier()
    invalid_notifier.recipient = "123456"  # 缺少+号
    with pytest.raises(AssertionError):
        invalid_notifier.send_sms("test message")

if __name__ == "__main__":
    #test_black_swan_event()
    test_sms_notifier()
    #test_data_validation()
    # 生产环境执行
    #detector = BlackSwanDetector()
    #print(detector.send_alert())