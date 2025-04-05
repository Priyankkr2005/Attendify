import redis

# Connect to Redis Client
r=redis.StrictRedis(host='redis-15217.c275.us-east-1-4.ec2.redns.redis-cloud.com',
                    port=15217,
                    password='CCJQsW7tni8VPIOzv0ddEzvgae4feGTg')

# Simulated Logs
with open('simulated_logs.txt', 'r') as f:
    logs_text = f.read()

encoded_logs = logs_text.split('\n')

# Push into Redis database
r.lpush('attendance:logs', *encoded_logs)
