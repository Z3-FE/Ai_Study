
#全局作用域
num = 100
for n in range(0,3):
    num += n
    print(n)
    print(f'内部num:{num}')

print(f'外部num:{num}')

def func1():
    global num # 使用global 可以调用全局变量
    num += 1
    print(f'num加1：{num}')

func1()