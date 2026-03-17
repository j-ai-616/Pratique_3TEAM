#  국고보조금
# 승용 및 초소형 전기자동차(2026년)~건설기계
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
last_category = ""
last_maker = ""

# ⭐ 전기화물차(2026년) = 무공해_2
btn = buttons[1]

driver.execute_script("arguments[0].scrollIntoView();", btn)
time.sleep(1)

driver.execute_script("arguments[0].click();", btn)
time.sleep(2)

table = btn.find_element(By.XPATH, "following::table[1]")
rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

for row in rows:

    cols = row.find_elements(By.XPATH, "./th|./td")
    texts = [c.text.strip() for c in cols if c.text.strip() != ""]

    # 5컬럼 (구분 포함)
    if len(texts) == 5:
        type_ = texts[0]
        category = texts[1]
        maker = texts[2]
        car = texts[3]
        subsidy = texts[4]

        last_type = type_
        last_category = category
        last_maker = maker

    # 제조사 rowspan
    elif len(texts) == 4:
        type_ = last_type
        category = texts[0]
        maker = texts[1]
        car = texts[2]
        subsidy = texts[3]

        last_category = category
        last_maker = maker

     # 제조사 + 차종 + 보조금 (구분 rowspan)
    elif len(cols) == 3:
        type_ = last_type
        category = last_category
        maker = cols[0].text.strip()
        car = cols[1].text.strip()
        subsidy = cols[2].text.strip()

        last_maker = maker

    # 차종만 있는 경우
    elif len(texts) == 2:
        type_ = last_type
        category = last_category
        maker = last_maker
        car = texts[0]
        subsidy = texts[1]

    else:
        continue

    data.append([type_, category, maker, car, subsidy])


df = pd.DataFrame(
    data,
    columns=["구분", "차량분류", "제조사", "차종", "국고보조금 지원금액(만원)"]
)

df.to_excel("무공해_2.xlsx", index=False)

print("무공해_2.xlsx 저장 완료")
print("총 데이터:", len(df))

driver.quit()