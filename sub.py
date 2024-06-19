import tkinter as tk

root = tk.Tk()
root.title("テストウィンドウ")
root.geometry("200x100")  # ウィンドウサイズを200x100ピクセルに設定

label = tk.Label(root, text="Hello, Tkinter!")
label.pack()

root.mainloop()
