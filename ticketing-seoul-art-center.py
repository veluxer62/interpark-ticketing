# -*- encoding:utf8 -*-

from selenium import webdriver
from bs4 import BeautifulSoup
import sys
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


userID = "아이디"
userPW = "비밀번호"
userNum = "생년월일"

# 티켓 번호
groupCode = "20010077"

# 티켓상세URL
userSearch = "http://ticket.interpark.com/Ticket/Goods/GoodsInfo.asp?GroupCode=" + groupCode

# 날짜
userDate = "20201128"

# 회차 번호 1: 첫번재, 2: 두번째
userTime = "1"

# 반복 횟수
max_loop_count = 100000

# 스케줄 여부
set_schedule = True

# 스케줄 시간
schedule_time = datetime(2020, 11, 20, 14, 0, 0)

now = time.localtime()

userTicket = "일반"
userBank = 38051  # 국민은행

# VIP, R, S, A, 나머지
cbCheck = [1, 1, 1, 1, 1]

chrome_driver = '/usr/local/bin/chromedriver'
driver = webdriver.Chrome(chrome_driver)
wait = WebDriverWait(driver, 1)
driver.implicitly_wait(1)
g_dnow = ""


def log_in():
    try:
        login_url = "https://ticket.interpark.com/Gate/TPLogin.asp?CPage=B&MN=Y&tid1=main_gnb&tid2=right_top&tid3=login&tid4=login"
        driver.get(login_url)
        driver.switch_to_frame(driver.find_element_by_tag_name("iframe"))
        time.sleep(0.5)
        driver.find_element_by_id('userId').send_keys(userID)  # ID 입력
        driver.find_element_by_id('userPwd').send_keys(userPW)  # PW 입력
        driver.find_element_by_id('btn_login').click()
        wait.until(EC.presence_of_element_located((By.ID, "logstatus")))
    except:
        print("got exception(log_in)")


def move_to_ticket_page():
    try:
        driver.get(userSearch)
        # 공연 기간 정보 가져오기
        global g_dnow
        g_dnow = driver.find_element_by_xpath('//p[@class="time"]').text
        g_dnow = g_dnow[g_dnow.find('~ ') + 2:].replace('.', '')
    except:
        print("got exception(move_to_ticket_page)")


def open_reservation_page():
    try:
        driver.execute_script('javascript:fnNormalBooking();')
        driver.switch_to.window(driver.window_handles[1])
    except:
        print("got exception(open_reservation_page)")


def select_date_and_time():
    try:
        # 날짜
        # 1단계 프레임 받아오기
        frame = wait.until(
            EC.presence_of_element_located((By.ID, "ifrmBookStep")))
        driver.switch_to.frame(frame)

        # 달(月) 바꾸기
        driver.execute_script(
            "javascript: fnChangeMonth('" + userDate[:6] + "');")
        # 날짜 선택하기
        try:
            # 달력 정보가 존재할 경우
            # 달력 정보 가져오기
            wait.until(EC.presence_of_element_located((By.ID, "CellPlayDate")))
            time.sleep(0.5)
            bs4 = BeautifulSoup(driver.page_source, "html.parser")
            calender = bs4.findAll('a', id='CellPlayDate')
            elem = calender[0]["onclick"]

            # 사용자의 입력값과 일치하는 함수를 찾는다.
            for i in range(0, len(calender)):
                if "fnSelectPlayDate(" + str(i) + ", '" + userDate + "')" == calender[i]["onclick"]:
                    elem = calender[i]["onclick"]
                    print("same with input date %s" % elem)
                    break

            # 해당 날짜 선택하기
            print("selected date: %s" % elem)
            driver.execute_script("javascript: " + elem)
        except:
            print("no date info")
            print(g_dnow)
            # 달력 정보가 존재하지 않을 경우
            # 공연가능한 마지막 달로 이동한다
            driver.execute_script(
                "javascript: fnChangeMonth('" + g_dnow[:6] + "');")
            # 달력 정보 가져오기
            wait.until(EC.presence_of_element_located((By.ID, "CellPlayDate")))
            time.sleep(0.5)
            bs4 = BeautifulSoup(driver.page_source, "html.parser")
            calender = bs4.findAll('a', id='CellPlayDate')
            select_script = calender[len(calender) - 1]["onclick"]
            # 해당 날짜 선택하기
            driver.execute_script("javascript:" + select_script)

        # 페이지 로딩 대기
        wait.until(EC.presence_of_element_located((By.ID, "CellPlaySeq")))

        # 회차
        # 회차 정보 가져오기
        bs4 = BeautifulSoup(driver.page_source, "html.parser")
        timeList = bs4.find('div', class_='scrollY').find(
            'span', id='TagPlaySeq').findAll('a', id='CellPlaySeq')

        # 회차 유효성 검사
        try:
            if int(userTime[0]) <= len(timeList):
                elem = timeList[int(userTime[0]) - 1]["onclick"]
            else:
                elem = timeList[0]["onclick"]
        except:
            elem = timeList[0]["onclick"]

        # 회차 선택하기
        driver.execute_script("javascript:" + elem)
        print(elem)

        # 다음단계
        # 메인 프레임 받아오기
        driver.switch_to.default_content()

        # 2단계 넘어가기
        driver.execute_script("javascript:fnNextStep('P');")

        # 당일 예매 경고창 감지
        try:
            alert = driver.switch_to_alert()
            alert.accept()
        except:
            elem = ''

    except:
        # 관람일/회차선택 단계가 없을 경우
        if (len(driver.window_handles) == 2):
            # 팝업이 있는경우
            driver.switch_to_window(driver.window_handles[1])
            driver.execute_script("javascript:fnClose();")
            driver.switch_to_window(driver.window_handles[0])
            driver.execute_script('javascript:fnNormalBooking();')
        else:
            elem = ''
            print("process00 %s" % sys.exc_info())


def is_preferred_and_available_seat(seat):
    if seat is None:
        return None

    # seat = seatList[j]
    text = seat['alt'][seat['alt'].find('[') + 1:]
    if (text.find("VIP") != -1) & (cbCheck[0] == 1):
        return True
    if (text.find("R") != -1) & (cbCheck[1] == 1):
        return True
    if (text.find("S") != -1) & (cbCheck[2] == 1):
        return True
    if (text.find("A") != -1) & (cbCheck[3] == 1):
        return True
    if cbCheck[4] == 1:
        return True

    return False


def selct_ticket_price():
    try:
        # 가격/할인선택 (3단계)
        # 3단계 프레임 받아오기
        driver.switch_to.default_content()
        wait.until(EC.presence_of_element_located((By.ID, "ifrmBookStep")))
        frame = driver.find_element_by_id('ifrmBookStep')
        driver.switch_to.frame(frame)

        # 표 선택하기
        # 표 정보를 가져온다.
        bs4 = BeautifulSoup(driver.page_source, "html.parser")
        ticketList = bs4.findAll('select')

        # 사용자의 입력값과 일치하는 함수를 찾는다.
        for i in range(0, len(ticketList)):
            ticketStr = ticketList[i]["pricegradename"]
            if ticketStr.find(userTicket) != -1:
                # 사용자의 입력값과 일치하는 선택지가 있다면
                elem = ticketList[i]["index"]
                break

        # 표 선택하기
        try:
            driver.find_element_by_xpath(
                "//td[@class='taL']//select[@index='" + str(elem) + "']//option[@value='1']").click()
        except:
            driver.find_element_by_xpath(
                "//td[@class='taL']//select[@pricegrade='01']//option[@value='1']").click()

        # 다음단계
        # 메인 프레임 받아오기
        driver.switch_to.default_content()
        time.sleep(0.5)
        # 4단계 넘어가기
        driver.execute_script("javascript:fnNextStep('P');")

        # 특수표 경고창 감지
        try:
            alert = driver.switch_to_alert()
            alert.accept()
        except:
            elem = ''
    except:
        print("got error(selct_ticket_price)")


def fill_order():
    try:
        # print(driver.page_source)
        wait.until(EC.presence_of_element_located((By.ID, "ifrmBookStep")))
        frame = driver.find_element_by_id('ifrmBookStep')
        driver.switch_to.frame(frame)
        time.sleep(0.5)
        # print(driver.page_source)
        # send number
        wait.until(EC.presence_of_element_located((By.ID, "YYMMDD")))
        # birth_day.send_keys(userNum)
        driver.find_element_by_xpath(
            "//td[@class='form']//input[@id='YYMMDD']").send_keys(userNum)
        # move to next
        driver.switch_to.default_content()
        driver.execute_script("javascript:fnNextStep('P');")

        wait.until(EC.presence_of_element_located((By.ID, "ifrmBookStep")))
        frame = driver.find_element_by_id('ifrmBookStep')
        driver.switch_to.frame(frame)

        elem = driver.find_element_by_xpath(
            "//tr[@id='Payment_22004']//input[@name='Payment']")
        elem.click()
        # elem = wait.until(EC.presence_of_element_located((By.ID, "BankCode")))
        elem = driver.find_element_by_xpath(
            "//select[@id='BankCode']//option[@value='" + str(userBank) + "']")
        elem.click()

        driver.switch_to.default_content()
        driver.execute_script("javascript:fnNextStep('P');")
    except:
        print("got error(fill_order)")


def pay_for_ticket():
    try:
        wait.until(EC.presence_of_element_located((By.ID, "ifrmBookStep")))
        frame = driver.find_element_by_id('ifrmBookStep')
        driver.switch_to.frame(frame)
        # 약관 동의
        # 취소수수료/취소기한을 확인하였으며, 동의합니다.
        elem = driver.find_element_by_xpath("//input[@id='CancelAgree']")
        elem.click()
        # 제3자 정보제공 내용에 동의합니다.
        elem = driver.find_element_by_xpath("//input[@id='CancelAgree2']")
        elem.click()
    except:
        print("got error(pay_for_ticket)")


def select_seat():
    cnt = 0
    rst = False
    while (True):
        rst = select_seat_internal()

        print("result: {}, cnt: {}".format(rst, cnt))

        if (rst):
            break

        if (cnt == max_loop_count):
            break

        cnt += 1

    return rst


def select_seat_internal():
    succeeded = False

    # 2단계 프레임 받아오기
    try:
        # driver.switch_to.default_content()
        driver.switch_to_window(driver.window_handles[1])
        frame = driver.find_element_by_id('ifrmSeat')
        driver.switch_to.frame(frame)

        driver.execute_script('javascript:fnRefresh();')

        # 미니맵 존재여부 검사
        try:
            wait.until(EC.presence_of_element_located((By.ID, "ifrmSeatView")))
            frame = driver.find_element_by_id('ifrmSeatView')
            driver.switch_to.frame(frame)
            wait.until(EC.presence_of_element_located((By.NAME, "Map")))
            bs4 = BeautifulSoup(driver.page_source, "html.parser")
            elem = bs4.find('map')
        except:
            elem = None

        time.sleep(0.5)
        # 좌석 프레임 받아오기
        driver.switch_to.default_content()
        wait.until(EC.presence_of_element_located((By.ID, "ifrmSeat")))
        frame = driver.find_element_by_id('ifrmSeat')
        driver.switch_to.frame(frame)
        frame = driver.find_element_by_id('ifrmSeatDetail')
        driver.switch_to.frame(frame)
        # 좌석 정보를 읽어온다.
        bs4 = BeautifulSoup(driver.page_source, "html.parser")
        seatList = bs4.findAll('img', class_='stySeat')
        print("got seat list: %d" % (len(seatList)))

        # 좌석이 존재할 경우 error X -> except 실행 X
        for i in range(0, len(seatList)):
            seat = seatList[i]
            if is_preferred_and_available_seat(seat):
                # 좌석 선택하기
                try:
                    driver.execute_script(seat['onclick'] + ";")
                    # 2단계 프레임 받아오기
                    driver.switch_to.default_content()
                    wait.until(EC.presence_of_element_located(
                        (By.ID, "ifrmSeat")))
                    frame = driver.find_element_by_id('ifrmSeat')
                    driver.switch_to.frame(frame)
                    # 3단계 넘어가기
                    driver.execute_script("javascript:fnSelect();")
                    succeeded = True
                    # 경고창 감지
                    try:
                        alert = driver.switch_to_alert()
                        alert.accept()
                        time.sleep(0.5)
                        succeeded = False
                        continue
                    except:
                        elem = ''
                        print("no alert window or got exception")

                    break
                except:
                    print("try to move to final stage. but failed: %s" % seat)
    except:
        print("got unexpected except(select_seat)")

    return succeeded


def interval_time():
    n = datetime.now()

    print("interval start - now({}), schedule({})".format(n, schedule_time))

    interval = schedule_time - n
    interval_seconds = interval.seconds + 1

    print("inerval time - {}".format(interval_seconds))

    if (interval.days < 0):
        print("previous time can't interval")
    else:
        time.sleep(interval_seconds)

    print("interval end - {}".format(datetime.now()))


if __name__ == '__main__':
    log_in()
    move_to_ticket_page()

    if (set_schedule):
        interval_time()

    open_reservation_page()
    select_date_and_time()
    seat_result = select_seat()

    print("seat_result: {}".format(seat_result))

    if (seat_result):
        selct_ticket_price()
        fill_order()
        pay_for_ticket()
