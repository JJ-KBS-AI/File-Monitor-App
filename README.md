# 파일 입고 모니터링 시스템 (File-Monitor-App)

Windows 환경에서 영상/미디어 파일 입고를 감시하는 PyQt5 기반 데스크톱 앱입니다.  
방송 제작/후반 작업 환경에서 **새 파일 유입 감지**, **입고 완료 판정**, **토스트+사운드 알림**을 제공합니다.

---

## 핵심 기능

### 1) 폴더 감시
- 다중 폴더 감시 지원
- 폴더별 상태 표시: `대기 중`, `감시 중`, `입고 중`, `입고 완료`, `중지됨`
- 감시 시작/정지를 하나의 토글 버튼(`▶/⏹`)으로 제어
- 감시 중 설정 버튼 비활성화로 실행 중 값 변경 방지

### 2) 확장자 관리 다이얼로그
- 기본/사용자 확장자를 **단일 리스트**로 통합 관리
- 확장자 토글 버튼으로 포함/제외
- `✕` 버튼으로 리스트 삭제
- 직접 입력 + Enter/추가 버튼으로 신규 확장자 등록
- 3열 그리드 배치로 가독성 향상

### 3) 입고 판정 로직 (네트워크 스토리지 보강)
- 감시 주기(`interval`)마다 파일 스캔
- 신규 파일 감지 시 `입고 시작` 이벤트 발생
- 완료 판정은 아래 조건을 모두 충족해야 함
  - `size` 변화 없음
  - `mtime`(수정 시각) 변화 없음
  - 안정 시간(`stable_seconds`) 이상 유지
  - 연속 안정 스캔 횟수(`MIN_STABLE_CHECKS`) 이상
- 네트워크 공유 스토리지의 일시 정체 구간에서 발생하던 조기 완료 오탐을 완화

### 4) 알림/사운드
- 입고 시작: `start.wav`
- 입고 완료: `complete.wav`
- 개발 실행/패키징 실행 모두에서 리소스 경로 자동 탐색

### 5) 프리셋 저장/불러오기
- 저장 항목: 감시 폴더 목록, 확장자 목록, 감시 주기
- 프리셋 저장 경로를 사용자 쓰기 가능 경로로 변경
  - `C:\Users\<사용자>\AppData\Local\KBS\MXFMonitorApp\mxf_monitor_preset.json`
- 구버전 호환: 새 경로가 없으면 기존 상대 경로 프리셋도 로드
- 저장/불러오기 실패 시 예외 메시지 표시(Freeze 방지)

### 6) UI/UX
- 좌측(감시/완료 테이블) + 우측(제어 패널) 레이아웃
- KBS CI 색상 적용(보라/블루/오렌지)
- `KBS_CI.ttf` 폰트 로딩 및 제목 스타일 반영
- 모든 버튼 라운드 처리
- 버튼 도움말 1초 지연 표시 + 도움말 ON/OFF 토글(`❓`)
- 도움말 토글 버튼은 OFF 상태에서도 고정 안내 툴팁 표시

---

## 기본 설정값

- 감시 주기 기본값: **30초**
- 입고 완료 대기시간 기본값: **60초**
- 완료 대기시간 범위: **10~300초**
- 최소 안정 스캔 횟수: **3회** (`MIN_STABLE_CHECKS`)

---

## 프로젝트 구조

```text
MXFMonitorAppForWin/
  main.py
  MXFMonitorApp.py
  MXFMonitorApp.spec
  MXFMonitorAppInstaller.iss
  MXFMonitorApp.ico
  KBS_CI.ttf
  app/
    config.py
    models.py
    monitor.py
    notifications.py
    presets.py
    styles.py
    ui_main_window.py
    ui_extensions_dialog.py
    assets/
      sounds/
        start.wav
        complete.wav
  requirements.txt
  requirements-dev.txt
```

---

## 로컬 실행

```bash
pip install -r requirements.txt
py main.py
```

---

## 테스트

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 빌드

### 1) 실행 파일(EXE) 빌드

`MXFMonitorApp.spec` 기준으로 빌드합니다.

```bash
py -m PyInstaller --clean MXFMonitorApp.spec
```

산출물:
- `dist/MXFMonitorApp.exe`

포함 리소스:
- `app/assets/sounds/start.wav`
- `app/assets/sounds/complete.wav`
- `MXFMonitorApp.ico`
- `KBS_CI.ttf`

### 2) 설치 파일(Setup) 빌드

Inno Setup 6 기준:

```bash
ISCC MXFMonitorAppInstaller.iss
```

산출물:
- `installer/MXFMonitorApp_Setup.exe`

---

## 기술 스택

- Python 3.x
- PyQt5
- plyer
- PyInstaller
- Inno Setup 6
- pytest / pytest-qt
