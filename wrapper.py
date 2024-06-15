import re
#pre_work, 세미콜론, post_process_message
state_mapping = {
    'state': 0,
    'write_state': 1,
    'write_state_work': 2,
    'read_state': 3,
    'read_state_work': 4,
    'hand_state': 5,
    'request_state': 6
    # 'read_state_first_init': 7,
    # 'no_cert_verify': 8,
    # 'in_init': 9,
    # 'hello_retry_request': 10,
    # 'early_data_state': 11,
    # 'server': 12,
    # 'init_buf': 13,
    # 'init_num': 14,
    # 'change_cipher_spec': 15,
    # 'init_msg': 16,
    # 'first_packet': 17,
    # 'rwstate': 18,
    # 'total_renegotiations': 19,
    # 'early_data': 20
}

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None

def instrument(variables,file_path, output_file):
    file_content = read_file(file_path)
    
    new_state = []
    applied = []
    #print(file_content)
    # # for variable in variables:
    # pattern = fr"(((st?)->(\w+)\.?(\w+)?)\s*=\s*(\w+)(\(.*\b\))?)( ?.)"

    for variable in variables:
        pattern = fr"((({variable})->(\w+)\.?(\w+)?)\s*=\s*(\w+)(\(.*\b\))?)( ?.)"

        group_count = len(re.compile(pattern).groupindex)
        matches = re.finditer(pattern, file_content, re.MULTILINE)

        for match in matches:
            # if match.group(7) == None: #maybe '==' case
            #     continue

            for i in range(0,9):
                print(f"{i}:{match.group(i)}")

            try:
                if match.group(5):  # st->a.b   case
                    flag = state_mapping[match.group(5)]
                else:               # st->a     case
                    flag = state_mapping[match.group(4)]
            except KeyError as e:
                error_message = f"{e}"
                new_state.append(error_message)
                continue

            if match.group(1) in applied: #already replaced
                continue
            applied.append(match.group(1))

            if (str(match.group(8)).strip() == ";"):
                replace = f"{match.group(0)}\nwrapper((int*)&{match.group(2)}, {flag});"
                replace = "{\n" + replace + "\n}"
            else :
                replace = f"(({match.group(0)})\n& wrapper((int*)&{match.group(2)}, {flag}))"

            # file_content = re.sub(match.group(0), replace, file_content)
            file_content = file_content.replace(match.group(0), replace)
            # print(f"replaced:\n{replace}")

        # for new in new_state:
        #     print(new)
    
    return file_content


#==============main==============
#input setting
variable = ["st", "s"]
file_path = "./openssl/ssl/statem/statem_clnt.c" #directory path
output_file = "statem_mod_clnt.c"

mod_content = instrument(variable, file_path, output_file)

# print(mod_content)

with open(output_file, 'w') as file:
    file.write(mod_content)
