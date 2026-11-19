# Worship Stem Player — MVP v0.1

교회 내부에서 테스트하기 위한 **로컬 단일 서버** MVP입니다. 상용 SaaS 완성품이 아닙니다.

## 실행

Python 3.10~3.12 권장. ffmpeg 설치 및 PATH 등록 필요. Demucs 실행에는 PyTorch와 모델 다운로드가 필요합니다.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install demucs
uvicorn app:app --host 127.0.0.1 --port 8000
```

브라우저에서 http://127.0.0.1:8000 접속. 첫 AI 실행 시 모델 가중치 다운로드로 시간이 걸릴 수 있습니다. CPU 분리는 느리므로 GPU 권장. 기기별 브라우저 재생 테스트 필요.

## 구현됨
- 파일 업로드(100MB 제한, 확장자 검사), SQLite 곡 저장
- Demucs htdemucs_6s 비동기 작업 시작, 처리 상태 확인
- WAV 분리 결과 제공, 악기별 볼륨/음소거
- Web Audio API 기반 동시 시작, 재생/일시정지/탐색
- 모바일 대응 UI

## 구현되지 않음 / 상용화 전 필수
- 회원가입/조직별 격리/권한, 구독 결제, 안전한 클라우드 저장
- 파일 MIME/콘텐츠 검증, 바이러스 검사, 업로드 악용 방지, 인증, 요청 제한
- 영속 작업 큐, 동시 작업 제어, 실패 재시도, GPU 작업 분산
- 오프라인 재생, PWA 설치, 콘티, 클릭/큐, 다중 채널 출력
- 큰 음원에 대한 스트리밍 재생/메모리 최적화, 기기별 호환성 테스트
- 음원 라이선스 확인 및 보관·삭제 정책

## 주의
Demucs 6-stem의 `guitar`는 **일렉기타 전용 트랙이 아닙니다**. 원곡에 따라 어쿠스틱 기타 등이 섞일 수 있고 분리 아티팩트가 발생할 수 있습니다. 음원 분리·재생 권한을 확보한 파일로만 시험하세요.

로컬 테스트용으로 인증이 없으므로 인터넷에 직접 공개하지 마세요. 분리 작업은 프로세스 종료 시 중단될 수 있습니다.
