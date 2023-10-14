class Conf:
    a: int = 1
    b: list[bool] = [True]


t = type(getattr(Conf, "b"))
for x in getattr(Conf, "b"):
    print(type(x))
