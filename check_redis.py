import redis

# Connect to Redis
REDIS_HOST = 'redis-15217.c275.us-east-1-4.ec2.redns.redis-cloud.com'
REDIS_PORT = 15217
REDIS_PASSWORD = 'CCJQsW7tni8VPIOzv0ddEzvgae4feGTg'

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

# WARNING: This will delete ALL data from Redis
r.flushall()
print("All data deleted from Redis.")
