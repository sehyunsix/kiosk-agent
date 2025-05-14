import cv2
import numpy as np
import pyautogui
from PIL import Image
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
import time
import json
from typing import List
import uvicorn

# --- Added for Gemini Integration ---
import os
from dotenv import load_dotenv
import google.generativeai as genai

# --- End Gemini Integration Additions ---

app = FastAPI()

# --- Added for Gemini Integration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Choose a model that supports vision, e.g., 'gemini-1.5-flash-latest' or 'gemini-pro-vision'
        # 'gemini-1.5-flash-latest' is often good for quick, general tasks.
        gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
        print("Gemini model initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        gemini_model = None
else:
    print(
        "GEMINI_API_KEY not found in .env file. AI description feature will be disabled."
    )
# --- End Gemini Integration Additions ---

# HTML 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 화면 캡처 및 리사이즈 설정
SCALE_FACTOR = 0.5
FRAME_RATE = 10


def capture_and_resize_screen():
    """화면을 캡처하고 지정된 비율로 리사이즈합니다."""
    try:
        screenshot = pyautogui.screenshot()
        width, height = screenshot.size
        new_width = int(width * SCALE_FACTOR)
        new_height = int(height * SCALE_FACTOR)
        resized_image = screenshot.resize((new_width, new_height), Image.LANCZOS)
        return resized_image
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return Image.new(
            "RGB", (int(100 * SCALE_FACTOR), int(100 * SCALE_FACTOR)), color="black"
        )


async def generate_frames():
    """화면 캡처 프레임을 JPEG 형식으로 생성하는 비동기 제너레이터 함수입니다."""
    while True:
        pil_image = capture_and_resize_screen()
        frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            await asyncio.sleep(0.01)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(encodedImage) + b"\r\n"
        )
        await asyncio.sleep(1 / FRAME_RATE)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


# --- AI Screen Description Function ---
async def get_ai_screen_description() -> str:
    if not gemini_model:
        return "AI description service is not available (model not initialized)."
    try:
        pil_image = capture_and_resize_screen()
        if pil_image.mode == "RGBA":  # Gemini API might prefer RGB
            pil_image = pil_image.convert("RGB")

        # Prepare content for Gemini API (prompt + image)
        prompt = "Describe what you see on this screen in a single, concise sentence."
        response = await gemini_model.generate_content_async([prompt, pil_image])

        if response and hasattr(response, "text") and response.text:
            return response.text
        elif response and response.parts:  # Fallback for some response structures
            for part in response.parts:
                if hasattr(part, "text") and part.text:
                    return part.text
        return "AI could not generate a description."

    except Exception as e:
        print(f"Error getting AI screen description: {e}")
        return f"Error communicating with AI: {str(e)}"


# --- End AI Screen Description Function ---


# --- WebSocket 채팅 로직 추가 ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_id_for_log = (
        f"{websocket.client.host}:{websocket.client.port}"  # For logging
    )
    print(f"Client connected: {client_id_for_log}")
    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                message_json = json.loads(data_str)
                user_message = message_json.get("message", "").strip()
                sender_id = message_json.get("senderId", "anonymous")

                if user_message.lower() == "/describe":
                    print(
                        f"Received /describe command from {sender_id} ({client_id_for_log})"
                    )
                    if not gemini_model:
                        ai_response_text = (
                            "AI description service is currently unavailable."
                        )
                    else:
                        # Inform users that description is being generated
                        generating_msg = {
                            "senderId": "System",
                            "message": "AI is generating screen description, please wait...",
                        }
                        await manager.broadcast(json.dumps(generating_msg))
                        ai_response_text = await get_ai_screen_description()

                    ai_message_payload = {
                        "senderId": "AI Assistant",
                        "message": ai_response_text,
                    }
                    await manager.broadcast(json.dumps(ai_message_payload))
                else:
                    # Broadcast regular user message
                    await manager.broadcast(
                        data_str
                    )  # Broadcast the original JSON string

            except json.JSONDecodeError:
                print(f"Invalid JSON received from {client_id_for_log}: {data_str}")
                error_payload = {
                    "senderId": "System",
                    "message": "Error: Invalid message format.",
                }
                await websocket.send_text(
                    json.dumps(error_payload)
                )  # Send error only to the sender
            except Exception as e:  # Catch other errors during message processing
                print(f"Error processing message from {client_id_for_log}: {e}")
                error_payload = {
                    "senderId": "System",
                    "message": f"Server error processing message: {str(e)}",
                }
                await websocket.send_text(json.dumps(error_payload))

    except WebSocketDisconnect:
        print(f"Client disconnected: {client_id_for_log}")
        # No need to broadcast user disconnect message unless you want to
        # disconnect_msg = {"senderId": "System", "message": f"User {sender_id if 'sender_id' in locals() else client_id_for_log} disconnected."}
        # await manager.broadcast(json.dumps(disconnect_msg))
    except Exception as e:
        print(f"Unexpected WebSocket error with {client_id_for_log}: {e}")
    finally:
        manager.disconnect(websocket)  # Ensure client is removed on any exit


# --- WebSocket 채팅 로직 종료 ---

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
