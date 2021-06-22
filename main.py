from flask import Flask, jsonify, request
from flask_restx import Api, Resource  # Api 구현을 위한 Api 객체 import
import re
import pandas as pd
import pymysql
import os
import datetime
from sklearn.metrics.pairwise import cosine_similarity
from connection import s3_connection
from config import BUCKET_NAME

app = Flask(__name__)
api = Api(app)


# 날씨에 따른 코디 추천
@app.route('/recommend', methods=['POST'])
def get_rec():
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


@app.route('/image', methods=['POST'])
def imgUpload():

    if request.method == 'POST':
        s3 = s3_connection()
        now = datetime.datetime.now().strftime('%y%m%d_%H%M%S')

        f = request.files['file']
        if f:
            extension = os.path.splitext(f.filename)[1]
            filename = now + extension
            f.save(filename)
            s3.upload_file(
                Bucket=BUCKET_NAME,
                Filename=filename,
                Key=filename
            )
            msg = "Upload Done!"

        return {"message": msg}

if __name__ == "__main__":
    app.run(host='0.0.0.0')
