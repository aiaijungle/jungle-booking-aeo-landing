import schedule
import time
import subprocess
import os
import datetime
import sys

# 스크립트 실행 폴더를 워킹 디렉토리로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_and_deploy_blog():
    print(f"\n==================================================")
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 자동 포스팅 스케줄 실행 시작!")
    print(f"==================================================")
    
    try:
        # 1. 블로그 생성 스크립트 실행
        print("[1/2] 블로그 포스팅 AI 자동 생성 중 (auto_blog_builder.py)...")
        subprocess.run([sys.executable, "auto_blog_builder.py"], cwd=BASE_DIR, check=True)
        
        # 2. Github 업데이트 (배포)
        print("[2/2] Github 자동 배포 (Git Push) 진행 중...")
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"Auto Deploy: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} 스케줄링 자동 포스팅"], cwd=BASE_DIR, check=False) # 변경사항 없을 시 대비 check=False
        subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
        
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 배포까지 완벽하게 완료되었습니다!\n")
    except Exception as e:
        print(f"오류 발생: {e}")

print("⏰ [정글부킹 마케팅] 블로그 자동화 스케줄러 동작 중...")
print("이 창을 켜두시면 다음 정해진 시간에 블로그가 '자동 생성 + 배포' 됩니다.")
print("목표 시간: 오전 09:00, 오후 12:00, 오후 15:00\n")

# 스케줄 등록
schedule.every().day.at("09:00").do(generate_and_deploy_blog)
schedule.every().day.at("12:00").do(generate_and_deploy_blog)
schedule.every().day.at("15:00").do(generate_and_deploy_blog)

if __name__ == "__main__":
    try:
        while True:
            schedule.run_pending()
            time.sleep(30) # 30초마다 확인
    except KeyboardInterrupt:
        print("스케줄러를 종료합니다.")
