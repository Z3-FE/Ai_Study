
# 打包入参
# def show_info(*args, **kwargs):
#     print(args, kwargs)
#     print(args[0], kwargs['name'])
#
#
# show_info(1, 2, 3, name='迪丽热巴', age=20, sex='女')


#解包传参
init_data = [1,2,3,4]
info_data = {'name':'迪丽热巴', 'ages': 20}

def show_info2(*args, **kwargs):
    print(args, kwargs)
    print(args[0], kwargs['name'])

show_info2(*init_data, **info_data)

