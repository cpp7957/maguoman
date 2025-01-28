import os
import json
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mcpi.minecraft import Minecraft
from mcpi.entity import PRIMED_TNT

# 로그 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 설정 파일 로드
def load_config(file_name="config.json"):
    default_config = {
        "channel_id": "UCPW8jTlTN-ihPfhsEJdABDQ",
        "check_interval": 2,
        "selenium_headless": False
    }
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)

    try:
        with open(file_path, "r") as file:
            config = json.load(file)
        return {**default_config, **config}
    except FileNotFoundError:
        logging.warning(f"'{file_name}' 파일이 존재하지 않습니다. 기본값을 사용합니다.")
        return default_config
    except json.JSONDecodeError:
        logging.warning(f"'{file_name}' 파일의 JSON 형식이 잘못되었습니다. 기본값을 사용합니다.")
        return default_config

# 마인크래프트 핸들러
class MinecraftHandler:
    ANVIL_BLOCK_ID = 145

    def __init__(self):
        try:
            self.mc = Minecraft.create()
            logging.info("Minecraft 서버에 성공적으로 연결되었습니다.")
        except Exception as e:
            logging.error(f"Minecraft 서버 연결 실패: {e}")
            self.mc = None

    def is_connected(self):
        return self.mc is not None

    def spawn_tnt(self, count):
        if not self.is_connected():
            logging.warning("Minecraft 서버와 연결되지 않았습니다.")
            return

        players = self.mc.getPlayerEntityIds()
        for player in players:
            x, y, z = self.mc.entity.getTilePos(player)
            for _ in range(count):
                self.mc.spawnEntity(x, y, z, PRIMED_TNT)
            logging.info(f"TNT {count}개 소환: {x}, {y}, {z}")

    def drop_anvil(self, height):
        if not self.is_connected():
            logging.warning("Minecraft 서버와 연결되지 않았습니다.")
            return

        players = self.mc.getPlayerEntityIds()
        for player in players:
            x, y, z = self.mc.entity.getTilePos(player)
            self.mc.setBlock(x, y + height, z, self.ANVIL_BLOCK_ID)
            logging.info(f"모루 배치: {x}, {y + height}, {z}")

# 구독자 체크 클래스 (Selenium 크롤링)
class SubscriberChecker:
    OD_TIMER_CLASS = "odometer-value"

    def __init__(self, channel_id, headless=None):
        self.channel_id = channel_id
        config = load_config()
        self.headless = headless if headless is not None else config.get("selenium_headless", False)

        try:
            self.driver = self._initialize_driver()
        except Exception as e:
            logging.error(f"WebDriver 초기화 실패: {e}")
            self.driver = None

    def _initialize_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--enable-webgl")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")
            logging.info("헤드리스 모드로 실행합니다.")
        else:
            logging.info("헤드리스 모드가 비활성화된 상태로 실행합니다.")
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-usb-discovery")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options)
        url = f"https://socialblade.com/youtube/channel/{self.channel_id}/realtime"
        driver.get(url)
        time.sleep(5)
        logging.info("WebDriver가 사이트를 성공적으로 로드했습니다.")
        return driver

    def get_subscriber_count(self):
        if not self.driver:
            logging.error("WebDriver가 초기화되지 않았습니다.")
            return None

        try:
            odometer_value = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, self.OD_TIMER_CLASS))
            )
            count = int(odometer_value.text.replace(",", ""))
            return count
        except Exception as e:
            logging.error(f"구독자 수 가져오기 실패: {e}")
            return None

    def __del__(self):
        if self.driver:
            self.driver.quit()

def main():
    config = load_config()
    channel_id = config.get("channel_id")
    check_interval = config.get("check_interval")

    mc_handler = MinecraftHandler()
    if not mc_handler.is_connected():
        logging.error("Minecraft 서버와 연결할 수 없습니다. 프로그램을 종료합니다.")
        return

    sub_checker = SubscriberChecker(channel_id)
    if not sub_checker.driver:
        logging.error("WebDriver 초기화에 실패했습니다. 프로그램을 종료합니다.")
        return

    current_subscriber_count = sub_checker.get_subscriber_count()
    if current_subscriber_count is not None:
        logging.info(f"구독자 로드 성공: 현재 구독자 수는 {current_subscriber_count}명입니다.")
    else:
        logging.error("초기 구독자 수를 가져오는 데 실패했습니다. 프로그램을 종료합니다.")
        return

    print("\n구독자 증가 시 실행할 기능을 선택하세요:")
    print("1. TNT 소환")
    print("2. 모루 떨어뜨리기")
    valid_choices = {"1": "TNT", "2": "Anvil"}
    choice = input("선택 (1 또는 2): ").strip()
    while choice not in valid_choices:
        print("잘못된 입력입니다. 1 또는 2를 선택하세요.")
        choice = input("선택 (1 또는 2): ").strip()
    event_choice = valid_choices[choice]

    prev_subscriber_count = None
    last_log_time = time.time()

    try:
        while True:
            current_subscriber_count = sub_checker.get_subscriber_count()
            if current_subscriber_count is None:
                logging.warning("구독자 수를 가져올 수 없습니다.")
                time.sleep(check_interval)
                continue

            # 구독자 증가 감지
            if prev_subscriber_count and current_subscriber_count > prev_subscriber_count:
                logging.info(f"구독자 증가 감지: {prev_subscriber_count} -> {current_subscriber_count}")
                if event_choice == "TNT":
                    mc_handler.spawn_tnt(current_subscriber_count - prev_subscriber_count)
                elif event_choice == "Anvil":
                    mc_handler.drop_anvil(current_subscriber_count - prev_subscriber_count)

            # 30초마다 구독자 수 로그 출력
            if time.time() - last_log_time >= 30:
                logging.info(f"현재 구독자 수: {current_subscriber_count}")
                last_log_time = time.time()

            prev_subscriber_count = current_subscriber_count
            time.sleep(check_interval)

    except KeyboardInterrupt:
        logging.info("프로그램이 종료되었습니다.")
    except Exception as e:
        logging.error(f"예기치 못한 오류 발생: {e}", exc_info=True)

if __name__ == "__main__":
    main()
