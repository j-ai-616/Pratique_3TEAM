import urllib.request
import json
import os
import time
from bs4 import BeautifulSoup
import pandas as pd

def crawl_hyundai_faq_api():
    all_faq_data = []
    pk_counter = 1
    
    for i in range(1, 21):
        cat_code = str(i).zfill(2)
        true_cat_name = ""
        
        for page in range(1, 16): 
            api_url = "https://www.hyundai.com/kr/ko/gw/customer-support/v1/customer-support/faq/list"
            payload_dict = {
                "siteTypeCode": "H", "faqCategoryCode": cat_code, "faqCode": "", "faqSeq": "",
                "searchKeyword": "", "pageNo": page, "pageSize": "10", "externalYn": ""
            }
            payload_bytes = json.dumps(payload_dict).encode('utf-8')
            headers = {
                'ep-channel': 'homepage',
                'Referer': 'https://www.hyundai.com/kr/ko/e/customer/center/faq',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json', 'Content-Type': 'application/json;charset=UTF-8'
            }
            req = urllib.request.Request(api_url, data=payload_bytes, headers=headers, method='POST')
            
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = response.read().decode('utf-8')
                    json_data = json.loads(res_data)
                    data_node = json_data.get('data')
                    
                    faq_list = []
                    if isinstance(data_node, dict):
                        faq_list = data_node.get('faqList', data_node.get('list', data_node.get('items', [])))
                    elif isinstance(data_node, list):
                        faq_list = data_node
                        
                    if not faq_list:
                        if page > 1:
                            print(f"  ✅ {page-1}페이지까지 수집 완료. 다음 카테고리로 이동!")
                        break 
                        
                    if page == 1:
                        true_cat_name = faq_list[0].get('faqCategoryName', f'알수없는카테고리({cat_code})')
                        print(f"\n{'='*40}\n 📂 [{true_cat_name}] 수집 시작! (서버 코드: {cat_code})\n{'='*40}")
                        
                    print(f"  -> {page}페이지 수집 중...")
                        
                    for item in faq_list:
                        question = item.get('faqQuestion', '제목없음')
                        answer = item.get('faqAnswer', '내용없음')
                        
                        soup = BeautifulSoup(answer, "html.parser")
                        clean_answer = soup.get_text(separator='\n').strip()
                        all_faq_data.append([pk_counter, true_cat_name, question, clean_answer])
                        pk_counter += 1
                        
                time.sleep(1) 
                
            except Exception as e:
                print(f" 에러 발생 (코드 {cat_code}, {page}페이지): {e}")
                break

    # 엑셀 파일 저장
    save_dir = os.path.join('data', 'raw')
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, 'hyundai_faq_api_data.xlsx')
    
    df = pd.DataFrame(all_faq_data, columns=['번호', '질문 카테고리', '질문', '답'])
    df.to_excel(file_path, index=False, engine='openpyxl')
    
    print(f"\n수집 성공! 총 {len(all_faq_data)}건의 데이터가 파일 '{file_path}'에 저장되었습니다.")

if __name__ == "__main__":
    crawl_hyundai_faq_api()