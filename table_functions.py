from datetime import date, datetime

def dict_to_list_of_lists(obj_list,key_list, none_convert=0):
    hdrs = []
    attr_list = []

    #get the table headers from the keys
    for key, val in obj_list[0].__dict__.items():
        if key in key_list:
            hdrs.append(key)

    #convert each object attribute to a list
    for obj in obj_list:
        the_attr_list = []
        for key, val in obj.__dict__.items():
            if key in key_list:
                if val == None:
                    val = none_convert
                if type(val) is datetime.date:
                    val = val.strftime('%Y-%m-%d')
                the_attr_list.append(val)

        attr_list.append(the_attr_list)

    return hdrs, attr_list