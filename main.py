from tkinter import Tk
from gui.app import ArticleApp

def main():
    root = Tk()
    app = ArticleApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
