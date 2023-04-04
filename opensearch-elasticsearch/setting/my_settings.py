DEBUG_FLAG          = False
TIMEZONE            = 'Asia/Bangkok'

# ---------------------------------------
#        Service Mode
# ---------------------------------------
SERVICE_MODE        = False     # Set to False to run in the production mode.
# ---------------------------------------
CONFIG_CHECK        = True
INIT_ISM            = False
INIT_DATA_STREAM    = False


# ---------------------------------------
#        Production Mode
# ---------------------------------------
RUN_AS_SERVICE      = True     # Set to False to run at once (batch mode).
ENABLE_SCHEDULE_RUN = True     # Set to False to skip scheduling tasks.
# ---------------------------------------


# ---- Setting for one time (batch) download (active only if SERVICE_MODE = False, RUN_AS_SERVICE=False, ENABLE_SCHEDULE_RUN = x) ----
START_DATETIME        = '2022-12-01T00:00:00+07:00'
STOP_DATETIME         = '2023-03-31T23:59:59+07:00'


# ---- Setting for scheduling download (active only if SERVICE_MODE = False, RUN_AS_SERVICE=True, ENABLE_SCHEDULE_RUN = True) ----
# Executing a log download job. Default is “At every 30th minute past every hour from 0 through 23.”
# Ref1. https://crontab.guru/#*/30_0-23_*_*_*
# Ref2. https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html
CRON_TRIGGER_HOUR   = '0-23'
CRON_TRIGGER_MINUTE = '*/30'

# Specify lookback periods
LAST_X_DAYS   = 0
LAST_X_HOURS  = 1
LAST_X_MINS   = 0
