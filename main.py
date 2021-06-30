import datetime
import json
import os

import pandas as pd
import pymysql.cursors
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api
from sklearn.metrics.pairwise import cosine_similarity

import rec_image
from config_parser import BUCKET_NAME
from connection import s3_connection, db_connection
from prediction import ClassificationModel
from preference import save_preference

app = Flask(__name__)
CORS(app)
api = Api(app)


# 날씨에 따른 코디 추천
@app.route('/recommend', methods=['POST'])
def get_rec():
    conn = db_connection()
    params = request.get_json()
    userId = params['user_id']
    temp = int(params['temp'])

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

    try:

        # img attr
        qryImg = 'select * from rec_image WHERE temp = "' + str(range) + '"'
        imgAttr = pd.read_sql_query(qryImg, conn, index_col='imageId')
        imgAttr = imgAttr.drop(['num', 'imageURL', 'temp', 'list'], axis='columns')

        # user attr
        qryUser = 'select * from mem_preference WHERE id = "' + userId + '"'
        userAttr = pd.read_sql_query(qryUser, conn, index_col='id')

        # 유효한 userID인 경우
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
            sim_scores = [(index2id[i], score) for i, score in sim_scores[0:4]]

            # 이미지 파일명으로 url 조회하여 결과 전달
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            url_res =[]

            for i in sim_scores:
                get_url_qry = 'select imageURL from rec_image WHERE imageId = "' + i[0] + '"'
                cursor.execute(get_url_qry)
                url = cursor.fetchall()
                url_res.append(url[0]['imageURL'])

            return jsonify(url_res)

        else:
            return {"error": "userID 확인 필요"}

    finally:
        conn.close()


@app.route('/image', methods=['POST'])
def imgUpload():
    if request.method == 'POST':
        f = request.files['file']

        if f:
            # 이미지 attribute 예측
            MODEL_PATH = './models/attr_resnet34_0628.pkl'
            CLASSES_PATH = './models/classes.txt'

            model = ClassificationModel()
            model.load(MODEL_PATH, CLASSES_PATH)
            prediction = model.predict(f)

            # 이미지 attribute가 있는 경우에만 s3, db에 저장
            if prediction:

                now = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
                extension = os.path.splitext(f.filename)[1]
                filename = now + extension

                f.seek(0)
                f.save(filename)

                # S3 이미지 저장
                s3 = s3_connection()

                s3.upload_file(
                    Bucket=BUCKET_NAME,
                    Filename=filename,
                    Key=filename,
                    ExtraArgs={
                        "ContentType": 'image/jpeg'
                    }
                )

                imageURL = f'https://wwuptest.s3.ap-northeast-2.amazonaws.com/{filename}'

                # rec_image DB 저장
                rec_image.insert_rec_image(filename, imageURL, prediction)

                imgUploadResult = {
                    'URL': imageURL,
                    'PREDICTION': prediction
                }

                return json.dumps(imgUploadResult, indent=4, sort_keys=True)


            else:
                return {"error": "Attribute prediction failed"}


@app.route('/preference', methods=['POST'])
def update_preference():
    params = request.get_json()
    user_id = params['user_id']
    img_id = params['img_id']

    res = save_preference(user_id, img_id)
    return {"updated attr": res}


@app.route('/userpreference', methods=['POST'])
def set_preference():
    conn = db_connection()
    params = request.get_json()
    user_id = params['user_id']
    img_ids = params['img_id']

    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # user 행 생성
    set_preference_qry = f'INSERT INTO mem_preference(id) VALUES (\'{user_id}\')'
    cursor.execute(set_preference_qry)
    conn.commit()

    # TODO img_ids가 1개인 경우 오류 발생 => 수정필요
    for img_id in img_ids:

        get_list_qry = (f'SELECT list FROM rec_image WHERE imageId = \'{img_id}\'')

        cursor.execute(get_list_qry)
        attr_temp = cursor.fetchall()
        attr_temp = attr_temp[0].get('list')
        attr = attr_temp.split(',')

        for i in attr:
            update_attr_qry = (f'UPDATE mem_preference SET {i} = {i} + 1 WHERE id = \'{user_id}\'')
            cursor.execute(update_attr_qry)
            conn.commit()

    return {"message": "Success"}


if __name__ == "__main__":
    app.run(host='0.0.0.0')