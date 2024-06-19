import tkinter as tk
from tkinter import simpledialog, messagebox

def login():
    window = tk.Toplevel(root)
    window.title("ログイン")
    
    tk.Label(window, text="メールアドレス").pack()
    email_entry = tk.Entry(window)
    email_entry.pack()
    
    tk.Label(window, text="パスワード").pack()
    password_entry = tk.Entry(window, show="*")
    password_entry.pack()
    
    def attempt_login():
        # ここでログインの検証を行います（例: データベースとの照合）
        # 仮にログインが成功したと仮定します
        messagebox.showinfo("ログイン成功", "ログインに成功しました！")
    
    tk.Button(window, text="ログイン", command=attempt_login).pack()

def signup():
    window = tk.Toplevel(root)
    window.title("新規登録")
    
    tk.Label(window, text="ユーザー名").pack()
    username_entry = tk.Entry(window)
    username_entry.pack()
    
    tk.Label(window, text="メールアドレス").pack()
    email_entry = tk.Entry(window)
    email_entry.pack()
    
    tk.Label(window, text="パスワード").pack()
    password_entry = tk.Entry(window, show="*")
    password_entry.pack()
    
    def attempt_signup():
        # ここで新規登録の検証を行います（例: データベースへの保存）
        # 仮に新規登録が成功したと仮定します
        messagebox.showinfo("新規登録成功", "新規登録に成功しました！")
    
    tk.Button(window, text="登録", command=attempt_signup).pack()

root = tk.Tk()
root.title("トップ画面")

tk.Button(root, text="ログイン", command=login).pack(fill=tk.X)
tk.Button(root, text="新規登録", command=signup).pack(fill=tk.X)

root.mainloop()
