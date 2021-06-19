from flask import Flask  # 서버 구현을 위한 Flask 객체 import
from flask import jsonify
from flask import request
from flask_restx import Api, Resource  # Api 구현을 위한 Api 객체 import
import re
import pandas as pd
import pymysql
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)  # Flask 객체 선언
api = Api(app)  # Flask 객체에 Api 객체 등록


@app.route('/')
def home():
    return 'Hello, World!'


# 날씨에 따른 코디 추천
@app.route('/recommend', methods=['POST'])
def get_rec():
    # print(request.is_json)
    params = request.get_json()
    userId = params['user_id']
    temp = int(re.sub('[℃]', '', params['temp']))

    # 날씨 range 적용
    if temp < 5:
        range = 1
    elif temp < 11:
        range = 2
    elif temp < 18:
        range = 3
    elif temp < 25:
        range = 4
    else:
        range = 5

    conn = pymysql.connect(host='aoo.myds.me', port=3306,
                           user='bituser',
                           password='Maria21417791%',
                           database='ww')

    # img attr
    qryImg = 'select * from test_imgdata2 WHERE temp = "' + str(range) + '"'
    imgAttr = pd.read_sql_query(qryImg, conn, index_col='imgId')
    imgAttr = imgAttr.drop(['temp'], axis='columns')

    # user attr
    qryUser = 'select * from test_userdata WHERE id = "' + userId + '"'
    userAttr = pd.read_sql_query(qryUser, conn, index_col='id')
    userAttr = userAttr.drop(['list'], axis='columns')


    if len(userAttr) == 1:

        imgUserAttr = imgAttr.append(userAttr)

        target_index = imgUserAttr.shape[0] - 1
        cosine_matrix = cosine_similarity(imgUserAttr, imgUserAttr)
        sim_index = cosine_matrix[target_index, :30].reshape(-1)
        sim_index = sim_index[sim_index != target_index]

        sim_scores = [(i, c) for i, c in enumerate(cosine_matrix[target_index]) if i != target_index]

        # 유사도순으로 정렬
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        index2id = {}
        for i, c in enumerate(imgUserAttr.index): index2id[i] = c

        # 인덱스를 이미지 파일명으로 변환
        sim_scores = [(index2id[i], score) for i, score in sim_scores[0:10]]
        print(sim_scores)
        return jsonify(sim_scores)

    else:
        return {"error": "userID 확인 필요"}


# label predict
@app.route('/predict', methods=['POST'])
def make_prediction():
    if request.method == 'POST':

        file = request.files['image']
        if not file:
            return {"error": "이미지를 업로드 해주세요"}


if __name__ == "__main__":
    app.run(host='0.0.0.0')
