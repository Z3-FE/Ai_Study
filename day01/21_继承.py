class Person:

    def __init__(self, name, job, age):
        self.name = name
        self.job = job
        self.age = age

    # 实例方法
    def speak(self, message):
        print(f'我叫：{self.name},工作：{self.job},年龄：{self.age}，我想说：{message}')

# student 子类/派生类   Person 父类 /超类 / 基类
class Student(Person):
    def __init__(self, name, job, age, stu_id, grade):
        # 方法一
        # Person.__init__(self, name, job, age)
        # self.stu_id = stu_id
        # self.grade = grade
        # 方法二
        super().__init__(name, job, age)
        self.stu_id = stu_id
        self.grade = grade




stu1 = Student('张三','学生','18','25001','高三二班')
p1 = Person('李四','人', '20')
print(stu1.name, stu1.job, stu1.age, stu1.stu_id, stu1.grade)

# speak查找方法： 1.查找自身 =》 2.查找Student类 =》 3.查找Person类
stu1.speak('德玛西亚')

# 判断某个对象，是否是指定的子类或类的实例
print(isinstance(stu1, Student))
print(isinstance(stu1, Person))
print(isinstance(p1, Person))
print(isinstance(p1, Student))

# 判断某个类，是否是指定的类的子类
print(issubclass(Student, Person))
print(issubclass(Person, Student))