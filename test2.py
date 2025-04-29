# from client import CloudFragment
# from apscheduler.schedulers.background import BackgroundScheduler
# import random, time, sys

# scheduler = BackgroundScheduler()
# scheduler.start()
# def a(data=None):
#     print("NEW:", data)

# frag1 = CloudFragment(fragmentID="d90507e925844e5ab1cba1537102a060", secret="a123456", url="http://localhost:8250")
# print(frag1.initStream())

# def w():
#     frag1.writeWS({"number": random.randint(0, 100)})
#     print("wrote")

# j1 = scheduler.add_job(frag1.liveStream, args=[a])
# j2 = scheduler.add_job(w, 'interval', seconds=3)

# time.sleep(30)
# scheduler.shutdown()
# sys.exit(0)

from client import CloudFragment

frag1 = CloudFragment(fragmentID="095f8d79897e4acb85eb5fcb06d07375", secret="lmao123", url="http://localhost:8250", wsURL="ws://localhost:8250")
print(frag1.initStream())

while True:
    try:
        exec(input(">>> "))
    except Exception as e:
        print(e)