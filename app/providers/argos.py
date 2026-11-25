"""Motor local gratuito basado en Argos Translate (sin cuenta, sin claves de API).

Requiere internet solo una vez por par de idiomas, para descargar los modelos.
Si no existe un modelo directo (p. ej. ja->es), Argos usa el inglés como puente (ja->en->es).
"""
from typing import List, Optional, Tuple

from .base import ProgressFn, ProviderError, TranslationProvider


class ArgosProvider(TranslationProvider):
    name = "argos"
    label = "Argos Translate (local, gratis)"

    @staticmethod
    def _import():
        from .stanza_stub import install_if_missing

        install_if_missing()   # variante liviana: Argos importa stanza pero no lo necesita
        try:
            import argostranslate.package as package
            import argostranslate.translate as translate
            return package, translate
        except ImportError as exc:
            raise ProviderError(
                "Argos Translate no está instalado. Ejecuta: pip install argostranslate"
            ) from exc

    def is_available(self) -> Tuple[bool, str]:
        try:
            self._import()
            return True, ""
        except ProviderError as exc:
            return False, str(exc)

    def _get_translation(self, source_lang: str, target_lang: str):
        _, translate = self._import()
        langs = translate.get_installed_languages()
        src = next((lang for lang in langs if lang.code == source_lang), None)
        tgt = next((lang for lang in langs if lang.code == target_lang), None)
        if not src or not tgt:
            return None
        return src.get_translation(tgt)

    def is_pair_ready(self, source_lang: str, target_lang: str) -> bool:
        return self._get_translation(source_lang, target_lang) is not None

    def prepare(self, source_lang: str, target_lang: str, progress: Optional[ProgressFn] = None) -> None:
        if self.is_pair_ready(source_lang, target_lang):
            return
        package, _ = self._import()
        if progress:
            progress("Descargando índice de modelos…", 0, 1)
        try:
            package.update_package_index()
        except Exception as exc:  # error de red
            raise ProviderError(
                "No se pudo descargar el índice de modelos. Conéctate a internet una vez para "
                f"instalar los idiomas. Detalle: {exc}"
            ) from exc
        available = package.get_available_packages()

        def find(a: str, b: str):
            return next((p for p in available if p.from_code == a and p.to_code == b), None)

        hops = [(source_lang, target_lang)] if find(source_lang, target_lang) else \
            [(source_lang, "en"), ("en", target_lang)]
        packages = []
        for a, b in hops:
            pkg = find(a, b)
            if pkg is None:
                raise ProviderError(f"Argos no tiene un modelo para {a} → {b}.")
            packages.append(pkg)
        for i, pkg in enumerate(packages):
            if progress:
                progress(f"Instalando modelo {pkg.from_code} → {pkg.to_code}…", i, len(packages))
            package.install_from_path(pkg.download())
        if not self.is_pair_ready(source_lang, target_lang):
            raise ProviderError(f"No se pudo dejar listo el par {source_lang} → {target_lang}.")

    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        translation = self._get_translation(source_lang, target_lang)
        if translation is None:
            raise ProviderError(
                f"El par {source_lang} → {target_lang} no está instalado. Usa «Preparar idiomas» primero."
            )
        return [translation.translate(t) for t in texts]
