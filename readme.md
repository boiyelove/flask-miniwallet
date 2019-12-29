# Miniwallet with flask and paystack implementation 



## Setup

```

pip install -r req.txt
```

Setup Paystack Keys
[Get it here:](https://dashboard.paystack.com/#/settings/developer)
- Change Paystack Secret Key
- Change Paystack Public Key

[configuration file](./config.py)

Flask setup

```

FLASK_APP = run.py
FLASK_CONFIG = development
```

Database setup

```

flask db init
flask db migrate
flask db upgrade
```

Finally run the app

```

flask run
```
