from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import time

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://www.ev.or.kr/nportal/buySupprt/initBuySubsidySupprtAction.do")

wait = WebDriverWait(driver, 10)

# 국고 보조금 탭 클릭
tab = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'국고 보조금')]"))
)
tab.click()

time.sleep(2)

buttons = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#subPage button"))
)

print("아코디언 개수:", len(buttons))

data = []

last_type = ""
last_maker = ""

# ⭐ 무공해_6
btn = buttons[5]

driver.execute_script("arguments[0].scrollIntoView();", btn)
time.sleep(1)

driver.execute_script("arguments[0].click();", btn)
time.sleep(2)

# ⭐ 모든 테이블 가져오기
tables = btn.find_elements(By.XPATH, "following::table")

for table in tables:

    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

    for row in rows:

        cols = row.find_elements(By.XPATH, "./th|./td")
        texts = [c.text.strip() for c in cols if c.text.strip() != ""]

        # 구분 + 제조사 + 차종 + 보조금
        if len(texts) == 4:
            type_ = texts[0]
            maker = texts[1]
            car = texts[2]
            subsidy = texts[3]

            last_type = type_
            last_maker = maker

        # 제조사 rowspan
        elif len(texts) == 3:
            type_ = last_type
            maker = texts[0]
            car = texts[1]
            subsidy = texts[2]

            last_maker = maker

        # 차종만 있는 경우
        elif len(texts) == 2:
            type_ = last_type
            maker = last_maker
            car = texts[0]
            subsidy = texts[1]

        else:
            continue

        data.append([type_, maker, car, subsidy])


df = pd.DataFrame(
    data,
    columns=["구분", "제조사", "차종", "국고보조금 지원금액(만원)"]
)

df.to_excel("무공해_6.xlsx", index=False)

print("무공해_6.xlsx 저장 완료")
print("총 데이터:", len(df))

driver.quit()