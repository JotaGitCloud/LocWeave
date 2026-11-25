import customtkinter as ctk
from tkinter import filedialog, messagebox
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models
from app.services.extraction import extract_file

Base.metadata.create_all(bind=engine)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ProjectCard(ctk.CTkFrame):
    def __init__(self, master, project, on_import_success=None, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        self.project = project
        self.on_import_success = on_import_success
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text=project.name,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        desc = project.description or "Sin descripción"
        ctk.CTkLabel(
            self, text=desc,
            font=ctk.CTkFont(size=12),
            text_color="gray65",
            anchor="w",
            wraplength=320
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            self,
            text=f"ID: {project.id}  •  Creado: {project.created_at.strftime('%Y-%m-%d') if project.created_at else 'N/A'}",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            anchor="w"
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Import Strings",
            height=32,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.import_strings
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="Open Editor",
            height=32,
            fg_color="gray30",
            hover_color="gray40",
            command=lambda: print(f"Abrir editor: {project.name}")
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def import_strings(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de strings",
            filetypes=[
                ("Archivos soportados", "*.json *.txt"),
                ("JSON", "*.json"),
                ("Texto", "*.txt"),
                ("Todos", "*.*")
            ]
        )
        if not file_path:
            return

        db: Session = SessionLocal()
        try:
            count = extract_file(file_path, self.project.id, db)
            messagebox.showinfo(
                "Importación exitosa",
                f"Se importaron {count} strings al proyecto \"{self.project.name}\"."
            )
            if self.on_import_success:
                self.on_import_success()
        except Exception as e:
            messagebox.showerror("Error al importar", str(e))
        finally:
            db.close()

class NewProjectDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        self.title("Nuevo Proyecto")
        self.geometry("420x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="Crear nuevo proyecto", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))

        ctk.CTkLabel(self, text="Nombre del proyecto").pack(anchor="w", padx=30)
        self.name_entry = ctk.CTkEntry(self, width=360, height=36, placeholder_text="Ej: Mi Juego Indie")
        self.name_entry.pack(padx=30, pady=(4, 12))

        ctk.CTkLabel(self, text="Descripción (opcional)").pack(anchor="w", padx=30)
        self.desc_entry = ctk.CTkEntry(self, width=360, height=36, placeholder_text="Breve descripción")
        self.desc_entry.pack(padx=30, pady=(4, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=5)

        ctk.CTkButton(btn_frame, text="Cancelar", width=120, fg_color="gray30", hover_color="gray40", command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Crear Proyecto", width=140, command=self.create_project).pack(side="left", padx=8)

    def create_project(self):
        name = self.name_entry.get().strip()
        description = self.desc_entry.get().strip() or None
        if not name:
            return

        db = SessionLocal()
        try:
            project = models.Project(name=name, description=description)
            db.add(project)
            db.commit()
            self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            db.rollback()
        finally:
            db.close()

class LocWeaveApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LocWeave - Localización para Videojuegos")
        self.geometry("1100x700")
        self.minsize(950, 600)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self.sidebar, text="LocWeave", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=18, pady=(22, 2), sticky="w")
        ctk.CTkLabel(self.sidebar, text="Studio v0.1.0", font=ctk.CTkFont(size=11), text_color="gray60").grid(row=1, column=0, padx=18, pady=(0, 22), sticky="w")

        self.nav_buttons = {}
        for i, (name, cmd) in enumerate([
            ("Projects", self.show_projects),
            ("Texts", self.show_texts),
            ("Languages", self.show_languages),
            ("Settings", self.show_settings),
        ]):
            btn = ctk.CTkButton(self.sidebar, text=name, anchor="w", height=36, fg_color="transparent", text_color="gray80", hover_color="#2a2a2a", command=cmd)
            btn.grid(row=i+2, column=0, padx=10, pady=3, sticky="ew")
            self.nav_buttons[name] = btn

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="#111111")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self.show_projects()

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def highlight_nav(self, active):
        for name, btn in self.nav_buttons.items():
            if name == active:
                btn.configure(fg_color="#2a2a2a", text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color="gray80")

    def get_projects(self):
        db = SessionLocal()
        try:
            return db.query(models.Project).order_by(models.Project.id.desc()).all()
        finally:
            db.close()

    def show_projects(self):
        self.clear_content()
        self.highlight_nav("Projects")

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 6))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Game Projects", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="+ New Project", width=140, height=34, fg_color="#3b82f6", hover_color="#2563eb", command=self.open_new_project_dialog).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(self.content, text="Crea proyectos e importa strings desde JSON o TXT.", font=ctk.CTkFont(size=13), text_color="gray60").grid(row=1, column=0, sticky="w", padx=24, pady=(0, 12))

        self.grid_frame = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        self.grid_frame.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.grid_frame.grid_columnconfigure((0, 1), weight=1)

        self.render_projects()

    def render_projects(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        projects = self.get_projects()
        if not projects:
            ctk.CTkLabel(self.grid_frame, text="No hay proyectos todavía.\nHaz clic en “+ New Project” para crear el primero.", font=ctk.CTkFont(size=14), text_color="gray50").grid(row=0, column=0, columnspan=2, pady=60)
            return

        for i, project in enumerate(projects):
            card = ProjectCard(self.grid_frame, project, on_import_success=self.render_projects)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")

    def open_new_project_dialog(self):
        NewProjectDialog(self, on_success=self.render_projects)

    def show_texts(self):
        self.clear_content()
        self.highlight_nav("Texts")
        ctk.CTkLabel(self.content, text="Sección Texts (próximamente)", font=ctk.CTkFont(size=16)).pack(expand=True)

    def show_languages(self):
        self.clear_content()
        self.highlight_nav("Languages")
        ctk.CTkLabel(self.content, text="Sección Languages (próximamente)", font=ctk.CTkFont(size=16)).pack(expand=True)

    def show_settings(self):
        self.clear_content()
        self.highlight_nav("Settings")
        ctk.CTkLabel(self.content, text="Sección Settings (próximamente)", font=ctk.CTkFont(size=16)).pack(expand=True)

if __name__ == "__main__":
    app = LocWeaveApp()
    app.mainloop()