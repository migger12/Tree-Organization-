import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import json
import os
import subprocess

class TreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizational Tree App")

        # Configuração da área de desenho (Canvas) para a árvore
        self.canvas = tk.Canvas(self.root, bg="white", scrollregion=(0, 0, 2000, 2000))
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Adicionando barras de rolagem para o Canvas
        self.scroll_x = tk.Scrollbar(self.root, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.config(xscrollcommand=self.scroll_x.set)

        self.scroll_y = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.scroll_y.set)

        # Criação do nó raiz
        self.root_node = TreeNode("Root", x=300, y=100)
        self.nodes = [self.root_node]
        self.selected_node = None
        self.dragging_node = None

        # Mapear IDs dos nós e linhas
        self.node_ids = {}
        self.line_ids = []

        self.create_buttons()
        self.draw_tree()

        # Configuração de eventos para clique e arraste
        self.canvas.bind("<Button-1>", self.on_single_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drop)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

    def create_buttons(self):
        # Criando botões para movimentação e controle dos nós
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Botões de movimentação
        move_frame = tk.Frame(control_frame)
        move_frame.grid(row=0, column=0, padx=5)

        tk.Button(move_frame, text="⬆", command=lambda: self.move_selected_node(0, -20)).grid(row=0, column=1)
        tk.Button(move_frame, text="⬅", command=lambda: self.move_selected_node(-20, 0)).grid(row=1, column=0)
        tk.Button(move_frame, text="⬇", command=lambda: self.move_selected_node(0, 20)).grid(row=1, column=1)
        tk.Button(move_frame, text="➡", command=lambda: self.move_selected_node(20, 0)).grid(row=1, column=2)

        # Botões de adicionar nó
        btn_add_node = tk.Button(control_frame, text="Add Node", command=self.add_node)
        btn_add_node.grid(row=0, column=1)

        btn_add_twin_branch = tk.Button(control_frame, text="Add Twin Branch", command=self.add_twin_branch)
        btn_add_twin_branch.grid(row=0, column=2)

        btn_edit_node = tk.Button(control_frame, text="Edit Node", command=self.open_node_editor)
        btn_edit_node.grid(row=0, column=3)

        btn_delete_node = tk.Button(control_frame, text="Delete Node", command=self.delete_node)
        btn_delete_node.grid(row=0, column=4)

        # Botões de salvar e carregar
        btn_save_tree = tk.Button(control_frame, text="Save Tree", command=self.save_tree)
        btn_save_tree.grid(row=0, column=5)

        btn_load_tree = tk.Button(control_frame, text="Load Tree", command=self.load_tree)
        btn_load_tree.grid(row=0, column=6)

        # Campo e botão de pesquisa
        search_frame = tk.Frame(control_frame)
        search_frame.grid(row=1, column=0, columnspan=7, pady=5)

        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=0, padx=5)

        search_button = tk.Button(search_frame, text="Search", command=self.search_keyword)
        search_button.grid(row=0, column=1, padx=5)

    def move_selected_node(self, dx, dy):
        if self.selected_node:
            self.selected_node.x += dx
            self.selected_node.y += dy
            self.draw_tree()

    def add_node(self):
        if self.selected_node or not self.nodes:
            title = simpledialog.askstring("Add Node", "Enter title for the new node:")
            if title:
                new_node = TreeNode(title, x=self.selected_node.x + 100 if self.selected_node else 300,
                                    y=self.selected_node.y + 100 if self.selected_node else 100)
                if self.selected_node:
                    self.selected_node.add_child(new_node)
                else:
                    self.nodes.append(new_node)
                self.nodes.append(new_node)
                self.draw_tree()

    def add_twin_branch(self):
        if self.selected_node or not self.nodes:
            title = simpledialog.askstring("Add Twin Branch", "Enter title for the twin branch:")
            if title:
                twin_node = TreeNode(title, x=self.selected_node.x + 100 if self.selected_node else 300,
                                     y=self.selected_node.y if self.selected_node else 100)
                if self.selected_node:
                    self.selected_node.add_child(twin_node)
                else:
                    self.nodes.append(twin_node)
                self.nodes.append(twin_node)
                self.draw_tree()

    def draw_tree(self):
        self.canvas.delete("all")
        self.node_ids.clear()
        self.line_ids.clear()

        for node in self.nodes:
            self.draw_node(node)
            for child in node.children:
                self.draw_node(child)
                self.draw_line(node, child)

        self.canvas.update_idletasks()

    def draw_node(self, node):
        x, y = node.x, node.y
        node_id = self.canvas.create_oval(x-20, y-20, x+20, y+20, fill=self.get_color_based_on_priority(node.priority), tags="node")
        self.canvas.create_text(x, y-10, text=node.title, tags="node")
        self.canvas.create_text(x, y+10, text=f"P: {node.progress}%", tags="node")
        
        # Atualizando a exibição da quantidade de comentários
        comment_count_text = f"C: {len(node.comments)}"
        comment_color = "red" if node.comments else "black"
        self.canvas.create_text(x, y+25, text=comment_count_text, fill=comment_color, tags="node")

        self.node_ids[node] = node_id

    def draw_line(self, parent, child):
        x1, y1 = parent.x, parent.y
        x2, y2 = child.x, child.y
        line_id = self.canvas.create_line(x1, y1, x2, y2, tags="line")
        self.line_ids.append(line_id)

    def get_color_based_on_priority(self, priority):
        if priority == "{}":
            return "#ff0000"  # Urgente - Vermelho
        elif priority == "[]":
            return "#ffff00"  # Médio - Amarelo
        else:
            return "#add8e6"  # Baixo - Azul claro

    def on_single_click(self, event):
        clicked_node = self.find_node_at(event.x, event.y)
        if clicked_node:
            self.selected_node = clicked_node
            self.dragging_node = clicked_node

    def on_double_click(self, event):
        clicked_node = self.find_node_at(event.x, event.y)
        if clicked_node:
            self.selected_node = clicked_node
            self.open_node_editor()

    def on_drag(self, event):
        if self.dragging_node:
            self.dragging_node.x = event.x
            self.dragging_node.y = event.y
            self.draw_tree()

    def on_drop(self, event):
        self.dragging_node = None

    def find_node_at(self, x, y):
        for node in self.nodes:
            if abs(node.x - x) < 20 and abs(node.y - y) < 20:
                return node
        return None

    def open_node_editor(self):
        if self.selected_node:
            editor = tk.Toplevel(self.root)
            editor.title("Edit Node")
            editor.geometry("600x800")

            tk.Label(editor, text="Node Title:").pack()
            title_entry = tk.Entry(editor)
            title_entry.insert(0, self.selected_node.title)
            title_entry.pack()

            tk.Label(editor, text="Node Text:").pack()
            text_field = tk.Text(editor, height=10, width=40)
            text_field.insert(tk.END, self.selected_node.text)
            text_field.pack()

            tk.Label(editor, text="People Involved (comma separated):").pack()
            people_entry = tk.Entry(editor)
            people_entry.insert(0, ", ".join(self.selected_node.people))
            people_entry.pack()

            tk.Label(editor, text="Node Progress:").pack()
            progress_var = tk.IntVar(value=self.selected_node.progress)
            progress_scale = tk.Scale(editor, from_=0, to=100, orient=tk.HORIZONTAL, variable=progress_var)
            progress_scale.pack()

            tk.Label(editor, text="Node Priority:").pack()
            priority_var = tk.StringVar(value=self.selected_node.priority)
            tk.Radiobutton(editor, text="Urgent", variable=priority_var, value="{}").pack()
            tk.Radiobutton(editor, text="Medium", variable=priority_var, value="[]").pack()
            tk.Radiobutton(editor, text="Low", variable=priority_var, value="()").pack()

            def save_changes():
                self.selected_node.title = title_entry.get()
                self.selected_node.text = text_field.get("1.0", tk.END).strip()
                self.selected_node.people = people_entry.get().split(", ")
                self.selected_node.progress = progress_var.get()
                self.selected_node.priority = priority_var.get()
                self.draw_tree()
                editor.destroy()

            tk.Button(editor, text="Save", command=save_changes).pack()

            def manage_files_and_comments():
                manage_window = tk.Toplevel(self.root)
                manage_window.title("Manage Files, Texts, and Comments")
                manage_window.geometry("400x400")

                tk.Label(manage_window, text="Manage Files, Texts, and Comments").pack()

                # Listbox para exibir e selecionar arquivos, textos e comentários
                listbox = tk.Listbox(manage_window, selectmode=tk.SINGLE, width=50, height=15)
                for i, comment in enumerate(self.selected_node.comments):
                    listbox.insert(tk.END, f"Comment {i+1}: {comment}")
                if self.selected_node.text:
                    listbox.insert(tk.END, f"Text: {self.selected_node.text}")
                if self.selected_node.files:
                    for file in self.selected_node.files:
                        listbox.insert(tk.END, f"File: {file}")

                listbox.pack()

                def open_item():
                    selected = listbox.curselection()
                    if selected:
                        index = selected[0]
                        item = listbox.get(index)
                        if item.startswith("Comment"):
                            comment = self.selected_node.comments[index]
                            simpledialog.messagebox.showinfo("Open Comment", f"Opening Comment: {comment}")
                        elif item.startswith("Text:"):
                            simpledialog.messagebox.showinfo("Text", self.selected_node.text)
                        elif item.startswith("File:"):
                            file = item.split("File: ")[1]
                            if os.path.isfile(file):
                                subprocess.Popen(['xdg-open', file], shell=True)
                            else:
                                simpledialog.messagebox.showwarning("File Not Found", f"The file {file} does not exist.")

                def edit_item():
                    selected = listbox.curselection()
                    if selected:
                        index = selected[0]
                        item = listbox.get(index)
                        if item.startswith("Comment"):
                            old_comment = self.selected_node.comments[index]
                            new_comment = simpledialog.askstring("Edit Comment", "Edit the comment:", initialvalue=old_comment)
                            if new_comment is not None:
                                self.selected_node.comments[index] = new_comment
                                listbox.delete(index)
                                listbox.insert(index, f"Comment {index+1}: {new_comment}")
                        elif item.startswith("Text:"):
                            new_text = simpledialog.askstring("Edit Text", "Edit the text:", initialvalue=self.selected_node.text)
                            if new_text is not None:
                                self.selected_node.text = new_text
                                listbox.delete(index)
                                listbox.insert(index, f"Text: {new_text}")
                        elif item.startswith("File:"):
                            file = item.split("File: ")[1]
                            if os.path.isfile(file):
                                new_file = filedialog.askopenfilename(initialfile=file)
                                if new_file:
                                    self.selected_node.files.remove(file)
                                    self.selected_node.files.append(new_file)
                                    listbox.delete(index)
                                    listbox.insert(index, f"File: {new_file}")

                def delete_item():
                    selected = listbox.curselection()
                    if selected:
                        index = selected[0]
                        item = listbox.get(index)
                        if item.startswith("Comment"):
                            del self.selected_node.comments[index]
                        elif item.startswith("Text:"):
                            self.selected_node.text = ""
                        elif item.startswith("File:"):
                            file = item.split("File: ")[1]
                            if file in self.selected_node.files:
                                self.selected_node.files.remove(file)
                        listbox.delete(index)

                tk.Button(manage_window, text="Open", command=open_item).pack()
                tk.Button(manage_window, text="Edit", command=edit_item).pack()
                tk.Button(manage_window, text="Delete", command=delete_item).pack()

            tk.Button(editor, text="Manage Files/Comments", command=manage_files_and_comments).pack()

            # Novo botão para adicionar arquivos
            def add_file():
                file = filedialog.askopenfilename()
                if file:
                    self.selected_node.files.append(file)
                    self.draw_tree()

            tk.Button(editor, text="Add File", command=add_file).pack()

            tk.Button(editor, text="Cancel", command=editor.destroy).pack()

    def delete_node(self):
        if self.selected_node:
            if messagebox.askyesno("Confirm", "Are you sure you want to delete this node?"):
                self.nodes.remove(self.selected_node)
                for node in self.nodes:
                    if self.selected_node in node.children:
                        node.children.remove(self.selected_node)
                self.draw_tree()

    def save_tree(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            data = [node.to_dict() for node in self.nodes]
            with open(file_path, 'w') as file:
                json.dump(data, file)

    def load_tree(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.nodes = [TreeNode.from_dict(node) for node in data]
                self.draw_tree()

    def search_keyword(self):
        keyword = self.search_entry.get()
        if keyword:
            for node in self.nodes:
                if keyword.lower() in node.title.lower():
                    self.canvas.tag_raise(self.node_ids[node])
                    self.canvas.focus_set()
                    self.canvas.scan_dragto(node.x, node.y)
                    break

class TreeNode:
    def __init__(self, title, x=0, y=0, priority="()", progress=0, text="", people=None, comments=None, files=None):
        self.title = title
        self.x = x
        self.y = y
        self.priority = priority
        self.progress = progress
        self.text = text
        self.people = people if people else []
        self.comments = comments if comments else []
        self.files = files if files else []
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def to_dict(self):
        return {
            "title": self.title,
            "x": self.x,
            "y": self.y,
            "priority": self.priority,
            "progress": self.progress,
            "text": self.text,
            "people": self.people,
            "comments": self.comments,
            "files": self.files,
            "children": [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data):
        node = cls(
            title=data["title"],
            x=data["x"],
            y=data["y"],
            priority=data["priority"],
            progress=data["progress"],
            text=data["text"],
            people=data["people"],
            comments=data["comments"],
            files=data["files"]
        )
        for child_data in data["children"]:
            child_node = cls.from_dict(child_data)
            node.add_child(child_node)
        return node

if __name__ == "__main__":
    root = tk.Tk()
    app = TreeApp(root)
    root.mainloop()
