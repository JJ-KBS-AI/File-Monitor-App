# 파일 입고 모니터링 시스템 (File-Monitor-App)

## 개요

`File-Monitor-App`은 **영상/미디어 파일의 입고 상태를 실시간으로 모니터링**하는 Windows 데스크톱 애플리케이션입니다. 지정 폴더를 주기적으로 감시하여:

- 새 파일이 생성되면 **입고 시작**
- 일정 시간 동안 파일 용량이 변하지 않으면 **입고 완료**

로 판단하고, **데스크톱 알림(토스트)**과 **WAV 알림음**을 재생합니다.

UI는 **PyQt5** 기반이며, PyInstaller로 단일 EXE 패키징을 지원합니다.

---

## 주요 기능

### 1. 폴더 감시 및 입고 상태 표시

- 여러 폴더를 동시에 감시 (초 단위 주기 설정, 기본 10초)
- 폴더별 상태: `대기 중`, `감시 중`, `입고 중`, `입고 완료`, `중지됨`

### 2. 확장자 관리 (체크박스 + 수동 추가)

- 기본 감시 확장자: `.mxf`, `.mov`, `.mp4`, `.mkv`, `.avi`, `.m4v`, `.ts`, `.m2ts`, `.wmv`, `.mpg`, `.mpeg`, `.prores`
- 체크박스로 개별 확장자 On/Off
- 리스트에 없는 확장자는 입력란 + "확장자 추가" 버튼으로 추가

### 3. 용량 기반 입고 시작/완료 판단

- **입고 시작**: 새 파일 발견 시 즉시 "파일 입고가 시작되었습니다." 알림
- **입고 완료**: 파일 용량이 일정 시간(기본 30초) 변하지 않으면 "파일 입고가 완료되었습니다." 알림
- 각 파일별 시작/완료 알림 각 1회만 발생

### 4. 네트워크 경로 고려

- "입고 완료 판정 대기시간"을 10~300초 범위로 조정 가능
- 네트워크 드라이브에서는 값을 크게(예: 60초 이상) 설정 권장

### 5. 경로 추가/삭제 + 프리셋

- "+ 폴더 추가", "- 폴더 삭제" 버튼
- 감시 경로·주기·알림음을 JSON 프리셋으로 저장/불러오기

### 6. WAV 알림음 번들링

- PyInstaller 패키징 시 기본 WAV를 EXE에 포함 가능 (`assets/sounds/notify.wav`)

---

## 프로젝트 구조

```
MXFMonitorAppForWin/
  main.py                 # 실행 진입점
  app/
    config.py             # 상수, 기본 설정
    models.py             # FileStatus, MonitoredFile
    monitor.py            # FolderCheckerWorker, MonitorController
    notifications.py      # 토스트 + WAV 알림
    ui_main_window.py     # MainWindow
    presets.py            # 프리셋 JSON IO
    resources/
  MXFMonitorApp.py        # main.py 위임 래퍼
  MXFMonitorApp.spec      # PyInstaller 스펙
  requirements.txt
  requirements-dev.txt
  tests/
```

---

## 실행 방법

```bash
pip install -r requirements.txt
python main.py
```

또는 `py main.py`

---

## 테스트

```bash
pip install -r requirements-dev.txt
pytest
```

---

## PyInstaller 패키징

```bash
pyinstaller MXFMonitorApp.spec
```

`datas`에 `assets/sounds/notify.wav`를 포함하면 기본 알림음이 EXE에 번들링됩니다.

---

## 기술 스택

- Python 3.x
- PyQt5
- plyer
- pytest / pytest-qt
- PyInstaller
