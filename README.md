# MS2025-MCP-Azure
MCP with MS Azure: MS CAIP intern

# Repository Quickstart (Per-Folder Template)

이 저장소는 **각 폴더마다 독립적인 uv 기반 Python 프로젝트**로 구성됩니다.
새 폴더(모듈)를 만들거나, 기존 폴더에서 바로 실습을 시작하려면 아래를 따르세요.

---

## 1. 새 폴더(모듈) 만들 때

```bash
# 1) 프로젝트 생성 (원하는 폴더명으로 변경)
uv init <YOUR_FOLDER_NAME>

# 2) 경로 이동
cd <YOUR_FOLDER_NAME>

# 3) 가상환경 생성 및 활성화
uv venv
# Windows (Git Bash)
source .venv/Scripts/activate
# Windows (PowerShell)
# .\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

# 4) MCP CLI 포함 설치
uv add "mcp[cli]"
```

---

## 2. 기존 폴더에서 시작할 때

이미 저장소에 폴더가 있다면, 해당 폴더로 이동 후 3번부터 진행하세요.

```bash
cd <EXISTING_FOLDER_NAME>
uv venv
# Windows (Git Bash)
source .venv/Scripts/activate
# Windows (PowerShell)
# .\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

uv add "mcp[cli]"
```

---

## 참고

* 사전 요구사항: Python 설치 및 `uv` 사용 가능 환경 (Python 3.10+)
* 가상환경 비활성화는 `deactivate`