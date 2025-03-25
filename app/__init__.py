# from flask import Flask
# from app.db import init_db
#
#
# def create_app():
#     app = Flask(__name__,
#                 static_folder='../static',
#                 template_folder='../templates')
#
#     app.config.from_object('app.config')
#
#     with app.app_context():
#         init_db()
#
#         from app.routes import main
#         app.register_blueprint(main)
#
#     return app
from flask import Flask
from app.db import init_db, get_db


def create_app():
    app = Flask(__name__,
                static_folder='../static',
                template_folder='../templates')

    app.config.from_object('app.config')

    with app.app_context():
        # 检查数据库是否存在，如果不存在才初始化
        try:
            db = get_db()
            # 尝试查询数据库，如果表不存在会抛出异常
            db.execute('SELECT 1 FROM conversations LIMIT 1')
        except:
            # 只有当表不存在时才初始化数据库
            init_db()
            print("Database initialized.")

        from app.routes import main
        app.register_blueprint(main)

    return app
