import json
import os
import sys
import re

state_mapping = {
    'state': 0,
    # 'write_state': 1,
    # 'write_state_work': 2,
    # 'read_state': 3,
    # 'read_state_work': 4,
    'hand_state': 5,
    # 'request_state': 6
}

def insert_probe(state_id,vcount):
  # largest_id = max([num for num in state_id])
  print(state_id)
  print(vcount)
  prefix = ""
  for i in state_id:
    prefix += f"static int prev{i} = 0;\n";
  prefix += "static inline int __probe(int value, int id){\n\tswitch(id){\n"
  for case_iter in range(len(state_id)): #case 만들기, 변수 개수만큼 실행
    prefix += f"\t\tcase {state_id[case_iter]}:\n"
    cur_value = []
    for i in range(len(state_id)):
      cur_value.append(0)
    print(vcount[case_iter])
    while True:
      print(vcount[case_iter])
      for value_iter in range(vcount[case_iter]):
        template = "\t\t\tif("
        for i in range(len(state_id)):
          template += f"prev{state_id[i]} == {cur_value[i]} && "
        #TODO: case랑 value같으면 넘어가기.
        if(cur_value[case_iter] == value_iter):
          continue
        template += f"value == {value_iter}"
        template += ")\n"
        template += "\t\t\t{\n"
        template += f"\t\t\t\tprev{state_id[case_iter]} = value;\n"
        template += "\t\t\t\treturn value;\n"
        template += "\t\t\t}\n"
        prefix += template
      done=0
      for cur_iter in range(len(cur_value)):
        cur_value[cur_iter] += 1
        if cur_value[cur_iter] < vcount[cur_iter]:
          break
        if cur_iter == len(cur_value)-1:
          done = 1
        cur_value[cur_iter] = 0
      if(done == 1):
        break
  prefix += "\t}\n\treturn value;\n}\n" 
  print(prefix)
  return prefix
      

  # maxval = 0
  # for i in range(len(state_id)):
  #   maxval+=(max(state_value[i])*(10**(len(state_id)-i-1)))
  # for l in range(len(state_id)):
  #   prefix += f"\t\tcase {state_id[l]}:\n"
  #   for k in range(len(state_value[l])):
  #     for i in range(maxval+1):
  #       vector = []
  #       for j in range(len(state_id)):
  #         v = (i%(10**(j+1)))//(10**j)
  #         if v in state_value[len(state_value)-j-1]:
  #           vector.append(v)
  #       if len(vector)==len(state_id):
  #         flag = 0
  #         template = "\t\t\tif("
  #         for j in range(len(state_id)):
  #           num = vector.pop()
  #           template += f"prev{state_id[j]} == {num} && "
  #           if j == l and num == state_value[l][k]:
  #             flag=1
  #         template += f"value == {state_value[l][k]})\n"
  #         if flag==0:
  #           prefix += template
  #           prefix += "\t\t\t{\n"
  #           prefix += f"\t\t\t\tprev{state_id[l]} = value;\n"
  #           prefix += "\t\t\t\treturn value;\n"
  #           prefix += "\t\t\t}\n"
  
  postfix = "\t}\n\treturn value;\n}\n"

  # print(prefix+postfix)
  probe_func = prefix + postfix
  return probe_func

def instrument(file_path,state_variables,variables):
  mod_flag = 0
  new_state = []
  applied = []
  try:
    with open(file_path, "r") as file:
      file_content = file.read()
  except Exception as e:
    print(f"Failed to open file: {e}")
    sys.exit(1)

  lines = file_content.split("\n")
  for word in state_variables:
    search_str = word + ' = '
    for line in lines:
      if search_str in line:

        for variable in variables:
          pattern = fr"(((st?)->(\w+)\.?(\w+)?)\s*=\s*(\w+)(\(.*\b\))?)( ?.)"

          group_count = len(re.compile(pattern).groupindex)
          matches = re.finditer(pattern, file_content, re.MULTILINE)

          for match in matches:
              # for i in range(0,9):
                  # print(f"{i}:{match.group(i)}")

              try:
                  if match.group(5):  # st->a.b   case
                      flag = state_mapping[match.group(5)]
                  else:               # st->a     case
                      flag = state_mapping[match.group(4)]
              except KeyError as e:
                  error_message = f"{e}"
                  new_state.append(error_message)
                  continue

              mod_flag = 1
              if match.group(1) in applied: #already replaced
                  continue
              applied.append(match.group(1))

              if (str(match.group(8)).strip() == ";"):
                  replace = f"{match.group(0)}\n__probe((int){match.group(2)}, {flag});"
                  replace = "{\n" + replace + "\n}"
              else :
                  replace = f"(({match.group(0)})\n& __probe((int){match.group(2)}, {flag}))"

              # file_content = re.sub(match.group(0), replace, file_content)
              file_content = file_content.replace(match.group(0), replace)
              # print(replace)
        # print(line.strip())
  return file_content, mod_flag


if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    print(f"usage: python3 {sys.argv[0]} <folder_path>");
    sys.exit(1)

with open('openssl2.json', 'r') as f:
  openssl_data = json.load(f)
  
# openssl.json에서 id의 value 갯수 읽고 그 수만큼 prev_state 만들기
state_id = openssl_data['id']
state_variables = openssl_data['name']
count_ids = len(state_variables)
prev_state = [0] * count_ids

# state_value = []
vcount = openssl_data['vcount']
# for count in range(len(vcount)):
#   state_value.append([])
#   for i in range(vcount[count]): 
#     state_value[count].append(i)
# print(state_value)

variables = ["s", "st"]

probe_func = insert_probe(state_id,vcount)

if os.path.isfile(path):
  if path.endswith(".c"):
    try:
      with open(path, "r") as f:
        pass
    except Exception as e:
      print(f"Failed to open file: {e}")
    mod_content, flag=instrument(path,state_variables,variables)
    # TODO: output_file = file_path
    output_file = path
    # output_file = "/mnt/hdd/HK/HK1/new_file2.c"
    with open(output_file, 'w') as file:
      file.write(mod_content)
    if flag == 1:
      try:
        with open(output_file, "r+") as file:
          content = file.read()        
          file.seek(0)
          file.write(probe_func)
          file.write(content)
          print(f"probe_func가 {file.name} 파일 맨 앞에 추가되었습니다.")
      except Exception as e:
          print(f"에러 발생: {e}")
  sys.exit(0)


for root, dirs, files in os.walk(path):
  print(f"Enter in {dirs}\n")
  for file in files:
    print(f"Checking {file}\n")
    file_path = os.path.join(root, file)
    if file_path.endswith(".c"): 
      mod_content, flag=instrument(file_path,state_variables,variables)
      # TODO: output_file = file_path
      output_file = file_path
      # output_file = "/mnt/hdd/HK/HK1/new_file2.c"
      with open(output_file, 'w') as file:
        file.write(mod_content)
      if flag == 1:
        try:
          with open(output_file, "r+") as file:
            content = file.read()        
            file.seek(0)
            file.write(probe_func)
            file.write(content)
            print(f"probe_func가 {file_path} 파일 맨 앞에 추가되었습니다.")
        except Exception as e:
            print(f"에러 발생: {e}")