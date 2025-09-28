from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from database import DatabaseManager

load_dotenv()

app = Flask(__name__)
CORS(app)
db_manager = DatabaseManager()

class AltTextEvaluator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def evaluate_alt_text(self, alt_text, image_data):
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            '''
                            role: 이미지에 대한 <대체텍스트> 평가 및 대체텍스트 생성

                        task:

                        해당 이미지가 웹 사이트 내에서 하는 역할을 추측하여 이미지 유형을 분류한다.

                        [ 이미지 유형 정의 ]

                        1. 정보성 이미지: 본문 내용을 보조하거나 문맥상 중요한 정보를 제공
                        2. 기능성 이미지: 클릭, 터치 등의 인터랙션을 유발하는 이미지
                        3. 장식적 이미지: 시각적 미관 목적, 정보 전달 역할 없음
                        4. 복합적 이미지: 표, 차트, 인포그래픽 등 구조적 설명이 필요한 경우

                        입력된 대체텍스트가 다음 가이드라인 준수/미준수 여부와 그 이유를 설명한다.

                        < 준수로 판단하는 조건:

                        1. 대체텍스트가 이미지가 의미하는 바를 명확하고 간결하게 설명하되 25% 이상의 정보를 제공.
                        2. 단, 그림에 대해 상세 묘사하는것은 준수 조건이 아니다 >

                        < 미준수로 판단하는 조건:

                        1. 이미지 내용의 핵심 정보 누락-대체텍스트가 이미지의 핵심 정보를 포함하지 않은 경우(단, 제목, 날짜, 장소, 주요 참석자 등 25% 미만은 미준수로 판단).
                        2. 간결성 및 명확성 부족: 대체텍스트가 지나치게 길거나, 불필요한 정보가 포함되어 있어 이해하기 어려운 경우.정보 연관성 부족: 상황(예: 게시판에 게시된, 학교 홈페이지 등)과 대체텍스트가 관련이 없는 경우
                        3. 미준수일 경우 이미지 유형에 맞게 적절한 대체텍스트를 새로 생성하여 제안한다.

                        [ 고려사항 ]대체텍스트의 정의: 시각장애인이 이미지에 담긴 정보를 인지할 수 있도록 제공되는 텍스트이지만, 사진 속 상황이나 세부적인 것을 자세히 설명하는 것이 아닌 기능적으로 전달만 되면됨 준수(조금높음). 상세하게 설명까지 한 경우는 준수(매우높음)의 평가에 해당됨.대체텍스트의 작성 원칙:

                        - 간결하면서도 명확해야 함
                        - 불필요한 접두어나 문장 종결어미는 생략 ("입니다" 등)
                        - 줄 구분은 "/"로 구분
                        - 이미지의 정보 유형에 맞게 작성
                        - 정보성 이미지에 대해서는 이미지가 전달하는 핵심 정보를 전달하도록 함
                        - 기능성 이미지에 대해서는 이미지의 기능과 작동 결과를 설명하도록 함
                        - 장식적 이미지에 대해서는 '대체텍스트 없음'으로 처리
                        - 복합적 이미지(표·차트 등)에 대해서는 표의 제목, 열과 행을 설명
                        - 기능성 이미지 중 버튼, 드롭다운과 같이 기능이 중요한 이모지가 아닌 장식 이모지라고 판단되는 경우 alt 값을 공란으로 처리

                        [출력 형식]

                        반드시 다음 json 형식으로만 응답하세요:
                        {
                            "type": "이미지 유형 (정보성/기능성/장식적/복합적 중 하나)",
                            "grade": "준수 등급 (매우높음/조금높음/조금낮음/매우낮음 중 하나)",
                            "reason": "판단 근거를 간결히 설명하며 포함된 정보량을 %로 표시",
                            "improvement": "미준수 시 개선된 대체텍스트 제안 / 준수 시 기존 대체텍스트 또는 개선 사항"
                        }

                        --- [당신의 평가 대상은 이미지가 아닌 텍스트 입니다]대체텍스트 = {alt_text}'''
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"alt='{alt_text}'"},
                            {"type": "image_url", "image_url": {"url": image_data, "detail": "low"}}
                        ],
                    },
                ],
                temperature=0.2,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # 기존 형식과 호환성을 위한 compliant 값 추가
            compliant_map = {
                "매우높음": 0,
                "조금높음": 1,
                "조금낮음": 2,
                "매우낮음": 3,
            }

            result["compliant"] = compliant_map.get(result.get("grade"), 2)

            return result

        except Exception as e:
            return {"error": str(e)}

evaluator = AltTextEvaluator()

@app.route('/evaluate', methods=['POST'])
def evaluate_alt_text():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON 데이터가 필요합니다"}), 400

        alt_text = data.get('alt_text')
        image_data = data.get('image_data')

        if not alt_text:
            return jsonify({"error": "alt_text가 필요합니다"}), 400

        if not image_data:
            return jsonify({"error": "image_data가 필요합니다"}), 400

        # 이미지 데이터가 base64 형식인지 확인하고 data URL 형식으로 변환
        if not image_data.startswith('data:'):
            image_data = f"data:image/jpeg;base64,{image_data}"

        result = evaluator.evaluate_alt_text(alt_text, image_data)

        if "error" in result:
            return jsonify(result), 500

        # 평가 결과를 데이터베이스에 저장 (이미지 데이터 포함)
        evaluation_id = db_manager.save_evaluation(alt_text, result, image_data)
        result["evaluation_id"] = evaluation_id

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        history = db_manager.get_history(limit=limit, offset=offset)
        return jsonify({"history": history, "count": len(history)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history/<int:evaluation_id>', methods=['GET'])
def get_evaluation_detail(evaluation_id):
    try:
        evaluation = db_manager.get_evaluation_by_id(evaluation_id)

        if not evaluation:
            return jsonify({"error": "평가를 찾을 수 없습니다"}), 404

        return jsonify(evaluation)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/statistics', methods=['GET'])
def get_statistics():
    try:
        stats = db_manager.get_statistics()
        return jsonify(stats)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)