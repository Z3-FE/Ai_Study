name = 'zhangsan'
age = 20
weight = 20.65
"""
占位符
%s 万能的
%f 浮点型
%i 整数型
%d 十进制类型
控制占位符与精度
%m.ns 控制占位符
%m.nf 控制浮点类型的精度  n的截断会进行四舍五入
"""
# 把 %(name , age)  替换为 %s
print('我是%s,今年%s' % (name, age))

print('我叫%3.5s 你是真好' % name)
print('体重: %2.1f' % weight) # 体重:20.6
