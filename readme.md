# Miniwallet with flask and paystack implementation 



## Setup

```
pip install -r req.txt
```

Setup Paystack Keys in [config.py configuration file](./config.py)
[Get it here:](https://dashboard.paystack.com/#/settings/developer)
- Change Paystack Secret Key: PAYSTACK_SECRET_KEY
- Change Paystack Public Key: PAYSTACK_PUBLIC_KEY


Flask setup from windows commandline

```winbatch
FLASK_APP = run.py
FLASK_CONFIG = development
FLASK_ENV = development
```

Database setup

```winbatch
flask db init
flask db migrate
flask db upgrade
```

Finally run the app

```winbatch
flask run
```
