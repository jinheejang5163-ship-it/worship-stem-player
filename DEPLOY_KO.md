# Worship Stem Player — 클라우드 웹 미리보기 배포

## 현재 범위
웹 화면, 로그인 보호(HTTP Basic), 곡 업로드, 목록, 믹서 화면이 포함됩니다. **AI 분리 기능은 기본 비활성화**입니다. 실제 분리 기능에는 별도의 Demucs/PyTorch 실행 환경과 충분한 CPU/GPU가 필요합니다. 이 프로젝트는 상용 서비스나 공개 업로드 서비스로 검증되지 않았습니다.

## 배포
1. GitHub에서 새 **Private** repository를 만듭니다. 이 폴더의 파일들을 repository 최상위에 업로드합니다 (Dockerfile, app.py, requirements.txt, static 폴더).
2. Render에서 New > Web Service > GitHub repository를 연결합니다.
3. Language/Runtime은 **Docker**, Dockerfile Path는 `./Dockerfile`로 설정합니다.
4. Environment에 `APP_USERNAME`과 `APP_PASSWORD`를 등록합니다. 비밀번호는 충분히 길고 고유한 값을 사용합니다. `ENABLE_AI=false`로 둡니다.
5. 먼저 웹 화면만 확인하려면 테스트용 파일만 사용하세요. **Render 기본 파일 시스템은 재배포/재시작 시 데이터가 사라집니다.**
6. 데이터를 보존하려면 유료 서비스의 persistent disk를 `/app/data`에 연결하고 `WORSHIP_DATA=/app/data`로 설정합니다. 그래도 이 구성은 교회별 격리, 사용자별 권한, 백업, 저작권 검증, 큐 기반 AI 작업을 지원하지 않습니다.
7. 배포가 성공하면 Render에서 제공하는 `https://...onrender.com` 주소를 엽니다. 브라우저의 사용자 이름/암호 창에 위 값을 입력합니다.

## 주의
- HTTPS를 사용하는 Render URL에서만 비밀번호를 입력하세요.
- 인증 없이 서비스를 공개하지 마세요.
- 실제 저작권 있는 상용 음원을 테스트용으로 업로드하기 전에 권한을 확인하세요.
- Basic Auth는 소수의 내부 테스터를 위한 임시 접근 제한입니다. 상용 서비스에는 별도의 계정/권한 체계가 필요합니다.
- AI가 비활성화되어 있어 '악기 분리' 버튼은 안내 오류를 반환합니다. 정상적인 동작입니다.
