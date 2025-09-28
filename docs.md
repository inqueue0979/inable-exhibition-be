# 대체텍스트 평가 API 문서

Flask 기반의 대체텍스트 평가 서비스 API 문서입니다.

## 목차
- [서버 실행](#서버-실행)
- [API 엔드포인트](#api-엔드포인트)
- [요청/응답 예시](#요청응답-예시)
- [에러 코드](#에러-코드)

## 서버 실행

### 환경 설정
```bash
# 환경변수 설정
cp .env.example .env
# .env 파일에 OpenAI API 키 입력: OPENAI_API_KEY=your_api_key_here

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python app.py
```

서버는 기본적으로 `http://127.0.0.1:5000`에서 실행됩니다.

## API 엔드포인트

### 1. 대체텍스트 평가

**POST** `/evaluate`

이미지와 대체텍스트를 분석하여 품질을 평가합니다.

#### 요청 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| alt_text | string | O | 평가할 대체텍스트 |
| image_data | string | O | base64 인코딩된 이미지 또는 data URL |

#### 응답
```json
{
  "type": "이미지 유형",
  "grade": "준수 등급",
  "reason": "판단 근거",
  "improvement": "개선 제안",
  "compliant": 0,
  "evaluation_id": 1
}
```

#### 이미지 유형
- `정보성`: 본문 내용을 보조하거나 문맥상 중요한 정보를 제공
- `기능성`: 클릭, 터치 등의 인터랙션을 유발하는 이미지
- `장식적`: 시각적 미관 목적, 정보 전달 역할 없음
- `복합적`: 표, 차트, 인포그래픽 등 구조적 설명이 필요한 경우

#### 준수 등급
- `매우높음`: 상세한 설명까지 포함된 우수한 대체텍스트
- `조금높음`: 기능적으로 필요한 정보를 적절히 전달
- `조금낮음`: 일부 정보 누락이나 개선이 필요
- `매우낮음`: 핵심 정보 누락으로 대폭 개선 필요

#### Compliant 값
- `0`: 매우높음
- `1`: 조금높음
- `2`: 조금낮음
- `3`: 매우낮음

---

### 2. 평가 히스토리 조회

**GET** `/history`

과거 평가 기록을 조회합니다.

#### 쿼리 파라미터
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| limit | integer | 50 | 조회할 개수 |
| offset | integer | 0 | 건너뛸 개수 |

#### 응답
```json
{
  "history": [
    {
      "id": 1,
      "alt_text": "대체텍스트",
      "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
      "image_type": "이미지 유형",
      "grade": "준수 등급",
      "reason": "판단 근거",
      "improvement": "개선 제안",
      "compliant": 0,
      "created_at": "2024-01-01 10:00:00"
    }
  ],
  "count": 1
}
```

---

### 3. 특정 평가 상세 조회

**GET** `/history/{evaluation_id}`

특정 평가 ID의 상세 정보를 조회합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| evaluation_id | integer | O | 평가 ID |

#### 응답
```json
{
  "id": 1,
  "alt_text": "대체텍스트",
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "image_type": "이미지 유형",
  "grade": "준수 등급",
  "reason": "판단 근거",
  "improvement": "개선 제안",
  "compliant": 0,
  "created_at": "2024-01-01 10:00:00"
}
```

---

### 4. 통계 정보 조회

**GET** `/statistics`

전체 평가 통계를 조회합니다.

#### 응답
```json
{
  "total_evaluations": 100,
  "type_distribution": {
    "정보성": 40,
    "기능성": 30,
    "장식적": 20,
    "복합적": 10
  },
  "grade_distribution": {
    "매우높음": 25,
    "조금높음": 35,
    "조금낮음": 30,
    "매우낮음": 10
  },
  "compliant_distribution": {
    "0": 25,
    "1": 35,
    "2": 30,
    "3": 10
  }
}
```

---

### 5. 서버 상태 확인

**GET** `/health`

서버 상태를 확인합니다.

#### 응답
```json
{
  "status": "healthy"
}
```

## 요청/응답 예시

### 대체텍스트 평가 요청
```bash
curl -X POST http://127.0.0.1:5000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "alt_text": "회사 로고",
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
  }'
```

### 평가 응답
```json
{
  "type": "기능성",
  "grade": "조금낮음",
  "reason": "대체텍스트가 이미지의 핵심 정보를 20% 정도만 포함하고 있어 기능성을 명확히 전달하지 못함",
  "improvement": "메인 페이지로 이동하는 회사 로고 버튼",
  "compliant": 2,
  "evaluation_id": 1
}
```

### 히스토리 조회 요청
```bash
curl "http://127.0.0.1:5000/history?limit=10&offset=0"
```

### 특정 평가 조회 요청
```bash
curl "http://127.0.0.1:5000/history/1"
```

### 통계 조회 요청
```bash
curl "http://127.0.0.1:5000/statistics"
```

## 에러 코드

### 400 Bad Request
- JSON 데이터가 필요합니다
- alt_text가 필요합니다
- image_data가 필요합니다

### 404 Not Found
- 평가를 찾을 수 없습니다

### 500 Internal Server Error
- OpenAI API 호출 오류
- 데이터베이스 오류
- 기타 서버 내부 오류

## 데이터베이스

### 테이블 구조
- **evaluations** 테이블
  - `id`: 자동 증가 PRIMARY KEY
  - `alt_text`: 평가된 대체텍스트
  - `image_data`: base64 인코딩된 이미지 데이터
  - `image_type`: 이미지 유형
  - `grade`: 준수 등급
  - `reason`: 판단 근거
  - `improvement`: 개선 제안
  - `compliant`: 준수도 (0-3)
  - `created_at`: 생성 시간

데이터베이스 파일은 `alt_text_evaluations.db`로 자동 생성됩니다.