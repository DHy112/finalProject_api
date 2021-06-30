import pymysql
from connection import db_connection


def save_preference(user_id, img_id):
    conn = db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 이미지 아이디로 list 컬럼 조회
        get_list_qry = (f'SELECT list FROM rec_image WHERE imageId = \'{img_id}\'')

        cursor.execute(get_list_qry)
        attr_temp = cursor.fetchall()
        attr_temp = attr_temp[0].get('list')
        attr = attr_temp.split(',')

        for i in attr:
            update_attr_qry = (f'UPDATE mem_preference SET {i} = {i} + 1 WHERE id = \'{user_id}\'')
            cursor.execute(update_attr_qry)
            conn.commit()

        return attr
    finally:
        conn.close()
