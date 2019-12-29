import os

base_dir = os.path.dirname(os.path.dirname(__file__))

class Config(object):
	"""
	
	Common configurations
	
	"""
	SECRET_KEY = 'p9Bv<3Eid9%$i01'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False


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
	'production': ProductionConfig,

}

PAYSTACK_PUBLIC_KEY = 'pk_test_af15f1a5a947bf98e44d2ebaf0c83e9aae03a97c'
PAYSTACK_SECRET_KEY = "sk_test_c5ef3fb760da4fc6c145d888b26b945fa93b993a"