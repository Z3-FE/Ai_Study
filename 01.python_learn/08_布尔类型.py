a = True
b = False
print('1',a and b)
print('2',a & b)
print('3', a or b)
print('4',a | b)
print('5', a ^ b)
print('6',not a)
print('7',not b)
print(int(a)) # true 1
print(int(b)) # false 0

x = 'Positive' if 1 > 0 else 'Non-positive'
print(x)

numbers = [1, 2, 3, 4]
squares = [x for x in numbers if x % 2 == 0]
print(squares)