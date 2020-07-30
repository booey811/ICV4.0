ls1 = [None, "thing", None, "other thing"]
ls2 = []

for item in ls1:
    if item:
        ls2.append(item)

print(ls2)