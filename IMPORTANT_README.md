# 🚨 중요: 계정 정보 보호 가이드

## ⚠️ 절대 삭제하면 안 되는 파일

### 1. `.env` 파일
```
위치: E:\u\coupang-wing-cs-automation\.env
중요도: ★★★★★ (최고)
```

**이 파일에는 암호화 키(`ENCRYPTION_KEY`)가 들어있습니다.**

- 이 키가 변경되거나 삭제되면 **저장된 모든 계정 정보를 복호화할 수 없습니다**
- 반드시 안전한 곳에 백업 보관하세요
- **절대 GitHub에 업로드하지 마세요** (.gitignore에 포함됨)

#### 백업 방법
```bash
# .env 파일을 USB나 안전한 곳에 복사
copy .env "D:\안전한백업\env_백업_2024.txt"
```

### 2. `database/coupang_cs.db` 파일
```
위치: E:\u\coupang-wing-cs-automation\database\coupang_cs.db
중요도: ★★★★★ (최고)
```

**이 파일에 모든 계정 정보와 반품 로그가 저장됩니다.**

#### 자동 백업 (권장)
```bash
# 백업 생성
python backup_database.py backup

# 백업 목록 확인
python backup_database.py list

# 복원 (필요시)
python backup_database.py restore backups/coupang_cs_backup_20241115_123456.db
```

## 📋 데이터 보호 체크리스트

- [ ] `.env` 파일을 USB에 백업했습니다
- [ ] `database/coupang_cs.db` 파일을 정기적으로 백업합니다
- [ ] `backups/` 폴더를 클라우드(구글 드라이브 등)에 백업합니다
- [ ] `.env` 파일의 `ENCRYPTION_KEY` 값을 별도로 기록했습니다

## 🔐 암호화 키 복구

만약 `.env` 파일이 손실된 경우:

1. **백업이 있는 경우**: 백업된 `.env` 파일을 복사
2. **백업이 없는 경우**: **저장된 계정 정보를 복호화할 수 없습니다**
   - 계정을 다시 등록해야 합니다

## 💾 정기 백업 권장

**매일 자동 백업 설정 (Windows 작업 스케줄러)**

1. "작업 스케줄러" 열기
2. "기본 작업 만들기" 클릭
3. 이름: "쿠팡 DB 백업"
4. 트리거: 매일, 새벽 2시
5. 작업: 프로그램 시작
   - 프로그램: `python`
   - 인수: `E:\u\coupang-wing-cs-automation\backup_database.py backup`
   - 시작 위치: `E:\u\coupang-wing-cs-automation`

## 🆘 긴급 복구 가이드

### 서버가 재시작되었는데 계정 정보가 사라진 경우

**원인**: `.env` 파일의 `ENCRYPTION_KEY`가 없어서 매번 새로운 키가 생성됨

**해결**:
1. `.env` 파일 확인
2. `ENCRYPTION_KEY=` 라인이 있는지 확인
3. 없으면 백업에서 복구하거나, 계정을 다시 등록

### 데이터베이스가 손상된 경우

```bash
# 최신 백업에서 복원
python backup_database.py list
python backup_database.py restore backups/[최신_백업파일.db]
```

## 📞 문제 발생 시

1. `backups/` 폴더 확인
2. 최신 백업 파일 확인
3. `.env` 백업 파일 확인
4. 위의 복구 가이드 따라하기

---

**⚠️ 이 파일을 프린트하거나 안전한 곳에 보관하세요!**
