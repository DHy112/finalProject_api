from connection import db_connection


def insert_rec_image(imageId, imageURL, prediction):
    conn = db_connection()
    cursor = conn.cursor()

    try:
        insert_image_qry = (f'INSERT INTO rec_image(imageId, imageURL) VALUES (\'{imageId}\', \'{imageURL}\')')
        cursor.execute(insert_image_qry)

        # list column 문자열 저장
        col_list = ",".join(prediction)
        insert_image_attr_qry = (f'UPDATE rec_image SET list = \'{col_list}\' WHERE imageId = \'{imageId}\'')
        cursor.execute(insert_image_attr_qry)
        conn.commit()

        for i in prediction:
            insert_attr_qry = (f'UPDATE rec_image SET {i} = {i} + 1 WHERE imageId = \'{imageId}\'')
            cursor.execute(insert_attr_qry)
            conn.commit()

    finally:
        conn.close()
