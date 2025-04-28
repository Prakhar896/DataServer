from client import CloudFragment

frag1 = CloudFragment(fragmentID="d90507e925844e5ab1cba1537102a060", secret="a123456", url="http://localhost:8250")
print(frag1.initStream())

while True:
    try:
        exec(input(">>> "))
    except Exception as e:
        print(e)