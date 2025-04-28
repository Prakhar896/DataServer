from client import CloudFragment

frag = CloudFragment(fragmentID="bc42f6b0f53b47c39b3c6d7217ef9fe2", secret="a123456", url="http://localhost:8250")
print(frag.initStream())

while True:
    try:
        exec(input(">>> "))
    except Exception as e:
        print(e)