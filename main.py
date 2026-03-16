from fastapi import FastAPI, UploadFile, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.websockets import WebSocketState
import asyncio
import copy
import logging
import os
import resource
import shutil
import tempfile
import uuid
import zipfile
from labs import LABS_CONFIG as labs

logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

class LogIPAddressMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        request.state.client_ip = client_ip
        response = await call_next(request)
        return response

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(LogIPAddressMiddleware)
clients = {}

check_semaphore = asyncio.Semaphore(1)
waiting_tasks = 0

def replace(data, replacements):
    if isinstance(data, list):
        return [replace(item, replacements) for item in data]
    elif isinstance(data, str):
        for placeholder, replacement in replacements.items():
            data = data.replace(placeholder, replacement)
        return data
    else:
        return data

@app.get("/get-labs")
async def get_labs():
    result = {}
    for lab_id, data in labs.items():
        result[lab_id] = data
    return result

def limit_student_resources():
    # Желаемый лимит: 512 МБ
    desired_limit = 512 * 1024 * 1024 
    
    # Получаем текущие лимиты системы (soft, hard)
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    
    # Если желаемый лимит выше жесткого, берем максимально доступный жесткий
    if hard != resource.RLIM_INFINITY and desired_limit > hard:
        final_limit = hard
    else:
        final_limit = desired_limit

    # Устанавливаем лимит (Hard limit не трогаем, меняем только Soft)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (final_limit, hard))
    except Exception as e:
        # Если не сработало, просто выходим — безопасность обеспечит Semaphore и Timeout
        pass

    # 🔒 Ограничение CPU
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))

    # 🔒 Ограничение числа процессов
    resource.setrlimit(resource.RLIMIT_NPROC, (5, 5))

    # 🔒 Ограничение файлов
    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))

@app.post("/upload-zip")
async def upload_zip(file: UploadFile, request: Request, session_id: str, lab_id: str, task: str):
    logging.info(f"ZIP upload: {file.filename}, Lab {lab_id}, Task: {task}, Session: {session_id}, IP: {request.state.client_ip}")

    if not all([session_id, lab_id, task]):
        return {"error": "Не переданы session_id, lab_id или task"}

    if session_id not in clients:
        return {"error": f"Сессия {session_id} не активна"}

    if lab_id not in labs:
        return {"error": f"Параметр lab_id должен иметь значение из списка {labs}"}

    if file.size > 32768:
        return {"error": "Размер архива превышает допустимые 32 KB"}

    # Создаем уникальную папку для этой проверки
    unique_id = str(uuid.uuid4())
 #   temp_dir = os.path.join("tmp", unique_id)
 #   os.makedirs(temp_dir, exist_ok=True)
    import tempfile
    temp_dir = os.path.join("/home/apprunner", "tmp", unique_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    zip_path = os.path.join(temp_dir, "upload.zip")

    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Извлекаем файлы напрямую в temp_dir, игнорируя вложенность архива если нужно
            for member in zip_ref.namelist():
                member_path = os.path.abspath(os.path.join(temp_dir, member))
                if not member_path.startswith(os.path.abspath(temp_dir)):
                    raise Exception("Zip path traversal detected")

            zip_ref.extractall(temp_dir)
        
        os.remove(zip_path)
        
        # Запускаем фоновую задачу
        asyncio.create_task(process_folder(session_id, temp_dir, lab_id, task))
        
        return {"message": "Архив принят и поставлен в очередь на проверку"}
    
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {"error": f"Ошибка обработки архива: {str(e)}"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()
    clients[session_id] = ws

    try:
        while True:
            await ws.receive_text()
    except:
        del clients[session_id]
        print(f"Удален session_id: {session_id}")

async def process_folder(session_id: str, folder_path: str, lab_id: str, task_filter: str):
    global waiting_tasks
    waiting_tasks += 1

    try:
        # Уведомляем пользователя о позиции, если сервер занят
        ws = clients.get(session_id)
        if waiting_tasks > 1:
            await safe_send(ws, f"Сервер занят. Вы в очереди: {waiting_tasks - 1}")

        # Используем семафор: если кто-то уже проверяется, этот подождет здесь
        async with check_semaphore:
            waiting_tasks -= 1

            if session_id not in clients:
                shutil.rmtree(folder_path, ignore_errors=True)
                return

            ws = clients[session_id]
            
            async def safe_send(text: str):
                if session_id in clients and ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(text)

            await safe_send(f"Начинаем проверку лабораторной {lab_id}...")

            # Определяем список задач
            tasks_to_check = labs[lab_id]["tests"].keys() if task_filter == "Все" else [task_filter]

            try:
                # Ищем файлы рекурсивно
                for root, _, files in os.walk(folder_path):
                    print("root", root)
                    for filename in files:
                        if filename in tasks_to_check:
                            file_path = os.path.join(root, filename)
                            tests = labs[lab_id]["tests"][filename]

                            await safe_send(f"<br>Тестируем {filename}...")

                            for t_type, timeout, args, expected in tests:
                                args_fact = replace(args, {"$USER$": root + "/"})
                                args_user = replace(args, {f"files/{lab_id}/": "", "$USER$": ""})
                                if t_type == "pub":
                                    if args and "$USER$" in args[-1]:
                                        await safe_send(f"<br>Тест: {' '.join(args_user)}, таймаут: {timeout}s")
                                        await safe_send(f"<img src=\"{expected}\" width=\"600\">")
                                    else:
                                        await safe_send(f"<br>Тест: {' '.join(args_user)}, ожидаемый результат: {expected}, таймаут: {timeout}s")
                                else:
                                    await safe_send(f"<br>Голуб Никита гей, таймаут: {timeout}s")

                                start_time = asyncio.get_running_loop().time()
                                proc = None
                                
                                try:
                                    # ЗАПУСК С ОГРАНИЧЕНИЯМИ
                                    proc = await asyncio.create_subprocess_exec(
                                        "python3", "-I", file_path, *args_fact,
                                        stdout=asyncio.subprocess.PIPE,
                                        stderr=asyncio.subprocess.PIPE,
                                        preexec_fn=limit_student_resources
                                    )
                                    
                                    try:
                                        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                                        elapsed = round(asyncio.get_running_loop().time() - start_time, 3)
                                        
                                        stdout = stdout[:10000] if stdout else b""
                                        stderr = stderr[:10000] if stderr else b""

                                        output = stdout.decode(errors="ignore").strip() if stdout else stderr.decode(errors="ignore").strip()
                                        
                                        if args and "$USER$" in args[-1]:
                                            await safe_send(f"Результат ({elapsed}s): <span style='color: blue'>IMAGE</span>")
                                            if t_type == 'pub':
                                                await safe_send(f"<img src=\"{args_fact[-1]}\" width=\"600\">")
                                            else:
                                                await safe_send(f"Вывод: ***")
                                        else:
                                            is_ok = (output == str(expected))
                                            status = "<span style='color: green'>OK</span>" if is_ok else "<span style='color: red'>ERROR</span>"      
                                            await safe_send(f"Результат ({elapsed}s): {status}<br>Вывод: {output if t_type == 'pub' else '***'}")
                         
                                    except asyncio.TimeoutError:
                                        if proc: proc.kill()
                                        await safe_send(f"<span style='color: orange'>TIMEOUT</span>: скрипт работал дольше {timeout}с")
                                        
                                except Exception as e:
                                    await safe_send(f"Ошибка запуска: {str(e)}")

                            await safe_send("<hr>")

            finally:
                await safe_send("<br><b>Все тесты завершены.</b>")
                await safe_send("<br>Проверка завершена")
                # Удаляем временные файлы сразу
                shutil.rmtree(folder_path, ignore_errors=True)
                # await asyncio.sleep(60)
                # shutil.rmtree(folder_path, ignore_errors=True)
    finally:
        pass

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/tmp/{file_path:path}")
async def get_tmp_file(file_path: str):

    base = os.path.abspath("tmp")
    full_path = os.path.abspath(os.path.join(base, file_path))

    if not full_path.startswith(base):
        return {"error": "Access denied"}

    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)

    return {"error": "Файл не найден"}

@app.get("/files/{file_path:path}")
async def get_file(file_path: str):

    base = os.path.abspath("files")
    full_path = os.path.abspath(os.path.join(base, file_path))

    if not full_path.startswith(base):
        return {"error": "Access denied"}

    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)

    return {"error": "Файл не найден"}
