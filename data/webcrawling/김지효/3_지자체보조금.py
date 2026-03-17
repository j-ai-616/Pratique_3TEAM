from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import time
import os

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get("https://www.ev.or.kr/nportal/buySupprt/initBuySubsidySupprtAction.do")

wait = WebDriverWait(driver, 20)

# 지자체 보조금 탭 클릭
tab = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'지자체 보조금')]"))
)

driver.execute_script("arguments[0].click();", tab)

time.sleep(2)

# 테이블 로딩 대기
wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".tabPage table tbody"))
)

rows = driver.find_elements(By.CSS_SELECTOR, ".tabPage table tbody tr")

data = []

for row in rows:

    cols = row.find_elements(By.TAG_NAME, "td")

    # 실제 데이터 행만 가져오기
    if len(cols) == 3:

        city = cols[0].text.strip()
        ev = cols[1].text.strip()
        hydrogen = cols[2].text.strip()

        # 빈 행 제거
        if city != "":
            data.append([city, ev, hydrogen])

# 데이터프레임 생성
df = pd.DataFrame(
    data,
    columns=["시도", "전기자동차", "수소자동차"]
)

print(df)
print("총 데이터:", len(df))

# 엑셀 저장
file_name = "지자체_보조금.xlsx"

df.to_excel(
    file_name,
    index=False,
    engine="openpyxl"
)

print("엑셀 저장 완료")
print("저장 위치:", os.getcwd())

driver.quit()