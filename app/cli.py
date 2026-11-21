"""Interfaz de línea de comandos (útil para automatizar y para probar sin interfaz gráfica)."""
import argparse
import sys

from .config import db_path
from .database import Database
from .languages import LANGUAGES
from .parsers import FormatError
from .providers import DEFAULT_PROVIDER, ProviderError, provider_names
from .services.pipeline import PipelineError
from .services.project_service import LocWeaveService


def _progress(msg, done, total):
    print(f"  {msg} ({done}/{total})" if total else f"  {msg}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="locweave", description="LocWeave: localización de videojuegos indie")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("import", help="Importar un archivo de textos como proyecto")
    p.add_argument("file")
    p.add_argument("--name", default="")
    p.add_argument("--src", default="auto", help="idioma de origen o 'auto'")
    p.add_argument("--tgt", default="es", choices=list(LANGUAGES))

    p = sub.add_parser("translate", help="Traducir los segmentos de un proyecto")
    p.add_argument("project", type=int)
    p.add_argument("--provider", default=DEFAULT_PROVIDER, choices=provider_names())
    p.add_argument("--all", action="store_true", help="retraducir todo lo que no esté revisado")

    p = sub.add_parser("export", help="Exportar el archivo traducido")
    p.add_argument("project", type=int)
    p.add_argument("output")

    sub.add_parser("list", help="Listar proyectos")
    p = sub.add_parser("show", help="Mostrar los segmentos de un proyecto")
    p.add_argument("project", type=int)

    args = parser.parse_args(argv)
    service = LocWeaveService(Database(db_path()))
    try:
        if args.cmd == "import":
            project = service.import_file(args.file, args.name, args.src, args.tgt, _progress)
            print(f"Proyecto {project.id} creado: {project.name} ({project.source_lang} → {project.target_lang}, "
                  f"{service.stats(project.id)['total']} segmentos)")
        elif args.cmd == "translate":
            print(service.translate(args.project, args.provider, not args.all, _progress))
        elif args.cmd == "export":
            print(service.export(args.project, args.output))
        elif args.cmd == "list":
            for p in service.list_projects():
                print(f"{p.id:>3}  {p.name}  [{p.source_lang}→{p.target_lang}]  {p.file_format}")
        elif args.cmd == "show":
            for s in service.segments(args.project):
                print(f"{s.id:>4} [{s.status}] {s.key}\n      {s.source_text!r}\n   →  {s.target_text!r}")
    except (PipelineError, ProviderError, FormatError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
