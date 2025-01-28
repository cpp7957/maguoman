import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import logging
import threading
import time
import json
import os
from main import MinecraftHandler, SubscriberChecker, load_config

# GUI 로그 핸들러
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        message = self.format(record)
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)

class MinecraftGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("마구오만")
        self.root.geometry("500x750")
        self.root.configure(bg="#2b2b2b")
        self.mc_handler = MinecraftHandler()
        self.sub_checker = None
        self.running = False

        # 설정 값 로드
        self.config = load_config()

        # GUI 요소 설정
        self.setup_widgets()

        # 로그 핸들러 설정
        self.text_handler = TextHandler(self.log_text)
        self.text_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(self.text_handler)
        logging.getLogger().setLevel(logging.INFO)

    def setup_widgets(self):
        tk.Label(self.root, text="마구오만", font=("Helvetica", 18, "bold"), fg="#ffffff", bg="#2b2b2b").pack(pady=5)
        tk.Label(self.root, text="(마인크래프트에서 구독자가 오르는 만큼)", font=("Helvetica", 10), fg="#aaaaaa", bg="#2b2b2b").pack(pady=5)

        # 현재 구독자 수
        self.current_sub_label = tk.Label(self.root, text="현재 구독자 수: -", font=("Helvetica", 14), fg="#4caf50", bg="#2b2b2b")
        self.current_sub_label.pack(pady=5)

        # 설정 입력 요소
        self.channel_id_label = tk.Label(self.root, text="채널 ID:", font=("Helvetica", 12), fg="#ffffff", bg="#2b2b2b")
        self.channel_id_label.pack(pady=5)
        self.channel_id_entry = tk.Entry(self.root, font=("Helvetica", 12))
        self.channel_id_entry.insert(0, self.config.get("channel_id", ""))
        self.channel_id_entry.pack(pady=5)

        self.check_interval_label = tk.Label(self.root, text="체크 간격 (초):", font=("Helvetica", 12), fg="#ffffff", bg="#2b2b2b")
        self.check_interval_label.pack(pady=5)
        self.check_interval_entry = tk.Entry(self.root, font=("Helvetica", 12))
        self.check_interval_entry.insert(0, str(self.config.get("check_interval", 2)))
        self.check_interval_entry.pack(pady=5)

        self.headless_checkbox = tk.IntVar(value=1 if self.config.get('selenium_headless') else 0)
        self.headless_toggle = tk.Checkbutton(
            self.root,
            text="Selenium Headless 활성화",
            variable=self.headless_checkbox,
            font=("Helvetica", 12),
            fg="#ffffff",
            bg="#2b2b2b",
            selectcolor="#2b2b2b",
            activebackground="#2b2b2b",
            activeforeground="#ffffff"
        )
        self.headless_toggle.pack(pady=5)

        # 이벤트 선택
        self.event_label = tk.Label(self.root, text="이벤트 선택:", font=("Helvetica", 12), fg="#ffffff", bg="#2b2b2b")
        self.event_label.pack(pady=5)

        self.event_options = ["TNT 소환", "모루 떨어뜨리기"]
        self.event_var = tk.StringVar(value=self.event_options[0])
        self.event_selector = ttk.Combobox(self.root, textvariable=self.event_var, values=self.event_options, state="readonly", font=("Helvetica", 12))
        self.event_selector.pack(pady=5)

        # 설정 적용 버튼
        self.apply_config_button = tk.Button(self.root, text="설정 파일 적용", command=self.apply_config, width=15, font=("Helvetica", 12, "bold"), bg="#ff9800", fg="#ffffff", relief="flat")
        self.apply_config_button.pack(pady=10)

        # 설정 저장 버튼
        self.save_config_button = tk.Button(self.root, text="설정 파일 저장", command=self.save_config, width=15, font=("Helvetica", 12, "bold"), bg="#2196f3", fg="#ffffff", relief="flat")
        self.save_config_button.pack(pady=10)

        # 시작/중지 버튼
        self.start_button = tk.Button(self.root, text="시작", command=self.start_program, width=15, font=("Helvetica", 12, "bold"), bg="#4caf50", fg="#ffffff", relief="flat")
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="중지", command=self.stop_program, state=tk.DISABLED, width=15, font=("Helvetica", 12, "bold"), bg="#f44336", fg="#ffffff", relief="flat")
        self.stop_button.pack(pady=10)

        self.log_frame = tk.Frame(self.root, bg="#2b2b2b")
        self.log_frame.pack(pady=20, fill="both", expand=True)

        self.log_text = tk.Text(self.log_frame, height=15, width=50, state=tk.DISABLED, font=("Courier", 10), bg="#1e1e1e", fg="#d4d4d4", relief="flat", wrap="word")
        self.log_text.pack(pady=10, padx=10, fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview, bg="#2b2b2b")
        self.scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=self.scrollbar.set)

    def apply_config(self):
        config_path = filedialog.askopenfilename(title="설정 파일 선택", filetypes=[("JSON 파일", "*.json")])
        if config_path:
            try:
                with open(config_path, "r") as file:
                    loaded_config = json.load(file)
                logging.info(f"적용된 설정: {loaded_config}")  # 디버깅용 로그 출력
                self.channel_id_entry.delete(0, tk.END)
                self.channel_id_entry.insert(0, loaded_config.get("channel_id", ""))
                self.check_interval_entry.delete(0, tk.END)
                self.check_interval_entry.insert(0, str(loaded_config.get("check_interval", 2)))
                self.headless_checkbox.set(1 if loaded_config.get("selenium_headless", False) else 0)
                messagebox.showinfo("성공", "설정이 적용되었습니다!")
            except json.JSONDecodeError:
                messagebox.showerror("오류", "잘못된 JSON 파일 형식입니다.")
            except Exception as e:
                messagebox.showerror("오류", f"설정을 적용하는 중 오류가 발생했습니다: {e}")

    def save_config(self):
        new_config = {
            "channel_id": self.channel_id_entry.get(),
            "check_interval": int(self.check_interval_entry.get()),
            "selenium_headless": bool(self.headless_checkbox.get())
        }
        config_path = filedialog.asksaveasfilename(title="설정 파일 저장", initialfile="config", defaultextension=".json", filetypes=[("JSON 파일", "*.json")])
        if config_path:
            try:
                with open(config_path, "w") as file:
                    json.dump(new_config, file, indent=4)
                messagebox.showinfo("성공", "설정이 저장되었습니다!")
            except Exception as e:
                messagebox.showerror("오류", f"설정을 저장하는 중 오류가 발생했습니다: {e}")

    def start_program(self):
        # 설정 변경 비활성화
        self.channel_id_entry.config(state=tk.DISABLED)
        self.check_interval_entry.config(state=tk.DISABLED)
        self.headless_toggle.config(state=tk.DISABLED)
        self.event_selector.config(state=tk.DISABLED)
        self.save_config_button.config(state=tk.DISABLED)
        self.apply_config_button.config(state=tk.DISABLED)

        if not self.mc_handler.is_connected():
            messagebox.showerror("오류", "Minecraft 서버와 연결할 수 없습니다.")
            return

        # 체크/인풋박스의 값을 사용하여 설정 반영
        selenium_headless = bool(self.headless_checkbox.get())
        channel_id = self.channel_id_entry.get()
        selected_event = self.event_var.get()
        self.sub_checker = SubscriberChecker(channel_id, headless=selenium_headless)

        if not self.sub_checker.driver:
            messagebox.showerror("오류", "WebDriver 초기화에 실패했습니다.")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        threading.Thread(target=self.run_checker, args=(selected_event,), daemon=True).start()

    def stop_program(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # 설정 변경 활성화
        self.channel_id_entry.config(state=tk.NORMAL)
        self.check_interval_entry.config(state=tk.NORMAL)
        self.headless_toggle.config(state=tk.NORMAL)
        self.event_selector.config(state=tk.NORMAL)
        self.save_config_button.config(state=tk.NORMAL)
        self.apply_config_button.config(state=tk.NORMAL)

    def run_checker(self, selected_event):
        prev_subscriber_count = None
        check_interval = int(self.check_interval_entry.get())

        try:
            while self.running:
                current_subscriber_count = self.sub_checker.get_subscriber_count()

                if current_subscriber_count is not None:
                    self.current_sub_label.config(text=f"현재 구독자 수: {current_subscriber_count}")

                    if prev_subscriber_count is not None and current_subscriber_count > prev_subscriber_count:
                        increase = current_subscriber_count - prev_subscriber_count
                        logging.info(f"구독자 수 변동: {prev_subscriber_count} -> {current_subscriber_count}")

                        if selected_event == "TNT 소환":
                            self.mc_handler.spawn_tnt(increase)
                        elif selected_event == "모루 떨어뜨리기":
                            self.mc_handler.drop_anvil(increase)

                    prev_subscriber_count = current_subscriber_count
                else:
                    logging.info("구독자 수를 가져올 수 없습니다.")

                time.sleep(check_interval)
        except Exception as e:
            logging.error(f"오류 발생: {e}")
        finally:
            self.stop_program()

if __name__ == "__main__":
    root = tk.Tk()
    app = MinecraftGUI(root)
    root.mainloop()
