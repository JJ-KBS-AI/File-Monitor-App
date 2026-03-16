# 파일 입고 모니터링 시스템 (File-Monitor-App)

Windows 환경에서 영상/미디어 파일 입고를 자동 감시하는 PyQt5 기반 데스크톱 앱입니다.

- 새 파일 감지 시: **입고 시작**
- 파일 크기가 일정 시간 변하지 않으면: **입고 완료**
- 입고 이벤트마다 토스트 알림 + WAV 사운드 재생

---

## 현재 버전 주요 기능

### 1) 폴더 감시

- 다중 폴더 감시 지원
- 폴더 상태 표시: `대기 중`, `감시 중`, `입고 중`, `입고 완료`, `중지됨`
- 감시 시작/정지 토글 버튼으로 즉시 전환

### 2) 확장자 관리 (단일 리스트 구조)

- 기본/사용자 추가 구분 없이 **하나의 리스트로 통합 관리**
- 토글 버튼: 감시 포함/제외
- `✕` 버튼: 리스트에서 완전 삭제
- 직접 입력 + Enter 또는 추가 버튼으로 확장자 등록
- 예시: `.mxf`, `.mov`, `.mp4` (기본값)

### 3) 입고 판정 로직

- 감시 주기(`interval`)마다 스캔
- 새 파일 발견 시 입고 시작 이벤트 발생
- 파일 크기 변화가 `stable_seconds` 동안 없으면 입고 완료 처리

### 4) 알림/사운드

- 시작 알림음: `start.wav`
- 완료 알림음: `complete.wav`
- 앱 실행/패키징 환경 모두에서 리소스 경로 자동 처리

### 5) 프리셋 저장/불러오기

- JSON 프리셋 저장 항목:
  - 감시 폴더 목록
  - 확장자 목록
  - 감시 주기
- 버튼 도움말(툴팁)로 저장 항목 안내

### 6) UI/UX 개선 사항

- KBS CI 기반 색상/폰트 적용
- `KBS_CI` 폰트 우선 사용(없으면 시스템 폰트 폴백)
- 좌측 리스트(감시 폴더/입고 완료 목록) + 우측 제어 패널 구성
- 창 확장 시 좌측 리스트 영역 중심으로 확장
- 버튼 hover 1초 후 도움말 표시 + ON/OFF 토글 지원

---

## 기본 설정값

- 감시 주기 기본값: **30초**
- 입고 완료 판정 대기시간 기본값: **60초**
- 대기시간 허용 범위: **10 ~ 300초**

---

## 프로젝트 구조

```text
MXFMonitorAppForWin/
  main.py
  MXFMonitorApp.py
  MXFMonitorApp.spec
  MXFMonitorApp.ico
  start.wav
  complete.wav
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
  tests/
  requirements.txt
  requirements-dev.txt
```

---

## 실행 방법

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

## 패키징 (PyInstaller)

`MXFMonitorApp.spec` 기준으로 빌드합니다.

```bash
py -m PyInstaller --clean MXFMonitorApp.spec
```

빌드 결과:

- `dist/MXFMonitorApp.exe`

스펙 파일에 다음 리소스가 포함됩니다.

- `app/assets/sounds/start.wav`
- `app/assets/sounds/complete.wav`
- `MXFMonitorApp.ico`

---

## 기술 스택

- Python 3.x
- PyQt5
- plyer
- PyInstaller
- pytest / pytest-qt
