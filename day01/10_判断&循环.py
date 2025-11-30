
# 单分支
"""

age = 18
print('请输入你的年龄：')
inptAge =  input()
intAge = int(inptAge)

if intAge >=    age:
    print('你是成年人')
    print(f'再过10年你就{10 + intAge}岁了')
elif 5 <= intAge < 18:  # 假设青年人是 5 岁到 18 岁之间（不含18）
    print('你是青年人')
elif intAge < 5 and intAge >= 0: # 假设幼儿是 0 岁到 5 岁之间（不含5）
    print('你是幼儿')
else:
    print('你是胚胎')

print('这里跳出if循环')

"""
# 嵌套
""""
age = int(input('请输入您的年龄：'))
report = input('是否提交体检报告')
level = int(input('请输入您的会员等级'))

if 18<=age<=45:
    print('✅️您符合参赛年龄！')
    if report == '是':
        print('体检报告验证通过')
        if  level > 3:
            print('3等级以上会员可以领取18k黄金100g')
        else:
            print('3等级以下会员没有奖励')
    else:
        print('没有报告不能参加比赛')
else:
    print(f'{age}岁不符合参赛年龄')

"""

# while 循环
"""
n = 1
while n <= 10:
    print(n)
    n += 1
"""
"""
ask = '你是什么人?'
res = '你的心上人！❤️'
guess = ''
while res != guess:
    print(f'问题：{ask}')
    guess = input('请输入你的答案：')
    if res == guess:
        print('回答正确')
"""

# for 循环
# range(0, 10) 0<= i < 10 的数组
i = 0

for i in range(10):
    i += 1 # 这里不会影响循环次数
    print(i)

print(i) # 外部的 i 是变化的

arr = [x * 2 for x in range(2, 11, 2*2)]
print(arr)