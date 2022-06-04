# https://blog.ftx.com/blog/api-authentication/
# TODO write test function for ftx conncetion

# Historical-data-Basket trader-Your Basket account

from urllib import response
import requests
from dotenv import load_dotenv

def test_ftx_api_connection():
    """
    
    """
    # write function ftx api connect
    # TODO refactor to try except expression
    load_dotenv()
    endpoint_url = "https://ftx.com/api/markets"
    response = requests.get(endpoint_url)
    assert response.status_code == 200

if __name__ == '__main__':
    test_ftx_api_connection()
