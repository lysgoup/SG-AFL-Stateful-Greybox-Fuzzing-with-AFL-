import tkinter as tk
from tkinter import ttk

# 텍스트 파일 읽기
with open("modified_transition_result.txt", "r") as file:
    lines = file.readlines()

nodes = []
edges = []

# 노드 정보 파싱
for line in lines:
    if line.strip():
        if line.startswith("#"):
            mode = "edges" if line.strip() == "# transition" else "nodes"
        elif mode == "nodes":
            nodes.append(line.strip())
        elif mode == "edges":
            edge = line.strip().split()
            edges.append((edge[0], edge[1]))

# 창 생성
root = tk.Tk()
root.title("Tree Graph")

# 스크롤바 생성
scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 캔버스 생성
canvas = tk.Canvas(root, width=1500, height=800, bg="#92C5C8")
canvas.pack()

# 스크롤바와 캔버스 연결
scrollbar.config(command=canvas.yview)

# 드래그 상태 변수
drag_state = False
prev_x, prev_y = 0, 0

# 마우스 이벤트 핸들러
def start_drag(event):
    global drag_state, prev_x, prev_y
    drag_state = True
    prev_x, prev_y = event.x, event.y

def end_drag(event):
    global drag_state
    drag_state = False

def drag(event):
    global prev_x, prev_y
    if drag_state:
        dx, dy = event.x - prev_x, event.y - prev_y
        canvas.move("all", dx, dy)
        prev_x, prev_y = event.x, event.y
        

def on_mouse_wheel(event):
    scale = 1.1 if event.delta > 0 else 0.9
    canvas.scale("all", event.x, event.y, scale, scale)

# 마우스 이벤트 바인딩
canvas.bind("<ButtonPress-1>", start_drag)
canvas.bind("<ButtonRelease-1>", end_drag)
canvas.bind("<B1-Motion>", drag)

# 노드 그리기 함수
def draw_node(node, x, y, radius=20):
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#E6F4F1", outline="#005C71", tags="node")
    canvas.create_text(x, y, text=node, font=("Arial", 12), tags="node")

# 엣지 그리기 함수
def draw_edge(node1, node2, x1, y1, x2, y2):
    canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, tags="edge", smooth = True)
    
def draw_curve(x1, y1, x2, y2, curve_factor=0.2, color='black'):
    # 중간점 계산
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2

    # 곡선을 위한 제어점 계산
    control_x = mid_x + (y2 - y1) * curve_factor
    control_y = mid_y - (x2 - x1) * curve_factor

    # 곡선 그리기
    canvas.create_line(x1, y1, control_x, control_y, x2, y2, smooth=True, fill=color)
    
# 트리 그리기
added = {node: 0 for node in nodes}
levels = {node: 0 for node in nodes}
added_node = [[]]
max_level = 0
for edge in edges:
    parent, child = edge
    if added[parent] == 0:
        added_node[max_level].append(parent)
        levels[parent] = max_level
        added[parent] = 1
    
    if added[child] == 0:
        levels[child] = levels[parent] + 1
        max_level = max(max_level, levels[child])
        if max_level+1 > len(added_node):
            added_node.extend([[]])
        added_node[levels[child]].append(child)
        added[child] = 1

# x_spacing = 600 / (max_level + 1)
# y_spacing = 500 / (len(nodes) + 1)

x_spacing = 150
y_spacing = 200

for level in range(len(added_node)):
    for i, node in enumerate(added_node[level]):
        y = (level+1) * y_spacing
        x = (i+1+level) * x_spacing
        draw_node(node, x, y)

# for i, node in enumerate(nodes):
#     level = levels[node]
#     x = (level + 1) * x_spacing
#     y = (i + 1) * y_spacing
#     draw_node(node, x, y)

for edge in edges:
    parent, child = edge
    parent_y = (levels[parent] + 1) * y_spacing
    parent_x = (added_node[levels[parent]].index(parent) + 1 + levels[parent]) * x_spacing
    child_y = (levels[child] + 1) * y_spacing
    child_x = (added_node[levels[child]].index(child) + 1 + levels[child]) * x_spacing
#     draw_edge(parent, child, parent_x, parent_y, child_x, child_y)
    if levels[parent] >= levels[child]:
        draw_curve(parent_x, parent_y, child_x, child_y, color='#1D0B8A')
    else:
        draw_curve(parent_x, parent_y, child_x, child_y, color='#C30000')

# for edge in edges:
#     parent, child = edge
#     parent_x = (levels[parent] + 1) * x_spacing
#     parent_y = nodes.index(parent) * y_spacing + y_spacing
#     child_x = (levels[child] + 1) * x_spacing
#     child_y = nodes.index(child) * y_spacing + y_spacing
#     draw_edge(parent, child, parent_x, parent_y, child_x, child_y)

# 버튼 프레임 생성
button_frame = ttk.Frame(root)
button_frame.pack(side=tk.BOTTOM, pady=10)

# 버튼 생성
add_node_button = ttk.Button(button_frame, text="ADD NODE")
add_node_button.pack(side=tk.LEFT, padx=5)

delete_node_button = ttk.Button(button_frame, text="DELETE NODE")
delete_node_button.pack(side=tk.LEFT, padx=5)

add_branch_button = ttk.Button(button_frame, text="ADD BRANCH")
add_branch_button.pack(side=tk.LEFT, padx=5)

delete_branch_button = ttk.Button(button_frame, text="DELETE BRANCH")
delete_branch_button.pack(side=tk.LEFT, padx=5)

# 입력 라벨
input_label = ttk.Entry(button_frame)
input_label.pack(side=tk.RIGHT, padx=5)

# 마우스 휠 이벤트에 대한 바인딩
canvas.bind_all("<MouseWheel>", on_mouse_wheel)

root.mainloop()