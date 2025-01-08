from flask import Flask, render_template
from app.app_job_work.routes import app_job_work
from app.app_lab_inv.routes import app_lab_inv
from app.extensions import mysql

def create_app():
    app = Flask(__name__)

    # MySQL Configuration
    app.config['MYSQL_HOST'] = 'localhost'       
    app.config['MYSQL_USER'] = 'root'   
    app.config['MYSQL_PASSWORD'] = 'N@rendr@9702355153'
    app.config['MYSQL_DB'] = 'invoice_db'   
    
    mysql.init_app(app)  # Initialize MySQL with the app

    # Register blueprints for app_job_work and app_lab_inv
    app.register_blueprint(app_job_work, url_prefix='/app_job_work')
    app.register_blueprint(app_lab_inv, url_prefix='/app_lab_inv')

    # Common landing page route
    @app.route('/')
    def home_page():
        return render_template('index.html')

    return app
