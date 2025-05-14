# Kiosk Agent: 실시간 화면 공유 및 AI 기반 화면 설명 웹 애플리케이션

## 개요

Kiosk Agent는 사용자의 현재 화면을 실시간으로 웹 브라우저를 통해 공유하고, 연결된 다른 사용자와 채팅을 통해 소통하며, Google Gemini AI를 활용하여 화면 내용을 설명하는 기능을 제공하는 FastAPI 기반 웹 애플리케_이_션입니다.

이 프로젝트는 원격 지원, 화면 공유 기반의 협업, 또는 키오스크/디지털 사이니지 모니터링 등 다양한 시나리오에 활용될 수 있습니다.

## 주요 기능

*   **실시간 화면 스트리밍**: `pyautogui`를 사용하여 서버가 실행 중인 머신의 화면을 캡처하고, 이를 `multipart/x-mixed-replace` 스트림으로 웹 클라이언트에 전송하여 실시간으로 화면을 보여줍니다.
*   **웹소켓 기반 실시간 채팅**: FastAPI의 WebSocket 지원을 활용하여 여러 사용자가 동시에 접속하여 화면 내용에 대해 실시간으로 대화할 수 있습니다.
*   **AI 기반 화면 설명**:
    *   채팅창에 `"/describe"` 명령어를 입력하면, 현재 화면이 캡처되어 Google Gemini AI 모델로 전송됩니다.
    *   AI는 화면 내용을 분석하여 간결한 문장으로 설명하고, 이 설명은 "AI Assistant"라는 이름으로 채팅창에 표시됩니다.
*   **환경 변수를 통한 API 키 관리**: Google Gemini API 키는 `.env` 파일을 통해 안전하게 관리됩니다.

## 기술 스택

*   **백엔드**:
    *   Python 3
    *   FastAPI: 고성능 웹 프레임워크
    *   Uvicorn: ASGI 서버
    *   PyAutoGUI: 화면 캡처
    *   Pillow (PIL): 이미지 처리 및 리사이징
    *   OpenCV-Python: 이미지 인코딩 (JPEG)
    *   python-dotenv: 환경 변수 관리
    *   google-generativeai: Google Gemini API 연동
*   **프론트엔드**:
    *   HTML5
    *   CSS3
    *   JavaScript (Vanilla JS): 웹소켓 통신 및 동적 UI 업데이트

## 시스템 요구 사항

*   Python 3.8 이상
*   `pip` (Python 패키지 설치 관리자)
*   화면 캡처가 가능한 운영체제 (Windows, macOS, Linux with X server)
*   Google Gemini API 키 (AI 화면 설명 기능을 사용하려면 필요)

## 설치 및 실행 방법

1.  **저장소 복제 (Clone the repository):**
    ```bash
    git clone <repository-url>
    cd kiosk-agent
    ```

2.  **가상 환경 생성 및 활성화 (권장):**
    ```bash
    python -m venv venv
    # Windows
    # venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```

3.  **필요한 라이브러리 설치:**
    ```bash
    pip install -r requirements.txt
    ```
    (아래 `requirements.txt` 파일 생성 섹션 참조)

4.  **환경 변수 설정:**
    프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 Google Gemini API 키를 입력합니다.
    ```env
    # .env
    GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
    ```
    AI 기능을 사용하지 않으려면 이 단계를 건너뛸 수 있으며, 프로그램 실행 시 관련 기능이 비활성화됩니다.

5.  **FastAPI 애플리케이션 실행:**
    Python 스크립트 (예: `screen.py` 또는 `main.py`)가 있는 디렉토리에서 다음 명령어를 실행합니다.
    ```bash
    python screen.py
    ```
    또는 Uvicorn을 직접 사용하여 개발 모드로 실행할 수 있습니다 (자동 리로드 기능):
    ```bash
    uvicorn screen:app --reload --host 0.0.0.0 --port 8000
    ```
    (`screen`은 Python 파일 이름, `app`은 FastAPI 인스턴스 이름입니다. 실제 파일 및 인스턴스 이름에 맞게 수정하세요.)

6.  **웹 브라우저에서 접속:**
    웹 브라우저를 열고 `http://localhost:8000` (또는 서버 실행 시 표시된 주소)으로 접속합니다.

## `requirements.txt` 파일 생성

프로젝트의 의존성을 관리하기 위해 `requirements.txt` 파일을 생성하는 것이 좋습니다. 현재까지 언급된 라이브러리를 기반으로 한 예시는 다음과 같습니다:

```text
# requirements.txt
fastapi
uvicorn[standard]
pyautogui
Pillow
opencv-python
numpy
jinja2
python-dotenv
google-generativeai