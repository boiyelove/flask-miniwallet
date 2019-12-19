import os

base_dir = os.path.dirname(os.path.dirname(__file__))

class Config(object):
	"""
	
	Common configurations
	
	"""
	SECRET_KEY = 'p9Bv<3Eid9%$i01'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'app.db')



class DevelopmentConfig(Config):
	"""
	
	Development configurations
	
	"""

	DEBUG = True
	SQLALCHEMY_ECHO =  True

class ProductionConfig(Config):
	"""
	
	Production configurations
	
	"""
	DEBUG = False


app_config = {
	'development': DevelopmentConfig,
	'production': ProductionConfig
}
